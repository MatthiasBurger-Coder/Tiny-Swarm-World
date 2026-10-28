"""Read-only source admission, resource checks and pinned transition validation."""
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tomllib

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.models import ProductIdentity
from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductPlan, ProductRelease, SOURCE_RELEASE, admit_release_pair
from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import require_settled_updates
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import decode_manifest


def plan(installation, target):
    require_settled_updates(installation.root)
    _clean_source(installation, allow_external=True)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import prepare, reserve_bytes

    binding = prepare(installation)
    snapshot = installation.manifests.load()
    if any(item.startswith('interrupted_write') for item in snapshot.diagnostics):
        raise LifecycleStateError('Interrupted manifest write requires review before product upgrade.')
    manifest = snapshot.manifest
    if manifest is None:
        if installation.adoption_file is None:
            raise LifecycleStateError('Legacy installation needs an explicitly inventoried --adoption-manifest; no state inferred.')
        try:
            manifest = decode_manifest(Path(installation.adoption_file).read_bytes())
        except OSError:
            raise LifecycleStateError('Cannot read adoption manifest; supply a verified inventory without credential values.') from None
    installation.catalog.load().validate_manifest(manifest)
    source = installation._source_identity()
    if manifest.product != source.product:
        raise LifecycleStateError('Installation inventory differs from actual source revision/lock/release; inspect explicit adoption.')
    target_release, changes = installation.source.resolve(target)
    admit_release_pair(source, target_release)
    plan = ProductPlan(source=source, target=target_release, manifest=manifest, manifest_token=snapshot.token,
                       adoption=snapshot.manifest is None, configuration_changes=changes,
                       configuration_source=binding, resource_bytes=2147483648 + reserve_bytes(binding))
    installation.validate(plan)
    return plan

def _source_identity(installation):
    try:
        revision = installation._command(('git', 'rev-parse', '--verify', 'HEAD'))
        package = tomllib.loads((installation.root / 'pyproject.toml').read_text())['project']['version']
        lock = 'sha256:' + hashlib.sha256((installation.root / 'requirements.lock').read_bytes()).hexdigest()
        return ProductRelease(product=ProductIdentity(release=SOURCE_RELEASE, revision=revision, dependency_lock=lock),
                              package_version=package)
    except (OSError, ValueError, KeyError):
        raise LifecycleStateError('Source checkout identity cannot be verified.') from None

def _clean_source(installation, *, allow_external=False):
    configured_infra = os.environ.get('TSW_INFRA_ROOT')
    if not allow_external and configured_infra and Path(configured_infra).expanduser().resolve() != installation.root / 'infra':
        raise LifecycleStateError('Product controller requires anchor infrastructure; unset TSW_INFRA_ROOT and inventory effective overrides before upgrading.')
    if installation._command(('git', 'status', '--porcelain', '--untracked-files=normal')):
        raise LifecycleStateError('Dirty checkout or unrelated untracked files; preserve operator work and commit or move it before upgrading.')
    if installation._command(('git', 'rev-parse', '--show-toplevel')) != str(installation.root):
        raise LifecycleStateError('Product anchor must be the actual prepared checkout root.')
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OFFICIAL_REPOSITORY

    if installation._command(('git', 'remote', 'get-url', 'origin')) != OFFICIAL_REPOSITORY:
        raise LifecycleStateError('Source checkout must identify the official product repository without embedded credentials.')
    for name in ('.tiny-swarm-world', '.tiny-swarm-world/product', 'infra'):
        if (installation.root / name).is_symlink():
            raise LifecycleStateError('Product/state/configuration symlinks require manual review; no upgrade attempted.')
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_paths import require_private_product_paths

    require_private_product_paths(installation)

def validate(installation, plan):
    require_settled_updates(installation.root)
    _clean_source(installation, allow_external=plan.configuration_source is not None)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import validate as validate_configuration

    validate_configuration(installation, plan)
    if installation._source_identity() != plan.source:
        raise LifecycleStateError('Source checkout changed since admission; preserve checkpoint and inspect drift.')
    resolved, changes = installation.source.resolve(plan.target.product.release)
    if resolved != plan.target or changes != plan.configuration_changes:
        raise LifecycleStateError('Release ref/content moved; pinned operation cannot resume against a different target.')
    installation._host_and_resources(plan)
    snapshot = installation.manifests.load()
    expected = plan.manifest.model_copy(update={'product': plan.target.product})
    if not ((snapshot.token == plan.manifest_token and snapshot.manifest == (None if plan.adoption else plan.manifest))
            or snapshot.manifest == expected):
        raise LifecycleStateError('Installation state changed since product admission.')

def _host_and_resources(installation, plan):
    from tiny_swarm_world.infrastructure.adapters.host.host_environment_detector import HostEnvironmentDetector
    from tiny_swarm_world.domain.host_environment import HostEnvironmentKind

    detected = HostEnvironmentDetector().detect().environment
    expected = {'native-linux': HostEnvironmentKind.NATIVE_LINUX, 'wsl2': HostEnvironmentKind.WSL2}[plan.manifest.host]
    if detected != expected or sys.version_info[:2] != (3, 12):
        raise LifecycleStateError('Product upgrade requires matching Linux/WSL2 inventory and Python 3.12.')
    if shutil.disk_usage(installation.root).free < plan.resource_bytes:
        raise LifecycleStateError('Product staging requires at least 2 GiB free space; old checkout/environment are retained.')

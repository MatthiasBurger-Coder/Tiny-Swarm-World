"""Explicit effective-input authority for the existing prepared product lifecycle."""
import os
from pathlib import Path
import re
import time
from uuid import uuid4

from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductConfigurationSource
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_capture import (
    capture, create_binding, load_record,
)
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_validation import (
    MAX_BYTES, MAX_FILE_BYTES, read_tree, refused, require_capacity, validate_policy,
)
from tiny_swarm_world.infrastructure.process.runner import ProcessRunnerError


def _external(installation):
    configured = os.environ.get('TSW_INFRA_ROOT')
    if not configured:
        return None
    path = Path(configured).expanduser()
    # Never canonicalize away a symlink before descriptor traversal.
    if not path.is_absolute() or path.anchor != '/' or '..' in path.parts:
        raise refused()
    return None if path == installation.root / 'infra' else path


def _matches_git_blob(installation, content, digest, deadline):
    """Compare Git's canonical object ID without writing or filtering the payload."""
    if (not isinstance(content, bytes) or len(content) > MAX_FILE_BYTES
            or re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', digest) is None):
        raise refused()
    remaining = min(30.0, deadline - time.monotonic())
    if remaining <= 0:
        raise refused()
    try:
        result = installation.runner.run_bytes(('git', 'hash-object', '--no-filters', '--stdin'),
            cwd=installation.root, input=content, timeout=remaining, shell=False)
        if (result.returncode != 0 or result.stderr != b'' or not isinstance(result.stdout, bytes)
                or len(result.stdout) != len(digest) + 1
                or re.fullmatch(rb'(?:[0-9a-f]{40}|[0-9a-f]{64})\n', result.stdout) is None
                or time.monotonic() >= deadline):
            raise refused()
        return result.stdout == digest.encode('ascii') + b'\n'
    except (ProcessRunnerError, OSError, ValueError, TypeError):
        raise refused() from None


def _official(installation):
    tree = read_tree(installation.root / 'infra', private=False)
    listing = installation._command(('git', 'ls-tree', '-r', 'HEAD', '--', 'infra'))
    tracked = {}
    try:
        for line in listing.splitlines():
            header, name = line.split('\t', 1)
            mode, kind, digest = header.split()
            member = str(Path(name).relative_to('infra'))
            if mode not in ('100644', '100755') or kind != 'blob' or member in tracked:
                raise refused()
            tracked[member] = (mode, digest)
        if set(tracked) != set(tree.files):
            raise refused()
        directories = {parent.as_posix() for member in tracked for parent in Path(member).parents if parent != Path('.')}
        if set(tree.members) != set(tracked) | directories:
            raise refused()
        deadline = time.monotonic() + 30.0
        for member, content in tree.files.items():
            mode, digest = tracked[member]
            if (not _matches_git_blob(installation, content, digest, deadline)
                    or bool(tree.members[member][3] & 0o111) != (mode == '100755')):
                raise refused()
    except (ValueError, KeyError):
        raise refused() from None
    return tree


def _source_tree(installation, path):
    from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
    from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind
    from tiny_swarm_world.infrastructure.adapters.host.host_environment_detector import HostEnvironmentDetector
    from tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector import ProjectFilesystemInspector

    try:
        if path.anchor != '/' or path != path.resolve(strict=True):
            raise refused()
    except (OSError, RuntimeError):
        raise refused() from None
    if path.is_relative_to(installation.root) or installation.root.is_relative_to(path):
        raise refused()
    host_environment = HostEnvironmentDetector().detect().environment
    allowed_filesystem = {
        HostEnvironmentKind.NATIVE_LINUX: ProjectFilesystemKind.NATIVE_LINUX,
        HostEnvironmentKind.WSL2: ProjectFilesystemKind.WSL_LINUX,
    }.get(host_environment)
    if allowed_filesystem is None:
        raise refused()
    filesystem = ProjectFilesystemInspector().inspect(str(path), host_environment)
    if filesystem.kind is not allowed_filesystem:
        raise refused()
    tree = read_tree(path)
    for protected in (installation.root, installation.root / 'infra', installation.state):
        if protected.exists() and tree.root[:2] == [protected.stat().st_dev, protected.stat().st_ino]:
            raise refused()
    validate_policy(_official(installation), tree)
    require_capacity(tree, path)
    return tree


def prepare(installation):
    """Read-only admission. Persist neither input bytes nor binding metadata."""
    path = _external(installation)
    inputs = installation.state / 'inputs'
    if inputs.exists() and any(inputs.iterdir()):
        # No checkpoint owns a fresh plan yet: never adopt orphan input records.
        raise refused()
    if path is None:
        return None
    tree = _source_tree(installation, path)
    binding = ProductConfigurationSource(reference='effective-infra-' + uuid4().hex)
    installation._configuration_candidate = (binding, path, tree)
    return binding


def _directory(installation, plan):
    binding = plan.configuration_source
    if binding is None or not binding.reference.startswith('effective-infra-'):
        raise refused()
    return installation.state / 'inputs' / binding.reference


def _candidate(installation, plan):
    candidate = getattr(installation, '_configuration_candidate', None)
    if candidate is None or candidate[0] != plan.configuration_source:
        raise refused()
    _, path, tree = candidate
    if _external(installation) != path:
        raise refused()
    current = _source_tree(installation, path)
    if current.metadata() != tree.metadata() or current.files != tree.files:
        raise refused()
    return path, tree


def bind(installation, plan):
    """Called only by the journal after consent and authenticated admission."""
    if plan.configuration_source is None:
        return
    directory = _directory(installation, plan)
    if directory.exists() or directory.is_symlink():
        validate(installation, plan)
        return
    path, tree = _candidate(installation, plan)
    record = {'version': 1, 'reference': plan.configuration_source.reference,
              'source_revision': plan.source.product.revision, 'target_revision': plan.target.product.revision,
              'source_path': str(path), 'source_metadata': tree.metadata(),
              'capture_state': 'admitted', 'snapshot_metadata': None, 'pending_roots': {}}
    create_binding(directory, record)
    installation._configuration_candidate = None


def _bound(installation, plan):
    directory = _directory(installation, plan)
    record = load_record(directory)
    if (record['reference'] != plan.configuration_source.reference
            or record['source_revision'] != plan.source.product.revision
            or record['target_revision'] != plan.target.product.revision):
        raise refused()
    path = Path(record['source_path'])
    ambient = _external(installation)
    # Explicit anchor also counts as repointing; unset means continue original.
    if os.environ.get('TSW_INFRA_ROOT') and (ambient is None or ambient != path):
        raise refused()
    tree = _source_tree(installation, path)
    if tree.metadata() != record['source_metadata']:
        raise refused()
    return directory, record, tree


def validate(installation, plan):
    if plan.configuration_source is None:
        if _external(installation) is not None:
            raise refused()
        return
    if plan.resource_bytes != 2147483648 + reserve_bytes(plan.configuration_source):
        raise refused()
    directory = _directory(installation, plan)
    if not directory.exists():
        _candidate(installation, plan)
        return
    directory, record, tree = _bound(installation, plan)
    if record['capture_state'] == 'captured':
        capture(directory, record, tree)
    elif record['capture_state'] == 'capturing':
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_capture import validate_partial

        validate_partial(directory, record, tree)


def capture_source(installation, plan):
    if plan.configuration_source is not None:
        directory, record, tree = _bound(installation, plan)
        return capture(directory, record, tree)
    return installation.root / 'infra'


def effective_source(installation, plan):
    if plan.configuration_source is None:
        return installation.root / 'infra'
    directory, record, tree = _bound(installation, plan)
    if record['capture_state'] != 'captured':
        raise refused()
    return capture(directory, record, tree)


def reserve_bytes(binding):
    return 2 * MAX_BYTES if binding is not None else 0


def runtime_source(installation, plan):
    """Resolve the validated original/captured/migrated authority at this phase."""
    validate(installation, plan)
    managed = installation.state / 'infra' / plan.target.product.revision
    if managed.exists() or managed.is_symlink():
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration import verify_product_infra

        verify_product_infra(installation, plan)
        return managed
    if _directory(installation, plan).exists():
        directory, record, tree = _bound(installation, plan)
        if record['capture_state'] == 'captured':
            return capture(directory, record, tree)
        return Path(record['source_path'])
    return _candidate(installation, plan)[0]


def prepare_pending(installation, plan, pending, kind):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_capture import prepare_pending as prepare_owned

    directory, record, _ = _bound(installation, plan)
    installation._host_and_resources(plan)
    prepare_owned(directory, record, pending, kind)


def publish_pending(installation, plan, pending, destination, kind):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_capture import publish_pending as publish_owned

    directory, record, _ = _bound(installation, plan)
    publish_owned(directory, record, pending, destination, kind)

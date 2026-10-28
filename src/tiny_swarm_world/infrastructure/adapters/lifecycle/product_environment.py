"""Isolated product environment and atomic activation details."""
import os
import shlex
import sys
import tomllib
import hashlib

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OFFICIAL_REPOSITORY

GIT_STATUS = ('git', 'status', '--porcelain', '--untracked-files=normal')

def stage(installation, plan):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_paths import require_private_product_paths

    require_private_product_paths(installation)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import capture_source

    capture_source(installation, plan)
    destination = installation.directory(plan)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.is_symlink():
        raise LifecycleStateError('Staged product path must not be a symlink.')
    if not destination.exists():
        _clone_release(installation, plan)
    origin = installation._command(('git', 'remote', 'get-url', 'origin'), cwd=destination)
    if origin != OFFICIAL_REPOSITORY:
        raise LifecycleStateError('Staged product origin is not the official repository.')
    if installation._command(GIT_STATUS, cwd=destination):
        raise LifecycleStateError('Staged operator changes must be inspected before checkout.')
    installation._verify_checkout(plan)
    python = destination / '.venv' / 'bin' / 'python'
    if not python.exists():
        installation._command((sys.executable, '-m', 'venv', str(destination / '.venv')), timeout=120)
    installation._command((str(python), '-m', 'pip', 'install', '--require-hashes', '-r', str(destination / 'requirements.lock')), timeout=600)
    # Code loads from the immutable checkout through the launcher; no editable install.
    installation.verify_product(plan)


def _clone_release(installation, plan):
    from uuid import uuid4

    staging = installation.state / 'staging'
    staging.mkdir(parents=True, exist_ok=True, mode=0o700)
    pending = staging / plan.target.product.revision
    if plan.configuration_source is not None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import prepare_pending

        prepare_pending(installation, plan, pending, 'code')
    elif pending.exists():
        # Preserve an interrupted clone/checkout, then rebuild only this private staging slot.
        pending.rename(staging / (plan.target.product.revision + '.interrupted-' + uuid4().hex))
    installation._command(('git', 'clone', '--filter=blob:none', '--branch', plan.target.product.release,
                           OFFICIAL_REPOSITORY, str(pending)), timeout=300)
    revision = installation._command(('git', 'rev-parse', 'HEAD'), cwd=pending)
    dirty = installation._command(GIT_STATUS, cwd=pending)
    if revision != plan.target.product.revision or dirty:
        raise LifecycleStateError('Staged release ref changed or checkout incomplete; preserve staged clone for review.')
    if plan.configuration_source is not None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import publish_pending

        publish_pending(installation, plan, pending, installation.directory(plan), 'code')
    else:
        os.replace(pending, installation.directory(plan))
    descriptor = os.open(installation.directory(plan).parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

def _verify_checkout(installation, plan):
    destination = installation.directory(plan)
    if installation._command(('git', 'rev-parse', 'HEAD'), cwd=destination) != plan.target.product.revision:
        raise LifecycleStateError('Staged product revision mismatch.')
    if installation._command(GIT_STATUS, cwd=destination):
        raise LifecycleStateError('Staged product checkout is dirty; preserve it for inspection.')
    try:
        version = tomllib.loads((destination / 'pyproject.toml').read_text())['project']['version']
        lock = 'sha256:' + hashlib.sha256((destination / 'requirements.lock').read_bytes()).hexdigest()
        if version != plan.target.package_version or lock != plan.target.product.dependency_lock:
            raise ValueError
    except (OSError, ValueError, KeyError):
        raise LifecycleStateError('Staged product metadata/lock mismatch.') from None

def verify_product(installation, plan):
    installation._verify_checkout(plan)
    destination = installation.directory(plan)
    python = destination / '.venv/bin/python'
    installation._command((str(python), '-m', 'pip', 'check'), cwd=destination)
    installation._command((str(python), '-c',
        'import importlib.metadata,pathlib,re,sys; '
        'pins=re.findall(r"^([A-Za-z0-9_.-]+)==([0-9][A-Za-z0-9.+-]*)",pathlib.Path("requirements.lock").read_text(),re.M); '
        'sys.exit(0 if pins and all(importlib.metadata.version(n)==v for n,v in pins) else 1)'), cwd=destination)
    output = installation._command((str(python), '-c',
        'import pathlib,sys,tomllib; import tiny_swarm_world; '
        'sys.version_info[:2] == (3,12) or sys.exit(1); '
        'print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])'),
        cwd=destination, env={**os.environ, 'PYTHONPATH': str(destination / 'src')})
    if output != plan.target.package_version:
        raise LifecycleStateError('Executing target environment reports the wrong product version.')

def activate(installation, plan):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration import verify_product_infra
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_paths import require_private_product_paths

    require_private_product_paths(installation)
    verify_product_infra(installation, plan)
    destination = installation.directory(plan)
    configuration = installation.state / 'infra' / plan.target.product.revision
    if not configuration.is_dir():
        raise LifecycleStateError('Protected configuration migration is missing.')
    launcher = installation.state / 'tiny-swarm-world'
    active = installation.state / 'active'
    expected_activation = installation.state / 'activations' / plan.target.product.revision
    if (active.exists() or active.is_symlink()) and (not active.is_symlink() or active.resolve() != expected_activation):
        raise LifecycleStateError('Unrelated active product pointer; preserve it and inspect before switching.')
    if launcher.is_symlink():
        raise LifecycleStateError('Managed launcher must not be a symlink.')
    content = ('#!/bin/sh\n'
               f'export TSW_REPOSITORY_ROOT={shlex.quote(str(installation.root))}\n'
               f'export TSW_INFRA_ROOT={shlex.quote(str(installation.state / "active" / "infra"))}\n'
               f'export PYTHONPATH={shlex.quote(str(installation.state / "active" / "code" / "src"))}\n'
               f'exec {shlex.quote(str(installation.state / "active" / "code" / ".venv/bin/python"))} -m tiny_swarm_world "$@"\n')
    JsonManifestRepository(launcher)._replace(content.encode())
    launcher.chmod(0o700)
    activation = installation.state / 'activations' / plan.target.product.revision
    activation.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, target in (('code', destination), ('infra', configuration)):
        link = activation / name
        if not link.exists() and not link.is_symlink():
            link.symlink_to(target, target_is_directory=True)
        if link.resolve() != target:
            raise LifecycleStateError('Activation path differs from the pinned product/configuration.')
    temporary = installation.state / '.active-next'
    if temporary.is_symlink():
        temporary.unlink()
    temporary.symlink_to(activation, target_is_directory=True)
    os.replace(temporary, installation.state / 'active')
    descriptor = os.open(installation.state, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    installation.verify_active(plan)

def verify_active(installation, plan):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration import verify_product_infra

    verify_product_infra(installation, plan)
    active = installation.state / 'active'
    if (not active.is_symlink() or (active / 'code').resolve() != installation.directory(plan)
            or (active / 'infra').resolve() != installation.state / 'infra' / plan.target.product.revision):
        raise LifecycleStateError('Product activation drift; inspect original checkpoint before retrying.')

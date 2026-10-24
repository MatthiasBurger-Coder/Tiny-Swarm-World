"""Ordered protected-infra migration without overwriting operator assets."""
import os
from pathlib import Path
import shutil

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


def migrate_product_infra(installation, plan):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_paths import require_private_product_paths

    require_private_product_paths(installation)
    source = installation.root / 'infra'
    target = installation.directory(plan) / 'infra'
    destination = installation.state / 'infra' / plan.target.product.revision
    temporary = destination.with_name(destination.name + '.pending')
    if destination.exists():
        verify_product_infra(installation, plan)
        return
    if temporary.exists():
        if temporary.is_symlink() or any(path.is_symlink() for path in temporary.rglob('*')):
            raise LifecycleStateError('Interrupted migration contains unexpected symlinks; preserve it for review.')
        # Only discard this operation's incomplete private copy; original infra is untouched.
        shutil.rmtree(temporary)
    if any(path.is_symlink() for path in source.rglob('*')):
        raise LifecycleStateError('Protected infrastructure contains symlinks; inspect paths before migration.')
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    shutil.copytree(source, temporary)
    for path in temporary.rglob('*'):
        path.chmod(0o700 if path.is_dir() or path.stat().st_mode & 0o111 else 0o600)
    temporary.chmod(0o700)
    for relative in plan.configuration_changes:
        member = Path(relative)
        if member.is_absolute() or '..' in member.parts or member.parts[0] != 'infra':
            raise LifecycleStateError('Release configuration path is unsafe.')
        incoming = target / member.relative_to('infra')
        outgoing = temporary / member.relative_to('infra')
        if not incoming.is_file() or incoming.is_symlink():
            raise LifecycleStateError('Release configuration change is unsupported.')
        # Existing tracked source is clean. A new target path must not shadow an ignored override.
        tracked = installation._command(('git', 'ls-files', '--', relative))
        if not tracked and outgoing.exists():
            raise LifecycleStateError('New release asset conflicts with a protected local override; preserve both and review.')
        outgoing.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(incoming, outgoing)
        outgoing.chmod(0o700 if incoming.stat().st_mode & 0o111 else 0o600)
    for path in temporary.rglob('*'):
        if path.is_file():
            with path.open('rb') as stream:
                os.fsync(stream.fileno())
    os.replace(temporary, destination)
    descriptor = os.open(destination.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    verify_product_infra(installation, plan)


def verify_product_infra(installation, plan):
    """Recompare protected content privately; never persist credential fingerprints."""
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_paths import require_private_product_paths

    require_private_product_paths(installation)
    original = installation.root / 'infra'
    effective = installation.state / 'infra' / plan.target.product.revision
    code = installation.directory(plan)
    expected = {path.relative_to(original): path for path in original.rglob('*') if path.is_file()}
    for changed in plan.configuration_changes:
        member = Path(changed).relative_to('infra')
        expected[member] = code / changed
    if not effective.is_dir() or any(path.is_symlink() for path in effective.rglob('*')):
        raise LifecycleStateError('Protected configuration migration is missing or unsafe.')
    actual = {path.relative_to(effective) for path in effective.rglob('*') if path.is_file()}
    if actual != set(expected) or any((effective / member).read_bytes() != path.read_bytes() for member, path in expected.items()):
        raise LifecycleStateError('Protected configuration changed; preserve source/snapshot and inspect before recovery.')

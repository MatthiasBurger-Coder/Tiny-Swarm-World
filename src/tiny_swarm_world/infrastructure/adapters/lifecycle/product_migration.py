"""Ordered protected-infra migration without overwriting operator assets."""
import os
from pathlib import Path
import shutil

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


def migrate_product_infra(installation, plan):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_paths import require_private_product_paths

    require_private_product_paths(installation)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import effective_source

    source = effective_source(installation, plan)
    target = installation.directory(plan) / 'infra'
    destination = installation.state / 'infra' / plan.target.product.revision
    temporary = destination.with_name(destination.name + '.pending')
    if destination.exists():
        verify_product_infra(installation, plan)
        return
    if plan.configuration_source is not None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import prepare_pending

        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        prepare_pending(installation, plan, temporary, 'migration')
    elif temporary.exists():
        if temporary.is_symlink() or any(path.is_symlink() for path in temporary.rglob('*')):
            raise LifecycleStateError('Interrupted migration contains unexpected symlinks; preserve it for review.')
        # Only discard this operation's incomplete private copy; original infra is untouched.
        shutil.rmtree(temporary)
    if any(path.is_symlink() for path in source.rglob('*')):
        raise LifecycleStateError('Protected infrastructure contains symlinks; inspect paths before migration.')
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    shutil.copytree(source, temporary, dirs_exist_ok=plan.configuration_source is not None)
    for path in temporary.rglob('*'):
        path.chmod(0o700 if path.is_dir() or path.stat().st_mode & 0o111 else 0o600)
    temporary.chmod(0o700)
    _migrate_changed_assets(installation, plan, target, temporary)
    for path in temporary.rglob('*'):
        if path.is_file():
            with path.open('rb') as stream:
                os.fsync(stream.fileno())
    if plan.configuration_source is not None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import publish_pending

        publish_pending(installation, plan, temporary, destination, 'migration')
    else:
        os.replace(temporary, destination)
    descriptor = os.open(destination.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    verify_product_infra(installation, plan)


def _migrate_changed_assets(installation, plan, target, temporary):
    for relative in plan.configuration_changes:
        member = Path(relative)
        if member.is_absolute() or '..' in member.parts or member.parts[0] != 'infra':
            raise LifecycleStateError('Release configuration path is unsafe.')
        incoming = target / member.relative_to('infra')
        outgoing = temporary / member.relative_to('infra')
        if not incoming.is_file() or incoming.is_symlink():
            raise LifecycleStateError('Release configuration change is unsupported.')
        if plan.configuration_source is not None:
            original = installation.root / relative
            if original.exists() and outgoing.read_bytes() != original.read_bytes():
                if incoming.read_bytes() == original.read_bytes():
                    continue
                raise LifecycleStateError('Release asset conflicts with the bound effective override; preserve both for review.')
        # Existing tracked source is clean. A new target path must not shadow an ignored override.
        tracked = installation._command(('git', 'ls-files', '--', relative))
        if not tracked and outgoing.exists():
            raise LifecycleStateError('New release asset conflicts with a protected local override; preserve both and review.')
        outgoing.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(incoming, outgoing)
        outgoing.chmod(0o700 if incoming.stat().st_mode & 0o111 else 0o600)


def verify_product_infra(installation, plan):
    """Recompare protected content privately; never persist credential fingerprints."""
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_paths import require_private_product_paths

    require_private_product_paths(installation)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import effective_source

    original = effective_source(installation, plan)
    effective = installation.state / 'infra' / plan.target.product.revision
    code = installation.directory(plan)
    expected = {path.relative_to(original): path for path in original.rglob('*') if path.is_file()}
    for changed in plan.configuration_changes:
        member = Path(changed).relative_to('infra')
        if plan.configuration_source is not None:
            source = installation.root / changed
            if source.exists() and (original / member).read_bytes() != source.read_bytes():
                if (code / changed).read_bytes() == source.read_bytes():
                    continue
                raise LifecycleStateError('Release asset conflicts with the bound effective override; preserve both for review.')
        expected[member] = code / changed
    if not effective.is_dir() or any(path.is_symlink() for path in effective.rglob('*')):
        raise LifecycleStateError('Protected configuration migration is missing or unsafe.')
    actual = {path.relative_to(effective) for path in effective.rglob('*') if path.is_file()}
    if actual != set(expected) or any((effective / member).read_bytes() != path.read_bytes() for member, path in expected.items()):
        raise LifecycleStateError('Protected configuration changed; preserve source/snapshot and inspect before recovery.')
    if plan.configuration_source is not None and any(
            bool((effective / member).stat().st_mode & 0o111) != bool(path.stat().st_mode & 0o111)
            for member, path in expected.items()):
        raise LifecycleStateError('Protected executable modes changed; preserve the snapshot for review.')

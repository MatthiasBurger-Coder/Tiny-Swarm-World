"""Reject managed-path escapes before product filesystem mutation."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


def require_private_product_paths(installation):
    state = installation.state
    for parent in (state, state / 'releases', state / 'infra', state / 'activations', state / 'staging', state / 'inputs'):
        if parent.is_symlink() or not parent.resolve().is_relative_to(installation.root):
            raise LifecycleStateError('Managed product paths must remain inside the installation anchor without symlinks.')
        if parent.exists() and (not parent.is_dir() or parent.stat().st_mode & 0o022):
            raise LifecycleStateError('Managed product directories must not permit group/other writes.')
    for folder in ('releases', 'infra', 'activations', 'staging', 'inputs'):
        parent = state / folder
        if parent.exists() and any(child.is_symlink() for child in parent.iterdir()):
            raise LifecycleStateError('Managed release/configuration/activation entries must not be symlinks.')

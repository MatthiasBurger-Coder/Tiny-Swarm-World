"""Private platform profile authority and independent persisted read-only proof."""


def read_only_observer(root, operation):
    if operation is not None:
        return None
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_observation import ScopedProfileObserver
    from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service

    installation = build_installation_lifecycle_service(root)
    persisted = installation.manifests.load().manifest
    if persisted is not None and persisted.installation_profile is not None:
        return ScopedProfileObserver(root, installation)
    return None


def platform_workflows(workflows, root, operation):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import locked_workflows

    return locked_workflows(workflows, root, 'platform',
        None if operation is None else operation.lease, profile_operation=operation)

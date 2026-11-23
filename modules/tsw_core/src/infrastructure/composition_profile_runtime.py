"""Private platform profile authority and independent persisted read-only proof."""

from collections.abc import Awaitable, Callable
from pathlib import Path

from tiny_swarm_world.application.services.platform.preflight_service import RecoveryPortProof
from tiny_swarm_world.domain.deployment import ServiceStackProfile


def recovery_port_observer(
    enabled: bool, root: Path, profile: ServiceStackProfile | str,
) -> Callable[[], Awaitable[RecoveryPortProof | None]] | None:
    if enabled:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.recovery_port_ownership import (
            observe_recovery_ports, pending_creation_applies,
        )

        if pending_creation_applies(root):
            return lambda: observe_recovery_ports(root, profile)
    observer = read_only_observer(root, None)
    if observer is None:
        return None

    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import JsonProfileChangeJournal

    change = JsonProfileChangeJournal(root).load()
    if change is not None and not change.settled:
        return None
    return lambda: observer.observe_port_ownership(profile)



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

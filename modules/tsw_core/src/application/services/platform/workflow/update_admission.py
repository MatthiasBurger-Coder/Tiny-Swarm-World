"""Shared consent and explicit installation ownership for Classic transitions."""
from collections.abc import Awaitable, Callable

from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease, InstallationOperationLock, installation_operation
from tiny_swarm_world.application.services.platform.workflow.results import PlatformWorkflowResult
from tiny_swarm_world.domain.preflight import LiveConsent


async def with_update_operation(lock: InstallationOperationLock | None,
                                lease: InstallationLease | None,
                                policy_guard: Callable[[], None] | None,
                                operation: str, preview: bool, consent: LiveConsent | None,
                                invoke: Callable[[InstallationLease | None], Awaitable[PlatformWorkflowResult]]) -> PlatformWorkflowResult:
    if preview or consent is None or not consent.accepted:
        return await invoke(None)
    with installation_operation(lock, operation, lease) as admitted:
        if policy_guard is not None:
            policy_guard()
        return await invoke(admitted)

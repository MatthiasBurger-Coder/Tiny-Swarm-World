from __future__ import annotations

from collections.abc import Mapping

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
    SwarmServiceStatus,
)
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsureSwarmStack:
    def __init__(
        self,
        compose_repository: PortComposeFileRepository,
        swarm_runtime: PortSwarmStackRuntime,
        service_stack: ServiceStackContract,
        stack_environment: Mapping[str, str] | None = None,
    ):
        self.compose_repository = compose_repository
        self.swarm_runtime = swarm_runtime
        self.service_stack = service_stack
        self.stack_environment = dict(stack_environment or {})
        self.deployment_target_id = service_stack.stack_target_id
        self.verification_target_id = service_stack.stack_target_id

    async def run(self) -> None:
        stack_definition = self.compose_repository.get_compose_of(self.service_stack.stack_name)
        self.swarm_runtime.deploy_stack(stack_definition, self.stack_environment)

    async def verify(self) -> VerificationResult:
        try:
            stack_exists = self.swarm_runtime.stack_exists(self.service_stack.stack_name)
            observed_services = _observed_service_names(
                self.service_stack.stack_name,
                self.swarm_runtime.list_stack_services(self.service_stack.stack_name),
            )
        except Exception as exc:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Swarm stack registration verification failed: {exc.__class__.__name__}",
                evidence=_stack_evidence(self.service_stack, stack_registered="unknown"),
            )

        missing_services = tuple(
            service
            for service in self.service_stack.required_services
            if service not in observed_services
        )
        if stack_exists and not missing_services:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Swarm stack is registered with expected services.",
                evidence=_stack_evidence(
                    self.service_stack,
                    stack_registered="true",
                    observed_services=observed_services,
                ),
            )

        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Swarm stack is missing expected service registrations.",
            evidence=_stack_evidence(
                self.service_stack,
                stack_registered=str(stack_exists).lower(),
                missing_services=missing_services,
                observed_services=observed_services,
            ),
        )


def _observed_service_names(
    stack_name: str,
    services: tuple[SwarmServiceStatus, ...],
) -> tuple[str, ...]:
    prefix = f"{stack_name}_"
    observed: list[str] = []
    for service in services:
        service_name = getattr(service, "service_name", "")
        if service_name.startswith(prefix):
            observed.append(service_name[len(prefix) :])
        elif service_name:
            observed.append(service_name)
    return tuple(sorted(observed))


def _stack_evidence(
    service_stack: ServiceStackContract,
    *,
    stack_registered: str,
    missing_services: tuple[str, ...] = (),
    observed_services: tuple[str, ...] = (),
) -> dict[str, str]:
    return {
        "missing_services": ",".join(missing_services),
        "observed_services": ",".join(observed_services),
        "phase": "verify",
        "required_services": ",".join(service_stack.required_services),
        "stack_name": service_stack.stack_name,
        "stack_registered": stack_registered,
    }

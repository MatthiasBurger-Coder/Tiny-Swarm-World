from __future__ import annotations

import time

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
    SwarmServiceStatus,
)
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class VerifySwarmServiceReadiness:
    def __init__(
        self,
        swarm_runtime: PortSwarmStackRuntime,
        service_stack: ServiceStackContract,
        max_attempts: int = 60,
        wait_seconds: int = 10,
    ):
        self.swarm_runtime = swarm_runtime
        self.service_stack = service_stack
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.verification_target_id = service_stack.service_readiness_target_id

    async def verify(self) -> VerificationResult:
        last_services: tuple[SwarmServiceStatus, ...] = ()
        for attempt in range(1, self.max_attempts + 1):
            try:
                last_services = self.swarm_runtime.list_stack_services(self.service_stack.stack_name)
            except Exception as exc:
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.FAILED_TO_VERIFY,
                    message=f"Swarm service readiness verification failed: {exc.__class__.__name__}",
                    evidence=_readiness_evidence(self.service_stack, last_services, attempt=attempt),
                )

            if _all_required_services_ready(self.service_stack, last_services):
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.VERIFIED,
                    message="Swarm services reached desired replica counts.",
                    evidence=_readiness_evidence(self.service_stack, last_services, attempt=attempt),
                )

            if attempt < self.max_attempts:
                time.sleep(self.wait_seconds)

        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Swarm services did not reach desired replica counts in time.",
            evidence=_readiness_evidence(
                self.service_stack,
                last_services,
                attempt=self.max_attempts,
            ),
        )


def _all_required_services_ready(
    service_stack: ServiceStackContract,
    services: tuple[SwarmServiceStatus, ...],
) -> bool:
    services_by_name = _service_status_by_short_name(service_stack.stack_name, services)
    return all(
        service_name in services_by_name and services_by_name[service_name].ready
        for service_name in service_stack.required_services
    )


def _service_status_by_short_name(
    stack_name: str,
    services: tuple[SwarmServiceStatus, ...],
) -> dict[str, SwarmServiceStatus]:
    prefix = f"{stack_name}_"
    by_name: dict[str, SwarmServiceStatus] = {}
    for service in services:
        short_name = service.service_name
        if short_name.startswith(prefix):
            short_name = short_name[len(prefix) :]
        by_name[short_name] = service
    return by_name


def _readiness_evidence(
    service_stack: ServiceStackContract,
    services: tuple[SwarmServiceStatus, ...],
    *,
    attempt: int,
) -> dict[str, str]:
    by_name = _service_status_by_short_name(service_stack.stack_name, services)
    replica_summary = {
        name: f"{status.current_replicas}/{status.desired_replicas}"
        for name, status in by_name.items()
    }
    missing = tuple(
        service
        for service in service_stack.required_services
        if service not in by_name
    )
    return {
        "attempt": str(attempt),
        "missing_services": ",".join(missing),
        "phase": "verify",
        "replicas": ",".join(f"{name}={replicas}" for name, replicas in sorted(replica_summary.items())),
        "required_services": ",".join(service_stack.required_services),
        "stack_name": service_stack.stack_name,
    }

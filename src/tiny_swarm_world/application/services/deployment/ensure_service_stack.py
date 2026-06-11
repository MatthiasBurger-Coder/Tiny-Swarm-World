from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping

from tiny_swarm_world.application.ports.clients.port_portainer_client import PortPortainerClient
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsureServiceStack:
    def __init__(
        self,
        compose_repository: PortComposeFileRepository,
        portainer_client: PortPortainerClient,
        service_stack: ServiceStackContract,
        endpoint_name: str,
        stack_environment: Mapping[str, str] | None = None,
        verify_attempts: int = 3,
        verify_wait_seconds: float = 5.0,
    ):
        if verify_attempts <= 0:
            raise ValueError("Portainer stack verify attempts must be positive.")
        if verify_wait_seconds < 0:
            raise ValueError("Portainer stack verify wait seconds must not be negative.")
        self.compose_repository = compose_repository
        self.portainer_client = portainer_client
        self.service_stack = service_stack
        self.endpoint_name = endpoint_name
        self.stack_environment = dict(stack_environment or {})
        self.verify_attempts = verify_attempts
        self.verify_wait_seconds = verify_wait_seconds
        self.deployment_target_id = service_stack.stack_target_id
        self.verification_target_id = service_stack.stack_target_id
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> None:
        await asyncio.sleep(0)
        stack_definition = self.compose_repository.get_compose_of(self.service_stack.stack_name)
        if stack_definition.name != self.service_stack.stack_name:
            raise ValueError("compose stack definition name does not match the service stack contract")
        endpoint_id = self.portainer_client.get_endpoint_id_by_name(self.endpoint_name)
        stack_id = self.portainer_client.find_stack_id_by_name(stack_definition.name)

        if stack_id is None:
            self.logger.info("Creating Portainer-managed stack '%s'.", stack_definition.name)
            try:
                self.portainer_client.create_stack(
                    stack_definition,
                    endpoint_id,
                    self.stack_environment,
                )
            except Exception:
                if not await self._stack_is_registered_after_apply_error():
                    raise
            return

        self.logger.info("Updating Portainer-managed stack '%s'.", stack_definition.name)
        try:
            self.portainer_client.update_stack(
                stack_id,
                stack_definition,
                endpoint_id,
                self.stack_environment,
            )
        except Exception:
            if not await self._stack_is_registered_after_apply_error():
                raise

    async def verify(self) -> VerificationResult:
        last_exception: Exception | None = None
        for attempt in range(1, self.verify_attempts + 1):
            await asyncio.sleep(0 if attempt == 1 else self.verify_wait_seconds)
            try:
                stack_id = self.portainer_client.find_stack_id_by_name(self.service_stack.stack_name)
            except Exception as exc:
                last_exception = exc
                continue
            if stack_id is not None:
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.VERIFIED,
                    message=(
                        "Portainer stack is registered; service readiness remains a "
                        "separate observed-state verification."
                    ),
                    evidence=_stack_registration_evidence(
                        self.service_stack,
                        stack_registered="true",
                        verify_attempt=attempt,
                    ),
                )

        if last_exception is not None:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=(
                    "Portainer stack registration verification failed: "
                    f"{last_exception.__class__.__name__}"
                ),
                evidence=_stack_registration_evidence(
                    self.service_stack,
                    stack_registered="unknown",
                    classification="deployment_apply_failed",
                    exception_type=last_exception.__class__.__name__,
                    verify_attempt=self.verify_attempts,
                ),
            )

        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Portainer stack is missing after apply.",
            evidence=_stack_registration_evidence(
                self.service_stack,
                stack_registered="false",
                classification="deployment_apply_failed",
                verify_attempt=self.verify_attempts,
            ),
        )

    async def _stack_is_registered_after_apply_error(self) -> bool:
        verification = await self.verify()
        return verification.status == VerificationStatus.VERIFIED


def _stack_registration_evidence(
    service_stack: ServiceStackContract,
    *,
    stack_registered: str,
    classification: str | None = None,
    exception_type: str | None = None,
    verify_attempt: int | None = None,
) -> dict[str, str]:
    evidence = {
        "phase": "verify",
        "readiness_observed": "false",
        "registration_scope": "portainer_stack",
        "required_service_count": str(len(service_stack.required_services)),
        "required_services": ",".join(service_stack.required_services),
        "stack_registered": stack_registered,
        "stack_name": service_stack.stack_name,
    }
    if classification is not None:
        evidence["classification"] = classification
    if exception_type is not None:
        evidence["exception_type"] = exception_type
    if verify_attempt is not None:
        evidence["verify_attempt"] = str(verify_attempt)
    return evidence

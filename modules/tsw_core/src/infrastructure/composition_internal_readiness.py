"""Internal Swagger HTTP readiness through the existing managed-node runtime."""
from collections.abc import Callable
import asyncio
import time

from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.infrastructure.process.runner import ProcessRunnerError


class InternalSwaggerReadinessCheck:
    def __init__(self, contract: ServiceStackContract, probe: Callable[[], bool], *,
                 max_attempts: int = 12, wait_seconds: int = 5):
        if contract.stack_name != 'swagger' or contract.endpoints or max_attempts <= 0 or wait_seconds < 0:
            raise ValueError('Internal Swagger readiness requires its non-published contract and bounded attempts.')
        self.probe, self.max_attempts, self.wait_seconds = probe, max_attempts, wait_seconds
        self.verification_target_id = contract.service_readiness_target_id
        self.deployment_target_id = self.verification_target_id
        self._verification = self.result(VerificationStatus.BLOCKED)

    def result(self, status: VerificationStatus) -> VerificationResult:
        return VerificationResult(target_id=self.verification_target_id, status=status,
            message='Internal Swagger HTTP readiness ' + status.value + '.',
            evidence={'evidence_kind': 'container_internal_http', 'stack_name': 'swagger', 'published_ports': 'none'})

    def once(self) -> bool:
        try:
            return self.probe() is True
        except (OperationError, ProcessRunnerError, OSError):
            return False

    async def run(self) -> None:
        self._verification = await self.verify_async()

    async def verify_async(self) -> VerificationResult:
        if self._verification.status is not VerificationStatus.BLOCKED:
            return self._verification
        for attempt in range(self.max_attempts):
            if await asyncio.to_thread(self.once):
                self._verification = self.result(VerificationStatus.VERIFIED)
                return self._verification
            if attempt + 1 < self.max_attempts:
                await asyncio.sleep(self.wait_seconds)
        self._verification = self.result(VerificationStatus.FAILED_TO_VERIFY)
        return self._verification

    def verify(self) -> VerificationResult:
        if self._verification.status is not VerificationStatus.BLOCKED:
            return self._verification
        for attempt in range(self.max_attempts):
            if self.once():
                self._verification = self.result(VerificationStatus.VERIFIED)
                return self._verification
            if attempt + 1 < self.max_attempts:
                time.sleep(self.wait_seconds)
        self._verification = self.result(VerificationStatus.FAILED_TO_VERIFY)
        return self._verification

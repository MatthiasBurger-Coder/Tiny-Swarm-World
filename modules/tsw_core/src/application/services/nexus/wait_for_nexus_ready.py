import asyncio
import logging

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure
from tiny_swarm_world.application.services.shared.operation_results import failure_from_exception
from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.application.ports.progress import (
    NullWorkflowProgress,
    PortWorkflowProgress,
    report_readiness_wait,
)
from tiny_swarm_world.application.services.shared import (
    ReadinessRetry,
    wait_for_readiness_retry,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class NexusReadinessTimeout(OperationError, TimeoutError):
    pass


class WaitForNexusReady:
    verification_target_id = "artifacts:nexus-ready"

    def __init__(
        self,
        nexus_client: PortNexusClient,
        max_attempts: int,
        wait_seconds: int,
        progress: PortWorkflowProgress | None = None,
    ):
        self.nexus_client = nexus_client
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.progress = progress or NullWorkflowProgress()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> None:
        last_exception: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                if self.nexus_client.is_available():
                    self.logger.info(f"Nexus became ready on attempt {attempt}.")
                    return
                last_exception = None
            except Exception as exc:
                last_exception = exc

            if attempt < self.max_attempts:
                self.logger.info(
                    f"Nexus is not ready yet. Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                await wait_for_readiness_retry(
                    ReadinessRetry(
                        attempt=attempt,
                        max_attempts=self.max_attempts,
                        wait_seconds=self.wait_seconds,
                    ),
                    on_wait=self._report_wait,
                )

        failure = failure_from_exception(last_exception, "artifacts.nexus.readiness", "artifacts") if last_exception is not None else OperationFailure.for_cause("artifacts.nexus.readiness", "artifacts", "dependency_unavailable")
        raise NexusReadinessTimeout(failure) from None

    def _report_wait(self, retry: ReadinessRetry) -> None:
        report_readiness_wait(
            self.progress,
            workflow="artifacts prepare",
            phase="nexus readiness",
            target=self.verification_target_id,
            task="Nexus readiness",
            attempt=retry.attempt,
            max_attempts=retry.max_attempts,
            wait_seconds=retry.wait_seconds,
        )

    async def verify(self) -> VerificationResult:
        self.operation_failure: OperationFailure | None = None
        await asyncio.sleep(0)
        try:
            available = self.nexus_client.is_available()
        except Exception as exc:
            self.operation_failure = failure_from_exception(exc, "artifacts.verify", "artifacts")
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Nexus readiness verification failed: {exc.__class__.__name__}",
                evidence={"available": "unknown", "phase": "verify"},
            )
        if available:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Nexus HTTP API is available.",
                evidence={"available": "true", "phase": "verify"},
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Nexus HTTP API is not available.",
            evidence={"available": "false", "phase": "verify"},
        )

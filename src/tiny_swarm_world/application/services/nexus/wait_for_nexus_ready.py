import logging
import time

from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class WaitForNexusReady:
    verification_target_id = "artifacts:nexus-ready"

    def __init__(self, nexus_client: PortNexusClient, max_attempts: int, wait_seconds: int):
        self.nexus_client = nexus_client
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> None:
        for attempt in range(1, self.max_attempts + 1):
            if self.nexus_client.is_available():
                self.logger.info(f"Nexus became ready on attempt {attempt}.")
                return

            if attempt < self.max_attempts:
                self.logger.info(
                    f"Nexus is not ready yet. Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)

        raise TimeoutError(
            f"Nexus did not become ready after {self.max_attempts} attempts with {self.wait_seconds} seconds delay."
        )

    async def verify(self) -> VerificationResult:
        try:
            available = self.nexus_client.is_available()
        except Exception as exc:
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

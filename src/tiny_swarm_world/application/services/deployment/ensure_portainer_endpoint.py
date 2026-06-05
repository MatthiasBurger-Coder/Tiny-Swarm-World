from __future__ import annotations

import asyncio

from tiny_swarm_world.application.ports.clients.port_portainer_client import PortPortainerClient
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsurePortainerEndpoint:
    verification_target_id = "deployment:portainer-local-endpoint"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        portainer_client: PortPortainerClient,
        endpoint_name: str,
        max_attempts: int = 30,
        wait_seconds: int = 5,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("Portainer endpoint max_attempts must be positive.")
        if wait_seconds < 0:
            raise ValueError("Portainer endpoint wait_seconds must not be negative.")
        self.portainer_client = portainer_client
        self.endpoint_name = endpoint_name
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds

    async def run(self) -> None:
        last_exception: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                self.portainer_client.ensure_local_endpoint(self.endpoint_name)
                return
            except Exception as exc:
                last_exception = exc
                if attempt >= self.max_attempts:
                    break
                await asyncio.sleep(self.wait_seconds)
        raise RuntimeError("Portainer local endpoint could not be registered.") from last_exception

    async def verify(self) -> VerificationResult:
        last_exception: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                endpoint_id = self.portainer_client.get_endpoint_id_by_name(
                    self.endpoint_name,
                )
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.VERIFIED,
                    message="Portainer local Docker endpoint is registered.",
                    evidence={
                        "phase": "verify",
                        "endpoint_name": self.endpoint_name,
                        "endpoint_ready": "true",
                        "endpoint_state": "registered",
                        "endpoint_id_present": str(endpoint_id > 0).lower(),
                    },
                )
            except Exception as exc:
                last_exception = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(self.wait_seconds)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message=(
                "Portainer local endpoint verification failed: "
                f"{last_exception.__class__.__name__}"
            ),
            evidence={
                "phase": "verify",
                "endpoint_name": self.endpoint_name,
                "endpoint_ready": "false",
                "endpoint_state": "unknown",
            },
        )

from __future__ import annotations

import time

from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortPortainerAdminClient,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsurePortainerAdminAccess:
    verification_target_id = "deployment:portainer-admin-access"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        portainer_admin_client: PortPortainerAdminClient,
        username: str,
        password: str,
        max_attempts: int = 30,
        wait_seconds: int = 5,
    ):
        self.portainer_admin_client = portainer_admin_client
        self.username = username
        self.password = password
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds

    async def run(self) -> None:
        for attempt in range(1, self.max_attempts + 1):
            if self.portainer_admin_client.can_authenticate(self.username, self.password):
                return

            try:
                self.portainer_admin_client.initialize_admin_user(self.username, self.password)
            except Exception:
                if attempt >= self.max_attempts:
                    raise
            else:
                if self.portainer_admin_client.can_authenticate(self.username, self.password):
                    return

            if attempt < self.max_attempts:
                time.sleep(self.wait_seconds)

        raise RuntimeError("Portainer admin access could not be initialized.")

    async def verify(self) -> VerificationResult:
        try:
            authenticated = self.portainer_admin_client.can_authenticate(self.username, self.password)
        except Exception as exc:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Portainer admin verification failed: {exc.__class__.__name__}",
                evidence={"phase": "verify", "authenticated": "unknown"},
            )

        if authenticated:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Portainer admin credentials are active.",
                evidence={"phase": "verify", "authenticated": "true"},
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Portainer admin credentials are not active.",
            evidence={"phase": "verify", "authenticated": "false"},
        )

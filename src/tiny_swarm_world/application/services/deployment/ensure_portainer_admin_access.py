from __future__ import annotations

import asyncio
import logging

from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortainerAdminInitializationRejected,
    PortPortainerAdminClient,
)
from tiny_swarm_world.application.ports.ui.port_ui import AGGREGATE_INSTANCE, PortUI
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
        ui: PortUI | None = None,
    ):
        self.portainer_admin_client = portainer_admin_client
        self.username = username
        self.password = password
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.ui = ui
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> None:
        for attempt in range(1, self.max_attempts + 1):
            if self._can_authenticate():
                return
            if self._initialize_admin_access(attempt):
                return
            if attempt < self.max_attempts:
                await asyncio.sleep(self.wait_seconds)

        raise RuntimeError("Portainer admin access could not be initialized.")

    def _initialize_admin_access(self, attempt: int) -> bool:
        try:
            self.portainer_admin_client.initialize_admin_user(self.username, self.password)
        except PortainerAdminInitializationRejected as exc:
            return self._handle_rejected_initialization(exc)
        except Exception:
            if attempt >= self.max_attempts:
                raise
            return False
        return self._can_authenticate()

    def _handle_rejected_initialization(
        self,
        exc: PortainerAdminInitializationRejected,
    ) -> bool:
        if self._can_authenticate():
            self.logger.info(
                "Portainer admin initialization was rejected after credentials became active."
            )
            return True
        safe_error = _safe_exception_summary(exc)
        self.logger.error(
            "Failed to initialize Portainer admin access. Error: %s",
            safe_error,
        )
        if self.ui is not None:
            self.ui.update_status(
                instance=AGGREGATE_INSTANCE,
                task=self.deployment_target_id,
                step="Error",
                result="failed_to_apply",
            )
        raise exc

    async def verify(self) -> VerificationResult:
        last_exception: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                if self.portainer_admin_client.can_authenticate(self.username, self.password):
                    return VerificationResult(
                        target_id=self.verification_target_id,
                        status=VerificationStatus.VERIFIED,
                        message="Portainer admin credentials are active.",
                        evidence={"phase": "verify", "access_state": "active"},
                    )
                last_exception = None
            except Exception as exc:
                last_exception = exc

            if attempt < self.max_attempts:
                await asyncio.sleep(self.wait_seconds)

        if last_exception is not None:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Portainer admin verification failed: {last_exception.__class__.__name__}",
                evidence={"phase": "verify", "access_state": "unknown"},
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Portainer admin credentials are not active.",
            evidence={"phase": "verify", "access_state": "inactive"},
        )

    def _can_authenticate(self) -> bool:
        try:
            return self.portainer_admin_client.can_authenticate(self.username, self.password)
        except Exception:
            return False


def _safe_exception_summary(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        return f"{exc.__class__.__name__} HTTP {status_code}. Diagnostic payload redacted."
    return f"{exc.__class__.__name__}. Diagnostic payload redacted."

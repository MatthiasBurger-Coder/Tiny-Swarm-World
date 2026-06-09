from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from tiny_swarm_world.application.ports.clients.port_sonarqube_client import (
    PortSonarqubeClient,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsureSonarqubeAdminAccess:
    verification_target_id = "deployment:sonarqube-admin-access"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        *,
        sonarqube_client: PortSonarqubeClient,
        username: str,
        password: str | Callable[[], str],
        initial_password: str = "admin",
        max_attempts: int = 60,
        wait_seconds: float = 5.0,
    ) -> None:
        if not username:
            raise ValueError("SonarQube admin username must not be empty.")
        if not password:
            raise ValueError("SonarQube admin password must not be empty.")
        self.sonarqube_client = sonarqube_client
        self.username = username
        self._password = password
        self.initial_password = initial_password
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self._status = "not_run"
        self.service_stack = _SyntheticServiceStack("sonarqube-admin-access")
        self.stack_environment: dict[str, str] = {}

    @property
    def password(self) -> str:
        value = self._password() if callable(self._password) else self._password
        if not value:
            raise ValueError("SonarQube admin password must not be empty.")
        return value

    def run(self) -> None:
        self._wait_until_available()
        if self.sonarqube_client.can_authenticate(self.username, self.password):
            self._status = "already_configured"
            return
        if not self.sonarqube_client.can_authenticate(self.username, self.initial_password):
            self._status = "blocked"
            raise RuntimeError("SonarQube admin access is unavailable.")
        self.sonarqube_client.change_password(
            self.username,
            self.initial_password,
            self.password,
        )
        self._status = "rotated"

    def verify(self) -> VerificationResult:
        configured = self.sonarqube_client.can_authenticate(self.username, self.password)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED if configured else VerificationStatus.BLOCKED,
            message="SonarQube admin credentials were verified without exposing values.",
            evidence={
                "access_state": "active" if configured else "unavailable",
                "phase": "verify",
                "status": self._status,
            },
        )

    def _wait_until_available(self) -> None:
        for attempt in range(1, self.max_attempts + 1):
            if self.sonarqube_client.is_available():
                return
            if attempt < self.max_attempts:
                time.sleep(self.wait_seconds)
        self._status = "blocked"
        raise RuntimeError("SonarQube did not become available.")


@dataclass(frozen=True)
class _SyntheticServiceStack:
    stack_name: str

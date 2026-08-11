from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tiny_swarm_world.application.ports.clients.port_sonarqube_client import (
    PortSonarqubeClient,
)
from tiny_swarm_world.application.services.shared import (
    ReadinessRetry,
    wait_for_readiness_retry,
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
        initial_credential: str = "admin",
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
        self.initial_credential = initial_credential
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

    async def run(self) -> None:
        await self._wait_until_available()
        if self._can_authenticate_once(self.password):
            self._status = "already_configured"
            return
        if not await self._can_authenticate_with_retry(self.initial_credential):
            self._status = "blocked"
            raise RuntimeError("SonarQube admin access is unavailable.")
        self.sonarqube_client.change_password(
            self.username,
            self.initial_credential,
            self.password,
        )
        self._status = "rotated"

    async def verify(self) -> VerificationResult:
        configured = await self._can_authenticate_with_retry(self.password)
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

    async def _wait_until_available(self) -> None:
        for attempt in range(1, self.max_attempts + 1):
            if self.sonarqube_client.is_available():
                return
            if attempt < self.max_attempts:
                await self._wait_for_retry(attempt)
        self._status = "blocked"
        raise RuntimeError("SonarQube did not become available.")

    def _can_authenticate_once(self, password: str) -> bool:
        try:
            return self.sonarqube_client.can_authenticate(self.username, password)
        except RuntimeError:
            return False

    async def _can_authenticate_with_retry(self, password: str) -> bool:
        for attempt in range(1, self.max_attempts + 1):
            try:
                authenticated = self.sonarqube_client.can_authenticate(self.username, password)
            except RuntimeError:
                if attempt < self.max_attempts:
                    await self._wait_for_retry(attempt)
                    continue
                self._status = "blocked"
                raise RuntimeError(
                    "SonarQube admin access check failed with redacted output."
                )
            if authenticated:
                return True
            if attempt < self.max_attempts:
                await self._wait_for_retry(attempt)
        return False

    async def _wait_for_retry(self, attempt: int) -> None:
        await wait_for_readiness_retry(
            ReadinessRetry(
                attempt=attempt,
                max_attempts=self.max_attempts,
                wait_seconds=self.wait_seconds,
            )
        )


@dataclass(frozen=True)
class _SyntheticServiceStack:
    stack_name: str

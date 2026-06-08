from __future__ import annotations

from tiny_swarm_world.application.ports.clients.port_infisical_bootstrap_client import (
    InfisicalBootstrapResult,
    InfisicalBootstrapState,
    PortInfisicalBootstrapClient,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsureInfisicalBootstrap:
    verification_target_id = "deployment:infisical-bootstrap"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        infisical_client: PortInfisicalBootstrapClient,
        login_email: str,
        password: str,
        organization: str,
    ):
        if not login_email:
            raise ValueError("Infisical bootstrap email must not be empty.")
        if not password:
            raise ValueError("Infisical bootstrap password must not be empty.")
        if not organization:
            raise ValueError("Infisical bootstrap organization must not be empty.")
        self.infisical_client = infisical_client
        self.login_email = login_email
        self.password = password
        self.organization = organization
        self._last_result: InfisicalBootstrapResult | None = None

    def run(self) -> None:
        self._last_result = self.infisical_client.bootstrap_instance(
            email=self.login_email,
            password=self.password,
            organization=self.organization,
        )

    def verify(self) -> VerificationResult:
        if self._last_result is None:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.BLOCKED,
                message="Infisical bootstrap has not run.",
                evidence={"phase": "verify", "bootstrap_state": "not_run"},
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message=_message_for_result(self._last_result),
            evidence={
                "phase": "verify",
                "bootstrap_state": self._last_result.state.value,
                "admin_email": self._last_result.admin_email,
                "organization": self._last_result.organization,
                "admin_identity_available": str(
                    self._last_result.token_returned
                ).lower(),
            },
        )


def _message_for_result(result: InfisicalBootstrapResult) -> str:
    if result.state is InfisicalBootstrapState.CREATED:
        return "Infisical instance was bootstrapped through the admin API."
    return "Infisical instance was already bootstrapped."

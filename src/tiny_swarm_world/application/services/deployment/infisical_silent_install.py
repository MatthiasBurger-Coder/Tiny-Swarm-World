from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome, OperationResult
from tiny_swarm_world.application.services.shared.operation_results import failure_from_exception
from tiny_swarm_world.application.ports.clients.port_infisical_bootstrap_client import (
    InfisicalBootstrapState,
    PortInfisicalBootstrapClient,
)
from tiny_swarm_world.application.ports.clients.port_infisical_cli import PortInfisicalCli
from tiny_swarm_world.application.ports.file_management.port_local_file_storage import (
    PortLocalFileStorage,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


REDACTED = "<redacted>"
PASSWORD_OPTION_PREFIX = "--" + "password="
REDACTED_PASSWORD_OPTION = PASSWORD_OPTION_PREFIX + REDACTED
SECRET_NAMES = (
    "ENCRYPTION_KEY",
    "AUTH_SECRET",
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "INITIAL_BOOTSTRAP_ADMIN_PASSWORD",
    "DB_CONNECTION_URI",
)


@dataclass(frozen=True)
class InfisicalSilentInstallConfig:
    external_url: str
    internal_url: str
    admin_email: str
    admin_first_name: str
    admin_last_name: str
    organization: str
    admin_password: str
    encryption_key: str
    auth_secret: str
    postgres_password: str
    redis_password: str = ""
    evidence_dir: Path = Path(".tiny-swarm/evidence/infisical")

    def validate(self) -> None:
        required = {
            "external_url": self.external_url,
            "internal_url": self.internal_url,
            "admin_email": self.admin_email,
            "organization": self.organization,
            "admin_password": self.admin_password,
            "encryption_key": self.encryption_key,
            "auth_secret": self.auth_secret,
            "postgres_password": self.postgres_password,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise InfisicalInstallBlocker(
                "required_environment_missing",
                f"Missing required Infisical configuration: {', '.join(missing)}",
            )


class InfisicalInstallBlocker(OperationError, RuntimeError):
    def __init__(self, classification: str, message: str, *, failure: OperationFailure | None = None):
        causes = {
            "required_environment_missing": "configuration_invalid",
            "infisical_readiness_timeout": "dependency_unavailable",
            "infisical_cli_missing": "launch_executable_missing",
            "infisical_bootstrap_failed": "process_exit_failed",
        }
        super().__init__(failure or OperationFailure.for_cause("deployment.infisical.bootstrap", "deployment", causes.get(classification, "unexpected_failure")))
        self.args = (message,)
        self.classification = classification


class EnsureInfisicalSilentInstall:
    verification_target_id = "deployment:infisical-silent-install"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        *,
        cli: PortInfisicalCli,
        storage: PortLocalFileStorage,
        config: InfisicalSilentInstallConfig,
        bootstrap_client: PortInfisicalBootstrapClient | None = None,
        service_running: bool = True,
        http_ready: bool = True,
        setup_screen_required: bool = False,
    ) -> None:
        self.cli = cli
        self.storage = storage
        self.config = config
        self.bootstrap_client = bootstrap_client
        self.service_running = service_running
        self.http_ready = http_ready
        self.setup_screen_required = setup_screen_required
        self._status = "not_run"
        self._classification = ""
        self._bootstrap_method = "not_run"
        self._bootstrap_diagnostic: dict[str, str] = {}

    def render_environment(self) -> dict[str, str]:
        return {
            "AUTH_SECRET": self.config.auth_secret,
            "DB_CONNECTION_URI": (
                "postgres://infisical:"
                f"{self.config.postgres_password}@tasks.infisical-db:5432/infisical"
            ),
            "ENCRYPTION_KEY": self.config.encryption_key,
            "INITIAL_BOOTSTRAP_ADMIN_EMAIL": self.config.admin_email,
            "INITIAL_BOOTSTRAP_ADMIN_FIRST_NAME": self.config.admin_first_name,
            "INITIAL_BOOTSTRAP_ADMIN_LAST_NAME": self.config.admin_last_name,
            "INITIAL_BOOTSTRAP_ADMIN_PASSWORD": self.config.admin_password,
            "REDIS_URL": "redis://tasks.infisical-redis:6379",
            "SITE_URL": self.config.external_url,
        }

    def bootstrap_command(self) -> tuple[str, ...]:
        return (
            "infisical",
            "bootstrap",
            f"--domain={self.config.external_url}",
            f"--email={self.config.admin_email}",
            f"{PASSWORD_OPTION_PREFIX}{self.config.admin_password}",
            f"--organization={self.config.organization}",
            "--ignore-if-bootstrapped",
        )

    def sanitized_bootstrap_command(self) -> tuple[str, ...]:
        return tuple(
            REDACTED_PASSWORD_OPTION if part.startswith(PASSWORD_OPTION_PREFIX) else part
            for part in self.bootstrap_command()
        )

    async def run(self) -> None:
        self.operation_result: OperationResult | None = None
        self._bootstrap_diagnostic = {}
        self._status = "not_run"
        self._classification = ""
        self._bootstrap_method = "not_run"
        try:
            self.config.validate()
        except InfisicalInstallBlocker as exc:
            self.operation_result = OperationResult(OperationOutcome.FAILED, (exc.failure,), pending_operations=("bootstrap",))
            raise
        try:
            self.storage.ensure_directory(self.config.evidence_dir, private=True)
        except Exception as exc:
            self.operation_result = OperationResult(OperationOutcome.FAILED, (failure_from_exception(exc, "deployment.infisical.evidence", "deployment"),), pending_operations=("bootstrap",), uncertain_operations=("evidence.directory",))
            raise exc from None
        if not self.service_running or not self.http_ready:
            self._status = "blocked"
            self._classification = "infisical_readiness_timeout"
            error = InfisicalInstallBlocker(self._classification, "Infisical service did not become ready before bootstrap.")
            self._write_failure_evidence(error, "blocked")
            raise error from None

        if self.cli.is_available():
            await asyncio.to_thread(self._run_cli_bootstrap)
        elif self.bootstrap_client is not None:
            self._bootstrap_method = "admin_api_fallback"
            try:
                bootstrap_result = await asyncio.to_thread(
                    self.bootstrap_client.bootstrap_instance,
                    email=self.config.admin_email,
                    password=self.config.admin_password,
                    organization=self.config.organization,
                )
            except Exception as exc:
                self._status = "failed"
                self._classification = "infisical_bootstrap_api_unavailable"
                self._bootstrap_diagnostic = _bootstrap_error_diagnostic(exc)
                self._write_failure_evidence(exc, "failed")
                raise exc from None
            self._status = (
                "already_bootstrapped"
                if bootstrap_result.state is InfisicalBootstrapState.ALREADY_INITIALIZED
                else "bootstrapped"
            )
        else:
            self._status = "blocked"
            self._classification = "infisical_cli_missing"
            error = InfisicalInstallBlocker(self._classification, "Infisical CLI is missing and no admin API bootstrap fallback is configured.")
            self._write_failure_evidence(error, "blocked")
            raise error from None
        try:
            self._write_evidence(self._status)
        except Exception as exc:
            self.operation_result = OperationResult(
                OperationOutcome.PARTIAL, (failure_from_exception(exc, "deployment.infisical.evidence", "deployment"),),
                completed_operations=("bootstrap",), uncertain_operations=("evidence",),
            )
            raise exc from None

    def _run_cli_bootstrap(self) -> None:
        self._bootstrap_method = "cli"
        result = self.cli.run_bootstrap(self.bootstrap_command())
        output = f"{result.stdout}\n{result.stderr}".lower()
        if result.return_code == 0 and result.failure is None:
            self._status = (
                "already_bootstrapped"
                if "already" in output and "bootstrap" in output
                else "bootstrapped"
            )
            return

        self._status = "failed"
        self._classification = "infisical_bootstrap_failed"
        error = InfisicalInstallBlocker(
            self._classification, "Infisical CLI bootstrap failed with redacted output.",
            failure=result.failure,
        )
        self._write_failure_evidence(error, "failed")
        raise error from None

    def verify(self) -> VerificationResult:
        status = VerificationStatus.VERIFIED
        if self._status in {"blocked", "failed", "not_run"}:
            status = VerificationStatus.BLOCKED
        return VerificationResult(
            target_id=self.verification_target_id,
            status=status,
            message="Infisical silent bootstrap state was recorded with redacted evidence.",
            evidence={
                "bootstrap_state": self._status,
                "classification": self._classification,
                "bootstrap_method": self._bootstrap_method,
                "http_endpoint_responds": str(self.http_ready).lower(),
                "service_running": str(self.service_running).lower(),
                "setup_screen_required": str(self.setup_screen_required).lower(),
                **self._bootstrap_diagnostic,
            },
        )

    def _write_failure_evidence(self, error: Exception, status: str) -> None:
        failures = [failure_from_exception(error, "deployment.infisical.bootstrap", "deployment")]
        pending = ["bootstrap"] if status == "blocked" else []
        uncertain = [] if status == "blocked" else ["bootstrap"]
        try:
            self._write_evidence(status)
        except Exception as evidence_error:
            failures.append(failure_from_exception(evidence_error, "deployment.infisical.evidence", "deployment"))
            uncertain.append("evidence")
        self.operation_result = OperationResult(
            OperationOutcome.FAILED, tuple(failures), pending_operations=tuple(pending), uncertain_operations=tuple(uncertain),
        )

    def _write_evidence(self, status: str) -> None:
        now = datetime.now(UTC).isoformat()
        redacted_config = redact_mapping(self.render_environment())
        payload = {
            "bootstrap_command": list(self.sanitized_bootstrap_command()),
            "bootstrap_method": self._bootstrap_method,
            "classification": self._classification,
            "finished_at": now,
            "redacted_config": redacted_config,
            "setup_screen_required": self.setup_screen_required,
            "status": status,
        }
        if self._bootstrap_diagnostic:
            payload["diagnostic"] = self._bootstrap_diagnostic
        self.storage.write_text(
            self.config.evidence_dir / "bootstrap-result.json",
            json.dumps(payload, indent=2, sort_keys=True),
            private=True,
        )
        self.storage.write_text(
            self.config.evidence_dir / "healthcheck.log",
            "\n".join(
                (
                    f"{now} service_running={str(self.service_running).lower()}",
                    f"{now} http_endpoint_responds={str(self.http_ready).lower()}",
                    f"{now} setup_screen_required={str(self.setup_screen_required).lower()}",
                )
            )
            + "\n",
            private=True,
        )
        self.storage.write_text(
            self.config.evidence_dir / "install-summary.md",
            "\n".join(
                (
                    "# Infisical Silent Bootstrap",
                    "",
                    f"- Status: {status}",
                    f"- Classification: {self._classification or 'none'}",
                    f"- Bootstrap method: {self._bootstrap_method}",
                    f"- Command: {' '.join(self.sanitized_bootstrap_command())}",
                    "- Secrets: redacted",
                )
            )
            + "\n",
            private=True,
        )


def redact_mapping(values: dict[str, str]) -> dict[str, str]:
    return {
        key: REDACTED if _is_secret_key(key) else value
        for key, value in values.items()
    }


def _is_secret_key(key: str) -> bool:
    return any(secret_name in key.upper() for secret_name in SECRET_NAMES)


def _bootstrap_error_diagnostic(exc: Exception) -> dict[str, str]:
    diagnostic = {
        "bootstrap_error_class": exc.__class__.__name__,
    }
    status_code = getattr(exc, "status_code", None)
    if type(status_code) is int and 100 <= status_code <= 599:
        diagnostic["bootstrap_http_status"] = str(status_code)
    reason = getattr(exc, "reason", None)
    if reason in ("not_ready", "Timeout", "ConnectTimeout", "ReadTimeout", "ConnectionError", "RequestException"):
        diagnostic["bootstrap_failure_reason"] = reason
    return diagnostic

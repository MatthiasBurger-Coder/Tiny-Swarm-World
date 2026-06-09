from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tiny_swarm_world.application.ports.clients.port_infisical_cli import PortInfisicalCli
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


REDACTED = "<redacted>"
SECRET_NAMES = (
    "ENCRYPTION_KEY",
    "AUTH_SECRET",
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "INITIAL_BOOTSTRAP_ADMIN_PASSWORD",
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
    secret_file: Path = Path(".tiny-swarm/secrets/infisical.local.env")

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


class InfisicalInstallBlocker(RuntimeError):
    def __init__(self, classification: str, message: str):
        super().__init__(message)
        self.classification = classification


class EnsureInfisicalSilentInstall:
    verification_target_id = "deployment:infisical-silent-install"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        *,
        cli: PortInfisicalCli,
        config: InfisicalSilentInstallConfig,
        service_running: bool = True,
        http_ready: bool = True,
        setup_screen_required: bool = False,
    ) -> None:
        self.cli = cli
        self.config = config
        self.service_running = service_running
        self.http_ready = http_ready
        self.setup_screen_required = setup_screen_required
        self._status = "not_run"
        self._classification = ""

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
            f"--password={self.config.admin_password}",
            f"--organization={self.config.organization}",
            "--ignore-if-bootstrapped",
        )

    def sanitized_bootstrap_command(self) -> tuple[str, ...]:
        return tuple(
            "--password=<redacted>" if part.startswith("--password=") else part
            for part in self.bootstrap_command()
        )

    def run(self) -> None:
        self.config.validate()
        self.config.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.config.secret_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.cli.is_available():
            self._status = "blocked"
            self._classification = "infisical_cli_missing"
            self._write_evidence("blocked")
            raise InfisicalInstallBlocker(
                self._classification,
                "Infisical CLI is missing; install the CLI before silent bootstrap.",
            )
        if not self.service_running or not self.http_ready:
            self._status = "blocked"
            self._classification = "infisical_readiness_timeout"
            self._write_evidence("blocked")
            raise InfisicalInstallBlocker(
                self._classification,
                "Infisical service did not become ready before bootstrap.",
            )

        result = self.cli.run_bootstrap(self.bootstrap_command())
        output = f"{result.stdout}\n{result.stderr}".lower()
        if result.return_code == 0:
            self._status = (
                "already_bootstrapped"
                if "already" in output and "bootstrap" in output
                else "bootstrapped"
            )
        else:
            self._status = "failed"
            self._classification = "infisical_bootstrap_failed"
            self._write_evidence("failed")
            raise InfisicalInstallBlocker(
                self._classification,
                "Infisical CLI bootstrap failed with redacted output.",
            )
        self._write_evidence(self._status)

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
                "http_endpoint_responds": str(self.http_ready).lower(),
                "service_running": str(self.service_running).lower(),
                "setup_screen_required": str(self.setup_screen_required).lower(),
            },
        )

    def _write_evidence(self, status: str) -> None:
        now = datetime.now(UTC).isoformat()
        redacted_config = redact_mapping(self.render_environment())
        payload = {
            "bootstrap_command": list(self.sanitized_bootstrap_command()),
            "classification": self._classification,
            "finished_at": now,
            "redacted_config": redacted_config,
            "setup_screen_required": self.setup_screen_required,
            "status": status,
        }
        (self.config.evidence_dir / "bootstrap-result.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (self.config.evidence_dir / "healthcheck.log").write_text(
            "\n".join(
                (
                    f"{now} service_running={str(self.service_running).lower()}",
                    f"{now} http_endpoint_responds={str(self.http_ready).lower()}",
                    f"{now} setup_screen_required={str(self.setup_screen_required).lower()}",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (self.config.evidence_dir / "install-summary.md").write_text(
            "\n".join(
                (
                    "# Infisical Silent Bootstrap",
                    "",
                    f"- Status: {status}",
                    f"- Classification: {self._classification or 'none'}",
                    f"- Command: {' '.join(self.sanitized_bootstrap_command())}",
                    "- Secrets: redacted",
                )
            )
            + "\n",
            encoding="utf-8",
        )


def redact_mapping(values: dict[str, str]) -> dict[str, str]:
    return {
        key: REDACTED if _is_secret_key(key) else value
        for key, value in values.items()
    }


def _is_secret_key(key: str) -> bool:
    return any(secret_name in key.upper() for secret_name in SECRET_NAMES)

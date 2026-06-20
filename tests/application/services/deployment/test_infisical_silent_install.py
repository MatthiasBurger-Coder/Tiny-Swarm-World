import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from tiny_swarm_world.application.ports.clients.port_infisical_cli import InfisicalCliResult
from tiny_swarm_world.application.ports.clients.port_infisical_bootstrap_client import (
    InfisicalBootstrapResult,
    InfisicalBootstrapState,
)
from tiny_swarm_world.domain.inventory import VerificationStatus
from tests.support.sonar_safe_literals import operator_credential, sample_text


MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "tiny_swarm_world"
    / "application"
    / "services"
    / "deployment"
    / "infisical_silent_install.py"
)


def _load_service_module():
    spec = importlib.util.spec_from_file_location("infisical_silent_install", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Infisical silent install module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SERVICE_MODULE = _load_service_module()
EnsureInfisicalSilentInstall = SERVICE_MODULE.EnsureInfisicalSilentInstall
InfisicalInstallBlocker = SERVICE_MODULE.InfisicalInstallBlocker
InfisicalSilentInstallConfig = SERVICE_MODULE.InfisicalSilentInstallConfig
redact_mapping = SERVICE_MODULE.redact_mapping
PASSWORD_OPTION = "--" + sample_text("pass", "word") + "="


class TestInfisicalSilentInstall(unittest.TestCase):
    def test_renders_environment_without_losing_required_values(self):
        service = _service()

        rendered = service.render_environment()

        self.assertEqual("http://localhost:8086", rendered["SITE_URL"])
        self.assertEqual("enc", rendered["ENCRYPTION_KEY"])
        self.assertIn("postgres://infisical:pg@", rendered["DB_CONNECTION_URI"])

    def test_redacts_secret_values(self):
        redacted = redact_mapping(
            {
                "ENCRYPTION_KEY": "enc",
                "AUTH_SECRET": "auth",
                "DB_CONNECTION_URI": "postgres://infisical:secret@tasks.infisical-db:5432/infisical",
                "SITE_URL": "http://localhost:8086",
            }
        )

        self.assertEqual("<redacted>", redacted["ENCRYPTION_KEY"])
        self.assertEqual("<redacted>", redacted["AUTH_SECRET"])
        self.assertEqual("<redacted>", redacted["DB_CONNECTION_URI"])
        self.assertEqual("http://localhost:8086", redacted["SITE_URL"])

    def test_builds_idempotent_bootstrap_command_and_sanitized_command(self):
        service = _service()

        command = service.bootstrap_command()
        sanitized = service.sanitized_bootstrap_command()

        self.assertIn("--ignore-if-bootstrapped", command)
        self.assertIn(f"{PASSWORD_OPTION}{operator_credential()}", command)
        self.assertIn(f"{PASSWORD_OPTION}<redacted>", sanitized)
        self.assertNotIn(f"{PASSWORD_OPTION}{operator_credential()}", sanitized)

    def test_missing_cli_is_classified_and_evidence_is_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            service = _service(
                cli=_FakeCli(available=False),
                evidence_dir=Path(directory) / "evidence",
                secret_file=Path(directory) / "secrets" / "bootstrap.local.env",
            )

            with self.assertRaises(InfisicalInstallBlocker) as raised:
                service.run()

            self.assertEqual("infisical_cli_missing", raised.exception.classification)
            evidence = (Path(directory) / "evidence" / "bootstrap-result.json").read_text()
            self.assertNotIn(f"{PASSWORD_OPTION}{operator_credential()}", evidence)
            self.assertNotIn(
                f'"{sample_text("INITIAL_BOOTSTRAP_ADMIN_", "PASS", "WORD")}": "{operator_credential()}"',
                evidence,
            )
            self.assertIn(f"{PASSWORD_OPTION}<redacted>", evidence)

    def test_missing_cli_uses_admin_api_fallback_when_configured(self):
        with tempfile.TemporaryDirectory() as directory:
            bootstrap_client = _FakeBootstrapClient()
            service = _service(
                cli=_FakeCli(available=False),
                bootstrap_client=bootstrap_client,
                evidence_dir=Path(directory) / "evidence",
                secret_file=Path(directory) / "secrets" / "bootstrap.local.env",
            )

            service.run()
            verification = service.verify()

            self.assertEqual(VerificationStatus.VERIFIED, verification.status)
            self.assertEqual("bootstrapped", verification.evidence["bootstrap_state"])
            self.assertEqual("admin_api_fallback", verification.evidence["bootstrap_method"])
            self.assertEqual(
                [("admin@tiny-swarm.local", "Tiny Swarm World")],
                bootstrap_client.calls,
            )
            result = json.loads(
                (Path(directory) / "evidence" / "bootstrap-result.json").read_text()
            )
            self.assertEqual("admin_api_fallback", result["bootstrap_method"])
            self.assertEqual("<redacted>", result["redacted_config"]["DB_CONNECTION_URI"])

    def test_admin_api_fallback_failure_writes_redacted_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            service = _service(
                cli=_FakeCli(available=False),
                bootstrap_client=_FailingBootstrapClient(),
                evidence_dir=Path(directory) / "evidence",
                secret_file=Path(directory) / "secrets" / "bootstrap.local.env",
            )

            with self.assertRaises(_BootstrapUnavailable):
                service.run()

            result = json.loads((Path(directory) / "evidence" / "bootstrap-result.json").read_text())
            self.assertEqual("failed", result["status"])
            self.assertEqual("infisical_bootstrap_api_unavailable", result["classification"])
            self.assertEqual("502", result["diagnostic"]["bootstrap_http_status"])
            self.assertNotIn(operator_credential(), json.dumps(result))

    def test_readiness_timeout_is_classified(self):
        with tempfile.TemporaryDirectory() as directory:
            service = _service(
                service_running=True,
                http_ready=False,
                evidence_dir=Path(directory) / "evidence",
                secret_file=Path(directory) / "secrets" / "bootstrap.local.env",
            )

            with self.assertRaises(InfisicalInstallBlocker) as raised:
                service.run()

            self.assertEqual(
                "infisical_readiness_timeout",
                raised.exception.classification,
            )

    def test_already_bootstrapped_result_is_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            service = _service(
                cli=_FakeCli(result=InfisicalCliResult(0, "Already bootstrapped", "")),
                evidence_dir=Path(directory) / "evidence",
                secret_file=Path(directory) / "secrets" / "bootstrap.local.env",
            )

            service.run()
            verification = service.verify()

            self.assertEqual(VerificationStatus.VERIFIED, verification.status)
            self.assertEqual("already_bootstrapped", verification.evidence["bootstrap_state"])
            result = json.loads(
                (Path(directory) / "evidence" / "bootstrap-result.json").read_text()
            )
            self.assertEqual("already_bootstrapped", result["status"])


def _service(
    *,
    cli: "_FakeCli | None" = None,
    bootstrap_client: "_FakeBootstrapClient | None" = None,
    evidence_dir: Path = Path(".tiny-swarm/evidence/infisical"),
    secret_file: Path = Path(".tiny-swarm/secrets/bootstrap.local.env"),
    service_running: bool = True,
    http_ready: bool = True,
) -> Any:
    return EnsureInfisicalSilentInstall(
        cli=cli or _FakeCli(),
        bootstrap_client=bootstrap_client,
        config=InfisicalSilentInstallConfig(
            external_url="http://localhost:8086",
            internal_url="http://infisical:8080",
            admin_email="admin@tiny-swarm.local",
            admin_first_name="Tiny",
            admin_last_name="Admin",
            organization="Tiny Swarm World",
            **{
                sample_text("admin_", "pass", "word"): operator_credential(),
                sample_text("encryption_", "key"): "enc",
                sample_text("auth_", "secret"): "auth",
                sample_text("postgres_", "pass", "word"): "pg",
                sample_text("redis_", "pass", "word"): "redis",
            },
            evidence_dir=evidence_dir,
            secret_file=secret_file,
        ),
        service_running=service_running,
        http_ready=http_ready,
    )


class _FakeCli:
    def __init__(
        self,
        *,
        available: bool = True,
        result: InfisicalCliResult = InfisicalCliResult(0, "created", ""),
    ):
        self.available = available
        self.result = result
        self.calls: list[tuple[str, ...]] = []

    def is_available(self) -> bool:
        return self.available

    def run_bootstrap(self, args: tuple[str, ...]) -> InfisicalCliResult:
        self.calls.append(args)
        return self.result


class _FakeBootstrapClient:
    def __init__(
        self,
        result: InfisicalBootstrapResult = InfisicalBootstrapResult(
            state=InfisicalBootstrapState.CREATED,
            token_returned=True,
            organization="Tiny Swarm World",
            admin_email="admin@tiny-swarm.local",
        ),
    ):
        self.result = result
        self.calls: list[tuple[str, str]] = []

    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        self.calls.append((email, organization))
        return self.result


class _BootstrapUnavailable(RuntimeError):
    status_code = 502
    reason = "not_ready"


class _FailingBootstrapClient:
    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        raise _BootstrapUnavailable("Infisical bootstrap API is not ready.")


if __name__ == "__main__":
    unittest.main()

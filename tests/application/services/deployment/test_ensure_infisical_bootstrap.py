import importlib.util
import unittest
from pathlib import Path

from tiny_swarm_world.application.ports.clients.port_infisical_bootstrap_client import (
    InfisicalBootstrapResult,
    InfisicalBootstrapState,
)
from tiny_swarm_world.domain.inventory import VerificationStatus

MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "tiny_swarm_world"
    / "application"
    / "services"
    / "deployment"
    / "ensure_infisical_bootstrap.py"
)


def _load_service_module():
    spec = importlib.util.spec_from_file_location("ensure_infisical_bootstrap", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Infisical bootstrap service module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EnsureInfisicalBootstrap = _load_service_module().EnsureInfisicalBootstrap


class TestEnsureInfisicalBootstrap(unittest.TestCase):
    def test_bootstraps_instance_without_exposing_password_or_token(self):
        client = _FakeBootstrapClient(
            InfisicalBootstrapResult(
                state=InfisicalBootstrapState.CREATED,
                token_returned=True,
                organization="Tiny Swarm World",
                admin_email="admin@tiny-swarm-world.local",
            )
        )
        service = EnsureInfisicalBootstrap(
            client,
            "admin@tiny-swarm-world.local",
            "infisical-password",
            "Tiny Swarm World",
        )

        service.run()
        result = service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(
            "created",
            result.evidence["bootstrap_state"],
        )
        self.assertEqual("true", result.evidence["admin_identity_available"])
        self.assertNotIn("infisical-password", str(result.evidence))
        self.assertNotIn("token", str(client.calls))

    def test_verify_blocks_before_run(self):
        service = EnsureInfisicalBootstrap(
            _FakeBootstrapClient(
                InfisicalBootstrapResult(InfisicalBootstrapState.CREATED)
            ),
            "admin@tiny-swarm-world.local",
            "infisical-password",
            "Tiny Swarm World",
        )

        result = service.verify()

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("not_run", result.evidence["bootstrap_state"])

    def test_run_propagates_redacted_bootstrap_unavailable(self):
        service = EnsureInfisicalBootstrap(
            _FailingBootstrapClient(),
            "admin@tiny-swarm-world.local",
            "infisical-password",
            "Tiny Swarm World",
        )

        with self.assertRaises(_BootstrapUnavailable) as raised:
            service.run()

        self.assertEqual(502, raised.exception.status_code)
        self.assertNotIn("infisical-password", str(raised.exception))


class _FakeBootstrapClient:
    def __init__(self, result: InfisicalBootstrapResult):
        self.result = result
        self.calls: list[dict[str, str]] = []

    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        self.calls.append(
            {
                "email": email,
                "password": password,
                "organization": organization,
            }
        )
        return self.result


class _BootstrapUnavailable(RuntimeError):
    status_code = 502
    reason = "not_ready"

    def __str__(self):
        return "Infisical bootstrap API is not ready."


class _FailingBootstrapClient:
    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        raise _BootstrapUnavailable()


if __name__ == "__main__":
    unittest.main()

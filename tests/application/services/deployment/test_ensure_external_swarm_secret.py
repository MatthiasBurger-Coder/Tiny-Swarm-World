import unittest

from tiny_swarm_world.application.services.deployment.ensure_external_swarm_secret import (
    EnsureExternalSwarmSecret,
)


class TestEnsureExternalSwarmSecret(unittest.TestCase):
    def test_creates_external_secret_through_runtime_port(self):
        runtime = _FakeSwarmRuntime()
        service = EnsureExternalSwarmSecret(
            runtime,
            "tsw_vaultwarden_admin_token",
            "operator-token",
        )

        service.run()

        self.assertEqual(
            [("tsw_vaultwarden_admin_token", "operator-token")],
            runtime.ensured_secrets,
        )

    def test_rejects_empty_secret_name(self):
        with self.assertRaises(ValueError):
            EnsureExternalSwarmSecret(_FakeSwarmRuntime(), "", "operator-token")

    def test_rejects_empty_secret_value(self):
        with self.assertRaises(ValueError):
            EnsureExternalSwarmSecret(_FakeSwarmRuntime(), "tsw_vaultwarden_admin_token", "")


class _FakeSwarmRuntime:
    def __init__(self):
        self.ensured_secrets: list[tuple[str, str]] = []

    def deploy_stack(self, stack_definition, stack_environment=None):
        return None

    def stack_exists(self, stack_name: str) -> bool:
        return False

    def list_stack_services(self, stack_name: str) -> tuple[object, ...]:
        return ()

    def external_secret_exists(self, name: str) -> bool:
        return False

    def ensure_external_secret(self, name: str, value: str) -> None:
        self.ensured_secrets.append((name, value))


if __name__ == "__main__":
    unittest.main()

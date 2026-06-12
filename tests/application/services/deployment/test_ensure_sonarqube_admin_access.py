import unittest

from tiny_swarm_world.application.services.deployment.ensure_sonarqube_admin_access import (
    EnsureSonarqubeAdminAccess,
)
from tiny_swarm_world.application.ports.clients.port_sonarqube_client import (
    PortSonarqubeClient,
)
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsureSonarqubeAdminAccess(unittest.TestCase):
    def test_keeps_existing_configured_password(self):
        client = _FakeSonarqubeClient(configured_valid=True, initial_valid=False)
        step = _step(client)

        step.run()
        verification = step.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("already_configured", verification.evidence["status"])
        self.assertEqual([], client.changed_passwords)

    def test_rotates_default_admin_password_to_configured_password(self):
        client = _FakeSonarqubeClient(configured_valid=False, initial_valid=True)
        step = _step(client)

        step.run()

        self.assertEqual([("admin", "admin", "configured")], client.changed_passwords)

    def test_blocks_when_neither_configured_nor_default_password_works(self):
        client = _FakeSonarqubeClient(configured_valid=False, initial_valid=False)
        step = _step(client)

        with self.assertRaises(RuntimeError):
            step.run()

    def test_retries_transient_authentication_transport_failures(self):
        client = _FakeSonarqubeClient(
            configured_valid=False,
            initial_valid=True,
            transient_auth_failures=1,
        )
        step = _step(client)

        step.run()

        self.assertEqual([("admin", "admin", "configured")], client.changed_passwords)

    def test_retries_default_admin_false_until_sonarqube_auth_is_ready(self):
        client = _FakeSonarqubeClient(
            configured_valid=False,
            initial_valid=True,
            initial_false_responses=2,
        )
        step = _step(client)

        step.run()

        self.assertEqual([("admin", "admin", "configured")], client.changed_passwords)
        self.assertEqual(3, client.password_auth_attempts["admin"])


def _step(client: "_FakeSonarqubeClient") -> EnsureSonarqubeAdminAccess:
    return EnsureSonarqubeAdminAccess(
        sonarqube_client=client,
        username="admin",
        password="configured",
        wait_seconds=0,
    )


class _FakeSonarqubeClient(PortSonarqubeClient):
    def __init__(
        self,
        *,
        configured_valid: bool,
        initial_valid: bool,
        transient_auth_failures: int = 0,
        initial_false_responses: int = 0,
    ):
        self.configured_valid = configured_valid
        self.initial_valid = initial_valid
        self.transient_auth_failures = transient_auth_failures
        self.initial_false_responses = initial_false_responses
        self.changed_passwords: list[tuple[str, str, str]] = []
        self.password_auth_attempts: dict[str, int] = {}

    def is_available(self) -> bool:
        return True

    def can_authenticate(self, username: str, password: str) -> bool:
        self.password_auth_attempts[password] = self.password_auth_attempts.get(password, 0) + 1
        if self.transient_auth_failures:
            self.transient_auth_failures -= 1
            raise RuntimeError("redacted transient auth failure")
        if password == "configured":
            return self.configured_valid
        if password == "admin":
            if self.initial_false_responses:
                self.initial_false_responses -= 1
                return False
            return self.initial_valid
        return False

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        self.changed_passwords.append((username, current_password, new_password))
        self.configured_valid = True
        self.initial_valid = False


if __name__ == "__main__":
    unittest.main()

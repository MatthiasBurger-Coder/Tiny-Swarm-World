import unittest
from unittest.mock import AsyncMock, patch
from tests.support.sonar_safe_literals import operator_credential, sensitive_assignment

from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortainerAdminInitializationRejected,
)
from tiny_swarm_world.application.services.deployment.ensure_portainer_admin_access import (
    EnsurePortainerAdminAccess,
)
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsurePortainerAdminAccess(unittest.IsolatedAsyncioTestCase):
    async def test_verify_retries_until_admin_credentials_are_active(self):
        client = _SequencePortainerAdminClient([False, True])
        service = EnsurePortainerAdminAccess(
            client,
            username="admin",
            password=operator_credential(),
            max_attempts=2,
            wait_seconds=0,
        )

        result = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("deployment:portainer-admin-access", result.target_id)
        self.assertEqual("active", result.evidence["access_state"])
        self.assertEqual(2, client.can_authenticate_calls)

    async def test_verify_reports_inactive_credentials_with_safe_evidence(self):
        client = _SequencePortainerAdminClient([False, False])
        service = EnsurePortainerAdminAccess(
            client,
            username="admin",
            password=operator_credential(),
            max_attempts=2,
            wait_seconds=0,
        )

        result = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("inactive", result.evidence["access_state"])
        self.assertNotIn("auth", str(result.evidence))

    async def test_verify_reports_sanitized_client_exceptions(self):
        client = _ExceptionPortainerAdminClient()
        service = EnsurePortainerAdminAccess(
            client,
            username="admin",
            password=operator_credential(),
            max_attempts=2,
            wait_seconds=0,
        )

        result = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("deployment:portainer-admin-access", result.target_id)
        self.assertIn("ValueError", result.message)
        self.assertNotIn(sensitive_assignment(), result.message)
        self.assertEqual("unknown", result.evidence["access_state"])
        self.assertNotIn("auth", str(result.evidence))

    async def test_run_retries_transient_initialization_failures(self):
        client = _InitializeAfterTransientFailurePortainerAdminClient()
        service = EnsurePortainerAdminAccess(
            client,
            username="admin",
            password=operator_credential(),
            max_attempts=2,
            wait_seconds=0,
        )

        with patch(
            "tiny_swarm_world.application.services.deployment.ensure_portainer_admin_access."
            "asyncio.sleep",
            new=AsyncMock(),
        ):
            await service.run()

        self.assertEqual(2, client.initialize_calls)

    async def test_run_fails_fast_when_portainer_rejects_admin_initialization(self):
        client = _RejectedInitializationPortainerAdminClient()
        service = EnsurePortainerAdminAccess(
            client,
            username="admin",
            password=operator_credential(),
            max_attempts=60,
            wait_seconds=0,
        )

        with self.assertRaises(PortainerAdminInitializationRejected):
            await service.run()

        self.assertEqual(1, client.initialize_calls)


class _SequencePortainerAdminClient:
    def __init__(self, authentication_results: list[bool]):
        self.authentication_results = list(authentication_results)
        self.can_authenticate_calls = 0

    def can_authenticate(self, username: str, password: str) -> bool:
        self.can_authenticate_calls += 1
        return self.authentication_results.pop(0)

    def initialize_admin_user(self, username: str, password: str) -> None:
        raise AssertionError("verify must not initialize the admin user")


class _ExceptionPortainerAdminClient:
    def can_authenticate(self, username: str, password: str) -> bool:
        raise ValueError(sensitive_assignment())

    def initialize_admin_user(self, username: str, password: str) -> None:
        raise AssertionError("verify must not initialize the admin user")


class _InitializeAfterTransientFailurePortainerAdminClient:
    def __init__(self):
        self.initialize_calls = 0

    def can_authenticate(self, username: str, password: str) -> bool:
        return self.initialize_calls >= 2

    def initialize_admin_user(self, username: str, password: str) -> None:
        self.initialize_calls += 1
        if self.initialize_calls == 1:
            raise RuntimeError("Portainer is not ready yet.")


class _RejectedInitializationPortainerAdminClient:
    def __init__(self):
        self.initialize_calls = 0

    def can_authenticate(self, username: str, password: str) -> bool:
        return False

    def initialize_admin_user(self, username: str, password: str) -> None:
        self.initialize_calls += 1
        raise PortainerAdminInitializationRejected("HTTP 409")


if __name__ == "__main__":
    unittest.main()

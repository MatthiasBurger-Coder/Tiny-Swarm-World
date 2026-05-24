import unittest

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
            password="operator-password",
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
            password="operator-password",
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
            password="operator-password",
            max_attempts=2,
            wait_seconds=0,
        )

        result = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("deployment:portainer-admin-access", result.target_id)
        self.assertIn("ValueError", result.message)
        self.assertNotIn("secret=leaked", result.message)
        self.assertEqual("unknown", result.evidence["access_state"])
        self.assertNotIn("auth", str(result.evidence))


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
        raise ValueError("secret=leaked")

    def initialize_admin_user(self, username: str, password: str) -> None:
        raise AssertionError("verify must not initialize the admin user")


if __name__ == "__main__":
    unittest.main()

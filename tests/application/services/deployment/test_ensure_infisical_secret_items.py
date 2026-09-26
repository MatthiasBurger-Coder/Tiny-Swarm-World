import asyncio
import unittest
from unittest.mock import MagicMock
from tiny_swarm_world.application.services.deployment.workflows import DeploymentApplyWorkflow

from tests.support.sonar_safe_literals import operator_credential
from tiny_swarm_world.application.services.deployment.ensure_infisical_secret_items import (
    EnsureInfisicalSecretItems,
    InfisicalSecretItem,
)
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsureInfisicalSecretItems(unittest.TestCase):
    def test_authentication_exhaustion_is_expected_without_new_retries(self):
        client = MagicMock()
        client.can_authenticate.return_value = False
        service = EnsureInfisicalSecretItems(client, "admin@example.com", operator_credential(), (InfisicalSecretItem("item", "admin", operator_credential()),), max_attempts=2, wait_seconds=0)
        result = asyncio.run(DeploymentApplyWorkflow((service,)).run())
        self.assertEqual("dependency_unavailable", result.operation_result.failures[0].cause)
        self.assertEqual("deployment.infisical.authenticate", result.operation_result.failures[0].operation)
        self.assertEqual(2, client.can_authenticate.call_count)
        client.create_secret_item.assert_not_called()


    def test_creates_only_missing_items(self):
        existing = {"platform/jenkins"}
        client = _FakeInfisicalClient(existing)
        service = EnsureInfisicalSecretItems(
            client,
            "admin@example.com",
            operator_credential(),
            (
                InfisicalSecretItem("platform/jenkins", "admin", operator_credential()),
                InfisicalSecretItem("platform/nexus", "admin", operator_credential()),
            ),
            wait_seconds=0,
        )

        asyncio.run(service.run())

        self.assertEqual(client.created_items, ["platform/nexus"])

    def test_verify_reports_missing_item_names_without_secret_values(self):
        client = _FakeInfisicalClient({"platform/jenkins"})
        missing_value = operator_credential()
        service = EnsureInfisicalSecretItems(
            client,
            "admin@example.com",
            operator_credential(),
            (
                InfisicalSecretItem("platform/jenkins", "admin", operator_credential()),
                InfisicalSecretItem("platform/nexus", "admin", missing_value),
            ),
            wait_seconds=0,
        )

        result = asyncio.run(service.verify())

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(result.evidence["missing_items"], "platform/nexus")
        self.assertNotIn(missing_value, str(result.evidence))

    def test_verify_fails_when_login_is_inactive(self):
        client = _FakeInfisicalClient(set(), can_authenticate=False)
        service = EnsureInfisicalSecretItems(
            client,
            "admin@example.com",
            operator_credential(),
            (InfisicalSecretItem("platform/jenkins", "admin", operator_credential()),),
            wait_seconds=0,
        )

        result = asyncio.run(service.verify())

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(result.evidence["access_state"], "inactive")


class _FakeInfisicalClient:
    def __init__(self, existing_items: set[str], *, can_authenticate: bool = True):
        self.existing_items = existing_items
        self.authentication_active = can_authenticate
        self.created_items: list[str] = []

    def can_authenticate(self, email: str, password: str) -> bool:
        return self.authentication_active

    def secret_item_exists(self, email: str, password: str, item_name: str) -> bool:
        return item_name in self.existing_items

    def create_secret_item(
        self,
        email: str,
        password: str,
        item_name: str,
        username: str,
        secret_value: str,
    ) -> None:
        self.created_items.append(item_name)
        self.existing_items.add(item_name)


if __name__ == "__main__":
    unittest.main()

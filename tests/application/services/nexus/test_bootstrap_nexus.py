import unittest
from unittest.mock import MagicMock, patch

from application.services.nexus.bootstrap_nexus import BootstrapNexus
from application.services.nexus.enable_nexus_anonymous_access import EnableNexusAnonymousAccess
from application.services.nexus.ensure_nexus_admin_access import EnsureNexusAdminAccess
from application.services.nexus.ensure_nexus_stack import EnsureNexusStack
from application.services.nexus.wait_for_nexus_ready import WaitForNexusReady
from domain.deployment.stack_definition import StackDefinition
from domain.nexus.nexus_user import NexusUser


class TestEnsureNexusStack(unittest.TestCase):
    def test_creates_stack_when_missing(self):
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = StackDefinition(name="nexus", compose_content="services: {}")
        portainer_client = MagicMock()
        portainer_client.get_endpoint_id_by_name.return_value = 1
        portainer_client.find_stack_id_by_name.return_value = None

        service = EnsureNexusStack(compose_repository, portainer_client, "nexus", "local")
        service.run()

        portainer_client.create_stack.assert_called_once()
        portainer_client.update_stack.assert_not_called()

    def test_updates_stack_when_present(self):
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = StackDefinition(name="nexus", compose_content="services: {}")
        portainer_client = MagicMock()
        portainer_client.get_endpoint_id_by_name.return_value = 1
        portainer_client.find_stack_id_by_name.return_value = 7

        service = EnsureNexusStack(compose_repository, portainer_client, "nexus", "local")
        service.run()

        portainer_client.update_stack.assert_called_once_with(
            7,
            StackDefinition(name="nexus", compose_content="services: {}"),
            1,
        )
        portainer_client.create_stack.assert_not_called()


class TestWaitForNexusReady(unittest.TestCase):
    @patch("application.services.nexus.wait_for_nexus_ready.time.sleep")
    def test_retries_until_nexus_is_ready(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.is_available.side_effect = [False, False, True]

        service = WaitForNexusReady(nexus_client, max_attempts=3, wait_seconds=1)
        service.run()

        self.assertEqual(nexus_client.is_available.call_count, 3)

    @patch("application.services.nexus.wait_for_nexus_ready.time.sleep")
    def test_raises_timeout_when_nexus_never_becomes_ready(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.is_available.return_value = False

        service = WaitForNexusReady(nexus_client, max_attempts=2, wait_seconds=1)

        with self.assertRaises(TimeoutError):
            service.run()


class TestEnsureNexusAdminAccess(unittest.TestCase):
    @patch("application.services.nexus.ensure_nexus_admin_access.time.sleep")
    def test_skips_rotation_when_credentials_are_already_valid(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.return_value = True
        container_runtime = MagicMock()

        service = EnsureNexusAdminAccess(
            nexus_client=nexus_client,
            container_runtime=container_runtime,
            admin_username="admin",
            admin_password="secret",
            container_name_filter="nexus",
            initial_password_path="/nexus-data/admin.password",
            max_attempts=2,
            wait_seconds=1,
        )
        service.run()

        container_runtime.find_container_names.assert_not_called()
        nexus_client.change_password.assert_not_called()

    @patch("application.services.nexus.ensure_nexus_admin_access.time.sleep")
    def test_activates_admin_and_rotates_password(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.side_effect = [False, True]
        nexus_client.get_user.return_value = NexusUser(userId="admin", status="disabled", roles=["nx-admin"])
        container_runtime = MagicMock()
        container_runtime.find_container_names.return_value = ["nexus-app-1"]
        container_runtime.file_exists.return_value = True
        container_runtime.read_file.return_value = "initial-password"

        service = EnsureNexusAdminAccess(
            nexus_client=nexus_client,
            container_runtime=container_runtime,
            admin_username="admin",
            admin_password="secret",
            container_name_filter="nexus",
            initial_password_path="/nexus-data/admin.password",
            max_attempts=2,
            wait_seconds=1,
        )
        service.run()

        nexus_client.get_user.assert_called_once_with("admin", "initial-password", "admin")
        nexus_client.change_password.assert_called_once_with("admin", "initial-password", "admin", "secret")
        updated_user = nexus_client.update_user.call_args.args[2]
        self.assertEqual(updated_user.status, "active")


class TestBootstrapNexus(unittest.TestCase):
    def test_runs_bootstrap_steps_in_order(self):
        execution_order: list[str] = []

        ensure_nexus_stack = MagicMock()
        ensure_nexus_stack.run.side_effect = lambda: execution_order.append("stack")
        wait_for_nexus_ready = MagicMock()
        wait_for_nexus_ready.run.side_effect = lambda: execution_order.append("wait")
        ensure_nexus_admin_access = MagicMock()
        ensure_nexus_admin_access.run.side_effect = lambda: execution_order.append("admin")
        enable_nexus_anonymous_access = MagicMock()
        enable_nexus_anonymous_access.run.side_effect = lambda: execution_order.append("anonymous")

        bootstrapper = BootstrapNexus(
            ensure_nexus_stack=ensure_nexus_stack,
            wait_for_nexus_ready=wait_for_nexus_ready,
            ensure_nexus_admin_access=ensure_nexus_admin_access,
            enable_nexus_anonymous_access=enable_nexus_anonymous_access,
        )
        bootstrapper.run()

        self.assertEqual(execution_order, ["stack", "wait", "admin", "anonymous"])


class TestEnableNexusAnonymousAccess(unittest.TestCase):
    def test_enables_anonymous_access(self):
        nexus_client = MagicMock()

        service = EnableNexusAnonymousAccess(nexus_client, "admin", "secret")
        service.run()

        nexus_client.set_anonymous_access.assert_called_once_with("admin", "secret", enabled=True)

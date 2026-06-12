import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests.support.sonar_safe_literals import sample_text

from tiny_swarm_world.application.services.nexus.bootstrap_nexus import BootstrapNexus
from tiny_swarm_world.application.services.nexus.enable_nexus_anonymous_access import EnableNexusAnonymousAccess
from tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access import EnsureNexusAdminAccess
from tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access import (
    NexusAdminAccessRecoveryBlocked,
)
from tiny_swarm_world.application.services.nexus.nexus_bootstrap_configuration import NexusBootstrapConfiguration
from tiny_swarm_world.application.services.nexus.wait_for_nexus_ready import WaitForNexusReady
from tiny_swarm_world.domain.nexus.nexus_user import NexusUser


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class TestWaitForNexusReady(unittest.TestCase):
    @patch("tiny_swarm_world.application.services.nexus.wait_for_nexus_ready.time.sleep")
    def test_retries_until_nexus_is_ready(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.is_available.side_effect = [False, False, True]

        service = WaitForNexusReady(nexus_client, max_attempts=3, wait_seconds=1)
        service.run()

        self.assertEqual(nexus_client.is_available.call_count, 3)

    @patch("tiny_swarm_world.application.services.nexus.wait_for_nexus_ready.time.sleep")
    def test_retries_transient_connection_errors_until_nexus_is_ready(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.is_available.side_effect = [ConnectionError("connection refused"), True]

        service = WaitForNexusReady(nexus_client, max_attempts=2, wait_seconds=1)
        service.run()

        self.assertEqual(nexus_client.is_available.call_count, 2)

    @patch("tiny_swarm_world.application.services.nexus.wait_for_nexus_ready.time.sleep")
    def test_raises_timeout_when_nexus_never_becomes_ready(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.is_available.return_value = False

        service = WaitForNexusReady(nexus_client, max_attempts=2, wait_seconds=1)

        with self.assertRaises(TimeoutError):
            service.run()

    @patch("tiny_swarm_world.application.services.nexus.wait_for_nexus_ready.time.sleep")
    def test_raises_timeout_from_last_connection_error(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.is_available.side_effect = ConnectionError("connection refused")

        service = WaitForNexusReady(nexus_client, max_attempts=2, wait_seconds=1)

        with self.assertRaises(TimeoutError) as raised:
            service.run()

        self.assertIsInstance(raised.exception.__cause__, ConnectionError)


class TestEnsureNexusAdminAccess(unittest.TestCase):
    @patch("tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access.time.sleep")
    def test_skips_rotation_when_credentials_are_already_valid(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.return_value = True
        container_runtime = MagicMock()
        active_value = sample_text("se", "cret")

        service = EnsureNexusAdminAccess(
            nexus_client=nexus_client,
            container_runtime=container_runtime,
            admin_username="admin",
            admin_password=active_value,
            container_name_filter="nexus",
            initial_password_path="/nexus-data/admin.password",
            max_attempts=2,
            wait_seconds=1,
        )
        service.run()

        container_runtime.find_container_names.assert_not_called()
        nexus_client.change_password.assert_not_called()

    @patch("tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access.time.sleep")
    def test_activates_admin_and_rotates_password(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.side_effect = [False, False, True]
        nexus_client.get_user.return_value = NexusUser(userId="admin", status="disabled", roles=["nx-admin"])
        container_runtime = MagicMock()
        container_runtime.find_container_names.return_value = ["nexus-app-1"]
        container_runtime.file_exists.return_value = True
        initial_value = sample_text("initial", "-", "pass", "word")
        active_value = sample_text("se", "cret")
        container_runtime.read_file.return_value = initial_value

        service = EnsureNexusAdminAccess(
            nexus_client=nexus_client,
            container_runtime=container_runtime,
            admin_username="admin",
            admin_password=active_value,
            container_name_filter="nexus",
            initial_password_path="/nexus-data/admin.password",
            max_attempts=2,
            wait_seconds=1,
        )
        service.run()

        nexus_client.get_user.assert_called_once_with("admin", initial_value, "admin")
        nexus_client.change_password.assert_called_once_with("admin", initial_value, "admin", active_value)
        self.assertEqual(3, nexus_client.can_authenticate.call_count)
        updated_user = nexus_client.update_user.call_args.args[2]
        self.assertEqual(updated_user.status, "active")

    @patch("tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access.time.sleep")
    def test_retries_transient_admin_rotation_failures(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.side_effect = [False, False, True]
        nexus_client.get_user.side_effect = [
            RuntimeError("temporary Nexus API failure"),
            NexusUser(userId="admin", status="active", roles=["nx-admin"]),
        ]
        container_runtime = MagicMock()
        container_runtime.find_container_names.return_value = ["nexus-app-1"]
        container_runtime.file_exists.return_value = True
        initial_value = sample_text("initial", "-", "pass", "word")
        active_value = sample_text("se", "cret")
        container_runtime.read_file.return_value = initial_value

        service = EnsureNexusAdminAccess(
            nexus_client=nexus_client,
            container_runtime=container_runtime,
            admin_username="admin",
            admin_password=active_value,
            container_name_filter="nexus",
            initial_password_path="/nexus-data/admin.password",
            max_attempts=2,
            wait_seconds=1,
        )
        service.run()

        self.assertEqual(2, nexus_client.get_user.call_count)
        nexus_client.change_password.assert_called_once_with("admin", initial_value, "admin", active_value)

    def test_verify_reports_active_credentials_with_safe_evidence(self):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.return_value = True
        service = _nexus_admin_access(nexus_client)

        result = _run_async(service.verify())

        self.assertEqual("artifacts:nexus-admin-access", result.target_id)
        self.assertEqual("active", result.evidence["access_state"])
        self.assertNotIn("auth", str(result.evidence))

    def test_verify_reports_inactive_credentials_with_safe_evidence(self):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.return_value = False
        service = _nexus_admin_access(nexus_client)

        result = _run_async(service.verify())

        self.assertEqual("inactive", result.evidence["access_state"])
        self.assertNotIn("auth", str(result.evidence))

    def test_verify_reports_sanitized_client_exceptions(self):
        nexus_client = MagicMock()
        leaked_value = sample_text("pass", "word", "=leaked")
        nexus_client.can_authenticate.side_effect = ValueError(leaked_value)
        service = _nexus_admin_access(nexus_client)

        result = _run_async(service.verify())

        self.assertEqual("unknown", result.evidence["access_state"])
        self.assertNotIn(leaked_value, result.message)
        self.assertNotIn("auth", str(result.evidence))

    @patch("tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access.time.sleep")
    def test_run_logs_and_updates_ui_when_initial_password_is_unavailable(self, _mock_sleep):
        nexus_client = MagicMock()
        nexus_client.can_authenticate.return_value = False
        container_runtime = MagicMock()
        container_runtime.find_container_names.return_value = ["nexus-app-1"]
        container_runtime.file_exists.return_value = False
        ui = _RecordingUI()
        service = EnsureNexusAdminAccess(
            nexus_client=nexus_client,
            container_runtime=container_runtime,
            admin_username="admin",
            admin_password=sample_text("se", "cret"),
            container_name_filter="nexus",
            initial_password_path="/nexus-data/admin.password",
            max_attempts=1,
            wait_seconds=0,
            ui=ui,
        )

        with self.assertLogs("EnsureNexusAdminAccess", level="ERROR") as captured:
            with self.assertRaises(NexusAdminAccessRecoveryBlocked) as raised:
                service.run()

        self.assertEqual("initial_admin_value_unavailable", raised.exception.diagnostic)
        self.assertIn("NexusAdminAccessRecoveryBlocked", captured.output[0])
        self.assertIn("initial_admin_value_unavailable", captured.output[0])
        self.assertNotIn(sample_text("se", "cret"), captured.output[0])
        self.assertEqual(
            [("all", "artifacts:nexus-admin-access", "Error", "failed_to_apply")],
            ui.calls,
        )


class TestBootstrapNexus(unittest.TestCase):
    def test_runs_bootstrap_steps_in_order_without_anonymous_access_by_default(self):
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

        self.assertEqual(execution_order, ["stack", "wait", "admin"])
        enable_nexus_anonymous_access.run.assert_not_called()

    def test_runs_anonymous_access_step_only_when_enabled(self):
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
            enable_anonymous_access=True,
        )
        bootstrapper.run()

        self.assertEqual(execution_order, ["stack", "wait", "admin", "anonymous"])

    def test_bootstrap_configuration_does_not_carry_committed_credential_defaults(self):
        configuration = NexusBootstrapConfiguration()

        self.assertEqual("", configuration.portainer_password)
        self.assertEqual("", configuration.admin_password)
        self.assertFalse(configuration.anonymous_access_enabled)

    def test_committed_nexus_compose_matches_initial_password_path(self):
        compose_text = (
            REPOSITORY_ROOT / "infra" / "config" / "compose" / "nexus" / "docker-compose.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("nexus-data:/nexus-data", compose_text)
        self.assertNotIn("nexus-data:/sonatype-work:latest", compose_text)


class TestEnableNexusAnonymousAccess(unittest.TestCase):
    def test_enables_anonymous_access(self):
        nexus_client = MagicMock()
        active_value = sample_text("se", "cret")

        service = EnableNexusAnonymousAccess(nexus_client, "admin", active_value)
        service.run()

        nexus_client.set_anonymous_access.assert_called_once_with("admin", active_value, enabled=True)


def _nexus_admin_access(nexus_client: MagicMock) -> EnsureNexusAdminAccess:
    return EnsureNexusAdminAccess(
        nexus_client=nexus_client,
        container_runtime=MagicMock(),
        admin_username="admin",
        admin_password=sample_text("se", "cret"),
        container_name_filter="nexus",
        initial_password_path="/nexus-data/admin.password",
        max_attempts=2,
        wait_seconds=1,
    )


def _run_async(coro):
    import asyncio

    return asyncio.run(coro)


class _RecordingUI:
    def __init__(self):
        self.calls: list[tuple[str, str, str, str]] = []

    def update_status(self, instance, task, step, result=None):
        self.calls.append((instance, task, step, result))

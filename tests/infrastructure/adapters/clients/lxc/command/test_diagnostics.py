import subprocess
import unittest

from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.diagnostics import (
    command_failed,
    is_transient_manager_shell_failure,
    safe_log_text,
)


class TestLxcCommandDiagnostics(unittest.TestCase):
    def test_command_failed_supports_timeout_and_process_results(self):
        self.assertTrue(command_failed(type("TimedOut", (), {"returncode": 0, "timed_out": True})()))
        self.assertTrue(command_failed(type("Failed", (), {"returncode": 1, "timed_out": False})()))
        self.assertFalse(command_failed(type("Succeeded", (), {"returncode": 0, "timed_out": False})()))

    def test_safe_log_text_redacts_secrets_and_bounds_output(self):
        value = (
            "TSW_TOKEN=header.payload.signature Authorization: Bearer bearer-value "
            "authParams=token:parameter-value trailing-output"
        )

        result = safe_log_text(value, limit=35)

        self.assertNotIn("header.payload.signature", result)
        self.assertNotIn("bearer-value", result)
        self.assertNotIn("parameter-value", result)
        self.assertTrue(result.endswith("..."))
        self.assertLessEqual(len(result), 38)

    def test_transient_failure_requires_incus_child_pid_error(self):
        transient = subprocess.CompletedProcess(
            [],
            255,
            stdout="",
            stderr="Failed to retrieve PID of executing child process",
        )
        permanent = subprocess.CompletedProcess([], 255, stdout="", stderr="other failure")

        self.assertTrue(is_transient_manager_shell_failure(transient))
        self.assertFalse(is_transient_manager_shell_failure(permanent))

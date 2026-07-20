import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.host.hang_diagnostics import (
    ReadOnlyHangDiagnostics,
    _run_command,
)
from tiny_swarm_world.domain.preflight.hang_diagnostics import HangDiagnosticCommand


class HangDiagnosticsTests(unittest.TestCase):
    def test_rejects_non_positive_timeout(self):
        with self.assertRaises(ValueError):
            ReadOnlyHangDiagnostics(timeout_seconds=0)

    def test_collects_read_only_commands_with_bounded_timeout(self):
        calls = []

        def runner(name, args, timeout):
            calls.append((name, args, timeout))
            return HangDiagnosticCommand(name, "OK", "fixture")

        report = ReadOnlyHangDiagnostics(runner, timeout_seconds=3).collect()
        self.assertTrue(report.read_only)
        self.assertEqual(4, len(report.commands))
        self.assertTrue(all(call[2] == 3 for call in calls))
        self.assertEqual("processes", report.commands[0].name)

    @patch("tiny_swarm_world.infrastructure.adapters.host.hang_diagnostics.subprocess.run")
    def test_command_runner_maps_timeout(self, run):
        import subprocess

        run.side_effect = subprocess.TimeoutExpired(("ps",), 2)

        result = _run_command("processes", ("ps",), 2)

        self.assertEqual("TIMED_OUT", result.status)
        self.assertTrue(result.timed_out)

    @patch("tiny_swarm_world.infrastructure.adapters.host.hang_diagnostics.subprocess.run")
    def test_command_runner_maps_unavailable_command(self, run):
        run.side_effect = OSError("missing")

        result = _run_command("docker_services", ("docker",), 2)

        self.assertEqual("UNAVAILABLE", result.status)

    @patch("tiny_swarm_world.infrastructure.adapters.host.hang_diagnostics.subprocess.run")
    def test_command_runner_maps_non_zero_exit(self, run):
        run.return_value = type("Completed", (), {"returncode": 1, "stdout": "failure"})()

        result = _run_command("docker_tasks", ("docker",), 2)

        self.assertEqual("FAILED", result.status)
        self.assertEqual("failure", result.output)

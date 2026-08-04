import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.host.hang_diagnostics import (
    ReadOnlyHangDiagnostics,
    _classify,
    _contains_high_cpu_process,
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
        self.assertEqual(9, len(report.commands))
        self.assertTrue(all(call[2] == 3 for call in calls))
        self.assertEqual("processes", report.commands[0].name)

        docker_logs = next(call for call in calls if call[0] == "docker_logs")
        self.assertIn("docker logs --tail 100", docker_logs[1][2])

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

    def test_classifies_process_wait_states_without_mutation(self):
        cases = (
            ("<defunct>", "exited_uncollected"),
            ("wchan=io_schedule", "io_wait"),
            ("wchan=sock_read", "network_wait"),
            ("state D pipe_read", "blocked_child"),
            ("PID PPID STAT ETIME %CPU %MEM WCHAN CMD\n1 2 S 1 90.0 1.0 run worker", "cpu_bound"),
            ("PID PPID STAT ETIME %CPU %MEM WCHAN CMD\n1 2 S 1 invalid 1.0 run worker", "active"),
            ("", "unknown"),
        )

        for output, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(expected, _classify("processes", output))

    def test_classifies_runtime_commands_and_handles_short_process_rows(self):
        self.assertEqual("active", _classify("docker_services", "service"))
        self.assertEqual("unknown", _classify("docker_services", ""))
        self.assertEqual("active", _classify("other", "state"))
        self.assertEqual("unknown", _classify("other", ""))
        self.assertFalse(_contains_high_cpu_process("header\nshort\n1 2 S 1 invalid 1.0 run worker"))

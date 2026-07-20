import unittest

from tiny_swarm_world.infrastructure.adapters.host.hang_diagnostics import ReadOnlyHangDiagnostics
from tiny_swarm_world.domain.preflight.hang_diagnostics import HangDiagnosticCommand


class HangDiagnosticsTests(unittest.TestCase):
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


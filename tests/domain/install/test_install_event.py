import io
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.domain.install import InstallEvent, InstallEventType, InstallStatus
from tiny_swarm_world.infrastructure.adapters.ui.install_reporter import (
    NoopInstallReporter,
    PlainConsoleInstallReporter,
    render_install_event,
)


FORBIDDEN_CONSOLE_FRAGMENTS = (
    '{"step"',
    "{'step'",
    "InstallEvent(",
    "<InstallEvent",
    "!!python",
)


def assert_console_output_is_human_readable(testcase: unittest.TestCase, output: str) -> None:
    for fragment in FORBIDDEN_CONSOLE_FRAGMENTS:
        testcase.assertNotIn(fragment, output)


class TestInstallEvent(unittest.TestCase):
    def test_started_event_represents_step_and_target(self):
        event = InstallEvent.started(
            "Preflight",
            target="host",
            message="checking host prerequisites",
            sequence=1,
            total=3,
        )

        self.assertEqual(InstallStatus.STARTED, event.status)
        self.assertEqual(event.step, "Preflight")
        self.assertEqual(event.target, "host")
        self.assertEqual(event.sequence, 1)
        self.assertEqual(event.total, 3)

    def test_failed_event_represents_reason_evidence_and_diagnostics(self):
        event = InstallEvent.failed(
            "Docker bootstrap",
            target="swarm-worker-2",
            reason="Docker service did not become healthy.",
            evidence_path=Path(".tiny-swarm/evidence/docker.log"),
            suggested_commands=("lxc exec swarm-worker-2 -- docker info",),
        )

        self.assertEqual(InstallStatus.FAILED, event.status)
        self.assertEqual(event.reason, "Docker service did not become healthy.")
        self.assertEqual(Path(".tiny-swarm/evidence/docker.log"), event.evidence_path)
        self.assertEqual(tuple(event.suggested_commands), ("lxc exec swarm-worker-2 -- docker info",))

    def test_noop_reporter_accepts_events_without_output(self):
        event = InstallEvent.succeeded("Preflight", message="Python found")

        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            NoopInstallReporter().report(event)

        self.assertEqual(stdout.getvalue(), "")

    def test_plain_reporter_renders_success_without_raw_structures(self):
        output = io.StringIO()
        event = InstallEvent.succeeded("Preflight", message="Python 3.12 found")

        PlainConsoleInstallReporter(stdout=output).report(event)

        text = output.getvalue()
        self.assertIn("OK", text)
        self.assertIn("Python 3.12 found", text)
        assert_console_output_is_human_readable(self, text)

    def test_plain_reporter_renders_failure_diagnostics_without_running_commands(self):
        output = io.StringIO()
        event = InstallEvent.failed(
            "Docker bootstrap",
            target="swarm-worker-2",
            reason="Docker service did not become healthy.",
            evidence_path=Path(".tiny-swarm/evidence/docker.log"),
            suggested_commands=("lxc exec swarm-worker-2 -- docker info",),
        )

        PlainConsoleInstallReporter(stderr=output).report(event)

        text = output.getvalue()
        self.assertIn("FAILED Docker bootstrap on swarm-worker-2", text)
        self.assertIn("Docker service did not become healthy.", text)
        self.assertIn(".tiny-swarm/evidence/docker.log", text)
        self.assertIn("lxc exec swarm-worker-2 -- docker info", text)
        assert_console_output_is_human_readable(self, text)

    def test_ci_style_line_is_human_readable_and_not_json(self):
        event = InstallEvent.failed("docker-bootstrap", target="swarm-worker-2", reason="failed")
        line = f"INSTALL {event.step} {event.status.value} target={event.target}"

        self.assertEqual("INSTALL docker-bootstrap FAILED target=swarm-worker-2", line)
        assert_console_output_is_human_readable(self, line)

    def test_renderer_does_not_return_event_repr(self):
        rendered = "\n".join(render_install_event(InstallEvent.succeeded("Preflight", message="OK")))

        assert_console_output_is_human_readable(self, rendered)

    def test_renderer_covers_install_lifecycle_events(self):
        started = render_install_event(
            InstallEvent(
                event_type=InstallEventType.INSTALL_STARTED,
                status=InstallStatus.STARTED,
                step="setup",
            )
        )
        finished = render_install_event(
            InstallEvent(
                event_type=InstallEventType.INSTALL_FINISHED,
                status=InstallStatus.SUCCEEDED,
                step="Install",
                message="done",
            )
        )
        step_started = render_install_event(
            InstallEvent.started("Preflight", message="checking", sequence=1, total=2)
        )
        evidence = render_install_event(
            InstallEvent(
                event_type=InstallEventType.EVIDENCE_WRITTEN,
                status=InstallStatus.SUCCEEDED,
                step="Report",
                evidence_path=Path(".tiny-swarm/evidence/report.json"),
            )
        )

        self.assertEqual(started[0], "Tiny Swarm World Installer")
        self.assertIn("done", finished[0])
        self.assertEqual(step_started[0], "[1/2] Preflight")
        self.assertIn(".tiny-swarm/evidence/report.json", evidence[0])


if __name__ == "__main__":
    unittest.main()

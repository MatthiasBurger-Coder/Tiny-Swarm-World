import unittest

from tiny_swarm_world.application.ports.progress import (
    NullWorkflowProgress,
    PortWorkflowProgress,
    WorkflowProgressEvent,
    report_readiness_wait,
)


class TestWorkflowProgressEvent(unittest.TestCase):
    def test_event_contains_only_safe_progress_fields(self):
        event = WorkflowProgressEvent(
            workflow="setup run",
            phase="preflight",
            target="host",
            task="Validate host prerequisites",
            step="resource checks",
            status="started",
            result="pending",
            safe_message="Checking host prerequisites.",
            recovery_hint="Resolve reported blockers and rerun setup.",
            evidence_path=".tiny-swarm-world/evidence/preflight.json",
            correlation_id="setup-123",
            trace_id="trace-456",
        )

        self.assertEqual(
            event.to_dict(),
            {
                "workflow": "setup run",
                "phase": "preflight",
                "target": "host",
                "task": "Validate host prerequisites",
                "step": "resource checks",
                "status": "started",
                "result": "pending",
                "safe_message": "Checking host prerequisites.",
                "recovery_hint": "Resolve reported blockers and rerun setup.",
                "evidence_path": ".tiny-swarm-world/evidence/preflight.json",
                "correlation_id": "setup-123",
                "trace_id": "trace-456",
            },
        )

    def test_event_cannot_represent_raw_payload_keys(self):
        event = WorkflowProgressEvent(
            workflow="setup run",
            phase="platform init",
            target="node-provider",
            task="Apply platform step",
            step="provider readiness",
            status="blocked",
            result="blocked",
            safe_message="Provider readiness blocked platform mutation.",
        )

        forbidden_keys = {
            "command",
            "environment",
            "password",
            "raw",
            "secret",
            "stderr",
            "stdout",
            "token",
        }

        self.assertTrue(forbidden_keys.isdisjoint(event.to_dict()))

    def test_event_rejects_unsafe_text_content(self):
        unsafe_values = (
            "command failed",
            "stdout contained data",
            "stderr contained data",
            "environment variable leaked",
            "secret value present",
            "password value present",
            "token value present",
            "raw payload present",
            "metadata payload",
            "context details",
            "exception text",
            "Traceback (most recent call last)",
            "stack trace",
        )

        for unsafe_value in unsafe_values:
            with self.subTest(unsafe_value=unsafe_value):
                with self.assertRaises(ValueError):
                    WorkflowProgressEvent(
                        workflow="setup run",
                        phase="platform init",
                        target="node-provider",
                        task="Apply platform step",
                        step="provider readiness",
                        status="blocked",
                        result="blocked",
                        safe_message=unsafe_value,
                    )

    def test_unexpected_payload_argument_is_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowProgressEvent(
                workflow="setup run",
                phase="platform init",
                target="node-provider",
                task="Apply platform step",
                step="provider readiness",
                status="blocked",
                result="blocked",
                safe_message="Provider readiness blocked platform mutation.",
                stdout="unsafe payload",
            )


class TestNullWorkflowProgress(unittest.TestCase):
    def test_report_accepts_progress_event_without_side_effect(self):
        progress = NullWorkflowProgress()
        event = WorkflowProgressEvent(
            workflow="setup run",
            phase="preflight",
            target="host",
            task="Validate host prerequisites",
            step="resource checks",
            status="started",
            result="pending",
            safe_message="Checking host prerequisites.",
        )

        self.assertIsNone(progress.report(event))


class TestReadinessProgress(unittest.TestCase):
    def test_readiness_wait_reports_safe_attempt_metadata(self):
        class RecordingProgress(PortWorkflowProgress):
            def __init__(self):
                self.events = []

            def report(self, event):
                self.events.append(event)

        progress = RecordingProgress()
        report_readiness_wait(
            progress,
            workflow="setup run",
            phase="deployment",
            target="nexus",
            task="Nexus readiness",
            attempt=2,
            max_attempts=3,
            wait_seconds=1.5,
        )

        self.assertEqual(len(progress.events), 1)
        self.assertEqual(progress.events[0].step, "readiness wait 2/3")
        self.assertEqual(progress.events[0].status, "running")

    def test_readiness_wait_rejects_out_of_range_attempt(self):
        with self.assertRaises(ValueError):
            report_readiness_wait(
                NullWorkflowProgress(),
                workflow="setup run",
                phase="deployment",
                target="nexus",
                task="Nexus readiness",
                attempt=3,
                max_attempts=2,
                wait_seconds=1,
            )

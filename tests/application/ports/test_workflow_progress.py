import unittest

from tiny_swarm_world.application.ports.progress import (
    NullWorkflowProgress,
    WorkflowProgressEvent,
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
            event.to_dict(),
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

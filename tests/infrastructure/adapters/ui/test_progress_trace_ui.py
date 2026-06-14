import unittest

from tiny_swarm_world.application.ports.method_trace import MethodTraceEvent
from tiny_swarm_world.application.ports.progress import WorkflowProgressEvent
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    STATUS_ERROR,
    PortUI,
)
from tiny_swarm_world.infrastructure.adapters.ui.progress_trace_ui import (
    TerminalMethodTrace,
    TerminalWorkflowProgress,
)


class TestProgressTraceUi(unittest.TestCase):
    def test_workflow_progress_updates_aggregate_status(self):
        ui = RecordingUI()
        adapter = TerminalWorkflowProgress(ui)

        adapter.report(
            WorkflowProgressEvent(
                workflow="setup run",
                phase="platform init",
                target="platform",
                task="Run platform init",
                step="apply",
                status="started",
                result="pending",
                safe_message="Platform init started.",
                recovery_hint="Wait for platform init evidence.",
                evidence_path=".tiny-swarm-world/evidence/platform-init.json",
                correlation_id="setup-123",
                trace_id="trace-456",
            )
        )

        self.assertEqual(
            [(AGGREGATE_INSTANCE, "setup run", "platform init:apply", "pending")],
            ui.updates,
        )
        self.assertEqual(
            "Wait for platform init evidence.",
            ui.aggregate_status["recovery_hint"],
        )
        self.assertEqual(
            ".tiny-swarm-world/evidence/platform-init.json",
            ui.aggregate_status["evidence_path"],
        )
        self.assertEqual("setup-123", ui.aggregate_status["correlation_id"])
        self.assertEqual("trace-456", ui.aggregate_status["trace_id"])

    def test_raised_method_trace_updates_aggregate_failure_state(self):
        ui = RecordingUI()
        adapter = TerminalMethodTrace(ui)

        adapter.report(
            MethodTraceEvent(
                component="setup",
                module="tiny_swarm_world.application.services.setup.workflow",
                class_name="SetupWorkflowPhase",
                method_name="run",
                status="raised",
                correlation_id="trace-123",
                span_id="span-456",
                safe_result="failed",
                exception_type="RuntimeError",
            )
        )
        adapter.report(
            MethodTraceEvent(
                component="setup",
                module="tiny_swarm_world.application.services.setup.workflow",
                class_name="SetupWorkflow",
                method_name="run",
                status="returned",
                correlation_id="trace-123",
                span_id="span-789",
                safe_result="completed",
            )
        )

        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])
        self.assertEqual(
            [
                (AGGREGATE_INSTANCE, "SetupWorkflowPhase.run", "raised", "failed"),
                (AGGREGATE_INSTANCE, "SetupWorkflow.run", "returned", STATUS_ERROR),
            ],
            ui.updates,
        )


class RecordingUI(PortUI):
    def __init__(self):
        super().__init__(instances=(), test_mode=True)
        self.updates = []

    def update_status(self, instance, task, step, result=None):
        super().update_status(instance, task, step, result)
        target_status = self._status_for_instance(instance)
        self.updates.append((instance, task, step, target_status["result"]))

    def start(self):
        return None

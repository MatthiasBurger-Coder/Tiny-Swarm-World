from __future__ import annotations

from tiny_swarm_world.application.ports.method_trace import (
    MethodTraceEvent,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    PortWorkflowProgress,
    WorkflowProgressEvent,
)
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    ConsoleStatusEvent,
    PortUI,
)


class TerminalWorkflowProgress(PortWorkflowProgress):
    def __init__(self, ui: PortUI):
        self.ui = ui

    def report(self, event: WorkflowProgressEvent) -> None:
        self.ui.update_status_event(
            ConsoleStatusEvent(
                instance=AGGREGATE_INSTANCE,
                workflow_command=event.workflow,
                step=f"{event.phase}:{event.step}",
                result_status=event.result,
                recovery_hint=event.recovery_hint,
                evidence_path=event.evidence_path,
                correlation_id=event.correlation_id,
                trace_id=event.trace_id,
            )
        )


class TerminalMethodTrace(PortMethodTrace):
    def __init__(self, ui: PortUI):
        self.ui = ui

    def report(self, event: MethodTraceEvent) -> None:
        self.ui.update_status(
            instance=AGGREGATE_INSTANCE,
            task=f"{event.class_name}.{event.method_name}",
            step=event.status,
            result=_trace_result(event),
        )


def _trace_result(event: MethodTraceEvent) -> str:
    if event.status == "raised":
        return "failed"
    return event.safe_result or event.status

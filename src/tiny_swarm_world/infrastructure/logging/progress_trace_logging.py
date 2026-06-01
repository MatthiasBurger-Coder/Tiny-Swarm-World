from __future__ import annotations

import logging
from collections.abc import Sequence

from tiny_swarm_world.application.ports.method_trace import (
    MethodTraceEvent,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    PortWorkflowProgress,
    WorkflowProgressEvent,
)


class CompositeWorkflowProgress(PortWorkflowProgress):
    def __init__(self, sinks: Sequence[PortWorkflowProgress]):
        self.sinks = tuple(sinks)

    def report(self, event: WorkflowProgressEvent) -> None:
        for sink in self.sinks:
            sink.report(event)


class CompositeMethodTrace(PortMethodTrace):
    def __init__(self, sinks: Sequence[PortMethodTrace]):
        self.sinks = tuple(sinks)

    def report(self, event: MethodTraceEvent) -> None:
        for sink in self.sinks:
            sink.report(event)


class LoggingWorkflowProgress(PortWorkflowProgress):
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("WorkflowProgress")

    def report(self, event: WorkflowProgressEvent) -> None:
        self.logger.info(
            "workflow_progress workflow=%s phase=%s target=%s task=%s step=%s status=%s result=%s recovery=%s",
            event.workflow,
            event.phase,
            event.target,
            event.task,
            event.step,
            event.status,
            event.result,
            event.recovery_hint or "",
        )


class LoggingMethodTrace(PortMethodTrace):
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("MethodTrace")

    def report(self, event: MethodTraceEvent) -> None:
        self.logger.info(
            "method_trace component=%s module=%s class=%s method=%s status=%s result=%s correlation=%s span=%s parent=%s workflow=%s exception_type=%s",
            event.component,
            event.module,
            event.class_name,
            event.method_name,
            event.status,
            event.safe_result or "",
            event.correlation_id,
            event.span_id,
            event.parent_span_id or "",
            event.workflow or "",
            event.exception_type or "",
        )

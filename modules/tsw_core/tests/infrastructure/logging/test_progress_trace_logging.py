import logging
import unittest

from tiny_swarm_world.application.ports.method_trace import (
    MethodTraceEvent,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    PortWorkflowProgress,
    WorkflowProgressEvent,
)
from tiny_swarm_world.infrastructure.logging.progress_trace_logging import (
    CompositeMethodTrace,
    CompositeWorkflowProgress,
    LoggingMethodTrace,
    LoggingWorkflowProgress,
)


class TestProgressTraceLogging(unittest.TestCase):
    def test_method_trace_logging_writes_one_safe_record_per_event(self):
        logger, handler = _recording_logger("test.method.trace.logging")
        adapter = LoggingMethodTrace(logger)

        for event in (
            _method_trace_event("entered"),
            _method_trace_event("returned"),
            _method_trace_event("raised", exception_type="RuntimeError"),
        ):
            adapter.report(event)

        self.assertEqual(len(handler.records), 3)
        for record in handler.records:
            self.assertIsNone(record.exc_info)
            message = record.getMessage()
            self.assertIn("method_trace", message)
            self.assertNotIn("traceback", message)
            self.assertNotIn("raw vm output", message)
            self.assertNotIn("cannot connect to the socket", message)
            self.assertNotIn("stderr", message)
            self.assertNotIn("stdout", message)
            self.assertNotIn("exit 1", message)

    def test_workflow_progress_logging_uses_safe_fields_without_exc_info(self):
        logger, handler = _recording_logger("test.workflow.progress.logging")
        adapter = LoggingWorkflowProgress(logger)

        adapter.report(
            WorkflowProgressEvent(
                workflow="setup run",
                phase="platform init",
                target="platform",
                task="Run platform init",
                step="apply",
                status="completed",
                result="completed",
                safe_message="Platform init completed.",
                recovery_hint="Inspect evidence before retrying.",
            )
        )

        self.assertEqual(len(handler.records), 1)
        record = handler.records[0]
        self.assertIsNone(record.exc_info)
        message = record.getMessage()
        self.assertIn("workflow_progress", message)
        self.assertIn("workflow=setup run", message)
        self.assertNotIn("traceback", message)
        self.assertNotIn("raw", message)

    def test_composite_sinks_forward_to_all_configured_sinks(self):
        workflow_sink_a = _RecordingWorkflowProgress()
        workflow_sink_b = _RecordingWorkflowProgress()
        method_sink_a = _RecordingMethodTrace()
        method_sink_b = _RecordingMethodTrace()

        workflow_event = WorkflowProgressEvent(
            workflow="setup run",
            phase="setup",
            target="setup",
            task="Run setup workflow",
            step="workflow completed",
            status="completed",
            result="completed",
            safe_message="Setup run completed.",
        )
        method_event = _method_trace_event("returned")

        CompositeWorkflowProgress((workflow_sink_a, workflow_sink_b)).report(workflow_event)
        CompositeMethodTrace((method_sink_a, method_sink_b)).report(method_event)

        self.assertEqual(workflow_sink_a.events, [workflow_event])
        self.assertEqual(workflow_sink_b.events, [workflow_event])
        self.assertEqual(method_sink_a.events, [method_event])
        self.assertEqual(method_sink_b.events, [method_event])


class _RecordingHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.records = []

    def emit(self, record):
        self.records.append(record)


class _RecordingWorkflowProgress(PortWorkflowProgress):
    def __init__(self):
        self.events = []

    def report(self, event):
        self.events.append(event)


class _RecordingMethodTrace(PortMethodTrace):
    def __init__(self):
        self.events = []

    def report(self, event):
        self.events.append(event)


def _recording_logger(name: str):
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = _RecordingHandler()
    logger.addHandler(handler)
    return logger, handler


def _method_trace_event(status, exception_type=None):
    return MethodTraceEvent(
        component="setup",
        module="tiny_swarm_world.application.services.setup.workflow",
        class_name="SetupWorkflow",
        method_name="run",
        status=status,
        correlation_id="trace-123",
        span_id=f"span-{status}",
        workflow="setup run",
        safe_result="failed" if status == "raised" else "completed",
        exception_type=exception_type,
    )

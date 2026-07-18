import unittest

from tests.support.sonar_safe_literals import ipv4_address

from tiny_swarm_world.application.ports.method_trace import (
    MethodTraceEvent,
    NullMethodTrace,
)


class TestMethodTraceEvent(unittest.TestCase):
    def test_event_contains_only_safe_trace_fields(self):
        event = MethodTraceEvent(
            component="setup",
            module="tiny_swarm_world.application.services.setup.workflow",
            class_name="SetupWorkflow",
            method_name="run",
            status="entered",
            correlation_id="trace-123",
            span_id="span-456",
            parent_span_id="span-parent",
            workflow="setup run",
            safe_result="pending",
            recovery_hint="Resolve blockers and rerun setup.",
        )

        self.assertEqual(
            event.to_dict(),
            {
                "component": "setup",
                "module": "tiny_swarm_world.application.services.setup.workflow",
                "class_name": "SetupWorkflow",
                "method_name": "run",
                "status": "entered",
                "correlation_id": "trace-123",
                "span_id": "span-456",
                "parent_span_id": "span-parent",
                "workflow": "setup run",
                "safe_result": "pending",
                "recovery_hint": "Resolve blockers and rerun setup.",
                "exception_type": None,
            },
        )

    def test_event_cannot_represent_raw_payload_keys(self):
        event = MethodTraceEvent(
            component="platform",
            module="tiny_swarm_world.application.services.platform.workflows",
            class_name="PlatformInitWorkflow",
            method_name="run",
            status="returned",
            correlation_id="trace-123",
            span_id="span-456",
            workflow="platform init",
            safe_result="completed",
        )

        forbidden_keys = {
            "args",
            "kwargs",
            "return_value",
            "payload",
            "raw",
            "command",
            "stdout",
            "stderr",
            "environment",
            "secret",
            "password",
            "token",
            "traceback",
            "stack",
        }

        self.assertTrue(forbidden_keys.isdisjoint(event.to_dict()))

    def test_event_rejects_unsafe_text_content(self):
        unsafe_values = (
            "args values",
            "kwargs values",
            "command failed",
            "stdout contained data",
            "stderr contained data",
            "environment variable leaked",
            "secret value present",
            "password value present",
            "token value present",
            "raw payload present",
            "return value present",
            "exception text present",
            "Traceback (most recent call last)",
            "stack trace",
            "/home/operator/project",
            "/mnt/d/project",
            "C:\\Users\\operator\\project",
            ipv4_address(192, 168, 1, 10),
            ipv4_address(10, 0, 0, 4),
            ipv4_address(172, 16, 0, 3),
            ipv4_address(127, 0, 0, 1),
        )

        for unsafe_value in unsafe_values:
            with self.subTest(unsafe_value=unsafe_value):
                with self.assertRaises(ValueError):
                    MethodTraceEvent(
                        component="setup",
                        module="tiny_swarm_world.application.services.setup.workflow",
                        class_name="SetupWorkflow",
                        method_name="run",
                        status="entered",
                        correlation_id="trace-123",
                        span_id="span-456",
                        safe_result=unsafe_value,
                    )

    def test_unexpected_payload_argument_is_rejected(self):
        with self.assertRaises(TypeError):
            MethodTraceEvent(
                component="platform",
                module="tiny_swarm_world.application.services.platform.workflows",
                class_name="PlatformInitWorkflow",
                method_name="run",
                status="entered",
                correlation_id="trace-123",
                span_id="span-456",
                payload="unsafe payload",
            )

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(ValueError):
            MethodTraceEvent(
                component="setup",
                module="tiny_swarm_world.application.services.setup.workflow",
                class_name="SetupWorkflow",
                method_name="run",
                status="failed",
                correlation_id="trace-123",
                span_id="span-456",
            )

    def test_raised_status_requires_sanitized_exception_type(self):
        with self.assertRaises(ValueError):
            MethodTraceEvent(
                component="setup",
                module="tiny_swarm_world.application.services.setup.workflow",
                class_name="SetupWorkflow",
                method_name="run",
                status="raised",
                correlation_id="trace-123",
                span_id="span-456",
            )

        event = MethodTraceEvent(
            component="setup",
            module="tiny_swarm_world.application.services.setup.workflow",
            class_name="SetupWorkflow",
            method_name="run",
            status="raised",
            correlation_id="trace-123",
            span_id="span-456",
            safe_result="failed",
            exception_type="RuntimeError",
        )

        self.assertEqual(event.exception_type, "RuntimeError")

    def test_non_raised_status_rejects_exception_type(self):
        with self.assertRaises(ValueError):
            MethodTraceEvent(
                component="setup",
                module="tiny_swarm_world.application.services.setup.workflow",
                class_name="SetupWorkflow",
                method_name="run",
                status="returned",
                correlation_id="trace-123",
                span_id="span-456",
                exception_type="RuntimeError",
            )


class TestNullMethodTrace(unittest.TestCase):
    def test_report_accepts_trace_event_without_side_effect(self):
        trace = NullMethodTrace()
        event = MethodTraceEvent(
            component="setup",
            module="tiny_swarm_world.application.services.setup.workflow",
            class_name="SetupWorkflow",
            method_name="run",
            status="entered",
            correlation_id="trace-123",
            span_id="span-456",
        )

        self.assertIsNone(trace.report(event))

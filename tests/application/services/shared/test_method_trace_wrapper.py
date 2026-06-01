import asyncio
import unittest

from tiny_swarm_world.application.ports.method_trace import MethodTraceEvent
from tiny_swarm_world.application.services.shared import MethodTraceWrapper


class TestMethodTraceWrapper(unittest.TestCase):
    def test_sync_wrapper_reports_entered_and_returned(self):
        trace = _RecordingMethodTrace()
        wrapper = MethodTraceWrapper(
            trace,
            component="setup",
            workflow="setup run",
            correlation_id="trace-123",
            parent_span_id="span-parent",
        )

        class Target:
            def run(self, value):
                return {"raw": value}

        result = wrapper.wrap_sync(Target().run)(42)

        self.assertEqual({"raw": 42}, result)
        self.assertEqual(["entered", "returned"], [event.status for event in trace.events])
        self.assertEqual({"trace-123"}, {event.correlation_id for event in trace.events})
        self.assertEqual(1, len({event.span_id for event in trace.events}))
        self.assertEqual({"span-parent"}, {event.parent_span_id for event in trace.events})
        self.assertEqual(["pending", "completed"], [event.safe_result for event in trace.events])
        self.assertEqual(["Target", "Target"], [event.class_name for event in trace.events])
        self.assertEqual(["run", "run"], [event.method_name for event in trace.events])
        self.assertNotIn("return_value", trace.events[-1].to_dict())
        self.assertNotIn("raw", trace.events[-1].to_dict())

    def test_sync_wrapper_reports_entered_and_raised_without_swallowing_exception(self):
        trace = _RecordingMethodTrace()
        wrapper = MethodTraceWrapper(trace, correlation_id="trace-123")
        expected = RuntimeError("raw secret path /home/operator")

        class Target:
            def run(self):
                raise expected

        with self.assertRaises(RuntimeError) as raised:
            wrapper.wrap_sync(Target().run)()

        self.assertIs(expected, raised.exception)
        self.assertEqual(["entered", "raised"], [event.status for event in trace.events])
        self.assertEqual(["pending", "failed"], [event.safe_result for event in trace.events])
        self.assertEqual("RuntimeError", trace.events[-1].exception_type)
        self.assertNotIn(str(expected), str(trace.events[-1].to_dict()))

    def test_async_wrapper_reports_entered_and_returned(self):
        async def run_test():
            trace = _RecordingMethodTrace()
            wrapper = MethodTraceWrapper(
                trace,
                component="platform",
                workflow="platform init",
                correlation_id="trace-async",
            )

            class Target:
                async def run(self, value):
                    return {"raw": value}

            result = await wrapper.wrap_async(Target().run)(42)

            self.assertEqual({"raw": 42}, result)
            self.assertEqual(["entered", "returned"], [event.status for event in trace.events])
            self.assertEqual({"trace-async"}, {event.correlation_id for event in trace.events})
            self.assertEqual(1, len({event.span_id for event in trace.events}))
            self.assertEqual(["pending", "completed"], [event.safe_result for event in trace.events])
            self.assertEqual(["Target", "Target"], [event.class_name for event in trace.events])
            self.assertEqual(["run", "run"], [event.method_name for event in trace.events])

        asyncio.run(run_test())

    def test_async_wrapper_reports_entered_and_raised_without_swallowing_exception(self):
        async def run_test():
            trace = _RecordingMethodTrace()
            wrapper = MethodTraceWrapper(trace, correlation_id="trace-async")
            expected = ValueError("raw token payload")

            class Target:
                async def run(self):
                    raise expected

            with self.assertRaises(ValueError) as raised:
                await wrapper.wrap_async(Target().run)()

            self.assertIs(expected, raised.exception)
            self.assertEqual(["entered", "raised"], [event.status for event in trace.events])
            self.assertEqual("ValueError", trace.events[-1].exception_type)
            self.assertNotIn(str(expected), str(trace.events[-1].to_dict()))

        asyncio.run(run_test())

    def test_wrapper_generates_safe_correlation_and_span_ids_when_not_supplied(self):
        trace = _RecordingMethodTrace()
        wrapper = MethodTraceWrapper(trace)

        def target():
            return "ok"

        self.assertEqual("ok", wrapper.wrap_sync(target)())
        self.assertEqual(2, len(trace.events))
        self.assertEqual(1, len({event.correlation_id for event in trace.events}))
        self.assertEqual(1, len({event.span_id for event in trace.events}))
        self.assertTrue(trace.events[0].correlation_id.startswith("trace-"))
        self.assertTrue(trace.events[0].span_id.startswith("span-"))


class _RecordingMethodTrace:
    def __init__(self):
        self.events: list[MethodTraceEvent] = []

    def report(self, event: MethodTraceEvent) -> None:
        self.events.append(event)

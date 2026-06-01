from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar
from uuid import uuid4

from tiny_swarm_world.application.ports.method_trace import (
    MethodTraceEvent,
    NullMethodTrace,
    PortMethodTrace,
)

P = ParamSpec("P")
R = TypeVar("R")


class MethodTraceWrapper:
    def __init__(
        self,
        trace: PortMethodTrace | None = None,
        *,
        component: str = "application",
        workflow: str | None = None,
        correlation_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> None:
        self._trace = trace or NullMethodTrace()
        self._component = component
        self._workflow = workflow
        self._correlation_id = correlation_id
        self._parent_span_id = parent_span_id

    def wrap_sync(
        self,
        method: Callable[P, R],
        *,
        component: str | None = None,
        workflow: str | None = None,
        correlation_id: str | None = None,
        parent_span_id: str | None = None,
        method_name: str | None = None,
        result_classifier: Callable[[R], str] | None = None,
    ) -> Callable[P, R]:
        method_identity = _MethodIdentity.from_callable(method)
        if method_name is not None:
            method_identity = method_identity.with_method_name(method_name)

        def traced(*args: P.args, **kwargs: P.kwargs) -> R:
            context = self._trace_context(
                component=component,
                workflow=workflow,
                correlation_id=correlation_id,
                parent_span_id=parent_span_id,
            )
            self._report(method_identity.entered(context))
            try:
                result = method(*args, **kwargs)
            except Exception as exc:
                self._report(method_identity.raised(context, exc))
                raise
            self._report(
                method_identity.returned(
                    context,
                    safe_result=_safe_result(result, result_classifier),
                )
            )
            return result

        return traced

    def wrap_async(
        self,
        method: Callable[P, Awaitable[R]],
        *,
        component: str | None = None,
        workflow: str | None = None,
        correlation_id: str | None = None,
        parent_span_id: str | None = None,
        method_name: str | None = None,
        result_classifier: Callable[[R], str] | None = None,
    ) -> Callable[P, Awaitable[R]]:
        method_identity = _MethodIdentity.from_callable(method)
        if method_name is not None:
            method_identity = method_identity.with_method_name(method_name)

        async def traced(*args: P.args, **kwargs: P.kwargs) -> R:
            context = self._trace_context(
                component=component,
                workflow=workflow,
                correlation_id=correlation_id,
                parent_span_id=parent_span_id,
            )
            self._report(method_identity.entered(context))
            try:
                result = await method(*args, **kwargs)
            except Exception as exc:
                self._report(method_identity.raised(context, exc))
                raise
            self._report(
                method_identity.returned(
                    context,
                    safe_result=_safe_result(result, result_classifier),
                )
            )
            return result

        return traced

    def _trace_context(
        self,
        *,
        component: str | None,
        workflow: str | None,
        correlation_id: str | None,
        parent_span_id: str | None,
    ) -> "_TraceContext":
        return _TraceContext(
            component=component or self._component,
            workflow=workflow if workflow is not None else self._workflow,
            correlation_id=correlation_id or self._correlation_id or f"trace-{uuid4().hex}",
            span_id=f"span-{uuid4().hex}",
            parent_span_id=parent_span_id
            if parent_span_id is not None
            else self._parent_span_id,
        )

    def _report(self, event: MethodTraceEvent) -> None:
        self._trace.report(event)


class _TraceContext:
    def __init__(
        self,
        *,
        component: str,
        workflow: str | None,
        correlation_id: str,
        span_id: str,
        parent_span_id: str | None,
    ) -> None:
        self.component = component
        self.workflow = workflow
        self.correlation_id = correlation_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id


class _MethodIdentity:
    def __init__(self, *, module: str, class_name: str, method_name: str) -> None:
        self.module = module
        self.class_name = class_name
        self.method_name = method_name

    def with_method_name(self, method_name: str) -> "_MethodIdentity":
        return _MethodIdentity(
            module=self.module,
            class_name=self.class_name,
            method_name=method_name,
        )

    @classmethod
    def from_callable(cls, method: Callable[..., object]) -> "_MethodIdentity":
        module = getattr(method, "__module__", "unknown")
        qualname = getattr(method, "__qualname__", getattr(method, "__name__", "unknown"))
        parts = [part for part in qualname.split(".") if part != "<locals>"]
        method_name = parts[-1] if parts else "unknown"
        class_name = parts[-2] if len(parts) > 1 else _class_name_from_bound_method(method)
        return cls(module=module, class_name=class_name, method_name=method_name)

    def entered(self, context: _TraceContext) -> MethodTraceEvent:
        return self._event(context, status="entered", safe_result="pending")

    def returned(self, context: _TraceContext, *, safe_result: str) -> MethodTraceEvent:
        return self._event(context, status="returned", safe_result=safe_result)

    def raised(self, context: _TraceContext, exc: Exception) -> MethodTraceEvent:
        return self._event(
            context,
            status="raised",
            safe_result="failed",
            exception_type=exc.__class__.__name__,
        )

    def _event(
        self,
        context: _TraceContext,
        *,
        status: str,
        safe_result: str,
        exception_type: str | None = None,
    ) -> MethodTraceEvent:
        return MethodTraceEvent(
            component=context.component,
            module=self.module,
            class_name=self.class_name,
            method_name=self.method_name,
            status=status,  # type: ignore[arg-type]
            correlation_id=context.correlation_id,
            span_id=context.span_id,
            parent_span_id=context.parent_span_id,
            workflow=context.workflow,
            safe_result=safe_result,
            exception_type=exception_type,
        )


def _class_name_from_bound_method(method: Callable[..., object]) -> str:
    bound_self = getattr(method, "__self__", None)
    if bound_self is not None:
        return bound_self.__class__.__name__

    if inspect.ismethod(method):
        return method.__self__.__class__.__name__

    return "module"


def _safe_result(result: R, result_classifier: Callable[[R], str] | None) -> str:
    if result_classifier is None:
        return "completed"
    return result_classifier(result)

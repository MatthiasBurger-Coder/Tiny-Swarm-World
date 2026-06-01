from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Literal

MethodTraceStatus = Literal["entered", "returned", "raised"]

FORBIDDEN_METHOD_TRACE_TEXT_PARTS = (
    "args",
    "command failed",
    "command text",
    "context details",
    "environment",
    "exception text",
    "kwargs",
    "password",
    "payload",
    "raw",
    "raw command",
    "return value",
    "secret",
    "stack trace",
    "stderr",
    "stdout",
    "token",
    "traceback",
)

_HOST_PATH_PATTERN = re.compile(r"(^|[\s=:])(/home/|/mnt/|/root/|/tmp/|[A-Za-z]:[\\/])")
_LOCAL_IP_PATTERN = re.compile(
    r"\b("
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"127\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"169\.254\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}"
    r")\b"
)


@dataclass(frozen=True, kw_only=True)
class MethodTraceEvent:
    component: str
    module: str
    class_name: str
    method_name: str
    status: MethodTraceStatus
    correlation_id: str
    span_id: str
    parent_span_id: str | None = None
    workflow: str | None = None
    safe_result: str | None = None
    recovery_hint: str | None = None
    exception_type: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("entered", "returned", "raised"):
            raise ValueError("method trace status must be entered, returned, or raised")

        if self.status == "raised" and not self.exception_type:
            raise ValueError("raised method trace events require exception_type")

        if self.status != "raised" and self.exception_type is not None:
            raise ValueError("exception_type is only allowed for raised method trace events")

        for field_name, value in self.to_dict().items():
            if value is None:
                continue
            _reject_unsafe_method_trace_text(field_name, value)

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


class PortMethodTrace(ABC):
    @abstractmethod
    def report(self, event: MethodTraceEvent) -> None:
        pass


class NullMethodTrace(PortMethodTrace):
    def report(self, event: MethodTraceEvent) -> None:
        pass


def _reject_unsafe_method_trace_text(field_name: str, value: str) -> None:
    normalized_value = value.lower()
    if any(part in normalized_value for part in FORBIDDEN_METHOD_TRACE_TEXT_PARTS):
        raise ValueError(f"method trace field '{field_name}' contains unsafe text")
    if _HOST_PATH_PATTERN.search(value):
        raise ValueError(f"method trace field '{field_name}' contains host path text")
    if _LOCAL_IP_PATTERN.search(value):
        raise ValueError(f"method trace field '{field_name}' contains local IP text")

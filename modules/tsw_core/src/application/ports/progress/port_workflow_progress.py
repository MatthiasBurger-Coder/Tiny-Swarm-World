from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

FORBIDDEN_PROGRESS_TEXT_PARTS = (
    "command",
    "context",
    "details",
    "environment",
    "exception",
    "password",
    "payload",
    "raw",
    "secret",
    "stack trace",
    "stderr",
    "stdout",
    "token",
    "traceback",
)


@dataclass(frozen=True, kw_only=True)
class WorkflowProgressEvent:
    workflow: str
    phase: str
    target: str
    task: str
    step: str
    status: str
    result: str
    safe_message: str
    recovery_hint: str | None = None
    evidence_path: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None

    def __post_init__(self) -> None:
        for field_name, value in self.to_dict().items():
            if value is None:
                continue
            _reject_unsafe_progress_text(field_name, value)

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


class PortWorkflowProgress(ABC):
    @abstractmethod
    def report(self, event: WorkflowProgressEvent) -> None:
        pass


def report_readiness_wait(
    progress: PortWorkflowProgress,
    *,
    workflow: str,
    phase: str,
    target: str,
    task: str,
    attempt: int,
    max_attempts: int,
    wait_seconds: float,
) -> None:
    """Publish a safe, deterministic event before an asynchronous retry wait."""

    if attempt < 1 or max_attempts < attempt:
        raise ValueError("Readiness progress attempt must be within its limit.")
    if wait_seconds < 0:
        raise ValueError("Readiness progress wait must not be negative.")
    progress.report(
        WorkflowProgressEvent(
            workflow=workflow,
            phase=phase,
            target=target,
            task=task,
            step=f"readiness wait {attempt}/{max_attempts}",
            status="running",
            result="pending",
            safe_message=(
                f"{target} is not ready; waiting {wait_seconds:g} seconds "
                "before the next attempt."
            ),
        )
    )


class NullWorkflowProgress(PortWorkflowProgress):
    def report(self, event: WorkflowProgressEvent) -> None:
        return None


def _reject_unsafe_progress_text(field_name: str, value: str) -> None:
    normalized_value = value.lower()
    if any(part in normalized_value for part in FORBIDDEN_PROGRESS_TEXT_PARTS):
        raise ValueError(f"workflow progress field '{field_name}' contains unsafe text")

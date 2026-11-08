from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ArtifactSourceStatus(str, Enum):
    READY = "READY"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


@dataclass(frozen=True)
class ArtifactSourceAttempt:
    source: str
    kind: str
    status: ArtifactSourceStatus
    detail: str


@dataclass(frozen=True)
class ArtifactSourceReadiness:
    mode: str
    selected_source: str | None
    attempts: tuple[ArtifactSourceAttempt, ...]

    @property
    def ready(self) -> bool:
        return bool(self.attempts) and all(
            attempt.status is ArtifactSourceStatus.READY for attempt in self.attempts
        )

    @property
    def timed_out(self) -> bool:
        return not self.ready and any(
            attempt.status is ArtifactSourceStatus.TIMED_OUT for attempt in self.attempts
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "selected_source": self.selected_source,
            "ready": self.ready,
            "status": (
                ArtifactSourceStatus.READY.value
                if self.ready
                else ArtifactSourceStatus.TIMED_OUT.value
                if self.timed_out
                else ArtifactSourceStatus.FAILED.value
            ),
            "attempts": [
                {
                    "source": attempt.source,
                    "kind": attempt.kind,
                    "status": attempt.status.value,
                    "detail": attempt.detail,
                }
                for attempt in self.attempts
            ],
        }

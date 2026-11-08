"""Immutable Incus preparation observations and explicit readiness states."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IncusAction:
    id: str
    kind: str
    name: str
    payload: str = ""
    timeout_seconds: float = 60.0
    privilege: str = "user"
    restart: str = "none"


@dataclass(frozen=True)
class IncusSnapshot:
    fingerprint: str
    actions: tuple[IncusAction, ...] = ()
    blockers: tuple[str, ...] = ()
    restart_required: bool = False
    verified: bool = False


@dataclass(frozen=True)
class IncusPreparationResult:
    status: str
    completed: tuple[str, ...] = ()
    uncertain: tuple[str, ...] = ()
    message: str = ""
    transport_exit: int | None = None
    evidence_path: str | None = None
    stage_complete: bool = False
    services_verified: bool = field(default=False, init=False)

    @property
    def exit_code(self) -> int:
        if self.transport_exit is not None:
            return self.transport_exit
        return {"READY": 0, "BLOCKED": 2, "RESTART_REQUIRED": 3,
                "PARTIAL": 4, "FAILED": 1}[self.status]

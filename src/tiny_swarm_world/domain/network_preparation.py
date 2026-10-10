"""Explicit prerequisite readiness without deployment or authentication claims."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NetworkAction:
    id: str
    kind: str
    description: str
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class NetworkSnapshot:
    fingerprint: str
    invariant: str
    actions: tuple[NetworkAction, ...] = ()
    blockers: tuple[str, ...] = ()
    linux_ready: bool = False
    bridge_ready: bool = False
    is_wsl: bool = False

    @property
    def verified(self) -> bool:
        return self.linux_ready and (not self.is_wsl or self.bridge_ready)


@dataclass(frozen=True)
class NetworkPreparationResult:
    status: str
    completed: tuple[str, ...] = ()
    uncertain: tuple[str, ...] = ()
    message: str = ""
    evidence_path: str | None = None
    transport_exit: int | None = None
    services_verified: bool = field(default=False, init=False)
    endpoint_state: str = field(default="UNVERIFIED", init=False)
    login_state: str = field(default="UNVERIFIED", init=False)

    @property
    def exit_code(self) -> int:
        return self.transport_exit or {"READY": 0, "BLOCKED": 2, "PARTIAL": 4, "FAILED": 1}[self.status]

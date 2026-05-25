from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class HostRuntimeReadinessStatus(str, Enum):
    READY = "READY"
    EXECUTABLE_MISSING = "EXECUTABLE_MISSING"
    SOCKET_UNAVAILABLE = "SOCKET_UNAVAILABLE"
    DAEMON_UNAVAILABLE = "DAEMON_UNAVAILABLE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    DRIVER_UNAVAILABLE = "DRIVER_UNAVAILABLE"
    DRIVER_MISMATCH = "DRIVER_MISMATCH"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


@dataclass(frozen=True)
class HostRuntimeReadiness:
    runtime: str
    status: HostRuntimeReadinessStatus
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _reject_unsafe_evidence_keys(self.evidence)
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))

    @property
    def ready(self) -> bool:
        return self.status == HostRuntimeReadinessStatus.READY


def _reject_unsafe_evidence_keys(evidence: Mapping[str, str]) -> None:
    forbidden_parts = (
        "command",
        "environment",
        "password",
        "raw",
        "secret",
        "stderr",
        "stdout",
        "token",
    )
    for key in evidence:
        normalized_key = str(key).lower()
        if any(part in normalized_key for part in forbidden_parts):
            raise ValueError("runtime readiness evidence contains unsafe keys")

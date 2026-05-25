from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from tiny_swarm_world.domain.preflight.sanitized_evidence import sanitized_evidence


class MultipassReadinessStatus(str, Enum):
    READY = "ready"
    EXECUTABLE_MISSING = "executable_missing"
    VERSION_UNAVAILABLE = "version_unavailable"
    LIST_UNAVAILABLE = "list_unavailable"
    DRIVER_UNAVAILABLE = "driver_unavailable"
    DRIVER_MISMATCH = "driver_mismatch"
    DAEMON_UNAVAILABLE = "daemon_unavailable"
    SOCKET_UNAVAILABLE = "socket_unavailable"
    SOCKET_PERMISSION_DENIED = "socket_permission_denied"
    TIMEOUT = "timeout"
    UNKNOWN_FAILURE = "unknown_failure"


@dataclass(frozen=True)
class MultipassReadinessReport:
    status: MultipassReadinessStatus
    remediation: tuple[str, ...] = ()
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "remediation", tuple(self.remediation))
        object.__setattr__(self, "evidence", sanitized_evidence(self.evidence))

    @property
    def ready(self) -> bool:
        return self.status == MultipassReadinessStatus.READY

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "ready": self.ready,
            "remediation": list(self.remediation),
            "evidence": dict(self.evidence),
        }

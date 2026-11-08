from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class HostPreparationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    INTERRUPTED = "INTERRUPTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class HostPreparationResult:
    operation: str
    host_environment: str
    status: HostPreparationStatus
    message: str
    changed: bool = False
    verified: bool = False
    evidence: Mapping[str, str] = MappingProxyType({})

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))

    @property
    def succeeded(self) -> bool:
        return self.status is HostPreparationStatus.SUCCESS

    def to_dict(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "host_environment": self.host_environment,
            "status": self.status.value,
            "message": self.message,
            "changed": self.changed,
            "verified": self.verified,
            "evidence": dict(self.evidence),
        }

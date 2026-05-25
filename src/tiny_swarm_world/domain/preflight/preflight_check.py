from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class PreflightStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"


class PreflightCategory(str, Enum):
    HOST = "HOST"
    DEPENDENCY = "DEPENDENCY"
    RUNTIME = "RUNTIME"
    RESOURCE = "RESOURCE"
    PORT = "PORT"
    SECRET = "SECRET"
    LIVE_CONSENT = "LIVE_CONSENT"
    IGNORE_POLICY = "IGNORE_POLICY"
    CONFIGURATION = "CONFIGURATION"


class PreflightSeverity(str, Enum):
    MANDATORY = "MANDATORY"
    OPTIONAL = "OPTIONAL"
    RESOURCE_GATED = "RESOURCE_GATED"


@dataclass(frozen=True)
class PreflightCheck:
    check_id: str
    category: PreflightCategory
    status: PreflightStatus
    severity: PreflightSeverity
    message: str
    remediation: str
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))

    @property
    def passed(self) -> bool:
        return self.status == PreflightStatus.PASSED

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "category": self.category.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "remediation": self.remediation,
            "evidence": dict(self.evidence),
        }

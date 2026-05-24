from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from tiny_swarm_world.domain.inventory.safe_text import (
    validate_evidence_key,
    validate_evidence_value,
    validate_message_text,
    validate_target_id,
)


class VerificationStatus(str, Enum):
    NOT_CHECKED = "not_checked"
    VERIFIED = "verified"
    FAILED_TO_APPLY = "failed_to_apply"
    FAILED_TO_VERIFY = "failed_to_verify"
    BLOCKED = "blocked"
    REFUSED = "refused"


@dataclass(frozen=True)
class VerificationResult:
    target_id: str
    status: VerificationStatus = VerificationStatus.NOT_CHECKED
    message: str = ""
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_target_id(self.target_id)
        status = VerificationStatus(self.status)
        validate_message_text("message", self.message)
        evidence = _validate_evidence(self.evidence)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence", MappingProxyType(evidence))

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "status": self.status.value,
            "message": self.message,
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "VerificationResult":
        return cls(
            target_id=str(data.get("target_id", "")),
            status=VerificationStatus(str(data.get("status", VerificationStatus.NOT_CHECKED.value))),
            message=str(data.get("message", "")),
            evidence=_string_mapping(data.get("evidence", {})),
        )


def _validate_evidence(evidence: Mapping[str, str]) -> dict[str, str]:
    validated: dict[str, str] = {}
    for key, value in evidence.items():
        validate_evidence_key(str(key))
        string_value = str(value)
        validate_evidence_value(str(key), string_value)
        validated[str(key)] = string_value
    return validated


def _string_mapping(value: object) -> Mapping[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("verification evidence must be a mapping")
    return {str(key): str(item) for key, item in value.items()}

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from types import MappingProxyType
from typing import Mapping


class VerificationStatus(str, Enum):
    NOT_CHECKED = "not_checked"
    VERIFIED = "verified"
    FAILED_TO_APPLY = "failed_to_apply"
    FAILED_TO_VERIFY = "failed_to_verify"
    BLOCKED = "blocked"
    REFUSED = "refused"


RAW_EVIDENCE_KEYS = frozenset(
    {
        "command",
        "raw_command",
        "stdout",
        "raw_stdout",
        "stderr",
        "raw_stderr",
        "environment",
        "env",
    }
)
SENSITIVE_EVIDENCE_KEY_FRAGMENTS = ("password", "secret", "token")
RAW_EVIDENCE_VALUE_PATTERNS = (
    re.compile(r"[\r\n]"),
    re.compile(r"\b(stdout|stderr)\b", re.IGNORECASE),
    re.compile(r"\b(multipass|docker|sudo|curl)\s+\S+", re.IGNORECASE),
    re.compile(r"\b(token|password|secret)\b", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
)
RAW_MESSAGE_VALUE_PATTERNS = (
    re.compile(r"[\r\n]"),
    re.compile(r"\b(stdout|stderr)\b", re.IGNORECASE),
    re.compile(
        r"\b(multipass|docker|sudo|curl)\s+"
        r"(exec|swarm|system|volume|stack|run|compose|login|pull|push|network|"
        r"service|node|secret|config|cp|ssh|launch|delete|purge|restart|list|"
        r"transfer|set|install|update|sh|bash|curl)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(token|password|secret)\b", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
)


@dataclass(frozen=True)
class VerificationResult:
    target_id: str
    status: VerificationStatus = VerificationStatus.NOT_CHECKED
    message: str = ""
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.target_id:
            raise ValueError("verification target_id must not be empty")
        status = VerificationStatus(self.status)
        _validate_summary_text("message", self.message, RAW_MESSAGE_VALUE_PATTERNS)
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
        normalized_key = str(key).strip().lower()
        if not normalized_key:
            raise ValueError("verification evidence keys must not be empty")
        if normalized_key in RAW_EVIDENCE_KEYS:
            raise ValueError(f"raw verification evidence key is not allowed: {key}")
        if any(fragment in normalized_key for fragment in SENSITIVE_EVIDENCE_KEY_FRAGMENTS):
            raise ValueError(f"sensitive verification evidence key is not allowed: {key}")
        string_value = str(value)
        _validate_summary_text(key, string_value, RAW_EVIDENCE_VALUE_PATTERNS)
        validated[str(key)] = string_value
    return validated


def _validate_summary_text(
    key: str,
    value: str,
    raw_value_patterns: tuple[re.Pattern[str], ...],
) -> None:
    if any(pattern.search(value) for pattern in raw_value_patterns):
        raise ValueError(f"raw or sensitive verification text is not allowed: {key}")


def _string_mapping(value: object) -> Mapping[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("verification evidence must be a mapping")
    return {str(key): str(item) for key, item in value.items()}

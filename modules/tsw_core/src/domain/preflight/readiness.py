from __future__ import annotations

import math
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


MAX_READINESS_ATTEMPTS = 3
MAX_READINESS_TIMEOUT_SECONDS = 60.0
ARTIFACT_READINESS_TARGETS = (
    "docker:manager",
    "registry:endpoint",
    "nexus:endpoint",
    "nexus:repositories",
    "storage:manager",
    "build:inputs",
    "pull:public",
)


class ReadinessStatus(str, Enum):
    READY = "ready"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    TIMED_OUT = "timed_out"
    UNKNOWN = "unknown"
    PARTIAL = "partial"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class ReadinessProbeRequest:
    """Safe, bounded parameters for one read-only readiness observation."""

    target_id: str
    timeout_seconds: float = 5.0
    max_attempts: int = 1

    def __post_init__(self) -> None:
        validate_target_id(self.target_id)
        if not math.isfinite(self.timeout_seconds) or not (
            0.0 < self.timeout_seconds <= MAX_READINESS_TIMEOUT_SECONDS
        ):
            raise ValueError(
                f"readiness timeout must be finite and between 0 and "
                f"{MAX_READINESS_TIMEOUT_SECONDS:g} seconds"
            )
        if not 1 <= self.max_attempts <= MAX_READINESS_ATTEMPTS:
            raise ValueError(
                f"readiness max_attempts must be between 1 and {MAX_READINESS_ATTEMPTS}"
            )


@dataclass(frozen=True)
class ReadinessCheckResult:
    """Secret-safe outcome of a bounded readiness observation."""

    target_id: str
    status: ReadinessStatus
    message: str
    remediation: str
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_target_id(self.target_id)
        status = ReadinessStatus(self.status)
        validate_message_text("message", self.message)
        validate_message_text("remediation", self.remediation)
        validated_evidence: dict[str, str] = {}
        for key, value in self.evidence.items():
            string_key = str(key)
            string_value = str(value)
            validate_evidence_key(string_key)
            validate_evidence_value(string_key, string_value)
            validated_evidence[string_key] = string_value
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence", MappingProxyType(validated_evidence))

    @property
    def ready(self) -> bool:
        return self.status is ReadinessStatus.READY

    @property
    def blocks_mutation(self) -> bool:
        return not self.ready

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "evidence_scope": "live",
            "status": self.status.value,
            "message": self.message,
            "remediation": self.remediation,
            "evidence": dict(self.evidence),
        }

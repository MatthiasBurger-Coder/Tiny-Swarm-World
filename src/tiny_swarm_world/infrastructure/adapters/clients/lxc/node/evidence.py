"""Typed, serialization-only helpers for safe LXC verification evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias


EvidenceScalar: TypeAlias = str | int | bool | None


class EvidenceKey(StrEnum):
    """Stable keys shared by LXC lifecycle and provider-preflight evidence."""

    APPLIED = "applied"
    BACKEND = "backend"
    CLASSIFICATION = "classification"
    CLASSIFICATION_SOURCE = "classification_source"
    FAILED_APPLY_COUNT = "failed_apply_count"
    FAILED_VERIFY_COUNT = "failed_verify_count"
    FIRST_FAILURE_CLASSIFICATION = "first_failure_classification"
    HOST_KIND = "host_kind"
    INFO_PROBE = "info_probe"
    NODE = "node"
    NODE_NAME = "node_name"
    PHASE = "phase"
    PLANNED_COUNT = "planned_count"
    PROBE = "probe"
    PROVIDER = "provider"
    RETURN_CODE = "return_code"
    SELECTED_BACKEND = "selected_backend"
    SELECTED_REASON = "selected_reason"
    SELECTION_STATUS = "selection_status"
    SKIPPED_CANDIDATES = "skipped_candidates"
    SKIPPED_CANDIDATE_REASONS = "skipped_candidate_reasons"
    TIMED_OUT = "timed_out"
    VERIFIED_COUNT = "verified_count"
    VERSION_PROBE = "version_probe"


@dataclass(slots=True)
class EvidenceBuilder:
    """Build an evidence mapping without taking runtime or policy decisions."""

    _values: dict[str, str] = field(default_factory=dict)

    def add(self, key: EvidenceKey | str, value: EvidenceScalar) -> "EvidenceBuilder":
        """Add one safe scalar value, omitting intentionally absent values."""

        if value is None:
            return self
        self._values[_key_text(key)] = _serialize(value)
        return self

    def extend(
        self,
        values: Mapping[str, EvidenceScalar],
    ) -> "EvidenceBuilder":
        """Add already-classified producer values without changing their meaning."""

        for key, value in values.items():
            self.add(key, value)
        return self

    def build(self) -> dict[str, str]:
        """Return a copy so later builder changes cannot mutate emitted evidence."""

        return dict(self._values)


def _key_text(key: EvidenceKey | str) -> str:
    return key.value if isinstance(key, EvidenceKey) else str(key)


def _serialize(value: str | int | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

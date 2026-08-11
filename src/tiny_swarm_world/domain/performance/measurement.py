from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
import re
from types import MappingProxyType
from typing import Mapping, TypeAlias

from tiny_swarm_world.domain.sanitized_evidence import sanitized_evidence


MeasurementValue: TypeAlias = int | float | str
NumericValue: TypeAlias = int | float

_SAFE_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_ALLOWED_MEASUREMENT_SCOPES = frozenset({"local", "mocked", "synthetic", "live"})


@dataclass(frozen=True)
class PerformanceMeasurement:
    """Immutable, redacted and deterministic performance evidence."""

    issue_id: str
    workflow_id: str
    segment_id: str
    segment: str
    measurement_scope: str
    target_kind: str
    target_ids: tuple[str, ...]
    environment_summary: str
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    counters: Mapping[str, NumericValue] | None = None
    baseline: Mapping[str, MeasurementValue] | None = None
    new_values: Mapping[str, MeasurementValue] | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier(self.issue_id, "issue_id")
        _validate_identifier(self.workflow_id, "workflow_id")
        _validate_identifier(self.segment_id, "segment_id")
        _validate_safe_text(self.segment, "segment")
        _validate_identifier(self.measurement_scope, "measurement_scope")
        if self.measurement_scope not in _ALLOWED_MEASUREMENT_SCOPES:
            raise ValueError("measurement_scope is not supported")
        _validate_identifier(self.target_kind, "target_kind")

        target_ids = _sorted_identifiers(self.target_ids, "target_ids")
        if not target_ids:
            raise ValueError("target_ids must contain at least one target")
        object.__setattr__(self, "target_ids", target_ids)

        _validate_safe_text(self.environment_summary, "environment_summary")
        _validate_timestamp(self.started_at, "started_at")
        _validate_timestamp(self.finished_at, "finished_at")
        _validate_timestamp_order(self.started_at, self.finished_at)

        if self.duration_seconds is not None:
            _validate_number(self.duration_seconds, "duration_seconds")
            object.__setattr__(self, "duration_seconds", float(self.duration_seconds))

        object.__setattr__(
            self,
            "counters",
            _normalize_numeric_mapping(self.counters, "counters"),
        )
        object.__setattr__(
            self,
            "baseline",
            _normalize_measurement_mapping(self.baseline, "baseline"),
        )
        object.__setattr__(
            self,
            "new_values",
            _normalize_measurement_mapping(self.new_values, "new_values"),
        )

        limitations = tuple(sorted(set(self.limitations)))
        if not limitations:
            raise ValueError("limitations must contain at least one statement")
        for limitation in limitations:
            _validate_safe_text(limitation, "limitations")
        object.__setattr__(self, "limitations", limitations)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "baseline": dict(self.baseline or {}),
            "counters": dict(self.counters or {}),
            "duration_seconds": self.duration_seconds,
            "environment_summary": self.environment_summary,
            "finished_at": self.finished_at,
            "issue_id": self.issue_id,
            "limitations": list(self.limitations),
            "measurement_scope": self.measurement_scope,
            "new_values": dict(self.new_values or {}),
            "segment": self.segment,
            "segment_id": self.segment_id,
            "started_at": self.started_at,
            "target_ids": list(self.target_ids),
            "target_kind": self.target_kind,
            "workflow_id": self.workflow_id,
        }


def _validate_identifier(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _SAFE_IDENTIFIER.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase safe identifier")


def _sorted_identifiers(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        values = tuple(values)
    for value in values:
        _validate_identifier(value, field_name)
    return tuple(sorted(set(values)))


def _validate_safe_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must contain non-empty text")
    try:
        sanitized_evidence({"value": value})
    except ValueError as exc:
        raise ValueError(f"{field_name} contains unsafe evidence text") from exc


def _validate_timestamp(value: str | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be an ISO timestamp or None")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")


def _validate_timestamp_order(started_at: str | None, finished_at: str | None) -> None:
    if started_at is None or finished_at is None:
        return
    started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    if finished < started:
        raise ValueError("finished_at must not precede started_at")


def _validate_number(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    if not isfinite(float(value)) or float(value) < 0:
        raise ValueError(f"{field_name} must be finite and non-negative")


def _normalize_numeric_mapping(
    values: Mapping[str, NumericValue] | None,
    field_name: str,
) -> Mapping[str, NumericValue]:
    normalized: dict[str, NumericValue] = {}
    for key, value in sorted((values or {}).items()):
        _validate_identifier(key, f"{field_name} key")
        _validate_number(value, f"{field_name}.{key}")
        normalized[key] = value
    return MappingProxyType(normalized)


def _normalize_measurement_mapping(
    values: Mapping[str, MeasurementValue] | None,
    field_name: str,
) -> Mapping[str, MeasurementValue]:
    normalized: dict[str, MeasurementValue] = {}
    for key, value in sorted((values or {}).items()):
        _validate_identifier(key, f"{field_name} key")
        if isinstance(value, bool):
            raise ValueError(f"{field_name}.{key} must not be boolean")
        if isinstance(value, (int, float)):
            _validate_number(value, f"{field_name}.{key}")
        elif isinstance(value, str):
            _validate_safe_text(value, f"{field_name}.{key}")
        else:
            raise ValueError(f"{field_name}.{key} must be numeric or safe text")
        normalized[key] = value
    return MappingProxyType(normalized)

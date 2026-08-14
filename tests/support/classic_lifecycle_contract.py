"""Deterministic lifecycle assertions shared by the Classic acceptance tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from tiny_swarm_world.domain.inventory.verification import LiveVerificationState


FINAL_DECISIONS = frozenset(
    {
        "RC1_ACCEPTED",
        "RC1_REJECTED_BLOCKERS",
        "RC1_REJECTED_EVIDENCE_INCOMPLETE",
    }
)
NON_SUCCESS_CLASSIFICATIONS = frozenset(
    {
        "refused",
        "blocked",
        "resource-gated",
        "failed-to-apply",
        "failed-to-prepare",
        "failed-to-verify",
        "partial",
        "degraded",
    }
)
REQUIRED_EVIDENCE_FIELDS = (
    "scenario_id",
    "host",
    "commit",
    "started_utc",
    "finished_utc",
    "state",
    "result_classification",
    "exit_code",
    "readiness_summary",
    "transitions",
    "retry_metadata",
    "remediation",
    "rollback_cleanup",
    "evidence_files",
    "redaction_status",
    "checksum",
    "reviewer",
    "defects",
)


@dataclass(frozen=True)
class LifecycleEvidence:
    """Minimal redacted scenario record used by deterministic policy tests."""

    scenario_id: str
    host: str
    commit: str
    started_utc: str
    finished_utc: str
    state: str
    result_classification: str
    exit_code: int | None
    readiness_summary: str
    transitions: tuple[str, ...]
    retry_metadata: str
    remediation: str
    rollback_cleanup: str
    evidence_files: tuple[str, ...]
    redaction_status: str
    checksum: str
    reviewer: str
    defects: tuple[str, ...]

    def as_mapping(self) -> Mapping[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "host": self.host,
            "commit": self.commit,
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "state": self.state,
            "result_classification": self.result_classification,
            "exit_code": self.exit_code,
            "readiness_summary": self.readiness_summary,
            "transitions": self.transitions,
            "retry_metadata": self.retry_metadata,
            "remediation": self.remediation,
            "rollback_cleanup": self.rollback_cleanup,
            "evidence_files": self.evidence_files,
            "redaction_status": self.redaction_status,
            "checksum": self.checksum,
            "reviewer": self.reviewer,
            "defects": self.defects,
        }

    def is_complete(self) -> bool:
        values = self.as_mapping()
        required_values_present = all(
            key in values
            and values[key] not in (None, "", ())
            for key in REQUIRED_EVIDENCE_FIELDS
            if key != "defects"
        )
        return (
            required_values_present
            and values["defects"] is not None
            and values["redaction_status"] == "redacted"
        )

    def is_success(self) -> bool:
        return (
            self.is_complete()
            and self.state == LiveVerificationState.VERIFIED.value
            and self.result_classification == "passed"
            and self.exit_code == 0
            and self.redaction_status == "redacted"
        )


def final_decision(
    scenarios: tuple[LifecycleEvidence, ...],
    *,
    evidence_complete: bool,
) -> str:
    """Apply the RC1 fail-closed decision contract to synthetic scenarios."""

    if not scenarios or not evidence_complete or any(
        not scenario.is_complete() for scenario in scenarios
    ):
        return "RC1_REJECTED_EVIDENCE_INCOMPLETE"
    if any(not scenario.is_success() for scenario in scenarios):
        return "RC1_REJECTED_BLOCKERS"
    return "RC1_ACCEPTED"


@dataclass(frozen=True)
class ResourceSnapshot:
    identities: tuple[str, ...]
    unrelated_state: tuple[tuple[str, str], ...]
    ready: bool


def reconcile_is_idempotent(before: ResourceSnapshot, after: ResourceSnapshot) -> bool:
    """Return true only when identity, unrelated state and readiness converge."""

    return (
        len(after.identities) == len(set(after.identities))
        and before.identities == after.identities
        and before.unrelated_state == after.unrelated_state
        and after.ready
    )


def update_preserves_unrelated_state(
    before: ResourceSnapshot,
    after: ResourceSnapshot,
) -> bool:
    """Return true only when an update preserves unrelated healthy resources."""

    return before.unrelated_state == after.unrelated_state and after.ready


def restart_is_verified(before: ResourceSnapshot, after: ResourceSnapshot) -> bool:
    """Return true only when restart preserves identities and reaches ready."""

    return before.identities == after.identities and after.ready

from __future__ import annotations

from typing import Protocol

from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PLATFORM_WORKFLOW_TAXONOMY,
)
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class PlatformWorkflowOutcomeSource(Protocol):
    @property
    def kind(self) -> PlatformWorkflowKind:
        ...

    @property
    def status(self) -> PlatformWorkflowStatus:
        ...

    @property
    def verification_results(self) -> tuple[VerificationResult, ...]:
        ...


def platform_workflow_outcome(result: PlatformWorkflowOutcomeSource) -> dict[str, object]:
    kind = result.kind
    status = result.status
    verification_results = result.verification_results
    semantics = PLATFORM_WORKFLOW_TAXONOMY[kind]
    facts = _OutcomeFacts.from_result(status, verification_results)
    return {
        "mutation": _mutation_outcome(
            mutating=semantics.mutating,
            status=status,
            facts=facts,
        ),
        "verification": _verification_outcome(status=status, facts=facts),
    }


class _OutcomeFacts:
    def __init__(self, *, applied: bool, blocked: bool, verified: bool):
        self.applied = applied
        self.blocked = blocked
        self.verified = verified

    @classmethod
    def from_result(
        cls,
        status: PlatformWorkflowStatus,
        verification_results: tuple[VerificationResult, ...],
    ) -> _OutcomeFacts:
        return cls(
            applied=any(
                verification.evidence.get("applied") == "true"
                for verification in verification_results
            ),
            blocked=status == PlatformWorkflowStatus.BLOCKED
            or any(
                verification.status == VerificationStatus.BLOCKED
                for verification in verification_results
            ),
            verified=status == PlatformWorkflowStatus.COMPLETED
            and bool(verification_results)
            and all(
                verification.status == VerificationStatus.VERIFIED
                for verification in verification_results
            ),
        )


def _mutation_outcome(
    *,
    mutating: bool,
    status: PlatformWorkflowStatus,
    facts: _OutcomeFacts,
) -> dict[str, object]:
    result = _mutation_result(mutating=mutating, status=status, facts=facts)
    return {
        "planned": mutating,
        "executed": facts.applied,
        "result": result,
    }


def _mutation_result(
    *,
    mutating: bool,
    status: PlatformWorkflowStatus,
    facts: _OutcomeFacts,
) -> str:
    candidates = (
        (not mutating, "not_applicable"),
        (facts.blocked, "blocked"),
        (status == PlatformWorkflowStatus.FAILED_TO_APPLY, "failed_to_apply"),
        (status == PlatformWorkflowStatus.FAILED_TO_VERIFY, "failed_to_verify"),
        (facts.applied, "converged"),
        (facts.verified, "no_op"),
    )
    return next((result for matches, result in candidates if matches), "skipped")


def _verification_outcome(
    *,
    status: PlatformWorkflowStatus,
    facts: _OutcomeFacts,
) -> str:
    candidates = (
        (facts.blocked, "blocked"),
        (facts.verified, "verified"),
        (status == PlatformWorkflowStatus.COMPLETED, "not_available"),
    )
    return next((result for matches, result in candidates if matches), status.value)

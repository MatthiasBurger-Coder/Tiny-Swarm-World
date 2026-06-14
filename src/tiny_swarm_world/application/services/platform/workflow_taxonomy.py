from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


RESET_TINY_SWARM_PLATFORM_CONFIRMATION = "RESET_TINY_SWARM_PLATFORM"
DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION = "DESTROY_TINY_SWARM_PLATFORM"


class PlatformWorkflowKind(str, Enum):
    INIT = "init"
    RECONCILE = "reconcile"
    EXPOSE = "expose"
    REPAIR_LXC_PROXY_DRIFT = "repair-lxc-proxy-drift"
    RESET = "reset"
    DESTROY = "destroy"
    VERIFY = "verify"


class PlatformWorkflowStatus(str, Enum):
    COMPLETED = "completed"
    REFUSED = "refused"
    BLOCKED = "blocked"
    FAILED_TO_APPLY = "failed_to_apply"
    FAILED_TO_VERIFY = "failed_to_verify"


@dataclass(frozen=True)
class PlatformWorkflowSemantics:
    kind: PlatformWorkflowKind
    mutating: bool
    destructive: bool
    requires_confirmation: bool
    meaning: str
    confirmation_phrase: str | None = None


@dataclass(frozen=True)
class PlatformWorkflowResult:
    kind: PlatformWorkflowKind
    status: PlatformWorkflowStatus
    message: str
    executed: bool
    verification_results: tuple[VerificationResult, ...] = ()

    @property
    def workflow_name(self) -> str:
        return f"platform {self.kind.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "message": self.message,
            "outcome": _platform_workflow_outcome(self),
            "status": self.status.value,
            "verification_results": [
                verification.to_dict() for verification in self.verification_results
            ],
            "workflow": self.workflow_name,
        }

    @classmethod
    def completed(
        cls,
        semantics: PlatformWorkflowSemantics,
        *,
        executed: bool,
        verification_results: tuple[VerificationResult, ...] = (),
    ) -> PlatformWorkflowResult:
        return cls(
            kind=semantics.kind,
            status=PlatformWorkflowStatus.COMPLETED,
            message=f"{semantics.kind.value} workflow completed.",
            executed=executed,
            verification_results=verification_results,
        )

    @classmethod
    def refused(
        cls,
        semantics: PlatformWorkflowSemantics,
        message: str,
    ) -> PlatformWorkflowResult:
        return cls(
            kind=semantics.kind,
            status=PlatformWorkflowStatus.REFUSED,
            message=message,
            executed=False,
        )

    @classmethod
    def blocked(
        cls,
        semantics: PlatformWorkflowSemantics,
        message: str,
        verification_results: tuple[VerificationResult, ...] = (),
        *,
        executed: bool = False,
    ) -> PlatformWorkflowResult:
        return cls(
            kind=semantics.kind,
            status=PlatformWorkflowStatus.BLOCKED,
            message=message,
            executed=executed,
            verification_results=verification_results,
        )

    @classmethod
    def failed_to_apply(
        cls,
        semantics: PlatformWorkflowSemantics,
        message: str,
        verification_results: tuple[VerificationResult, ...],
    ) -> PlatformWorkflowResult:
        return cls(
            kind=semantics.kind,
            status=PlatformWorkflowStatus.FAILED_TO_APPLY,
            message=message,
            executed=True,
            verification_results=verification_results,
        )

    @classmethod
    def failed_to_verify(
        cls,
        semantics: PlatformWorkflowSemantics,
        message: str,
        verification_results: tuple[VerificationResult, ...],
    ) -> PlatformWorkflowResult:
        return cls(
            kind=semantics.kind,
            status=PlatformWorkflowStatus.FAILED_TO_VERIFY,
            message=message,
            executed=True,
            verification_results=verification_results,
        )


PLATFORM_WORKFLOW_TAXONOMY = {
    PlatformWorkflowKind.INIT: PlatformWorkflowSemantics(
        kind=PlatformWorkflowKind.INIT,
        mutating=True,
        destructive=False,
        requires_confirmation=False,
        meaning="create missing managed resources",
    ),
    PlatformWorkflowKind.RECONCILE: PlatformWorkflowSemantics(
        kind=PlatformWorkflowKind.RECONCILE,
        mutating=True,
        destructive=False,
        requires_confirmation=False,
        meaning="converge existing managed state",
    ),
    PlatformWorkflowKind.EXPOSE: PlatformWorkflowSemantics(
        kind=PlatformWorkflowKind.EXPOSE,
        mutating=True,
        destructive=False,
        requires_confirmation=False,
        meaning="expose published Swarm service ports through the LXC gateway",
    ),
    PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT: PlatformWorkflowSemantics(
        kind=PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT,
        mutating=True,
        destructive=False,
        requires_confirmation=False,
        meaning="remove stale direct LXC proxy devices after profile reconciliation",
    ),
    PlatformWorkflowKind.RESET: PlatformWorkflowSemantics(
        kind=PlatformWorkflowKind.RESET,
        mutating=True,
        destructive=True,
        requires_confirmation=True,
        meaning="explicitly reinitialize managed resources",
        confirmation_phrase=RESET_TINY_SWARM_PLATFORM_CONFIRMATION,
    ),
    PlatformWorkflowKind.DESTROY: PlatformWorkflowSemantics(
        kind=PlatformWorkflowKind.DESTROY,
        mutating=True,
        destructive=True,
        requires_confirmation=True,
        meaning="explicitly tear down managed resources",
        confirmation_phrase=DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION,
    ),
    PlatformWorkflowKind.VERIFY: PlatformWorkflowSemantics(
        kind=PlatformWorkflowKind.VERIFY,
        mutating=False,
        destructive=False,
        requires_confirmation=False,
        meaning="inspect current state",
    ),
}


def _platform_workflow_outcome(result: PlatformWorkflowResult) -> dict[str, object]:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[result.kind]
    applied = any(
        verification.evidence.get("applied") == "true"
        for verification in result.verification_results
    )
    blocked = result.status == PlatformWorkflowStatus.BLOCKED or any(
        verification.status == VerificationStatus.BLOCKED
        for verification in result.verification_results
    )
    verified = (
        result.status == PlatformWorkflowStatus.COMPLETED
        and bool(result.verification_results)
        and all(
            verification.status == VerificationStatus.VERIFIED
            for verification in result.verification_results
        )
    )
    return {
        "mutation": _mutation_outcome(
            mutating=semantics.mutating,
            status=result.status,
            applied=applied,
            blocked=blocked,
            verified=verified,
        ),
        "verification": _verification_outcome(
            status=result.status,
            blocked=blocked,
            verified=verified,
        ),
    }


def _mutation_outcome(
    *,
    mutating: bool,
    status: PlatformWorkflowStatus,
    applied: bool,
    blocked: bool,
    verified: bool,
) -> dict[str, object]:
    if not mutating:
        result = "not_applicable"
    elif blocked:
        result = "blocked"
    elif status == PlatformWorkflowStatus.FAILED_TO_APPLY:
        result = "failed_to_apply"
    elif status == PlatformWorkflowStatus.FAILED_TO_VERIFY:
        result = "failed_to_verify"
    elif applied:
        result = "converged"
    elif verified:
        result = "no_op"
    else:
        result = "skipped"
    return {
        "planned": mutating,
        "executed": applied,
        "result": result,
    }


def _verification_outcome(
    *,
    status: PlatformWorkflowStatus,
    blocked: bool,
    verified: bool,
) -> str:
    if blocked:
        return "blocked"
    if verified:
        return "verified"
    if status == PlatformWorkflowStatus.COMPLETED:
        return "not_available"
    return status.value

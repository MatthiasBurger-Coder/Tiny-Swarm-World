from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.domain.inventory import VerificationResult


RESET_TINY_SWARM_PLATFORM_CONFIRMATION = "RESET_TINY_SWARM_PLATFORM"
DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION = "DESTROY_TINY_SWARM_PLATFORM"


class PlatformWorkflowKind(str, Enum):
    INIT = "init"
    RECONCILE = "reconcile"
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
    ) -> PlatformWorkflowResult:
        return cls(
            kind=semantics.kind,
            status=PlatformWorkflowStatus.BLOCKED,
            message=message,
            executed=False,
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

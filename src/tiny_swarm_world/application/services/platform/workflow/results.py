from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.services.platform.workflow.outcomes import (
    platform_workflow_outcome,
)
from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PlatformWorkflowSemantics,
)
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import VerificationResult


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
            "outcome": platform_workflow_outcome(self),
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

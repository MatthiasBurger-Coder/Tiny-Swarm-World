from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ArtifactWorkflowKind(str, Enum):
    PREPARE = "prepare"
    VERIFY = "verify"


class ArtifactWorkflowStatus(str, Enum):
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ArtifactWorkflowResult:
    kind: ArtifactWorkflowKind
    status: ArtifactWorkflowStatus
    message: str
    reason: str
    executed: bool = False

    @property
    def workflow_name(self) -> str:
        return f"artifacts {self.kind.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "message": self.message,
            "reason": self.reason,
            "status": self.status.value,
            "workflow": self.workflow_name,
        }


class ArtifactPrepareWorkflow:
    async def run(self) -> ArtifactWorkflowResult:
        return ArtifactWorkflowResult(
            kind=ArtifactWorkflowKind.PREPARE,
            status=ArtifactWorkflowStatus.BLOCKED,
            message="artifacts prepare is blocked until artifact preparation contracts are wired.",
            reason=(
                "image build, image push, and Nexus repository setup require explicit live "
                "registry and Nexus contracts"
            ),
        )


class ArtifactVerifyWorkflow:
    async def run(self) -> ArtifactWorkflowResult:
        return ArtifactWorkflowResult(
            kind=ArtifactWorkflowKind.VERIFY,
            status=ArtifactWorkflowStatus.BLOCKED,
            message="artifacts verify is blocked until artifact verification contracts are wired.",
            reason=(
                "artifact registry observed-state verification is not implemented through "
                "an application port"
            ),
        )

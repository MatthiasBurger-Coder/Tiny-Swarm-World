from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeploymentWorkflowKind(str, Enum):
    APPLY = "apply"
    VERIFY = "verify"


class DeploymentWorkflowStatus(str, Enum):
    BLOCKED = "blocked"


@dataclass(frozen=True)
class DeploymentWorkflowResult:
    kind: DeploymentWorkflowKind
    status: DeploymentWorkflowStatus
    message: str
    reason: str
    executed: bool = False

    @property
    def workflow_name(self) -> str:
        return f"deployment {self.kind.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "message": self.message,
            "reason": self.reason,
            "status": self.status.value,
            "workflow": self.workflow_name,
        }


class DeploymentApplyWorkflow:
    async def run(self) -> DeploymentWorkflowResult:
        return DeploymentWorkflowResult(
            kind=DeploymentWorkflowKind.APPLY,
            status=DeploymentWorkflowStatus.BLOCKED,
            message="deployment apply is blocked until stack deployment contracts are wired.",
            reason=(
                "Portainer stack changes require command-backed verification and live "
                "operation contracts before apply can run"
            ),
        )


class DeploymentVerifyWorkflow:
    async def run(self) -> DeploymentWorkflowResult:
        return DeploymentWorkflowResult(
            kind=DeploymentWorkflowKind.VERIFY,
            status=DeploymentWorkflowStatus.BLOCKED,
            message="deployment verify is blocked until stack verification contracts are wired.",
            reason=(
                "stack and service observed-state verification is not implemented through "
                "deployment ports"
            ),
        )

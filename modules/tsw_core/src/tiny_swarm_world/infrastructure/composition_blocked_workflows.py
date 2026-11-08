from __future__ import annotations

import asyncio

from tiny_swarm_world.application.ports.operation_result import OperationFailure, OperationOutcome, OperationResult

from tiny_swarm_world.application.services.artifacts import (
    ArtifactWorkflowKind,
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
)
from tiny_swarm_world.application.services.deployment import (
    DeploymentWorkflowKind,
    DeploymentWorkflowResult,
    DeploymentWorkflowStatus,
)


class BlockedArtifactWorkflow:
    def __init__(self, kind: ArtifactWorkflowKind, reason: str):
        self.kind = kind
        self.reason = reason
        self.steps = ()
        self.checks = ()

    async def run(self) -> ArtifactWorkflowResult:
        await asyncio.sleep(0)
        return ArtifactWorkflowResult(
            kind=self.kind,
            status=ArtifactWorkflowStatus.BLOCKED,
            operation_result=OperationResult(OperationOutcome.BLOCKED, (OperationFailure.for_cause("artifacts.provider", "artifacts", "blocked"),), pending_operations=("artifacts.run",)),
            message=(
                f"artifacts {self.kind.value} is blocked for the selected node provider."
            ),
            reason=self.reason,
        )


class BlockedDeploymentWorkflow:
    def __init__(self, kind: DeploymentWorkflowKind, reason: str):
        self.kind = kind
        self.reason = reason
        self.steps = ()
        self.pre_apply_checks = ()
        self.checks = ()

    async def run(self) -> DeploymentWorkflowResult:
        await asyncio.sleep(0)
        return DeploymentWorkflowResult(
            kind=self.kind,
            status=DeploymentWorkflowStatus.BLOCKED,
            operation_result=OperationResult(OperationOutcome.BLOCKED, (OperationFailure.for_cause("deployment.provider", "deployment", "blocked"),), pending_operations=("deployment.run",)),
            message=(
                f"deployment {self.kind.value} is blocked for the selected node provider."
            ),
            reason=self.reason,
        )

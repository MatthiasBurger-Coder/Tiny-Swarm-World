"""Application dispatch for workflow actions selected by the command adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tiny_swarm_world.application.services.artifacts import (
    ArtifactPrepareWorkflow,
    ArtifactVerifyWorkflow,
    ArtifactWorkflowResult,
)
from tiny_swarm_world.application.services.deployment import (
    DeploymentApplyWorkflow,
    DeploymentVerifyWorkflow,
    DeploymentWorkflowResult,
)
from tiny_swarm_world.application.services.platform import (
    PlatformLifecycleOrchestrator,
    PlatformLifecycleRequest,
)
from tiny_swarm_world.application.services.platform.workflow.results import PlatformWorkflowResult
from tiny_swarm_world.application.services.platform.workflow.types import PlatformWorkflowKind
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.domain.update import ClassicUpdatePlan


class ClassicUpdateAction(Protocol):
    async def run(
        self, plan: ClassicUpdatePlan, *, preview: bool, live_consent: LiveConsent | None
    ) -> PlatformWorkflowResult: ...

    async def recover(
        self,
        stack_name: str,
        service_name: str,
        *,
        preview: bool,
        live_consent: LiveConsent | None,
    ) -> PlatformWorkflowResult: ...


@dataclass(frozen=True)
class ClassicUpdateActionRequest:
    plan: ClassicUpdatePlan | None
    preview: bool
    recover: bool
    stack_name: str | None
    service_name: str | None
    live_consent: LiveConsent | None


async def run_classic_update_action(
    workflow: ClassicUpdateAction,
    request: ClassicUpdateActionRequest,
) -> PlatformWorkflowResult:
    if request.recover:
        if request.plan is not None:
            raise ValueError("recovery cannot be combined with an update plan")
        if request.stack_name is None or request.service_name is None:
            raise ValueError("platform update recovery requires stack and service")
        return await workflow.recover(
            request.stack_name,
            request.service_name,
            preview=request.preview,
            live_consent=request.live_consent,
        )
    if request.plan is None:
        raise ValueError("platform update requires an update plan")
    return await workflow.run(
        request.plan,
        preview=request.preview,
        live_consent=request.live_consent,
    )


def require_setup_run(action: str, live_consent: LiveConsent | None) -> LiveConsent:
    if action != "run":
        raise ValueError(f"Unsupported setup workflow: {action}")
    if live_consent is None or not live_consent.accepted:
        raise ValueError("setup run requires accepted live consent")
    return live_consent


async def run_platform_action(
    lifecycle: PlatformLifecycleOrchestrator,
    kind: PlatformWorkflowKind,
    confirmation: str | None,
) -> PlatformWorkflowResult:
    return await lifecycle.run(PlatformLifecycleRequest(kind=kind, confirmation=confirmation))


async def run_artifact_action(
    action: str,
    prepare: ArtifactPrepareWorkflow,
    verify: ArtifactVerifyWorkflow,
) -> ArtifactWorkflowResult:
    match action:
        case "prepare":
            return await prepare.run()
        case "verify":
            return await verify.run()
        case _:
            raise ValueError(f"Unsupported artifacts workflow: {action}")


async def run_deployment_action(
    action: str,
    bootstrap: DeploymentApplyWorkflow,
    apply: DeploymentApplyWorkflow,
    verify: DeploymentVerifyWorkflow,
) -> DeploymentWorkflowResult:
    match action:
        case "bootstrap":
            return await bootstrap.run()
        case "apply":
            return await apply.run()
        case "verify":
            return await verify.run()
        case _:
            raise ValueError(f"Unsupported deployment workflow: {action}")

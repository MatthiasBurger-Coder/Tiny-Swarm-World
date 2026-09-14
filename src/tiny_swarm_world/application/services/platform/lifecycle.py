"""Application orchestration for the platform lifecycle.

This module owns lifecycle dispatch only. Platform capabilities are supplied
as workflow ports so the application layer does not construct or inspect
provider-specific infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tiny_swarm_world.application.services.platform.workflow.results import (
    PlatformWorkflowResult,
)
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
)


class _RunnableWorkflow(Protocol):
    async def run(self) -> PlatformWorkflowResult:
        """Run a non-destructive platform workflow."""


class _ConfirmableWorkflow(Protocol):
    async def run(self, confirmation: str | None = None) -> PlatformWorkflowResult:
        """Run a confirmation-gated platform workflow."""


@dataclass(frozen=True)
class PlatformLifecycleRequest:
    """The complete input needed to select one platform lifecycle action."""

    kind: PlatformWorkflowKind
    confirmation: str | None = None


@dataclass(frozen=True)
class PlatformLifecycleWorkflows:
    """Workflow ports required by the lifecycle orchestrator."""

    init: _RunnableWorkflow
    reconcile: _RunnableWorkflow
    expose: _RunnableWorkflow
    repair_lxc_proxy_drift: _RunnableWorkflow
    verify: _RunnableWorkflow
    reset: _ConfirmableWorkflow
    destroy: _ConfirmableWorkflow


class PlatformLifecycleOrchestrator:
    """Dispatch a typed request to exactly one platform use-case workflow."""

    def __init__(self, workflows: PlatformLifecycleWorkflows):
        self.workflows = workflows

    async def run(self, request: PlatformLifecycleRequest) -> PlatformWorkflowResult:
        """Execute the requested lifecycle action and return its typed result."""

        match request.kind:
            case PlatformWorkflowKind.INIT:
                return await self.workflows.init.run()
            case PlatformWorkflowKind.RECONCILE:
                return await self.workflows.reconcile.run()
            case PlatformWorkflowKind.EXPOSE:
                return await self.workflows.expose.run()
            case PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT:
                return await self.workflows.repair_lxc_proxy_drift.run()
            case PlatformWorkflowKind.VERIFY:
                return await self.workflows.verify.run()
            case PlatformWorkflowKind.RESET:
                return await self.workflows.reset.run(request.confirmation)
            case PlatformWorkflowKind.DESTROY:
                return await self.workflows.destroy.run(request.confirmation)
            case _:
                raise ValueError(f"Unsupported platform lifecycle action: {request.kind}")


__all__ = [
    "PlatformLifecycleOrchestrator",
    "PlatformLifecycleRequest",
    "PlatformLifecycleWorkflows",
]

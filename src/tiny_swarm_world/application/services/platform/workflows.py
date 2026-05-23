from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    PLATFORM_WORKFLOW_TAXONOMY,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowSemantics,
)


class AsyncWorkflowStep(Protocol):
    async def run(self) -> object:
        pass


class PlatformInitWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.INIT]

    def __init__(self, steps: Sequence[AsyncWorkflowStep]):
        self.steps = tuple(steps)

    async def run(self) -> PlatformWorkflowResult:
        await _run_steps(self.steps)
        return PlatformWorkflowResult.completed(self.semantics, executed=bool(self.steps))


class PlatformReconcileWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.RECONCILE]

    def __init__(self, steps: Sequence[AsyncWorkflowStep]):
        self.steps = tuple(steps)

    async def run(self) -> PlatformWorkflowResult:
        await _run_steps(self.steps)
        return PlatformWorkflowResult.completed(self.semantics, executed=bool(self.steps))


class PlatformResetWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.RESET]

    def __init__(self, steps: Sequence[AsyncWorkflowStep] = ()):
        self.steps = tuple(steps)

    async def run(self, confirmation: str | None = None) -> PlatformWorkflowResult:
        if not _confirmation_matches(self.semantics, confirmation):
            return _refused_for_confirmation(self.semantics)
        if not self.steps:
            return _blocked_until_retention_policy_exists(self.semantics)
        await _run_steps(self.steps)
        return PlatformWorkflowResult.completed(self.semantics, executed=True)


class PlatformDestroyWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.DESTROY]

    def __init__(self, steps: Sequence[AsyncWorkflowStep] = ()):
        self.steps = tuple(steps)

    async def run(self, confirmation: str | None = None) -> PlatformWorkflowResult:
        if not _confirmation_matches(self.semantics, confirmation):
            return _refused_for_confirmation(self.semantics)
        if not self.steps:
            return _blocked_until_retention_policy_exists(self.semantics)
        await _run_steps(self.steps)
        return PlatformWorkflowResult.completed(self.semantics, executed=True)


class PlatformVerifyWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.VERIFY]

    def __init__(self, steps: Sequence[AsyncWorkflowStep]):
        self.steps = tuple(steps)

    async def run(self) -> PlatformWorkflowResult:
        await _run_steps(self.steps)
        return PlatformWorkflowResult.completed(self.semantics, executed=bool(self.steps))


async def _run_steps(steps: Sequence[AsyncWorkflowStep]) -> None:
    for step in steps:
        await step.run()


def _confirmation_matches(
    semantics: PlatformWorkflowSemantics,
    confirmation: str | None,
) -> bool:
    return semantics.confirmation_phrase is not None and confirmation == semantics.confirmation_phrase


def _refused_for_confirmation(semantics: PlatformWorkflowSemantics) -> PlatformWorkflowResult:
    return PlatformWorkflowResult.refused(
        semantics,
        f"{semantics.kind.value} requires exact confirmation.",
    )


def _blocked_until_retention_policy_exists(
    semantics: PlatformWorkflowSemantics,
) -> PlatformWorkflowResult:
    return PlatformWorkflowResult.blocked(
        semantics,
        f"{semantics.kind.value} retention policy is not implemented.",
    )

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from tiny_swarm_world.application.ports.method_trace import (
    NullMethodTrace,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    NullWorkflowProgress,
    PortWorkflowProgress,
)
from tiny_swarm_world.application.ports.repositories.port_verification_evidence_repository import (
    PortVerificationEvidenceRepository,
)
from tiny_swarm_world.application.services.platform.workflow.results import (
    PlatformWorkflowResult,
)
from tiny_swarm_world.application.services.platform.workflow.runtime import (
    _blocked_until_retention_policy_exists,
    _confirmation_matches,
    _refused_for_confirmation,
    _report_workflow_progress,
    _run_mutating_steps,
    _trace_platform_run,
)
from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PLATFORM_WORKFLOW_TAXONOMY,
    PlatformWorkflowSemantics,
)
from tiny_swarm_world.application.services.platform.workflow.steps import AsyncWorkflowStep
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
    PlatformWorkflowStatus,
)


class _DestructivePlatformWorkflow:
    semantics: ClassVar[PlatformWorkflowSemantics]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep] = (),
        verification_evidence_repository: PortVerificationEvidenceRepository | None = None,
        progress: PortWorkflowProgress | None = None,
        method_trace: PortMethodTrace | None = None,
        trace_correlation_id: str | None = None,
    ):
        self.steps = tuple(steps)
        self.verification_evidence_repository = verification_evidence_repository
        self.progress = progress or NullWorkflowProgress()
        self.method_trace = method_trace or NullMethodTrace()
        self.trace_correlation_id = trace_correlation_id

    async def run(self, confirmation: str | None = None) -> PlatformWorkflowResult:
        return await _trace_platform_run(self, self._run, confirmation)

    async def _run(self, confirmation: str | None = None) -> PlatformWorkflowResult:
        if not _confirmation_matches(self.semantics, confirmation):
            _report_workflow_progress(
                self.progress,
                self.semantics,
                step="confirmation",
                status=PlatformWorkflowStatus.REFUSED.value,
                result=PlatformWorkflowStatus.REFUSED.value,
                safe_message="Platform workflow confirmation was refused.",
            )
            return _refused_for_confirmation(self.semantics)
        if not self.steps:
            _report_workflow_progress(
                self.progress,
                self.semantics,
                step="step configuration",
                status=PlatformWorkflowStatus.BLOCKED.value,
                result=PlatformWorkflowStatus.BLOCKED.value,
                safe_message="Platform workflow is blocked until steps are configured.",
            )
            return _blocked_until_retention_policy_exists(self.semantics)
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
            self.progress,
        )


class PlatformResetWorkflow(_DestructivePlatformWorkflow):
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.RESET]


class PlatformDestroyWorkflow(_DestructivePlatformWorkflow):
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.DESTROY]

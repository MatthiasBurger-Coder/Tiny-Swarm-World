from __future__ import annotations

from collections.abc import Sequence

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
    _run_mutating_steps,
    _run_pre_apply_guard,
    _trace_platform_run,
)
from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PLATFORM_WORKFLOW_TAXONOMY,
)
from tiny_swarm_world.application.services.platform.workflow.steps import AsyncWorkflowStep
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
)


class PlatformInitWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.INIT]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
        verification_evidence_repository: PortVerificationEvidenceRepository | None = None,
        pre_apply_guard: AsyncWorkflowStep | None = None,
        progress: PortWorkflowProgress | None = None,
        method_trace: PortMethodTrace | None = None,
        trace_correlation_id: str | None = None,
    ):
        self.steps = tuple(steps)
        self.verification_evidence_repository = verification_evidence_repository
        self.pre_apply_guard = pre_apply_guard
        self.progress = progress or NullWorkflowProgress()
        self.method_trace = method_trace or NullMethodTrace()
        self.trace_correlation_id = trace_correlation_id

    async def run(self) -> PlatformWorkflowResult:
        return await _trace_platform_run(self, self._run)

    async def _run(self) -> PlatformWorkflowResult:
        guard_verification, guard_result = await _run_pre_apply_guard(
            self.pre_apply_guard,
            self.semantics,
            self.verification_evidence_repository,
            self.progress,
        )
        if guard_result is not None:
            return guard_result
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
            self.progress,
            initial_verification_results=(
                (guard_verification,) if guard_verification is not None else ()
            ),
        )

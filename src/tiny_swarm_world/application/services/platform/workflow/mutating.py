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
    _trace_platform_run,
)
from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PLATFORM_WORKFLOW_TAXONOMY,
)
from tiny_swarm_world.application.services.platform.workflow.steps import AsyncWorkflowStep
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
)


class PlatformReconcileWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.RECONCILE]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
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

    async def run(self) -> PlatformWorkflowResult:
        return await _trace_platform_run(self, self._run)

    async def _run(self) -> PlatformWorkflowResult:
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
            self.progress,
        )

class PlatformExposeWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.EXPOSE]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
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

    async def run(self) -> PlatformWorkflowResult:
        return await _trace_platform_run(self, self._run)

    async def _run(self) -> PlatformWorkflowResult:
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
            self.progress,
        )


class PlatformRepairLxcProxyDriftWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
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

    async def run(self) -> PlatformWorkflowResult:
        return await _trace_platform_run(self, self._run)

    async def _run(self) -> PlatformWorkflowResult:
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
            self.progress,
        )

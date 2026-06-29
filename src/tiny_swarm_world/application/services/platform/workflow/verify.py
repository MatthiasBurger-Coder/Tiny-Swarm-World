from __future__ import annotations

import asyncio
from collections.abc import Sequence

from tiny_swarm_world.application.ports.method_trace import (
    NullMethodTrace,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    NullWorkflowProgress,
    PortWorkflowProgress,
)
from tiny_swarm_world.application.services.platform.workflow.results import (
    PlatformWorkflowResult,
)
from tiny_swarm_world.application.services.platform.workflow.runtime import (
    WORKFLOW_STOPPED_STEP,
    _report_step_progress,
    _report_verification_progress,
    _report_workflow_progress,
    _retryable_platform_verify_result,
    _trace_platform_run,
    _verification_result_from_verify_output,
    _verification_target_id,
    _verification_with_retry_attempt,
)
from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PLATFORM_WORKFLOW_TAXONOMY,
)
from tiny_swarm_world.application.services.platform.workflow.steps import AsyncWorkflowStep
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class PlatformVerifyWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.VERIFY]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
        progress: PortWorkflowProgress | None = None,
        method_trace: PortMethodTrace | None = None,
        trace_correlation_id: str | None = None,
        verify_retry_attempts: int = 1,
        verify_retry_delay_seconds: float = 0.0,
    ):
        self.steps = tuple(steps)
        self.progress = progress or NullWorkflowProgress()
        self.method_trace = method_trace or NullMethodTrace()
        self.trace_correlation_id = trace_correlation_id
        self.verify_retry_attempts = max(1, verify_retry_attempts)
        self.verify_retry_delay_seconds = max(0.0, verify_retry_delay_seconds)

    async def run(self) -> PlatformWorkflowResult:
        return await _trace_platform_run(self, self._run)

    async def _run(self) -> PlatformWorkflowResult:
        verification_results: list[VerificationResult] = []
        for step in self.steps:
            target_id = _verification_target_id(step)
            _report_step_progress(
                self.progress,
                self.semantics,
                target_id=target_id,
                step="verify step",
                status="started",
                result="pending",
                safe_message="Platform verify step started.",
            )
            verification_result = await self._run_verify_step_with_retry(step)
            if verification_result is None:
                continue
            verification_results.append(verification_result)
            _report_verification_progress(
                self.progress,
                self.semantics,
                verification_result,
                step="verify step",
            )
            if verification_result.status == VerificationStatus.BLOCKED:
                _report_workflow_progress(
                    self.progress,
                    self.semantics,
                    step=WORKFLOW_STOPPED_STEP,
                    status=PlatformWorkflowStatus.BLOCKED.value,
                    result=PlatformWorkflowStatus.BLOCKED.value,
                    safe_message="Platform workflow stopped after a blocked verification.",
                )
                return PlatformWorkflowResult.blocked(
                    self.semantics,
                    f"{self.semantics.kind.value} verification is blocked.",
                    tuple(verification_results),
                )
            if verification_result.status != VerificationStatus.VERIFIED:
                _report_workflow_progress(
                    self.progress,
                    self.semantics,
                    step=WORKFLOW_STOPPED_STEP,
                    status=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
                    result=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
                    safe_message="Platform workflow stopped after a failed verification.",
                )
                return PlatformWorkflowResult.failed_to_verify(
                    self.semantics,
                    f"{self.semantics.kind.value} verification failed.",
                    tuple(verification_results),
                )
        _report_workflow_progress(
            self.progress,
            self.semantics,
            step="workflow completed",
            status=PlatformWorkflowStatus.COMPLETED.value,
            result=PlatformWorkflowStatus.COMPLETED.value,
            safe_message="Platform workflow completed.",
        )
        return PlatformWorkflowResult.completed(
            self.semantics,
            executed=bool(self.steps),
            verification_results=tuple(verification_results),
        )

    async def _run_verify_step_with_retry(
        self,
        step: AsyncWorkflowStep,
    ) -> VerificationResult | None:
        last_result: VerificationResult | None = None
        for attempt in range(1, self.verify_retry_attempts + 1):
            step_result = await step.run()
            verification_result = _verification_result_from_verify_output(step_result)
            if verification_result is None:
                return None
            last_result = _verification_with_retry_attempt(verification_result, attempt)
            if not _retryable_platform_verify_result(verification_result):
                return last_result
            if attempt >= self.verify_retry_attempts:
                return last_result
            if self.verify_retry_delay_seconds:
                await asyncio.sleep(self.verify_retry_delay_seconds)
        return last_result

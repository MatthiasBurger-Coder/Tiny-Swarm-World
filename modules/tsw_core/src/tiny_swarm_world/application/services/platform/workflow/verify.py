from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import replace

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome
from tiny_swarm_world.application.services.shared.operation_results import aggregate_operation, failures_to_evidence, failures_from_evidence, progress_from_evidence

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
    PLATFORM_FAILURE_ORIGINS,
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
        completed: list[str] = []
        verification_indices: list[int] = []
        caught_failures: list[OperationFailure] = []
        missing: list[str] = []
        for index, step in enumerate(self.steps, 1):
            identity = f"platform.verify.step.{index}.verify"
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
            verification_result = await self._run_verify_step_with_retry(step, caught_failures)
            if verification_result is None:
                missing.append(identity)
                continue
            verification_indices.append(index)
            verification_results.append(verification_result)
            _report_verification_progress(
                self.progress,
                self.semantics,
                verification_result,
                step="verify step",
            )
            if verification_result.status == VerificationStatus.VERIFIED:
                completed.append(identity)
            if verification_result.status == VerificationStatus.BLOCKED:
                _report_workflow_progress(
                    self.progress,
                    self.semantics,
                    step=WORKFLOW_STOPPED_STEP,
                    status=PlatformWorkflowStatus.BLOCKED.value,
                    result=PlatformWorkflowStatus.BLOCKED.value,
                    safe_message="Platform workflow stopped after a blocked verification.",
                )
                legacy = PlatformWorkflowResult.blocked(
                    self.semantics,
                    f"{self.semantics.kind.value} verification is blocked.",
                    tuple(verification_results),
                )
                return self._with_operation(legacy, completed, (*missing, identity), index, verification_indices, caught_failures)
            if verification_result.status != VerificationStatus.VERIFIED:
                _report_workflow_progress(
                    self.progress,
                    self.semantics,
                    step=WORKFLOW_STOPPED_STEP,
                    status=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
                    result=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
                    safe_message="Platform workflow stopped after a failed verification.",
                )
                legacy = PlatformWorkflowResult.failed_to_verify(
                    self.semantics,
                    f"{self.semantics.kind.value} verification failed.",
                    tuple(verification_results),
                )
                return self._with_operation(legacy, completed, (*missing, identity), index, verification_indices, caught_failures)
        _report_workflow_progress(
            self.progress,
            self.semantics,
            step="workflow completed",
            status=PlatformWorkflowStatus.COMPLETED.value,
            result=PlatformWorkflowStatus.COMPLETED.value,
            safe_message="Platform workflow completed.",
        )
        legacy = PlatformWorkflowResult.completed(
            self.semantics,
            executed=bool(self.steps),
            verification_results=tuple(verification_results),
        )
        return self._with_operation(legacy, completed, missing, len(self.steps), verification_indices, caught_failures)

    def _with_operation(
        self, legacy: PlatformWorkflowResult, completed: list[str], requested_pending: Sequence[str],
        index: int, verification_indices: Sequence[int], caught_failures: Sequence[OperationFailure],
    ) -> PlatformWorkflowResult:
        pending = list((*requested_pending, *(f"platform.verify.step.{remaining}.verify" for remaining in range(index + 1, len(self.steps) + 1))))
        completed = list(completed)
        failures: list[OperationFailure] = []
        uncertain: list[str] = []
        for step_index, result in zip(verification_indices, legacy.verification_results, strict=True):
            identity = f"platform.verify.step.{step_index}.verify"
            allowed = frozenset(getattr(self.steps[step_index - 1], "operation_work_ids", ()))
            try:
                child_failures = failures_from_evidence(result.evidence, allowed_origins=PLATFORM_FAILURE_ORIGINS | frozenset((failure.operation, failure.component) for failure in caught_failures), fallback_operation="platform.verify", fallback_component="platform")
                child_fields = {field: progress_from_evidence(result.evidence, field, allowed_operations=allowed) for field in ("completed", "pending", "uncertain")} if allowed else {}
                aggregate_operation(OperationOutcome.SUCCESS, completed=tuple(value for values in child_fields.values() for value in values))
            except ValueError:
                child_failures = (OperationFailure.for_cause("platform.verify", "platform", "unexpected_failure"),)
                child_fields = {}
            failures.extend(child_failures)
            if child_fields and any(child_fields.values()):
                if identity in completed:
                    completed.remove(identity)
                if identity in pending:
                    pending.remove(identity)
                for field, destination in (("completed", completed), ("pending", pending), ("uncertain", uncertain)):
                    destination.extend(f"platform.verify.step.{step_index}.{value}" for value in child_fields[field])
                if (child_failures or result.status != VerificationStatus.VERIFIED) and not child_fields["pending"] and not child_fields["uncertain"]:
                    pending.append(identity)
            elif child_failures:
                if identity in completed:
                    completed.remove(identity)
                if identity not in pending:
                    pending.append(identity)
        if (pending or uncertain) and not failures:
            failures.append(OperationFailure.for_cause("platform.verify", "platform", "verification_failed"))
        outcome = OperationOutcome.SUCCESS if not failures and not pending and not uncertain else OperationOutcome.BLOCKED if legacy.status == PlatformWorkflowStatus.BLOCKED else OperationOutcome.FAILED
        return replace(legacy, operation_result=aggregate_operation(outcome, completed=completed, pending=pending, uncertain=uncertain, failures=failures))

    async def _run_verify_step_with_retry(
        self,
        step: AsyncWorkflowStep,
        caught_failures: list[OperationFailure],
    ) -> VerificationResult | None:
        last_result: VerificationResult | None = None
        for attempt in range(1, self.verify_retry_attempts + 1):
            try:
                step_result = await step.run()
            except OperationError as error:
                caught_failures.append(error.failure)
                return VerificationResult(
                    target_id=_verification_target_id(step), status=VerificationStatus.FAILED_TO_VERIFY,
                    message="Platform verification could not complete.",
                    evidence={"phase": "verify", **failures_to_evidence((error.failure,))},
                )
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

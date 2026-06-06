from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from tiny_swarm_world.application.ports.method_trace import (
    NullMethodTrace,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    NullWorkflowProgress,
    PortWorkflowProgress,
    WorkflowProgressEvent,
)
from tiny_swarm_world.application.ports.repositories.port_verification_evidence_repository import (
    PortVerificationEvidenceRepository,
)
from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    PLATFORM_WORKFLOW_TAXONOMY,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowSemantics,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.application.services.shared import MethodTraceWrapper
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.preflight import PreflightResult


class AsyncWorkflowStep(Protocol):
    async def run(self) -> object:
        # Protocol declaration; concrete workflow steps perform platform work.
        pass


class VerifiableWorkflowStep(AsyncWorkflowStep, Protocol):
    verification_target_id: str

    async def verify(self) -> VerificationResult:
        # Protocol declaration; concrete steps provide verification evidence.
        pass


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


class PlatformResetWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.RESET]

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


class PlatformDestroyWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.DESTROY]

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


class PlatformVerifyWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.VERIFY]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
        progress: PortWorkflowProgress | None = None,
        method_trace: PortMethodTrace | None = None,
        trace_correlation_id: str | None = None,
    ):
        self.steps = tuple(steps)
        self.progress = progress or NullWorkflowProgress()
        self.method_trace = method_trace or NullMethodTrace()
        self.trace_correlation_id = trace_correlation_id

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
            step_result = await step.run()
            verification_result = _verification_result_from_verify_output(step_result)
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
                    step="workflow stopped",
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
                    step="workflow stopped",
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


async def _trace_platform_run(workflow: object, run_method, *args: object) -> PlatformWorkflowResult:
    semantics = getattr(workflow, "semantics")
    return await MethodTraceWrapper(
        getattr(workflow, "method_trace"),
        component="platform",
        workflow=f"platform {semantics.kind.value}",
        correlation_id=getattr(workflow, "trace_correlation_id"),
    ).wrap_async(
        run_method,
        method_name="run",
        result_classifier=_platform_trace_result,
    )(*args)


def _platform_trace_result(result: PlatformWorkflowResult) -> str:
    return result.status.value


async def _run_steps(steps: Sequence[AsyncWorkflowStep]) -> tuple[object, ...]:
    results: list[object] = []
    for step in steps:
        results.append(await step.run())
    return tuple(results)


async def _run_pre_apply_guard(
    guard: AsyncWorkflowStep | None,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    progress: PortWorkflowProgress,
) -> tuple[VerificationResult | None, PlatformWorkflowResult | None]:
    if guard is None:
        return None, None

    target_id = f"platform:{semantics.kind.value}:preflight"
    _report_step_progress(
        progress,
        semantics,
        target_id=target_id,
        step="pre-apply guard",
        status="started",
        result="pending",
        safe_message="Platform pre-apply guard started.",
    )
    guard_output = await guard.run()

    verification_result = _pre_apply_guard_verification(guard_output)
    if verification_result is None:
        result = VerificationResult(
            target_id=f"platform:{semantics.kind.value}:preflight",
            status=VerificationStatus.BLOCKED,
            message="Pre-apply guard returned unsupported output.",
            evidence={"phase": "pre_apply", "reason": "unsupported_guard_output"},
        )
        _append_evidence(verification_evidence_repository, result)
        _report_verification_progress(
            progress,
            semantics,
            result,
            step="pre-apply guard",
        )
        _report_workflow_progress(
            progress,
            semantics,
            step="workflow stopped",
            status=PlatformWorkflowStatus.BLOCKED.value,
            result=PlatformWorkflowStatus.BLOCKED.value,
            safe_message="Platform workflow stopped after a blocked guard.",
        )
        return (
            None,
            PlatformWorkflowResult.blocked(
                semantics,
                f"{semantics.kind.value} workflow blocked by pre-apply guard.",
                (result,),
            ),
        )

    _append_evidence(verification_evidence_repository, verification_result)
    _report_verification_progress(
        progress,
        semantics,
        verification_result,
        step="pre-apply guard",
    )
    if verification_result.status == VerificationStatus.VERIFIED:
        return verification_result, None

    _report_workflow_progress(
        progress,
        semantics,
        step="workflow stopped",
        status=PlatformWorkflowStatus.BLOCKED.value,
        result=PlatformWorkflowStatus.BLOCKED.value,
        safe_message="Platform workflow stopped after a blocked guard.",
    )
    return (
        None,
        PlatformWorkflowResult.blocked(
            semantics,
            f"{semantics.kind.value} workflow blocked by live preflight before mutation.",
            (verification_result,),
        ),
    )


def _pre_apply_guard_verification(result: object) -> VerificationResult | None:
    if isinstance(result, VerificationResult):
        return result
    if not isinstance(result, PreflightResult):
        return None
    if result.passed:
        return VerificationResult(
            target_id="platform:init:preflight",
            status=VerificationStatus.VERIFIED,
            message="Live preflight checks passed before platform init.",
            evidence={
                "phase": "pre_apply",
                "check_count": str(len(result.checks)),
            },
        )
    return VerificationResult(
        target_id="platform:init:preflight",
        status=VerificationStatus.BLOCKED,
        message="Live preflight blocked platform init before mutation.",
        evidence={
            "phase": "pre_apply",
            "failed_check_count": str(len(result.failed_checks)),
            "runtime_failure_count": str(
                sum(
                    1
                    for check in result.failed_checks
                    if check.category.value == "RUNTIME"
                )
            ),
        },
    )


async def _run_mutating_steps(
    steps: Sequence[AsyncWorkflowStep],
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    progress: PortWorkflowProgress,
    initial_verification_results: Sequence[VerificationResult] = (),
) -> PlatformWorkflowResult:
    verification_results: list[VerificationResult] = list(initial_verification_results)
    for step in steps:
        blocking_result = _pre_apply_blocking_result(
            step,
            semantics,
            verification_evidence_repository,
            verification_results,
            progress,
        )
        if blocking_result is not None:
            return blocking_result

        if not _step_has_verification_contract(step):
            return _missing_verification_contract_result(
                step,
                semantics,
                verification_evidence_repository,
                verification_results,
                progress,
            )

        target_id = _verification_target_id(step)
        _report_step_progress(
            progress,
            semantics,
            target_id=target_id,
            step="apply",
            status="started",
            result="pending",
            safe_message="Platform mutating step started.",
        )
        try:
            apply_result = await step.run()
        except Exception as exc:
            return _failed_apply_result_from_exception(
                exc,
                target_id,
                semantics,
                verification_evidence_repository,
                verification_results,
                progress,
            )

        failed_apply_result = _failed_apply_result(apply_result)
        if failed_apply_result is not None:
            return _failed_apply_workflow_result(
                failed_apply_result,
                target_id,
                semantics,
                verification_evidence_repository,
                verification_results,
                progress,
            )

        _report_step_progress(
            progress,
            semantics,
            target_id=target_id,
            step="apply",
            status="completed",
            result="completed",
            safe_message="Platform mutating step completed.",
        )
        direct_verification = _direct_verification_result(apply_result)
        if direct_verification is not None:
            direct_result = _workflow_result_from_direct_verification(
                direct_verification,
                target_id,
                semantics,
                verification_evidence_repository,
                verification_results,
                progress,
            )
            if direct_result is None:
                continue
            return direct_result

        _report_step_progress(
            progress,
            semantics,
            target_id=target_id,
            step="verify",
            status="started",
            result="pending",
            safe_message="Platform verify step started.",
        )
        verification = await _verify_step(step, target_id)
        if verification is None:
            return _missing_verification_evidence_result(
                target_id,
                semantics,
                verification_evidence_repository,
                verification_results,
                progress,
            )

        verification_result = _workflow_result_from_verification(
            verification,
            target_id,
            semantics,
            verification_evidence_repository,
            verification_results,
            progress,
        )
        if verification_result is not None:
            return verification_result

    _report_workflow_progress(
        progress,
        semantics,
        step="workflow completed",
        status=PlatformWorkflowStatus.COMPLETED.value,
        result=PlatformWorkflowStatus.COMPLETED.value,
        safe_message="Platform workflow completed.",
    )
    return PlatformWorkflowResult.completed(
        semantics,
        executed=bool(steps),
        verification_results=tuple(verification_results),
    )


def _pre_apply_blocking_result(
    step: AsyncWorkflowStep,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
) -> PlatformWorkflowResult | None:
    pre_apply_verification = _pre_apply_verification(step)
    if pre_apply_verification is None:
        return None
    _record_evidence(
        verification_evidence_repository,
        verification_results,
        pre_apply_verification,
    )
    _report_verification_progress(
        progress,
        semantics,
        pre_apply_verification,
        step="pre-apply check",
    )
    if pre_apply_verification.status == VerificationStatus.VERIFIED:
        return None
    _report_workflow_progress(
        progress,
        semantics,
        step="workflow stopped",
        status=PlatformWorkflowStatus.BLOCKED.value,
        result=PlatformWorkflowStatus.BLOCKED.value,
        safe_message="Platform workflow stopped after a blocked pre-apply check.",
    )
    return PlatformWorkflowResult.blocked(
        semantics,
        f"{semantics.kind.value} step {pre_apply_verification.target_id} "
        "is blocked before apply: command-backed verification is not configured",
        tuple(verification_results),
    )


def _missing_verification_contract_result(
    step: AsyncWorkflowStep,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
) -> PlatformWorkflowResult:
    target_id = _verification_target_id(step)
    operator_reason = _operator_block_reason(step)
    result = VerificationResult(
        target_id=target_id,
        status=VerificationStatus.BLOCKED,
        message=f"Blocked before apply: {operator_reason}",
        evidence={"phase": "pre_apply", "reason": operator_reason},
    )
    _record_evidence(verification_evidence_repository, verification_results, result)
    _report_verification_progress(progress, semantics, result, step="pre-apply check")
    _report_workflow_progress(
        progress,
        semantics,
        step="workflow stopped",
        status=PlatformWorkflowStatus.BLOCKED.value,
        result=PlatformWorkflowStatus.BLOCKED.value,
        safe_message="Platform workflow stopped before apply.",
    )
    return PlatformWorkflowResult.blocked(
        semantics,
        f"{semantics.kind.value} step {target_id} is blocked before apply: "
        f"{operator_reason}",
        tuple(verification_results),
    )


def _failed_apply_result_from_exception(
    exc: Exception,
    target_id: str,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
) -> PlatformWorkflowResult:
    result = VerificationResult(
        target_id=target_id,
        status=VerificationStatus.FAILED_TO_APPLY,
        message=f"Apply failed for {target_id}: {exc.__class__.__name__}",
        evidence={"phase": "apply"},
    )
    return _failed_apply_workflow_result(
        result,
        target_id,
        semantics,
        verification_evidence_repository,
        verification_results,
        progress,
    )


def _failed_apply_workflow_result(
    result: VerificationResult,
    target_id: str,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
) -> PlatformWorkflowResult:
    _record_evidence(verification_evidence_repository, verification_results, result)
    _report_verification_progress(progress, semantics, result, step="apply result")
    _report_workflow_progress(
        progress,
        semantics,
        step="workflow stopped",
        status=PlatformWorkflowStatus.FAILED_TO_APPLY.value,
        result=PlatformWorkflowStatus.FAILED_TO_APPLY.value,
        safe_message="Platform workflow stopped after apply failure.",
    )
    return PlatformWorkflowResult.failed_to_apply(
        semantics,
        f"{semantics.kind.value} apply failed for {target_id}.",
        tuple(verification_results),
    )


def _workflow_result_from_direct_verification(
    verification: VerificationResult,
    target_id: str,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
) -> PlatformWorkflowResult | None:
    _record_evidence(verification_evidence_repository, verification_results, verification)
    _report_verification_progress(progress, semantics, verification, step="direct verification")
    if verification.status == VerificationStatus.VERIFIED:
        return None
    if verification.status == VerificationStatus.BLOCKED:
        _report_workflow_progress(
            progress,
            semantics,
            step="workflow stopped",
            status=PlatformWorkflowStatus.BLOCKED.value,
            result=PlatformWorkflowStatus.BLOCKED.value,
            safe_message="Platform workflow stopped after blocked direct verification.",
        )
        return PlatformWorkflowResult.blocked(
            semantics,
            f"{semantics.kind.value} step {target_id} is blocked.",
            tuple(verification_results),
            executed=_direct_verification_reports_apply(verification),
        )
    if verification.status == VerificationStatus.FAILED_TO_APPLY:
        _report_workflow_progress(
            progress,
            semantics,
            step="workflow stopped",
            status=PlatformWorkflowStatus.FAILED_TO_APPLY.value,
            result=PlatformWorkflowStatus.FAILED_TO_APPLY.value,
            safe_message="Platform workflow stopped after apply failure.",
        )
        return PlatformWorkflowResult.failed_to_apply(
            semantics,
            f"{semantics.kind.value} apply failed for {target_id}.",
            tuple(verification_results),
        )
    _report_workflow_progress(
        progress,
        semantics,
        step="workflow stopped",
        status=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
        result=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
        safe_message="Platform workflow stopped after failed direct verification.",
    )
    return PlatformWorkflowResult.failed_to_verify(
        semantics,
        f"{semantics.kind.value} verification failed for {target_id}.",
        tuple(verification_results),
    )


def _missing_verification_evidence_result(
    target_id: str,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
) -> PlatformWorkflowResult:
    result = VerificationResult(
        target_id=target_id,
        status=VerificationStatus.BLOCKED,
        message="Verification evidence is missing.",
        evidence={"phase": "verify"},
    )
    _record_evidence(verification_evidence_repository, verification_results, result)
    _report_verification_progress(progress, semantics, result, step="verify")
    _report_workflow_progress(
        progress,
        semantics,
        step="workflow stopped",
        status=PlatformWorkflowStatus.BLOCKED.value,
        result=PlatformWorkflowStatus.BLOCKED.value,
        safe_message="Platform workflow stopped after missing verification evidence.",
    )
    return PlatformWorkflowResult.blocked(
        semantics,
        f"{semantics.kind.value} verification evidence is missing for {target_id}.",
        tuple(verification_results),
        executed=True,
    )


def _workflow_result_from_verification(
    verification: VerificationResult,
    target_id: str,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
) -> PlatformWorkflowResult | None:
    _record_evidence(verification_evidence_repository, verification_results, verification)
    _report_verification_progress(progress, semantics, verification, step="verify")
    if verification.status == VerificationStatus.VERIFIED:
        return None
    if verification.status == VerificationStatus.BLOCKED:
        _report_workflow_progress(
            progress,
            semantics,
            step="workflow stopped",
            status=PlatformWorkflowStatus.BLOCKED.value,
            result=PlatformWorkflowStatus.BLOCKED.value,
            safe_message="Platform workflow stopped after blocked verification.",
        )
        return PlatformWorkflowResult.blocked(
            semantics,
            f"{semantics.kind.value} verification is blocked for {target_id}.",
            tuple(verification_results),
            executed=True,
        )
    _report_workflow_progress(
        progress,
        semantics,
        step="workflow stopped",
        status=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
        result=PlatformWorkflowStatus.FAILED_TO_VERIFY.value,
        safe_message="Platform workflow stopped after failed verification.",
    )
    return PlatformWorkflowResult.failed_to_verify(
        semantics,
        f"{semantics.kind.value} verification failed for {target_id}.",
        tuple(verification_results),
    )


def _record_evidence(
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    result: VerificationResult,
) -> None:
    _append_evidence(verification_evidence_repository, result)
    verification_results.append(result)


def _step_has_verification(step: AsyncWorkflowStep) -> bool:
    return callable(getattr(step, "verify", None))


def _step_has_verification_contract(step: AsyncWorkflowStep) -> bool:
    return _step_has_verification(step) or bool(
        getattr(step, "returns_verification_result", False)
    )


def _pre_apply_verification(step: AsyncWorkflowStep) -> VerificationResult | None:
    verify_pre_apply = getattr(step, "verify_pre_apply", None)
    if not callable(verify_pre_apply):
        return None
    result = verify_pre_apply()
    if isinstance(result, VerificationResult):
        return result
    return None


def _verification_target_id(step: AsyncWorkflowStep) -> str:
    target_id = getattr(step, "verification_target_id", "")
    if target_id:
        return str(target_id)
    return step.__class__.__name__


def _report_step_progress(
    progress: PortWorkflowProgress,
    semantics: PlatformWorkflowSemantics,
    *,
    target_id: str,
    step: str,
    status: str,
    result: str,
    safe_message: str,
) -> None:
    _report_progress(
        progress,
        semantics,
        phase=_phase_for_step(step),
        target=target_id,
        task="Run platform step",
        step=step,
        status=status,
        result=result,
        safe_message=safe_message,
    )


def _report_verification_progress(
    progress: PortWorkflowProgress,
    semantics: PlatformWorkflowSemantics,
    verification: VerificationResult,
    *,
    step: str,
) -> None:
    _report_progress(
        progress,
        semantics,
        phase=str(verification.evidence.get("phase", _phase_for_step(step))),
        target=verification.target_id,
        task="Record platform verification",
        step=step,
        status=verification.status.value,
        result=verification.status.value,
        safe_message=_safe_verification_progress_message(verification),
    )


def _report_workflow_progress(
    progress: PortWorkflowProgress,
    semantics: PlatformWorkflowSemantics,
    *,
    step: str,
    status: str,
    result: str,
    safe_message: str,
) -> None:
    _report_progress(
        progress,
        semantics,
        phase="platform",
        target=f"platform:{semantics.kind.value}",
        task="Run platform workflow",
        step=step,
        status=status,
        result=result,
        safe_message=safe_message,
    )


def _report_progress(
    progress: PortWorkflowProgress,
    semantics: PlatformWorkflowSemantics,
    *,
    phase: str,
    target: str,
    task: str,
    step: str,
    status: str,
    result: str,
    safe_message: str,
) -> None:
    progress.report(
        WorkflowProgressEvent(
            workflow=f"platform {semantics.kind.value}",
            phase=phase,
            target=target,
            task=task,
            step=step,
            status=status,
            result=result,
            safe_message=safe_message,
        )
    )


def _phase_for_step(step: str) -> str:
    if "pre-apply" in step:
        return "pre_apply"
    if "apply" in step:
        return "apply"
    return "verify"


def _safe_verification_progress_message(verification: VerificationResult) -> str:
    count_parts = [
        f"{key}={verification.evidence[key]}"
        for key in (
            "result_count",
            "verified_count",
            "blocked_count",
            "failed_apply_count",
            "failed_verify_count",
            "expected_count",
            "observed_count",
            "missing_count",
        )
        if key in verification.evidence
    ]
    if count_parts:
        return "Platform verification reached terminal state with " + ", ".join(count_parts) + "."
    return "Platform verification reached terminal state."


def _operator_block_reason(step: AsyncWorkflowStep) -> str:
    reason = getattr(step, "operator_block_reason", "")
    if reason:
        return str(reason)
    return "command-backed verification is not configured"


def _verification_result_from_verify_output(result: object) -> VerificationResult | None:
    if isinstance(result, VerificationResult):
        return result
    if isinstance(result, PreflightResult):
        return _verification_result_from_preflight(result)
    return None


def _verification_result_from_preflight(result: PreflightResult) -> VerificationResult:
    if result.passed:
        return VerificationResult(
            target_id="platform:preflight",
            status=VerificationStatus.VERIFIED,
            message="Preflight checks passed.",
            evidence={"phase": "verify", "check_count": str(len(result.checks))},
        )
    return VerificationResult(
        target_id="platform:preflight",
        status=VerificationStatus.FAILED_TO_VERIFY,
        message="Preflight checks failed.",
        evidence={"phase": "verify", "failed_check_count": str(len(result.failed_checks))},
    )


def _direct_verification_result(result: object) -> VerificationResult | None:
    if isinstance(result, VerificationResult):
        return result
    return None


def _direct_verification_reports_apply(verification: VerificationResult) -> bool:
    return verification.evidence.get("applied") == "true"


def _failed_apply_result(result: object) -> VerificationResult | None:
    if (
        isinstance(result, VerificationResult)
        and result.status == VerificationStatus.FAILED_TO_APPLY
    ):
        return result
    return None


async def _verify_step(
    step: AsyncWorkflowStep,
    target_id: str,
) -> VerificationResult | None:
    verify = getattr(step, "verify", None)
    if not callable(verify):
        return None
    try:
        result = await verify()
    except Exception as exc:
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message=f"Verification failed for {target_id}: {exc.__class__.__name__}",
            evidence={"phase": "verify"},
        )
    if isinstance(result, VerificationResult):
        return result
    return None


def _append_evidence(
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    result: VerificationResult,
) -> None:
    if verification_evidence_repository is not None:
        verification_evidence_repository.append(result)


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

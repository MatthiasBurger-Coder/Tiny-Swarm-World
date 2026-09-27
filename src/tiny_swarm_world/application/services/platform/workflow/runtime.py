from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome
from tiny_swarm_world.application.services.shared.operation_results import (
    aggregate_operation, failure_from_exception, failures_from_evidence, failures_to_evidence, progress_from_evidence,
)

from tiny_swarm_world.application.ports.progress import (
    PortWorkflowProgress,
    WorkflowProgressEvent,
)
from tiny_swarm_world.application.ports.repositories.port_verification_evidence_repository import (
    PortVerificationEvidenceRepository,
)
from tiny_swarm_world.application.services.platform.workflow.results import (
    PlatformWorkflowResult,
)
from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PlatformWorkflowSemantics,
)
from tiny_swarm_world.application.services.platform.workflow.steps import AsyncWorkflowStep
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowStatus,
)
from tiny_swarm_world.application.services.shared import MethodTraceWrapper
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.preflight import PreflightResult


# Exact serialized origins accepted from platform producers; arbitrary IDs stay untrusted.
PLATFORM_FAILURE_ORIGINS = frozenset({
    ("command.execute", "command_runner"),
    ("container.execute", "lxc_container_runtime"),
    ("swarm.execute", "lxc_gateway"),
    ("host.inspect", "host_preflight"),
    ("configuration.load", "configuration_source"),
    ("configuration.load", "repository"),
    ("evidence.write", "filesystem_evidence"),
    ("evidence.write", "evidence_repository"),
    ("exposure.observe", "socat"), ("exposure.start", "socat"),
    ("platform.apply", "platform"), ("platform.verify", "platform"),
    ("platform.docker.inspect", "platform"), ("platform.docker.install", "platform"),
    ("platform.docker.verify", "platform"),
    ("platform.preflight.evidence", "platform"), ("platform.preflight.configuration", "platform"),
    ("platform.preflight.artifacts", "platform"), ("platform.preflight.secrets", "platform"),
})


PLATFORM_PREFLIGHT_TARGET_ID = "platform:preflight"
PRE_APPLY_GUARD_STEP = "pre-apply guard"
WORKFLOW_STOPPED_STEP = "workflow stopped"


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
        step=PRE_APPLY_GUARD_STEP,
        status="started",
        result="pending",
        safe_message="Platform pre-apply guard started.",
    )
    try:
        guard_output = await guard.run()
    except OperationError as error:
        failure = error.failure
        return None, replace(PlatformWorkflowResult.blocked(
            semantics, "Platform pre-apply guard could not complete.",
        ), operation_result=aggregate_operation(
            OperationOutcome.BLOCKED, pending=(f"platform.{semantics.kind.value}.guard",), failures=(failure,),
        ))

    verification_result = _pre_apply_guard_verification(guard_output)
    if verification_result is None:
        result = VerificationResult(
            target_id=_preflight_target_id(semantics),
            status=VerificationStatus.BLOCKED,
            message="Pre-apply guard returned unsupported output.",
            evidence={"phase": "pre_apply", "reason": "unsupported_guard_output"},
        )
        failures = _verification_failures(result, f"platform.{semantics.kind.value}.guard")
        try:
            _append_evidence(verification_evidence_repository, result)
        except OperationError as error:
            failures = (*failures, error.failure)
        _report_verification_progress(
            progress,
            semantics,
            result,
            step=PRE_APPLY_GUARD_STEP,
        )
        _report_workflow_progress(
            progress,
            semantics,
            step=WORKFLOW_STOPPED_STEP,
            status=PlatformWorkflowStatus.BLOCKED.value,
            result=PlatformWorkflowStatus.BLOCKED.value,
            safe_message="Platform workflow stopped after a blocked guard.",
        )
        return (
            None,
            replace(PlatformWorkflowResult.blocked(
                semantics,
                f"{semantics.kind.value} workflow blocked by pre-apply guard.",
                (result,),
            ), operation_result=aggregate_operation(
                OperationOutcome.BLOCKED, pending=(f"platform.{semantics.kind.value}.guard",), failures=failures,
            )),
        )

    verification_result = replace(verification_result, evidence={**verification_result.evidence, "phase": "pre_apply"})
    if verification_result.status == VerificationStatus.VERIFIED and _safe_failure_evidence(verification_result.evidence, "platform.guard"):
        verification_result = replace(verification_result, status=VerificationStatus.BLOCKED, message="Guard evidence contains a failure or invalid metadata.")
    try:
        _append_evidence(verification_evidence_repository, verification_result)
    except OperationError as error:
        return None, replace(PlatformWorkflowResult.blocked(
            semantics, "Platform guard evidence could not be stored.", (verification_result,),
        ), operation_result=aggregate_operation(
            OperationOutcome.BLOCKED, pending=(f"platform.{semantics.kind.value}.guard",), failures=(*_verification_failures(verification_result, f"platform.{semantics.kind.value}.guard"), error.failure),
        ))
    _report_verification_progress(
        progress,
        semantics,
        verification_result,
        step=PRE_APPLY_GUARD_STEP,
    )
    if verification_result.status == VerificationStatus.VERIFIED:
        return verification_result, None

    _report_workflow_progress(
        progress,
        semantics,
        step=WORKFLOW_STOPPED_STEP,
        status=PlatformWorkflowStatus.BLOCKED.value,
        result=PlatformWorkflowStatus.BLOCKED.value,
        safe_message="Platform workflow stopped after a blocked guard.",
    )
    return (
        None,
        replace(PlatformWorkflowResult.blocked(
            semantics,
            f"{semantics.kind.value} workflow blocked by live preflight before mutation.",
            (verification_result,),
        ), operation_result=aggregate_operation(
            OperationOutcome.BLOCKED, pending=(f"platform.{semantics.kind.value}.guard",),
            failures=_verification_failures(verification_result, f"platform.{semantics.kind.value}.guard"),
        )),
    )


def _pre_apply_guard_verification(result: object) -> VerificationResult | None:
    if isinstance(result, VerificationResult):
        return result
    if not isinstance(result, PreflightResult):
        return None
    check_failures = tuple(failure for check in result.checks for failure in _safe_failure_evidence(check.evidence, "platform.preflight"))
    if result.passed and not check_failures:
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
            **failures_to_evidence(check_failures),
            "failed_check_count": str(len(result.failed_checks)),
            "runtime_failure_count": str(
                sum(
                    1
                    for check in result.failed_checks
                    if check.category.value == "RUNTIME"
                )
            ),
            "windows_exposure_failure_count": str(
                sum(
                    1
                    for check in result.failed_checks
                    if check.category.value == "WINDOWS_EXPOSURE"
                )
            ),
        },
    )


def _preflight_target_id(semantics: PlatformWorkflowSemantics) -> str:
    return f"platform:{semantics.kind.value}:preflight"


@dataclass
class _StepProgress:
    apply_started: bool = False
    failure_origins: frozenset[tuple[str, str]] = frozenset()


async def _run_mutating_steps(
    steps: Sequence[AsyncWorkflowStep],
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    progress: PortWorkflowProgress,
    initial_verification_results: Sequence[VerificationResult] = (),
) -> PlatformWorkflowResult:
    verification_results: list[VerificationResult] = list(initial_verification_results)
    completed: list[str] = []
    for index, step in enumerate(steps, 1):
        identity = f"platform.{semantics.kind.value}.step.{index}"
        start = len(verification_results)
        storage_failure: OperationFailure | None = None
        step_progress = _StepProgress()
        try:
            step_result = await _run_mutating_step(
                step, semantics, verification_evidence_repository, verification_results, progress, step_progress,
            )
        except _EvidenceWriteError as error:
            # Evidence is retained in memory before persistence; do not write recursively.
            storage_failure = error.failure
            step_result = PlatformWorkflowResult.failed_to_verify(
                semantics, "Platform operation evidence could not be completed.", tuple(verification_results),
            )
        except OperationError as error:
            step_progress.failure_origins = frozenset({(error.failure.operation, error.failure.component)})
            record = VerificationResult(
                target_id=_verification_target_id(step), status=VerificationStatus.BLOCKED,
                message="A required pre-apply check could not complete.",
                evidence={"phase": "pre_apply", **failures_to_evidence((error.failure,))},
            )
            verification_results.append(record)
            step_result = PlatformWorkflowResult.blocked(semantics, record.message, tuple(verification_results))
        records = verification_results[start:]
        nested_allowed = frozenset(getattr(step, "operation_work_ids", ()))
        nested_completed: list[str] = []
        nested_pending: list[str] = []
        uncertain: list[str] = []
        failures: list[OperationFailure] = []
        metadata_invalid = False
        try:
            for record in records:
                failures.extend(_verification_failures(record, identity, step_progress.failure_origins))
                if nested_allowed and record.evidence.get("phase") != "pre_apply":
                    for field, destination in (("completed", nested_completed), ("pending", nested_pending), ("uncertain", uncertain)):
                        destination.extend(f"{identity}.{value}" for value in progress_from_evidence(
                            record.evidence, field, allowed_operations=nested_allowed,
                        ))
            # Validate cross-field and cross-record identities before using any child effects.
            aggregate_operation(OperationOutcome.SUCCESS, completed=(*nested_completed, *nested_pending, *uncertain))
        except ValueError:
            metadata_invalid = True
            nested_completed, nested_pending, uncertain = [], [], []
            failures = [OperationFailure.for_cause(identity, "platform", "unexpected_failure")]
        if step_result is None and not failures and not nested_pending and not uncertain and not metadata_invalid:
            completed.extend(nested_completed or (f"{identity}.verify",))
            continue
        if step_result is None:
            step_result = PlatformWorkflowResult.failed_to_verify(
                semantics, "Platform operation evidence is incomplete or inconsistent.", tuple(verification_results),
            )
        completed.extend(nested_completed)
        if not nested_allowed and not metadata_invalid:
            if any(record.status == VerificationStatus.VERIFIED and not _verification_failures(record, identity, step_progress.failure_origins) and record.evidence.get("workflow_invocation") == "verify" for record in records):
                completed.append(f"{identity}.verify")
            elif any(record.evidence.get("applied") == "true" and record.evidence.get("phase") != "pre_apply" for record in records):
                completed.append(f"{identity}.apply")
        pending = [f"platform.{semantics.kind.value}.step.{remaining}.verify" for remaining in range(index + 1, len(steps) + 1)]
        pending.extend(nested_pending)
        if storage_failure is not None:
            failures.append(storage_failure)
            pending.append(f"{identity}.evidence")
        if not nested_pending and not uncertain and f"{identity}.verify" not in completed:
            pending.append(f"{identity}.verify")
            if step_progress.apply_started and f"{identity}.apply" not in completed and not nested_completed:
                uncertain.append(f"{identity}.apply")
        if not failures:
            cause = "blocked" if step_result.status == PlatformWorkflowStatus.BLOCKED else "verification_failed"
            failures.append(OperationFailure.for_cause(identity, "platform", cause))
        return replace(step_result, verification_results=tuple(verification_results), operation_result=aggregate_operation(
            OperationOutcome.BLOCKED if step_result.status == PlatformWorkflowStatus.BLOCKED else OperationOutcome.FAILED,
            completed=completed, pending=pending, uncertain=uncertain, failures=failures,
        ))
    _report_workflow_progress(
        progress, semantics, step="workflow completed", status=PlatformWorkflowStatus.COMPLETED.value,
        result=PlatformWorkflowStatus.COMPLETED.value, safe_message="Platform workflow completed.",
    )
    return PlatformWorkflowResult.completed(
        semantics, executed=bool(steps), verification_results=tuple(verification_results),
        operation_result=aggregate_operation(OperationOutcome.SUCCESS, completed=completed),
    )


def _safe_failure_evidence(evidence: Mapping[str, str], identity: str, trusted_origins: frozenset[tuple[str, str]] = frozenset()) -> tuple[OperationFailure, ...]:
    try:
        return failures_from_evidence(evidence, allowed_origins=PLATFORM_FAILURE_ORIGINS | trusted_origins, fallback_operation=identity, fallback_component="platform")
    except ValueError:
        return (OperationFailure.for_cause(identity, "platform", "unexpected_failure"),)


def _verification_failures(record: VerificationResult, identity: str, trusted_origins: frozenset[tuple[str, str]] = frozenset()) -> tuple[OperationFailure, ...]:
    failures = _safe_failure_evidence(record.evidence, identity, trusted_origins)
    if failures or record.status == VerificationStatus.VERIFIED:
        return failures
    cause = "blocked" if record.status == VerificationStatus.BLOCKED else "verification_failed"
    return (OperationFailure.for_cause(identity, "platform", cause),)


async def _run_mutating_step(
    step: AsyncWorkflowStep,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
    step_progress: _StepProgress,
) -> PlatformWorkflowResult | None:
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
    apply_result = await _apply_mutating_step(
        step,
        target_id,
        semantics,
        verification_evidence_repository,
        verification_results,
        progress,
        step_progress,
    )
    if isinstance(apply_result, PlatformWorkflowResult):
        return apply_result

    direct_verification = _direct_verification_result(apply_result)
    if direct_verification is not None:
        return _workflow_result_from_direct_verification(
            direct_verification,
            target_id,
            semantics,
            verification_evidence_repository,
            verification_results,
            progress,
        )

    return await _verification_workflow_result(
        step,
        target_id,
        semantics,
        verification_evidence_repository,
        verification_results,
        progress,
        step_progress,
    )


async def _apply_mutating_step(
    step: AsyncWorkflowStep,
    target_id: str,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
    step_progress: _StepProgress,
) -> object:
    _report_step_progress(
        progress,
        semantics,
        target_id=target_id,
        step="apply",
        status="started",
        result="pending",
        safe_message="Platform mutating step started.",
    )
    step_progress.apply_started = True
    try:
        apply_result = await step.run()
    except Exception as exc:
        if isinstance(exc, OperationError):
            step_progress.failure_origins = frozenset({(exc.failure.operation, exc.failure.component)})
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
    return apply_result


async def _verification_workflow_result(
    step: AsyncWorkflowStep,
    target_id: str,
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    verification_results: list[VerificationResult],
    progress: PortWorkflowProgress,
    step_progress: _StepProgress,
) -> PlatformWorkflowResult | None:
    _report_step_progress(
        progress,
        semantics,
        target_id=target_id,
        step="verify",
        status="started",
        result="pending",
        safe_message="Platform verify step started.",
    )
    verification = await _verify_step(step, target_id, step_progress)
    if verification is None:
        return _missing_verification_evidence_result(
            target_id,
            semantics,
            verification_evidence_repository,
            verification_results,
            progress,
        )
    return _workflow_result_from_verification(
        verification,
        target_id,
        semantics,
        verification_evidence_repository,
        verification_results,
        progress,
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
    pre_apply_verification = replace(pre_apply_verification, evidence={**pre_apply_verification.evidence, "phase": "pre_apply"})
    if pre_apply_verification.status == VerificationStatus.VERIFIED and _safe_failure_evidence(pre_apply_verification.evidence, "platform.guard"):
        pre_apply_verification = replace(pre_apply_verification, status=VerificationStatus.BLOCKED, message="Pre-apply evidence contains a failure or invalid metadata.")
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
        step=WORKFLOW_STOPPED_STEP,
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
        step=WORKFLOW_STOPPED_STEP,
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
        evidence={"phase": "apply", **failures_to_evidence((failure_from_exception(exc, "platform.apply", "platform"),))},
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
        step=WORKFLOW_STOPPED_STEP,
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
    verification = replace(verification, evidence={**verification.evidence, "workflow_invocation": "verify"})
    _record_evidence(verification_evidence_repository, verification_results, verification)
    _report_verification_progress(progress, semantics, verification, step="direct verification")
    if verification.status == VerificationStatus.VERIFIED:
        return None
    if verification.status == VerificationStatus.BLOCKED:
        _report_workflow_progress(
            progress,
            semantics,
            step=WORKFLOW_STOPPED_STEP,
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
            step=WORKFLOW_STOPPED_STEP,
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
        step=WORKFLOW_STOPPED_STEP,
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
        step=WORKFLOW_STOPPED_STEP,
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
    verification = replace(verification, evidence={**verification.evidence, "workflow_invocation": "verify"})
    _record_evidence(verification_evidence_repository, verification_results, verification)
    _report_verification_progress(progress, semantics, verification, step="verify")
    if verification.status == VerificationStatus.VERIFIED:
        return None
    if verification.status == VerificationStatus.BLOCKED:
        _report_workflow_progress(
            progress,
            semantics,
            step=WORKFLOW_STOPPED_STEP,
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
        step=WORKFLOW_STOPPED_STEP,
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
    verification_results.append(result)
    _append_evidence(verification_evidence_repository, result)


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
    check_failures = tuple(failure for check in result.checks for failure in _safe_failure_evidence(check.evidence, "platform.preflight"))
    if result.passed and not check_failures:
        return VerificationResult(
            target_id=PLATFORM_PREFLIGHT_TARGET_ID,
            status=VerificationStatus.VERIFIED,
            message="Preflight checks passed.",
            evidence={"phase": "verify", "check_count": str(len(result.checks))},
        )
    return VerificationResult(
        target_id=PLATFORM_PREFLIGHT_TARGET_ID,
        status=VerificationStatus.FAILED_TO_VERIFY,
        message="Preflight checks failed.",
        evidence={"phase": "verify", "failed_check_count": str(len(result.failed_checks)), **failures_to_evidence(check_failures)},
    )


def _retryable_platform_verify_result(result: VerificationResult) -> bool:
    return (
        result.target_id == PLATFORM_PREFLIGHT_TARGET_ID
        and result.status == VerificationStatus.FAILED_TO_VERIFY
    )


def _verification_with_retry_attempt(
    result: VerificationResult,
    attempt: int,
) -> VerificationResult:
    if attempt <= 1:
        return result
    return VerificationResult(
        target_id=result.target_id,
        status=result.status,
        message=result.message,
        evidence={**result.evidence, "verify_attempt": str(attempt)},
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
    step_progress: _StepProgress,
) -> VerificationResult | None:
    verify = getattr(step, "verify", None)
    if not callable(verify):
        return None
    try:
        result = await verify()
    except Exception as exc:
        if isinstance(exc, OperationError):
            step_progress.failure_origins = frozenset({(exc.failure.operation, exc.failure.component)})
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message=f"Verification failed for {target_id}: {exc.__class__.__name__}",
            evidence={"phase": "verify", **failures_to_evidence((failure_from_exception(exc, "platform.verify", "platform"),))},
        )
    if isinstance(result, VerificationResult):
        return result
    return None


class _EvidenceWriteError(OperationError):
    """Internal marker for a declared persistence failure after an observed fact."""


def _append_evidence(
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
    result: VerificationResult,
) -> None:
    if verification_evidence_repository is not None:
        try:
            verification_evidence_repository.append(result)
        except OperationError as error:
            raise _EvidenceWriteError(error.failure) from None


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

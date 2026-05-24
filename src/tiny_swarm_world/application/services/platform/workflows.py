from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from tiny_swarm_world.application.ports.repositories.port_verification_evidence_repository import (
    PortVerificationEvidenceRepository,
)
from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    PLATFORM_WORKFLOW_TAXONOMY,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowSemantics,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.preflight import PreflightResult


class AsyncWorkflowStep(Protocol):
    async def run(self) -> object:
        pass


class VerifiableWorkflowStep(AsyncWorkflowStep, Protocol):
    verification_target_id: str

    async def verify(self) -> VerificationResult:
        pass


class PlatformInitWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.INIT]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
        verification_evidence_repository: PortVerificationEvidenceRepository | None = None,
    ):
        self.steps = tuple(steps)
        self.verification_evidence_repository = verification_evidence_repository

    async def run(self) -> PlatformWorkflowResult:
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
        )


class PlatformReconcileWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.RECONCILE]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep],
        verification_evidence_repository: PortVerificationEvidenceRepository | None = None,
    ):
        self.steps = tuple(steps)
        self.verification_evidence_repository = verification_evidence_repository

    async def run(self) -> PlatformWorkflowResult:
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
        )


class PlatformResetWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.RESET]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep] = (),
        verification_evidence_repository: PortVerificationEvidenceRepository | None = None,
    ):
        self.steps = tuple(steps)
        self.verification_evidence_repository = verification_evidence_repository

    async def run(self, confirmation: str | None = None) -> PlatformWorkflowResult:
        if not _confirmation_matches(self.semantics, confirmation):
            return _refused_for_confirmation(self.semantics)
        if not self.steps:
            return _blocked_until_retention_policy_exists(self.semantics)
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
        )


class PlatformDestroyWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.DESTROY]

    def __init__(
        self,
        steps: Sequence[AsyncWorkflowStep] = (),
        verification_evidence_repository: PortVerificationEvidenceRepository | None = None,
    ):
        self.steps = tuple(steps)
        self.verification_evidence_repository = verification_evidence_repository

    async def run(self, confirmation: str | None = None) -> PlatformWorkflowResult:
        if not _confirmation_matches(self.semantics, confirmation):
            return _refused_for_confirmation(self.semantics)
        if not self.steps:
            return _blocked_until_retention_policy_exists(self.semantics)
        return await _run_mutating_steps(
            self.steps,
            self.semantics,
            self.verification_evidence_repository,
        )


class PlatformVerifyWorkflow:
    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.VERIFY]

    def __init__(self, steps: Sequence[AsyncWorkflowStep]):
        self.steps = tuple(steps)

    async def run(self) -> PlatformWorkflowResult:
        verification_results: list[VerificationResult] = []
        step_results = await _run_steps(self.steps)
        for step_result in step_results:
            verification_result = _verification_result_from_verify_output(step_result)
            if verification_result is None:
                continue
            verification_results.append(verification_result)
            if verification_result.status == VerificationStatus.BLOCKED:
                return PlatformWorkflowResult.blocked(
                    self.semantics,
                    f"{self.semantics.kind.value} verification is blocked.",
                    tuple(verification_results),
                )
            if verification_result.status != VerificationStatus.VERIFIED:
                return PlatformWorkflowResult.failed_to_verify(
                    self.semantics,
                    f"{self.semantics.kind.value} verification failed.",
                    tuple(verification_results),
                )
        return PlatformWorkflowResult.completed(
            self.semantics,
            executed=bool(self.steps),
            verification_results=tuple(verification_results),
        )


async def _run_steps(steps: Sequence[AsyncWorkflowStep]) -> tuple[object, ...]:
    results: list[object] = []
    for step in steps:
        results.append(await step.run())
    return tuple(results)


async def _run_mutating_steps(
    steps: Sequence[AsyncWorkflowStep],
    semantics: PlatformWorkflowSemantics,
    verification_evidence_repository: PortVerificationEvidenceRepository | None,
) -> PlatformWorkflowResult:
    verification_results: list[VerificationResult] = []
    for step in steps:
        if not _step_has_verification(step):
            target_id = _verification_target_id(step)
            operator_reason = _operator_block_reason(step)
            result = VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message=f"Blocked before apply: {operator_reason}",
                evidence={"phase": "pre_apply", "reason": operator_reason},
            )
            _append_evidence(verification_evidence_repository, result)
            verification_results.append(result)
            return PlatformWorkflowResult.blocked(
                semantics,
                f"{semantics.kind.value} step {target_id} is blocked before apply: "
                f"{operator_reason}",
                tuple(verification_results),
            )

        target_id = _verification_target_id(step)
        try:
            apply_result = await step.run()
        except Exception as exc:
            result = VerificationResult(
                target_id=target_id,
                status=VerificationStatus.FAILED_TO_APPLY,
                message=f"Apply failed for {target_id}: {exc.__class__.__name__}",
                evidence={"phase": "apply"},
            )
            _append_evidence(verification_evidence_repository, result)
            verification_results.append(result)
            return PlatformWorkflowResult.failed_to_apply(
                semantics,
                f"{semantics.kind.value} apply failed for {target_id}.",
                tuple(verification_results),
            )

        failed_apply_result = _failed_apply_result(apply_result)
        if failed_apply_result is not None:
            result = failed_apply_result
            _append_evidence(verification_evidence_repository, result)
            verification_results.append(result)
            return PlatformWorkflowResult.failed_to_apply(
                semantics,
                f"{semantics.kind.value} apply failed for {target_id}.",
                tuple(verification_results),
            )

        verification = await _verify_step(step, target_id)
        if verification is None:
            result = VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Verification evidence is missing.",
                evidence={"phase": "verify"},
            )
            _append_evidence(verification_evidence_repository, result)
            verification_results.append(result)
            return PlatformWorkflowResult.blocked(
                semantics,
                f"{semantics.kind.value} verification evidence is missing for {target_id}.",
                tuple(verification_results),
            )

        _append_evidence(verification_evidence_repository, verification)
        verification_results.append(verification)
        if verification.status == VerificationStatus.BLOCKED:
            return PlatformWorkflowResult.blocked(
                semantics,
                f"{semantics.kind.value} verification is blocked for {target_id}.",
                tuple(verification_results),
            )
        if verification.status != VerificationStatus.VERIFIED:
            return PlatformWorkflowResult.failed_to_verify(
                semantics,
                f"{semantics.kind.value} verification failed for {target_id}.",
                tuple(verification_results),
            )

    return PlatformWorkflowResult.completed(
        semantics,
        executed=bool(steps),
        verification_results=tuple(verification_results),
    )


def _step_has_verification(step: AsyncWorkflowStep) -> bool:
    return callable(getattr(step, "verify", None))


def _verification_target_id(step: AsyncWorkflowStep) -> str:
    target_id = getattr(step, "verification_target_id", "")
    if target_id:
        return str(target_id)
    return step.__class__.__name__


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

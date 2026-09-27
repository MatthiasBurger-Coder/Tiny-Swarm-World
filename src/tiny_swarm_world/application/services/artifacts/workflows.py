from __future__ import annotations

import inspect
import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import Enum
from typing import Protocol

from tiny_swarm_world.application.ports.operation_result import OperationFailure, OperationOutcome, OperationResult
from tiny_swarm_world.application.services.shared.operation_results import aggregate_operation, failure_from_exception, verification_failures
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class ArtifactWorkflowKind(str, Enum):
    PREPARE = "prepare"
    VERIFY = "verify"


class ArtifactWorkflowStatus(str, Enum):
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED_TO_PREPARE = "failed_to_prepare"
    FAILED_TO_VERIFY = "failed_to_verify"


class ArtifactPrepareStep(Protocol):
    def run(self) -> object:
        # Protocol declaration; concrete steps prepare artifact resources.
        pass

    def verify(self) -> object:
        # Protocol declaration; concrete steps report preparation evidence.
        pass


class ArtifactVerifyCheck(Protocol):
    def verify(self) -> object:
        # Protocol declaration; concrete checks inspect artifact resources.
        pass


@dataclass(frozen=True)
class ArtifactWorkflowResult:
    kind: ArtifactWorkflowKind
    status: ArtifactWorkflowStatus
    message: str
    reason: str
    executed: bool = False
    verification_results: tuple[VerificationResult, ...] = ()
    operation_result: OperationResult | None = None

    @property
    def workflow_name(self) -> str:
        return f"artifacts {self.kind.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "operation_result": self.operation_result.to_dict() if self.operation_result else None,
            "executed": self.executed,
            "message": self.message,
            "reason": self.reason,
            "status": self.status.value,
            "verification_results": [
                verification.to_dict() for verification in self.verification_results
            ],
            "workflow": self.workflow_name,
        }


DEFAULT_ARTIFACT_PREPARE_BLOCK_REASON = (
    "Nexus repository setup, registry configuration, and image publication "
    "require verified artifact contracts before prepare can run"
)
DEFAULT_ARTIFACT_VERIFY_BLOCK_REASON = (
    "Nexus repository and registry observed-state verification is not "
    "implemented through artifact ports"
)
ARTIFACT_PREPARE_CONTRACTS_BLOCKED_MESSAGE = (
    "artifacts prepare is blocked until artifact preparation contracts are wired."
)
VERIFICATION_EVIDENCE_MISSING_MESSAGE = "Verification evidence is missing."


class ArtifactPrepareWorkflow:
    def __init__(
        self,
        steps: Sequence[ArtifactPrepareStep] = (),
        blocked_reason: str = DEFAULT_ARTIFACT_PREPARE_BLOCK_REASON,
        bootstrap_steps: Sequence[ArtifactPrepareStep] = (),
    ):
        self.steps = tuple(steps)
        self.bootstrap_steps = tuple(bootstrap_steps)
        if self.steps[: len(self.bootstrap_steps)] != self.bootstrap_steps:
            raise ValueError("artifact bootstrap steps must be the prepare prefix")
        self.mutation_steps = self.steps[len(self.bootstrap_steps) :]
        self.blocked_reason = blocked_reason
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> ArtifactWorkflowResult:
        return await self._run_steps(self.steps)

    async def run_bootstrap(self) -> ArtifactWorkflowResult:
        """Run only the required Nexus/registry bootstrap steps.

        The complete ``artifacts prepare`` CLI workflow still runs every step.
        Setup orchestration uses this explicit sub-phase so live readiness can
        be checked before image build, pull or publication starts.
        """

        return await self._run_steps(self.bootstrap_steps)

    async def run_after_bootstrap(
        self,
        bootstrap_result: ArtifactWorkflowResult | None,
    ) -> ArtifactWorkflowResult:
        """Run image mutation steps only after a successful bootstrap result."""

        if (
            bootstrap_result is None
            or bootstrap_result.status is not ArtifactWorkflowStatus.COMPLETED
            or (bootstrap_result.operation_result is not None and bootstrap_result.operation_result.outcome != OperationOutcome.SUCCESS)
        ):
            return ArtifactWorkflowResult(
                kind=ArtifactWorkflowKind.PREPARE,
                status=ArtifactWorkflowStatus.BLOCKED,
                message="artifacts prepare is blocked until artifact bootstrap succeeds.",
                reason="artifact bootstrap result is missing or unsuccessful",
                operation_result=aggregate_operation(
                    OperationOutcome.BLOCKED,
                    completed=bootstrap_result.operation_result.completed_operations if bootstrap_result and bootstrap_result.operation_result else (),
                    pending=("artifacts.prepare.bootstrap",),
                    uncertain=bootstrap_result.operation_result.uncertain_operations if bootstrap_result and bootstrap_result.operation_result else (),
                    failures=bootstrap_result.operation_result.failures if bootstrap_result and bootstrap_result.operation_result and bootstrap_result.operation_result.failures else (OperationFailure.for_cause("artifacts.prepare.bootstrap", "artifacts", "blocked"),),
                ),
            )
        return await self._run_steps(self.mutation_steps, offset=len(self.bootstrap_steps))

    async def _run_steps(
        self,
        steps: Sequence[ArtifactPrepareStep],
        *, offset: int = 0,
    ) -> ArtifactWorkflowResult:
        completed: list[str] = []
        pending = [f"artifacts.prepare.step.{index}.verify" for index in range(offset + 1, offset + len(steps) + 1)]
        uncertain: list[str] = []
        failures: list[OperationFailure] = []

        def result(**kwargs) -> ArtifactWorkflowResult:
            status = kwargs["status"]
            outcome = OperationOutcome.SUCCESS if status == ArtifactWorkflowStatus.COMPLETED else OperationOutcome.BLOCKED if status == ArtifactWorkflowStatus.BLOCKED else OperationOutcome.FAILED
            context = failures or (() if outcome == OperationOutcome.SUCCESS else (OperationFailure.for_cause("artifacts.prepare", "artifacts", "blocked" if outcome == OperationOutcome.BLOCKED else "verification_failed"),))
            return ArtifactWorkflowResult(**kwargs, operation_result=aggregate_operation(outcome, completed=completed, pending=pending, uncertain=uncertain, failures=context))

        if not steps:
            return result(
                kind=ArtifactWorkflowKind.PREPARE,
                status=ArtifactWorkflowStatus.BLOCKED,
                message=ARTIFACT_PREPARE_CONTRACTS_BLOCKED_MESSAGE,
                reason=self.blocked_reason,
            )

        verification_results: list[VerificationResult] = []
        for index, step in enumerate(steps, offset + 1):
            identity = f"artifacts.prepare.step.{index}"
            target_id = _verification_target_id(step, "artifacts:prepare-step")
            if not _step_has_verification(step):
                blocked_verification = VerificationResult(
                    target_id=target_id,
                    status=VerificationStatus.BLOCKED,
                    message=VERIFICATION_EVIDENCE_MISSING_MESSAGE,
                    evidence={"phase": "pre_prepare", "reason": "verify_after_prepare_missing"},
                )
                verification_results.append(blocked_verification)
                return result(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.BLOCKED,
                    message=ARTIFACT_PREPARE_CONTRACTS_BLOCKED_MESSAGE,
                    reason="verify-after-prepare contract is missing for artifacts prepare",
                    verification_results=tuple(verification_results),
                )

            uncertain.append(identity + ".apply")
            try:
                prepare_result = step.run()
                if inspect.isawaitable(prepare_result):
                    await prepare_result
            except Exception as exc:
                failures.append(failure_from_exception(exc, identity + ".apply", "artifacts"))
                safe_error = _safe_exception_summary(exc)
                self.logger.error(
                    "Failed to prepare artifact target '%s'. Error: %s",
                    target_id,
                    safe_error,
                )
                return result(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.FAILED_TO_PREPARE,
                    message="artifacts prepare failed for a configured artifact contract.",
                    reason=_prepare_failure_reason(target_id, exc),
                    executed=True,
                    verification_results=(
                        *verification_results,
                        VerificationResult(
                            target_id=target_id,
                            status=VerificationStatus.FAILED_TO_APPLY,
                            message=f"Prepare failed for {target_id}: {safe_error}",
                            evidence=_prepare_failure_evidence(exc),
                        ),
                    ),
                )

            verification, step_failures = await _verify_step(step, target_id, identity + ".verify")
            failures.extend(step_failures)
            if verification.status == VerificationStatus.VERIFIED and not step_failures:
                completed.append(identity + ".verify")
                pending.remove(identity + ".verify")
                uncertain.remove(identity + ".apply")
            verification_results.append(verification)
            if verification.status == VerificationStatus.BLOCKED:
                return result(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.BLOCKED,
                    message="artifacts prepare is blocked until artifact preparation contracts are wired.",
                    reason=f"verification is blocked for {target_id}",
                    executed=True,
                    verification_results=tuple(verification_results),
                )
            if verification.status != VerificationStatus.VERIFIED:
                return result(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.FAILED_TO_VERIFY,
                    message="artifacts prepare failed verification for a configured artifact contract.",
                    reason=f"verification failed for {target_id}",
                    executed=True,
                    verification_results=tuple(verification_results),
                )

        return result(
            kind=ArtifactWorkflowKind.PREPARE,
            status=ArtifactWorkflowStatus.COMPLETED,
            message="artifacts prepare completed for configured artifact contracts.",
            reason="configured artifact contracts prepared and verified through artifact ports",
            executed=True,
            verification_results=tuple(verification_results),
        )


class ArtifactVerifyWorkflow:
    def __init__(
        self,
        checks: Sequence[ArtifactVerifyCheck] = (),
        blocked_reason: str = DEFAULT_ARTIFACT_VERIFY_BLOCK_REASON,
    ):
        self.checks = tuple(checks)
        self.blocked_reason = blocked_reason

    async def run(self) -> ArtifactWorkflowResult:
        completed: list[str] = []
        pending = [f"artifacts.verify.step.{index}" for index in range(1, len(self.checks) + 1)]
        failures: list[OperationFailure] = []

        def result(**kwargs) -> ArtifactWorkflowResult:
            status = kwargs["status"]
            outcome = OperationOutcome.SUCCESS if status == ArtifactWorkflowStatus.COMPLETED else OperationOutcome.BLOCKED if status == ArtifactWorkflowStatus.BLOCKED else OperationOutcome.FAILED
            context = failures or (() if outcome == OperationOutcome.SUCCESS else (OperationFailure.for_cause("artifacts.verify", "artifacts", "blocked" if outcome == OperationOutcome.BLOCKED else "verification_failed"),))
            return ArtifactWorkflowResult(**kwargs, operation_result=aggregate_operation(outcome, completed=completed, pending=pending, failures=context))

        if not self.checks:
            return result(
                kind=ArtifactWorkflowKind.VERIFY,
                status=ArtifactWorkflowStatus.BLOCKED,
                message="artifacts verify is blocked until artifact verification contracts are wired.",
                reason=self.blocked_reason,
            )

        verification_results: list[VerificationResult] = []
        for index, check in enumerate(self.checks, 1):
            identity = f"artifacts.verify.step.{index}"
            target_id = _verification_target_id(check, "artifacts:verify-check")
            verification, step_failures = await _verify_step(check, target_id, identity)
            failures.extend(step_failures)
            if verification.status == VerificationStatus.VERIFIED and not step_failures:
                completed.append(identity)
                pending.remove(identity)
            verification_results.append(verification)
            if verification.status == VerificationStatus.BLOCKED:
                return result(
                    kind=ArtifactWorkflowKind.VERIFY,
                    status=ArtifactWorkflowStatus.BLOCKED,
                    message="artifacts verify is blocked until artifact verification contracts are wired.",
                    reason=f"verification is blocked for {target_id}",
                    verification_results=tuple(verification_results),
                )
            if verification.status != VerificationStatus.VERIFIED:
                return result(
                    kind=ArtifactWorkflowKind.VERIFY,
                    status=ArtifactWorkflowStatus.FAILED_TO_VERIFY,
                    message="artifacts verify failed for a configured artifact contract.",
                    reason=f"verification failed for {target_id}",
                    verification_results=tuple(verification_results),
                )

        return result(
            kind=ArtifactWorkflowKind.VERIFY,
            status=ArtifactWorkflowStatus.COMPLETED,
            message="artifacts verify completed for configured artifact contracts.",
            reason="configured artifact contracts verified through artifact ports",
            verification_results=tuple(verification_results),
        )


def _step_has_verification(step: ArtifactPrepareStep | ArtifactVerifyCheck) -> bool:
    return callable(getattr(step, "verify", None))


def _verification_target_id(
    step: ArtifactPrepareStep | ArtifactVerifyCheck,
    fallback: str,
) -> str:
    target_id = getattr(step, "verification_target_id", "")
    if target_id:
        return str(target_id)
    artifact_target_id = getattr(step, "artifact_target_id", "")
    if artifact_target_id:
        return str(artifact_target_id)
    return fallback


async def _verify_step(step, target_id: str, identity: str) -> tuple[VerificationResult, tuple[OperationFailure, ...]]:
    verification, caught = await _verify_output(step, target_id)
    companion = getattr(step, "operation_failure", None)
    failure = caught if caught is not None else companion if isinstance(companion, OperationFailure) else None
    failures = verification_failures(verification.evidence, verified=verification.status == VerificationStatus.VERIFIED,
        operation=identity, component="artifacts", failure=failure, blocked=verification.status == VerificationStatus.BLOCKED)
    if failures and verification.status == VerificationStatus.VERIFIED:
        verification = replace(verification, status=VerificationStatus.FAILED_TO_VERIFY, message="Artifact verification contains contradictory failure evidence.")
    return verification, failures


async def _verify_output(
    step: ArtifactPrepareStep | ArtifactVerifyCheck,
    target_id: str,
) -> tuple[VerificationResult, OperationFailure | None]:
    verify = getattr(step, "verify", None)
    if not callable(verify):
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.BLOCKED,
            message=VERIFICATION_EVIDENCE_MISSING_MESSAGE,
            evidence={"phase": "verify"},
        ), None
    try:
        verification_output = verify()
        if inspect.isawaitable(verification_output):
            verification_output = await verification_output
    except Exception as exc:
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message=f"Verification failed for {target_id}: {exc.__class__.__name__}",
            evidence={"phase": "verify"},
        ), failure_from_exception(exc, "artifacts.verify", "artifacts")
    if isinstance(verification_output, VerificationResult):
        return verification_output, None
    return VerificationResult(
        target_id=target_id,
        status=VerificationStatus.BLOCKED,
        message=VERIFICATION_EVIDENCE_MISSING_MESSAGE,
        evidence={"phase": "verify"},
    ), None


def _safe_exception_summary(exc: Exception) -> str:
    diagnostic = _safe_diagnostic(exc)
    if diagnostic:
        return f"{exc.__class__.__name__}. Diagnostic: {diagnostic}."
    status_code = getattr(exc, "status_code", None)
    if type(status_code) is int and 100 <= status_code <= 599:
        return f"{exc.__class__.__name__} HTTP {status_code}. Diagnostic payload redacted."
    return f"{exc.__class__.__name__}. Diagnostic payload redacted."


def _prepare_failure_reason(target_id: str, exc: Exception) -> str:
    if _safe_diagnostic(exc):
        return f"prepare failed for {target_id}: {_safe_exception_summary(exc)}"
    return f"prepare failed with {exc.__class__.__name__}"


def _prepare_failure_evidence(exc: Exception) -> dict[str, str]:
    evidence = {"phase": "prepare", "failure_class": exc.__class__.__name__}
    diagnostic = _safe_diagnostic(exc)
    if diagnostic:
        evidence["diagnostic"] = str(diagnostic)
    operator_action = getattr(exc, "operator_action", None)
    if operator_action:
        evidence["operator_action_code"] = _safe_operator_action_code(exc)
    status_code = getattr(exc, "status_code", None)
    if type(status_code) is int and 100 <= status_code <= 599:
        evidence["http_status"] = str(status_code)
    return evidence


def _safe_diagnostic(exc: Exception) -> str:
    diagnostic = getattr(exc, "diagnostic", None)
    return diagnostic if diagnostic in (
        "rotated_credentials_inactive", "nexus_container_not_found", "initial_admin_value_unavailable",
    ) else ""


def _safe_operator_action_code(exc: Exception) -> str:
    diagnostic = _safe_diagnostic(exc)
    return f"{diagnostic}_recovery" if diagnostic else "operator_recovery"

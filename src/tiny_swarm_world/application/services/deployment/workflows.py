from __future__ import annotations

import inspect
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class DeploymentWorkflowKind(str, Enum):
    BOOTSTRAP = "bootstrap"
    APPLY = "apply"
    VERIFY = "verify"


class DeploymentWorkflowStatus(str, Enum):
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED_TO_APPLY = "failed_to_apply"
    FAILED_TO_PREPARE = "failed_to_prepare"
    FAILED_TO_VERIFY = "failed_to_verify"


class DeploymentApplyStep(Protocol):
    def run(self) -> object:
        # Protocol declaration; concrete steps apply stack changes.
        pass

    def verify(self) -> object:
        # Protocol declaration; concrete steps report post-apply evidence.
        pass


class DeploymentVerifyCheck(Protocol):
    def verify(self) -> object:
        # Protocol declaration; concrete checks inspect deployed state.
        pass


class DeploymentPreApplyCheck(Protocol):
    def verify(self) -> object:
        # Protocol declaration; concrete checks enforce pre-apply readiness.
        pass


@dataclass(frozen=True)
class DeploymentWorkflowResult:
    kind: DeploymentWorkflowKind
    status: DeploymentWorkflowStatus
    message: str
    reason: str
    executed: bool = False
    verification_results: tuple[VerificationResult, ...] = ()

    @property
    def workflow_name(self) -> str:
        return f"deployment {self.kind.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "message": self.message,
            "reason": self.reason,
            "status": self.status.value,
            "verification_results": [
                verification.to_dict() for verification in self.verification_results
            ],
            "workflow": self.workflow_name,
        }


DEFAULT_DEPLOYMENT_APPLY_BLOCK_REASON = (
    "Portainer stack changes require command-backed verification and live "
    "operation contracts before apply can run"
)
DEPLOYMENT_APPLY_CONTRACTS_BLOCKED_MESSAGE = (
    "deployment apply is blocked until stack deployment contracts are wired."
)
VERIFICATION_EVIDENCE_MISSING_MESSAGE = "Verification evidence is missing."


class DeploymentApplyWorkflow:
    def __init__(
        self,
        steps: Sequence[DeploymentApplyStep] = (),
        pre_apply_checks: Sequence[DeploymentPreApplyCheck] = (),
        blocked_reason: str = DEFAULT_DEPLOYMENT_APPLY_BLOCK_REASON,
        kind: DeploymentWorkflowKind = DeploymentWorkflowKind.APPLY,
    ):
        self.steps = tuple(steps)
        self.pre_apply_checks = tuple(pre_apply_checks)
        self.blocked_reason = blocked_reason
        self.kind = kind

    async def run(self) -> DeploymentWorkflowResult:
        if not self.steps:
            return DeploymentWorkflowResult(
                kind=self.kind,
                status=DeploymentWorkflowStatus.BLOCKED,
                message=DEPLOYMENT_APPLY_CONTRACTS_BLOCKED_MESSAGE,
                reason=self.blocked_reason,
            )

        verification_results: list[VerificationResult] = []
        pre_apply_result = await _run_pre_apply_checks(
            self.pre_apply_checks,
            self.kind,
            verification_results,
        )
        if pre_apply_result is not None:
            return pre_apply_result

        for step in self.steps:
            target_id = _verification_target_id(step, "deployment:apply-step")
            if not _step_has_verification(step):
                blocked_verification = VerificationResult(
                    target_id=target_id,
                    status=VerificationStatus.BLOCKED,
                    message=VERIFICATION_EVIDENCE_MISSING_MESSAGE,
                    evidence={"phase": "pre_apply", "reason": "verify_after_apply_missing"},
                )
                verification_results.append(blocked_verification)
                return DeploymentWorkflowResult(
                    kind=self.kind,
                    status=DeploymentWorkflowStatus.BLOCKED,
                    message=DEPLOYMENT_APPLY_CONTRACTS_BLOCKED_MESSAGE,
                    reason="verify-after-apply contract is missing for deployment apply",
                    verification_results=tuple(verification_results),
                )

            try:
                apply_result = step.run()
                if inspect.isawaitable(apply_result):
                    await apply_result
            except Exception as exc:
                return DeploymentWorkflowResult(
                    kind=self.kind,
                    status=DeploymentWorkflowStatus.FAILED_TO_PREPARE,
                    message="deployment prepare failed for a configured stack contract.",
                    reason=f"prepare failed with {exc.__class__.__name__}",
                    executed=True,
                    verification_results=(
                        *verification_results,
                        VerificationResult(
                            target_id=target_id,
                            status=VerificationStatus.FAILED_TO_APPLY,
                            message=f"Apply failed for {target_id}: {exc.__class__.__name__}",
                            evidence={"phase": "apply"},
                        ),
                    ),
                )

            verification = await _verify_step(step, target_id)
            verification_results.append(verification)
            if verification.status == VerificationStatus.BLOCKED:
                return DeploymentWorkflowResult(
                    kind=self.kind,
                    status=DeploymentWorkflowStatus.BLOCKED,
                    message=DEPLOYMENT_APPLY_CONTRACTS_BLOCKED_MESSAGE,
                    reason=f"verification is blocked for {target_id}",
                    executed=True,
                    verification_results=tuple(verification_results),
                )
            if verification.status != VerificationStatus.VERIFIED:
                return DeploymentWorkflowResult(
                    kind=self.kind,
                    status=DeploymentWorkflowStatus.FAILED_TO_VERIFY,
                    message="deployment apply failed verification for a configured stack contract.",
                    reason=f"verification failed for {target_id}",
                    executed=True,
                    verification_results=tuple(verification_results),
                )

        return DeploymentWorkflowResult(
            kind=self.kind,
            status=DeploymentWorkflowStatus.COMPLETED,
            message="deployment apply completed for configured stack contracts.",
            reason="configured stack contracts applied and verified through deployment ports",
            executed=True,
            verification_results=tuple(verification_results),
        )


class DeploymentVerifyWorkflow:
    def __init__(self, checks: Sequence[DeploymentVerifyCheck] = ()):
        self.checks = tuple(checks)

    async def run(self) -> DeploymentWorkflowResult:
        if not self.checks:
            return DeploymentWorkflowResult(
                kind=DeploymentWorkflowKind.VERIFY,
                status=DeploymentWorkflowStatus.BLOCKED,
                message="deployment verify is blocked until stack verification contracts are wired.",
                reason=(
                    "stack and service observed-state verification is not implemented through "
                    "deployment ports"
                ),
            )

        verification_results: list[VerificationResult] = []
        for check in self.checks:
            target_id = _verification_target_id(check, "deployment:verify-check")
            verification = await _verify_step(check, target_id)
            verification_results.append(verification)
            if verification.status == VerificationStatus.BLOCKED:
                return DeploymentWorkflowResult(
                    kind=DeploymentWorkflowKind.VERIFY,
                    status=DeploymentWorkflowStatus.BLOCKED,
                    message="deployment verify is blocked until stack verification contracts are wired.",
                    reason=f"verification is blocked for {target_id}",
                    verification_results=tuple(verification_results),
                )
            if verification.status != VerificationStatus.VERIFIED:
                return DeploymentWorkflowResult(
                    kind=DeploymentWorkflowKind.VERIFY,
                    status=DeploymentWorkflowStatus.FAILED_TO_VERIFY,
                    message="deployment verify failed for a configured stack contract.",
                    reason=f"verification failed for {target_id}",
                    verification_results=tuple(verification_results),
                )

        return DeploymentWorkflowResult(
            kind=DeploymentWorkflowKind.VERIFY,
            status=DeploymentWorkflowStatus.COMPLETED,
            message="deployment verify completed for configured stack contracts.",
            reason="configured stack contracts verified through deployment ports",
            verification_results=tuple(verification_results),
        )


def _step_has_verification(step: DeploymentApplyStep | DeploymentVerifyCheck) -> bool:
    return callable(getattr(step, "verify", None))


def _verification_target_id(
    step: DeploymentApplyStep | DeploymentVerifyCheck | DeploymentPreApplyCheck,
    fallback: str,
) -> str:
    target_id = getattr(step, "verification_target_id", "")
    if target_id:
        return str(target_id)
    deployment_target_id = getattr(step, "deployment_target_id", "")
    if deployment_target_id:
        return str(deployment_target_id)
    return fallback


async def _run_pre_apply_checks(
    checks: Sequence[DeploymentPreApplyCheck],
    kind: DeploymentWorkflowKind,
    verification_results: list[VerificationResult],
) -> DeploymentWorkflowResult | None:
    for check in checks:
        target_id = _verification_target_id(check, "deployment:pre-apply-check")
        verification = await _verify_step(check, target_id)
        verification_results.append(verification)
        if verification.status == VerificationStatus.BLOCKED:
            return DeploymentWorkflowResult(
                kind=kind,
                status=DeploymentWorkflowStatus.BLOCKED,
                message="deployment apply is blocked by pre-apply verification.",
                reason=f"pre-apply verification is blocked for {target_id}",
                verification_results=tuple(verification_results),
            )
        if verification.status != VerificationStatus.VERIFIED:
            return DeploymentWorkflowResult(
                kind=kind,
                status=DeploymentWorkflowStatus.FAILED_TO_VERIFY,
                message="deployment apply failed pre-apply verification.",
                reason=f"pre-apply verification failed for {target_id}",
                verification_results=tuple(verification_results),
            )
    return None


async def _verify_step(
    step: DeploymentApplyStep | DeploymentVerifyCheck | DeploymentPreApplyCheck,
    target_id: str,
) -> VerificationResult:
    verify = getattr(step, "verify", None)
    if not callable(verify):
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.BLOCKED,
            message=VERIFICATION_EVIDENCE_MISSING_MESSAGE,
            evidence={"phase": "verify"},
        )
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
        )
    if isinstance(verification_output, VerificationResult):
        return verification_output
    return VerificationResult(
        target_id=target_id,
        status=VerificationStatus.BLOCKED,
        message=VERIFICATION_EVIDENCE_MISSING_MESSAGE,
        evidence={"phase": "verify"},
    )

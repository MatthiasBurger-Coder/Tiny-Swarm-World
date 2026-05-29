from __future__ import annotations

import inspect
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

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

    @property
    def workflow_name(self) -> str:
        return f"artifacts {self.kind.value}"

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
    ):
        self.steps = tuple(steps)
        self.blocked_reason = blocked_reason

    async def run(self) -> ArtifactWorkflowResult:
        if not self.steps:
            return ArtifactWorkflowResult(
                kind=ArtifactWorkflowKind.PREPARE,
                status=ArtifactWorkflowStatus.BLOCKED,
                message=ARTIFACT_PREPARE_CONTRACTS_BLOCKED_MESSAGE,
                reason=self.blocked_reason,
            )

        verification_results: list[VerificationResult] = []
        for step in self.steps:
            target_id = _verification_target_id(step, "artifacts:prepare-step")
            if not _step_has_verification(step):
                blocked_verification = VerificationResult(
                    target_id=target_id,
                    status=VerificationStatus.BLOCKED,
                    message=VERIFICATION_EVIDENCE_MISSING_MESSAGE,
                    evidence={"phase": "pre_prepare", "reason": "verify_after_prepare_missing"},
                )
                verification_results.append(blocked_verification)
                return ArtifactWorkflowResult(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.BLOCKED,
                    message=ARTIFACT_PREPARE_CONTRACTS_BLOCKED_MESSAGE,
                    reason="verify-after-prepare contract is missing for artifacts prepare",
                    verification_results=tuple(verification_results),
                )

            try:
                prepare_result = step.run()
                if inspect.isawaitable(prepare_result):
                    await prepare_result
            except Exception as exc:
                return ArtifactWorkflowResult(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.FAILED_TO_PREPARE,
                    message="artifacts prepare failed for a configured artifact contract.",
                    reason=f"prepare failed with {exc.__class__.__name__}",
                    executed=True,
                    verification_results=(
                        *verification_results,
                        VerificationResult(
                            target_id=target_id,
                            status=VerificationStatus.FAILED_TO_APPLY,
                            message=f"Prepare failed for {target_id}: {exc.__class__.__name__}",
                            evidence={"phase": "prepare"},
                        ),
                    ),
                )

            verification = await _verify_step(step, target_id)
            verification_results.append(verification)
            if verification.status == VerificationStatus.BLOCKED:
                return ArtifactWorkflowResult(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.BLOCKED,
                    message="artifacts prepare is blocked until artifact preparation contracts are wired.",
                    reason=f"verification is blocked for {target_id}",
                    executed=True,
                    verification_results=tuple(verification_results),
                )
            if verification.status != VerificationStatus.VERIFIED:
                return ArtifactWorkflowResult(
                    kind=ArtifactWorkflowKind.PREPARE,
                    status=ArtifactWorkflowStatus.FAILED_TO_VERIFY,
                    message="artifacts prepare failed verification for a configured artifact contract.",
                    reason=f"verification failed for {target_id}",
                    executed=True,
                    verification_results=tuple(verification_results),
                )

        return ArtifactWorkflowResult(
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
        if not self.checks:
            return ArtifactWorkflowResult(
                kind=ArtifactWorkflowKind.VERIFY,
                status=ArtifactWorkflowStatus.BLOCKED,
                message="artifacts verify is blocked until artifact verification contracts are wired.",
                reason=self.blocked_reason,
            )

        verification_results: list[VerificationResult] = []
        for check in self.checks:
            target_id = _verification_target_id(check, "artifacts:verify-check")
            verification = await _verify_step(check, target_id)
            verification_results.append(verification)
            if verification.status == VerificationStatus.BLOCKED:
                return ArtifactWorkflowResult(
                    kind=ArtifactWorkflowKind.VERIFY,
                    status=ArtifactWorkflowStatus.BLOCKED,
                    message="artifacts verify is blocked until artifact verification contracts are wired.",
                    reason=f"verification is blocked for {target_id}",
                    verification_results=tuple(verification_results),
                )
            if verification.status != VerificationStatus.VERIFIED:
                return ArtifactWorkflowResult(
                    kind=ArtifactWorkflowKind.VERIFY,
                    status=ArtifactWorkflowStatus.FAILED_TO_VERIFY,
                    message="artifacts verify failed for a configured artifact contract.",
                    reason=f"verification failed for {target_id}",
                    verification_results=tuple(verification_results),
                )

        return ArtifactWorkflowResult(
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


async def _verify_step(
    step: ArtifactPrepareStep | ArtifactVerifyCheck,
    target_id: str,
) -> VerificationResult:
    verify = getattr(step, "verify", None)
    if not callable(verify):
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.BLOCKED,
            message="Verification evidence is missing.",
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
        message="Verification evidence is missing.",
        evidence={"phase": "verify"},
    )

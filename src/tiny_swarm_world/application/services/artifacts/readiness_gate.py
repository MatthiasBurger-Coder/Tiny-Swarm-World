from __future__ import annotations

from collections.abc import Sequence

from tiny_swarm_world.application.ports.preflight import PortLiveReadiness
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import LiveVerificationState
from tiny_swarm_world.domain.preflight import (
    ARTIFACT_READINESS_TARGETS,
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
    ReadinessCheckResult,
    ReadinessProbeRequest,
    ReadinessStatus,
)


DEFAULT_ARTIFACT_READINESS_TIMEOUT_SECONDS = 5.0
DEFAULT_ARTIFACT_READINESS_ATTEMPTS = 1


class ArtifactReadinessGate:
    """Evaluate mandatory live prerequisites before artifact mutation."""

    def __init__(
        self,
        readiness: PortLiveReadiness,
        requests: Sequence[ReadinessProbeRequest] | None = None,
    ) -> None:
        self.readiness = readiness
        self.requests = tuple(requests or _default_requests())
        request_targets = tuple(request.target_id for request in self.requests)
        if request_targets != ARTIFACT_READINESS_TARGETS:
            raise ValueError(
                "artifact readiness gate must check the complete ordered target set"
            )

    def run(
        self,
        *,
        static_preflight: PreflightResult | None,
        artifact_bootstrap: ArtifactWorkflowResult | None,
    ) -> PreflightResult:
        if (
            static_preflight is None
            or not static_preflight.checks
            or not static_preflight.passed
        ):
            return PreflightResult(
                checks=(_failed_prerequisite_check(
                    check_id="ARTIFACT-STATIC-PREFLIGHT",
                    message="Static artifact contract preflight did not pass.",
                    remediation="Resolve static artifact contract findings before live checks.",
                    evidence_scope="static",
                    reason="static_preflight_missing_or_failed",
                    live_state=LiveVerificationState.BLOCKED_BEFORE_MUTATION,
                ),),
            )

        if (
            artifact_bootstrap is None
            or artifact_bootstrap.status is not ArtifactWorkflowStatus.COMPLETED
            or not artifact_bootstrap.executed
        ):
            return PreflightResult(
                checks=(_failed_prerequisite_check(
                    check_id="ARTIFACT-BOOTSTRAP",
                    message="Required Nexus and registry bootstrap did not pass.",
                    remediation="Resolve artifact bootstrap findings before live checks.",
                    evidence_scope="live",
                    reason="artifact_bootstrap_missing_or_failed",
                    live_state=_bootstrap_live_state(artifact_bootstrap),
                ),),
                setup_profile=static_preflight.setup_profile,
            )

        checks = tuple(self._check(request) for request in self.requests)
        return PreflightResult(
            checks=checks,
            setup_profile=static_preflight.setup_profile,
        )

    def _check(self, request: ReadinessProbeRequest) -> PreflightCheck:
        try:
            result = self.readiness.check(request)
        except Exception:
            result = ReadinessCheckResult(
                target_id=request.target_id,
                status=ReadinessStatus.UNKNOWN,
                message="The live readiness observation could not be classified safely.",
                remediation="Inspect the bounded readiness adapter before retrying.",
                evidence={"evidence_scope": "live"},
            )
        if not isinstance(result, ReadinessCheckResult):
            result = ReadinessCheckResult(
                target_id=request.target_id,
                status=ReadinessStatus.UNKNOWN,
                message="The live readiness adapter returned no typed result.",
                remediation="Return a typed readiness result before artifact mutation.",
                evidence={"evidence_scope": "live"},
            )
        if result.target_id != request.target_id:
            result = ReadinessCheckResult(
                target_id=request.target_id,
                status=ReadinessStatus.UNKNOWN,
                message="The live readiness adapter returned an invalid target identity.",
                remediation="Align the readiness target identity before retrying.",
                evidence={"evidence_scope": "live"},
            )
        return PreflightCheck(
            check_id=f"ARTIFACT-READINESS-{request.target_id.upper().replace(':', '-')}",
            category=PreflightCategory.RUNTIME,
            status=PreflightStatus.PASSED if result.ready else PreflightStatus.FAILED,
            severity=PreflightSeverity.MANDATORY,
            message=result.message,
            remediation=result.remediation,
            evidence={
                "evidence_scope": "live",
                "live_state": _readiness_live_state(result.status).value,
                "readiness_status": result.status.value,
                **dict(result.evidence),
            },
        )


def _default_requests() -> tuple[ReadinessProbeRequest, ...]:
    return tuple(
        ReadinessProbeRequest(
            target_id=target_id,
            timeout_seconds=DEFAULT_ARTIFACT_READINESS_TIMEOUT_SECONDS,
            max_attempts=DEFAULT_ARTIFACT_READINESS_ATTEMPTS,
        )
        for target_id in ARTIFACT_READINESS_TARGETS
    )


def _failed_prerequisite_check(
    *,
    check_id: str,
    message: str,
    remediation: str,
    evidence_scope: str,
    reason: str,
    live_state: LiveVerificationState,
) -> PreflightCheck:
    return PreflightCheck(
        check_id=check_id,
        category=PreflightCategory.CONFIGURATION,
        status=PreflightStatus.FAILED,
        severity=PreflightSeverity.MANDATORY,
        message=message,
        remediation=remediation,
        evidence={
            "evidence_scope": evidence_scope,
            "live_state": live_state.value,
            "reason": reason,
        },
    )


def _bootstrap_live_state(
    result: ArtifactWorkflowResult | None,
) -> LiveVerificationState:
    if result is None or not result.executed:
        return LiveVerificationState.PREREQUISITE_MISSING
    return LiveVerificationState.FAILED_AFTER_MUTATION


def _readiness_live_state(status: ReadinessStatus) -> LiveVerificationState:
    if status is ReadinessStatus.READY:
        return LiveVerificationState.VERIFIED
    if status is ReadinessStatus.PARTIAL:
        return LiveVerificationState.PARTIAL
    if status is ReadinessStatus.DEGRADED:
        return LiveVerificationState.DEGRADED
    return LiveVerificationState.PREREQUISITE_MISSING

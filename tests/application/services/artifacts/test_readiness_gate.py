import unittest

from tiny_swarm_world.application.ports.preflight import PortLiveReadiness
from tiny_swarm_world.application.services.artifacts import (
    ArtifactReadinessGate,
    ArtifactWorkflowKind,
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
)
from tiny_swarm_world.domain.preflight import (
    ARTIFACT_READINESS_TARGETS,
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
    ReadinessCheckResult,
    ReadinessStatus,
)


class _FakeReadiness(PortLiveReadiness):
    def __init__(self, status: ReadinessStatus = ReadinessStatus.READY) -> None:
        self.status = status
        self.calls: list[str] = []

    def check(self, request):
        self.calls.append(request.target_id)
        return ReadinessCheckResult(
            target_id=request.target_id,
            status=self.status,
            message="safe readiness result",
            remediation="safe remediation",
            evidence={"probe_kind": "fake"},
        )


class TestArtifactReadinessGate(unittest.TestCase):
    def test_static_failure_blocks_without_live_observations(self):
        readiness = _FakeReadiness()
        result = ArtifactReadinessGate(readiness).run(
            static_preflight=_preflight(PreflightStatus.FAILED),
            artifact_bootstrap=_bootstrap_result(),
        )

        self.assertEqual(PreflightStatus.FAILED, result.checks[0].status)
        self.assertEqual("static_preflight_missing_or_failed", result.checks[0].evidence["reason"])
        self.assertEqual([], readiness.calls)
        self.assertEqual(
            "LIVE_BLOCKED_BEFORE_MUTATION",
            result.checks[0].evidence["live_state"],
        )

    def test_bootstrap_failure_blocks_without_live_observations(self):
        readiness = _FakeReadiness()
        result = ArtifactReadinessGate(readiness).run(
            static_preflight=_preflight(PreflightStatus.PASSED),
            artifact_bootstrap=ArtifactWorkflowResult(
                kind=ArtifactWorkflowKind.PREPARE,
                status=ArtifactWorkflowStatus.FAILED_TO_VERIFY,
                message="bootstrap failed",
                reason="bootstrap failed",
                executed=True,
            ),
        )

        self.assertEqual("ARTIFACT-BOOTSTRAP", result.checks[0].check_id)
        self.assertEqual([], readiness.calls)
        self.assertEqual(
            "LIVE_FAILED_AFTER_MUTATION",
            result.checks[0].evidence["live_state"],
        )

    def test_unknown_readiness_fails_closed_for_every_mandatory_target(self):
        readiness = _FakeReadiness(ReadinessStatus.UNKNOWN)
        result = ArtifactReadinessGate(readiness).run(
            static_preflight=_preflight(PreflightStatus.PASSED),
            artifact_bootstrap=_bootstrap_result(),
        )

        self.assertFalse(result.passed)
        self.assertEqual(list(ARTIFACT_READINESS_TARGETS), readiness.calls)
        self.assertTrue(
            all(check.status is PreflightStatus.FAILED for check in result.checks)
        )
        self.assertTrue(
            all(check.evidence["evidence_scope"] == "live" for check in result.checks)
        )
        self.assertTrue(
            all(
                check.evidence["live_state"] == "LIVE_PREREQUISITE_MISSING"
                for check in result.checks
            )
        )

    def test_ready_result_is_machine_readable_and_redacted(self):
        readiness = _FakeReadiness()
        result = ArtifactReadinessGate(readiness).run(
            static_preflight=_preflight(PreflightStatus.PASSED),
            artifact_bootstrap=_bootstrap_result(),
        )

        self.assertTrue(result.passed)
        payload = result.to_dict()
        self.assertEqual("PASSED", payload["status"])
        self.assertEqual("live", payload["checks"][0]["evidence"]["evidence_scope"])
        self.assertEqual("LIVE_VERIFIED", payload["checks"][0]["evidence"]["live_state"])
        self.assertNotIn("secret", str(payload).lower())
        self.assertNotIn("token", str(payload).lower())


def _preflight(status: PreflightStatus) -> PreflightResult:
    return PreflightResult(
        checks=(
            PreflightCheck(
                check_id="STATIC",
                category=PreflightCategory.CONFIGURATION,
                status=status,
                severity=PreflightSeverity.MANDATORY,
                message="static result",
                remediation="static remediation",
            ),
        )
    )


def _bootstrap_result() -> ArtifactWorkflowResult:
    return ArtifactWorkflowResult(
        kind=ArtifactWorkflowKind.PREPARE,
        status=ArtifactWorkflowStatus.COMPLETED,
        message="bootstrap complete",
        reason="bootstrap complete",
        executed=True,
    )

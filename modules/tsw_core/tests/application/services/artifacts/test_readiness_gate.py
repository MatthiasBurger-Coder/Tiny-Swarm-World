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


    def test_selected_public_targets_need_no_nexus_bootstrap(self):
        readiness = _FakeReadiness()
        targets = tuple(ARTIFACT_READINESS_TARGETS[index] for index in (0, 4, 6))
        gate = ArtifactReadinessGate(readiness, required_targets=targets, requires_bootstrap=False)
        result = gate.run(static_preflight=_preflight(PreflightStatus.PASSED), artifact_bootstrap=None)
        self.assertTrue(result.passed)
        self.assertEqual(list(targets), readiness.calls)

    def test_selected_public_targets_keep_failed_readiness_blocking(self):
        readiness = _FakeReadiness(ReadinessStatus.FAILED)
        targets = (ARTIFACT_READINESS_TARGETS[0], ARTIFACT_READINESS_TARGETS[6])
        result = ArtifactReadinessGate(
            readiness, required_targets=targets, requires_bootstrap=False,
        ).run(static_preflight=_preflight(PreflightStatus.PASSED), artifact_bootstrap=None)
        self.assertFalse(result.passed)
        self.assertEqual(list(targets), readiness.calls)

    def test_selected_public_targets_keep_static_failure_blocking(self):
        readiness = _FakeReadiness()
        result = ArtifactReadinessGate(
            readiness, required_targets=(ARTIFACT_READINESS_TARGETS[0],), requires_bootstrap=False,
        ).run(static_preflight=_preflight(PreflightStatus.FAILED), artifact_bootstrap=None)
        self.assertFalse(result.passed)
        self.assertEqual([], readiness.calls)

    def test_target_subsets_must_be_known_unique_nonempty_and_ordered(self):
        for targets in ((), ("unknown",), (ARTIFACT_READINESS_TARGETS[0],) * 2,
                        tuple(reversed(ARTIFACT_READINESS_TARGETS))):
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                ArtifactReadinessGate(_FakeReadiness(), required_targets=targets)


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

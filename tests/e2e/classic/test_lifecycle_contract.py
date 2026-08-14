"""Deterministic Classic lifecycle, fail-closed and evidence contract tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tiny_swarm_world.application.ports.preflight import PortLiveReadiness
from tiny_swarm_world.application.services.artifacts import (
    ArtifactReadinessGate,
    ArtifactWorkflowKind,
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
)
from tiny_swarm_world.application.services.platform.workflow import (
    PlatformReconcileWorkflow,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.inventory.verification import (
    LiveVerificationState,
    VerificationResult,
    VerificationStatus,
)
from tiny_swarm_world.domain.preflight import (
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
    ReadinessCheckResult,
    ReadinessStatus,
)
from tests.e2e.classic import browser_e2e_contract
from tests.e2e.classic.browser_e2e_contract import (
    BrowserRouteExpectation,
    BrowserRouteResult,
)
from tests.support.classic_lifecycle_contract import (
    FINAL_DECISIONS,
    NON_SUCCESS_CLASSIFICATIONS,
    LifecycleEvidence,
    ResourceSnapshot,
    final_decision,
    reconcile_is_idempotent,
    restart_is_verified,
    update_preserves_unrelated_state,
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
            message="synthetic readiness result",
            remediation="synthetic remediation",
            evidence={"probe_kind": "synthetic"},
        )


class ClassicLifecycleContractTest(unittest.IsolatedAsyncioTestCase):
    def test_missing_prerequisite_blocks_before_live_observation(self) -> None:
        readiness = _FakeReadiness()

        result = ArtifactReadinessGate(readiness).run(
            static_preflight=_preflight(PreflightStatus.FAILED),
            artifact_bootstrap=_bootstrap_result(),
        )

        self.assertEqual([], readiness.calls)
        self.assertEqual("LIVE_BLOCKED_BEFORE_MUTATION", result.checks[0].evidence["live_state"])

    def test_unknown_runtime_prerequisite_is_not_reported_as_ready(self) -> None:
        readiness = _FakeReadiness(ReadinessStatus.UNKNOWN)

        result = ArtifactReadinessGate(readiness).run(
            static_preflight=_preflight(PreflightStatus.PASSED),
            artifact_bootstrap=_bootstrap_result(),
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            "LIVE_PREREQUISITE_MISSING",
            result.checks[0].evidence["live_state"],
        )
        self.assertTrue(result.checks)
        self.assertTrue(readiness.calls)

    def test_partial_and_ambiguous_states_never_become_success(self) -> None:
        partial = _evidence(
            state=LiveVerificationState.PARTIAL.value,
            result_classification="partial",
        )
        ambiguous = _evidence(
            state=LiveVerificationState.DEGRADED.value,
            result_classification="degraded",
        )
        failed_after_mutation = _evidence(
            state=LiveVerificationState.FAILED_AFTER_MUTATION.value,
            result_classification="failed-to-apply",
        )

        self.assertTrue(NON_SUCCESS_CLASSIFICATIONS.issuperset({"partial", "degraded"}))
        self.assertEqual(
            "RC1_REJECTED_BLOCKERS",
            final_decision((partial, ambiguous, failed_after_mutation), evidence_complete=True),
        )

    def test_reconcile_rejects_duplicate_or_destructive_drift(self) -> None:
        before = ResourceSnapshot(
            identities=("stack:service-access", "service:dashboard"),
            unrelated_state=(("stack:nexus", "healthy"),),
            ready=True,
        )

        self.assertTrue(reconcile_is_idempotent(before, before))
        self.assertFalse(
            reconcile_is_idempotent(
                before,
                ResourceSnapshot(
                    identities=("stack:service-access", "stack:service-access"),
                    unrelated_state=before.unrelated_state,
                    ready=True,
                ),
            )
        )
        self.assertFalse(
            reconcile_is_idempotent(
                before,
                ResourceSnapshot(
                    identities=("stack:service-access",),
                    unrelated_state=before.unrelated_state,
                    ready=True,
                ),
            )
        )

    async def test_production_reconcile_workflow_reverifies_stable_identity(self) -> None:
        step = _ReconcileStep()

        first = await PlatformReconcileWorkflow([step]).run()
        second = await PlatformReconcileWorkflow([step]).run()

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, first.status)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, second.status)
        self.assertEqual(2, step.apply_calls)
        self.assertEqual(
            ("stack:service-access",),
            tuple(item.target_id for item in second.verification_results),
        )
        self.assertEqual("stable", second.verification_results[0].evidence["identity"])

    async def test_production_reconcile_failure_after_apply_is_not_success(self) -> None:
        step = _ReconcileStep(ready=False)

        result = await PlatformReconcileWorkflow([step]).run()

        self.assertEqual(PlatformWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(1, step.apply_calls)
        self.assertEqual(
            VerificationStatus.FAILED_TO_VERIFY,
            result.verification_results[0].status,
        )

    def test_update_requires_unrelated_state_preservation(self) -> None:
        before = ResourceSnapshot(
            identities=("stack:service-access", "stack:nexus"),
            unrelated_state=(("stack:sonarqube", "healthy"),),
            ready=True,
        )

        self.assertTrue(update_preserves_unrelated_state(before, before))
        self.assertFalse(
            update_preserves_unrelated_state(
                before,
                ResourceSnapshot(
                    identities=("stack:service-access", "stack:nexus"),
                    unrelated_state=(("stack:sonarqube", "removed"),),
                    ready=True,
                ),
            )
        )

    def test_restart_requires_same_identity_and_ready_state(self) -> None:
        before = ResourceSnapshot(
            identities=("node:manager", "node:worker-1"),
            unrelated_state=(),
            ready=True,
        )

        self.assertTrue(restart_is_verified(before, before))
        self.assertFalse(
            restart_is_verified(
                before,
                ResourceSnapshot(
                    identities=("node:manager", "node:worker-2"),
                    unrelated_state=(),
                    ready=True,
                ),
            )
        )
        self.assertFalse(
            restart_is_verified(
                before,
                ResourceSnapshot(
                    identities=before.identities,
                    unrelated_state=(),
                    ready=False,
                ),
            )
        )

    def test_evidence_completeness_and_exact_decision_values_are_fail_closed(self) -> None:
        passed = _evidence()
        incomplete = _evidence(evidence_files=())

        self.assertEqual(
            {
                "RC1_ACCEPTED",
                "RC1_REJECTED_BLOCKERS",
                "RC1_REJECTED_EVIDENCE_INCOMPLETE",
            },
            FINAL_DECISIONS,
        )
        self.assertEqual("RC1_ACCEPTED", final_decision((passed,), evidence_complete=True))
        self.assertEqual(
            "RC1_REJECTED_EVIDENCE_INCOMPLETE",
            final_decision((incomplete,), evidence_complete=True),
        )
        self.assertEqual(
            "RC1_REJECTED_EVIDENCE_INCOMPLETE",
            final_decision((passed,), evidence_complete=False),
        )
        self.assertEqual(
            "RC1_REJECTED_EVIDENCE_INCOMPLETE",
            final_decision((), evidence_complete=True),
        )

    def test_raw_redaction_status_cannot_qualify_for_acceptance(self) -> None:
        raw = _evidence(redaction_status="raw")

        self.assertFalse(raw.is_complete())
        self.assertEqual(
            "RC1_REJECTED_EVIDENCE_INCOMPLETE",
            final_decision((raw,), evidence_complete=True),
        )

    def test_serialized_browser_evidence_is_written_redacted(self) -> None:
        route = BrowserRouteResult(
            route_name="service-access",
            url="https://service-access.tsw.local",
            result="blocked",
            redacted_reason="live_consent_missing",
        )
        expectation = BrowserRouteExpectation(
            route_name="service-access",
            dashboard_url="https://service-access.tsw.local",
        )

        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(browser_e2e_contract, "E2E_EVIDENCE_ROOT", root):
                route_path = browser_e2e_contract._record_route_result(
                    route,
                    expectations=(expectation,),
                )

            payload = json.loads(route_path.read_text(encoding="utf-8"))
            self.assertEqual("blocked", payload["status"])
            self.assertEqual("live_consent_missing", payload["redacted_reason"])
            self.assertNotIn("password", repr(payload).casefold())
            self.assertNotIn("token", repr(payload).casefold())

    def test_verification_evidence_rejects_raw_command_or_secret_values(self) -> None:
        with self.assertRaises(ValueError):
            VerificationResult(
                target_id="classic:evidence",
                evidence={"summary": "docker ps output"},
            )

        safe = VerificationResult(
            target_id="classic:evidence",
            evidence={"summary": "redacted readiness summary"},
        )
        self.assertEqual("redacted readiness summary", safe.evidence["summary"])


def _evidence(
    *,
    state: str = LiveVerificationState.VERIFIED.value,
    result_classification: str = "passed",
    evidence_files: tuple[str, ...] = ("scenario.json",),
    redaction_status: str = "redacted",
) -> LifecycleEvidence:
    return LifecycleEvidence(
        scenario_id="RC1-S03",
        host="synthetic-linux",
        commit="abcdef0",
        started_utc="2026-08-14T00:00:00Z",
        finished_utc="2026-08-14T00:01:00Z",
        state=state,
        result_classification=result_classification,
        exit_code=0 if result_classification == "passed" else 1,
        readiness_summary="all synthetic required targets ready",
        transitions=("preflight->apply", "apply->verify"),
        retry_metadata="attempts=1; bounded=true",
        remediation="synthetic remediation recorded",
        rollback_cleanup="not-required; synthetic state preserved",
        evidence_files=evidence_files,
        redaction_status=redaction_status,
        checksum="sha256:synthetic",
        reviewer="synthetic-reviewer",
        defects=(),
    )


class _ReconcileStep:
    verification_target_id = "stack:service-access"

    def __init__(self, *, ready: bool = True) -> None:
        self.ready = ready
        self.apply_calls = 0

    async def run(self) -> None:
        self.apply_calls += 1

    async def verify(self) -> VerificationResult:
        return VerificationResult(
            target_id=self.verification_target_id,
            status=(
                VerificationStatus.VERIFIED
                if self.ready
                else VerificationStatus.FAILED_TO_VERIFY
            ),
            message="synthetic reconcile verification",
            evidence={
                "identity": "stable",
                "phase": "verify",
                "readiness_observed": "true" if self.ready else "false",
            },
        )


def _preflight(status: PreflightStatus) -> PreflightResult:
    return PreflightResult(
        checks=(
            PreflightCheck(
                check_id="STATIC",
                category=PreflightCategory.CONFIGURATION,
                status=status,
                severity=PreflightSeverity.MANDATORY,
                message="synthetic preflight result",
                remediation="synthetic remediation",
            ),
        )
    )


def _bootstrap_result() -> ArtifactWorkflowResult:
    return ArtifactWorkflowResult(
        kind=ArtifactWorkflowKind.PREPARE,
        status=ArtifactWorkflowStatus.COMPLETED,
        message="synthetic bootstrap complete",
        reason="synthetic bootstrap complete",
        executed=True,
    )


if __name__ == "__main__":
    unittest.main()

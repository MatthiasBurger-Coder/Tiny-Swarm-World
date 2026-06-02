import unittest
from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.ports.method_trace import (
    MethodTraceEvent,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    PortWorkflowProgress,
    WorkflowProgressEvent,
)
from tiny_swarm_world.application.services.platform import (
    DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION,
    PLATFORM_WORKFLOW_TAXONOMY,
    RESET_TINY_SWARM_PLATFORM_CONFIRMATION,
    PlatformDestroyWorkflow,
    PlatformInitWorkflow,
    PlatformReconcileWorkflow,
    PlatformResetWorkflow,
    PlatformVerifyWorkflow,
    PlatformWorkflowKind,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.preflight import (
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
)


class TestPlatformWorkflowTaxonomy(unittest.TestCase):
    def test_workflow_semantics_are_explicit(self):
        expected = {
            PlatformWorkflowKind.INIT: (True, False, False),
            PlatformWorkflowKind.RECONCILE: (True, False, False),
            PlatformWorkflowKind.RESET: (True, True, True),
            PlatformWorkflowKind.DESTROY: (True, True, True),
            PlatformWorkflowKind.VERIFY: (False, False, False),
        }

        self.assertEqual(set(expected), set(PLATFORM_WORKFLOW_TAXONOMY))
        for kind, (mutating, destructive, requires_confirmation) in expected.items():
            semantics = PLATFORM_WORKFLOW_TAXONOMY[kind]
            self.assertEqual(mutating, semantics.mutating)
            self.assertEqual(destructive, semantics.destructive)
            self.assertEqual(requires_confirmation, semantics.requires_confirmation)


class TestPlatformWorkflows(unittest.IsolatedAsyncioTestCase):
    async def test_init_and_reconcile_run_only_configured_safe_steps(self):
        init_step = _RecordingAction("init")
        reconcile_step = _RecordingAction("reconcile")

        init_result = await PlatformInitWorkflow([init_step]).run()
        reconcile_result = await PlatformReconcileWorkflow([reconcile_step]).run()

        self.assertEqual(["init"], init_step.calls)
        self.assertEqual(["reconcile"], reconcile_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, init_result.status)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, reconcile_result.status)
        self.assertFalse(PlatformInitWorkflow.semantics.destructive)
        self.assertFalse(PlatformReconcileWorkflow.semantics.destructive)
        self.assertEqual(1, len(init_step.verifications))
        self.assertEqual(1, len(reconcile_step.verifications))
        self.assertEqual(
            ("init",),
            tuple(item.target_id for item in init_result.verification_results),
        )
        self.assertEqual(
            ("reconcile",),
            tuple(item.target_id for item in reconcile_result.verification_results),
        )

    async def test_init_reports_method_trace_for_completion(self):
        trace = _RecordingMethodTrace()
        result = await PlatformInitWorkflow(
            [_RecordingAction("init")],
            method_trace=trace,
            trace_correlation_id="trace-platform",
        ).run()

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(
            [
                ("PlatformInitWorkflow", "run", "entered", "pending", None),
                ("PlatformInitWorkflow", "run", "returned", "completed", None),
            ],
            trace.summary(),
        )
        self.assertEqual({"trace-platform"}, {event.correlation_id for event in trace.events})

    async def test_init_reports_safe_failure_trace_when_apply_exception_is_converted(self):
        trace = _RecordingMethodTrace()
        result = await PlatformInitWorkflow(
            [_FailingApplyAction("init")],
            method_trace=trace,
            trace_correlation_id="trace-platform",
        ).run()

        self.assertEqual(PlatformWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(
            [
                ("PlatformInitWorkflow", "run", "entered", "pending", None),
                (
                    "PlatformInitWorkflow",
                    "run",
                    "returned",
                    "failed_to_apply",
                    None,
                ),
            ],
            trace.summary(),
        )

    async def test_verify_is_non_mutating_and_runs_configured_safe_steps(self):
        verify_step = _RecordingAction("verify")

        result = await PlatformVerifyWorkflow([verify_step]).run()

        self.assertEqual(["verify"], verify_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertFalse(PlatformVerifyWorkflow.semantics.mutating)
        self.assertFalse(PlatformVerifyWorkflow.semantics.destructive)

    async def test_verify_reports_failed_preflight_as_failed_to_verify(self):
        verify_step = _PreflightAction(
            PreflightResult(
                (
                    PreflightCheck(
                        check_id="HOST",
                        category=PreflightCategory.HOST,
                        status=PreflightStatus.FAILED,
                        severity=PreflightSeverity.MANDATORY,
                        message="Host is not ready.",
                        remediation="Run from Linux or WSL.",
                    ),
                )
            )
        )

        result = await PlatformVerifyWorkflow([verify_step]).run()

        self.assertEqual(["preflight"], verify_step.calls)
        self.assertEqual(PlatformWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertTrue(result.executed)
        self.assertEqual(
            VerificationStatus.FAILED_TO_VERIFY,
            result.verification_results[0].status,
        )
        self.assertEqual(
            {"phase": "verify", "failed_check_count": "1"},
            dict(result.verification_results[0].evidence),
        )

    async def test_init_pre_apply_guard_blocks_before_steps(self):
        progress = _RecordingProgress()
        guard = _PreflightAction(
            PreflightResult(
                (
                    PreflightCheck(
                        check_id="PROVIDER-LXC-DAEMON",
                        category=PreflightCategory.RUNTIME,
                        status=PreflightStatus.FAILED,
                        severity=PreflightSeverity.MANDATORY,
                        message="LXC provider daemon is not reachable.",
                        remediation="Repair LXD/Incus runtime access.",
                    ),
                )
            )
        )
        step = _RecordingAction("init")

        result = await PlatformInitWorkflow(
            [step],
            pre_apply_guard=guard,
            progress=progress,
        ).run()

        self.assertEqual(["preflight"], guard.calls)
        self.assertEqual([], step.calls)
        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("platform:init:preflight", result.verification_results[0].target_id)
        self.assertEqual(VerificationStatus.BLOCKED, result.verification_results[0].status)
        self.assertEqual("1", result.verification_results[0].evidence["runtime_failure_count"])
        self.assertEqual(
            [
                ("pre_apply", "pre-apply guard", "started", "pending"),
                ("pre_apply", "pre-apply guard", "blocked", "blocked"),
                ("platform", "workflow stopped", "blocked", "blocked"),
            ],
            progress.summary(),
        )

    async def test_init_provider_guard_blocks_before_any_platform_step(self):
        progress = _RecordingProgress()
        guard = _ProviderGuardAction(
            VerificationResult(
                target_id="platform:node-provider:lxc_native",
                status=VerificationStatus.BLOCKED,
                message="Provider selection blocked platform mutation.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "provider_selection_blocked",
                    "requested_provider": "lxc_native",
                    "selected_provider": "lxc_native",
                    "selection_status": "blocked",
                    "backend_status": "missing",
                    "backend_candidate_count": "0",
                    "remediation_count": "1",
                },
            )
        )
        step = _RecordingAction("init")

        result = await PlatformInitWorkflow(
            [step],
            pre_apply_guard=guard,
            progress=progress,
        ).run()

        self.assertEqual(["provider"], guard.calls)
        self.assertEqual([], step.calls)
        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("platform:node-provider:lxc_native", result.verification_results[0].target_id)
        self.assertEqual("provider_selection_blocked", result.verification_results[0].evidence["reason"])
        self.assertEqual("lxc_native", result.verification_results[0].evidence["requested_provider"])
        self.assertNotIn("multipass_legacy", repr(result.to_dict()))
        self.assertEqual(
            [
                ("pre_apply", "pre-apply guard", "started", "pending"),
                ("pre_apply", "pre-apply guard", "blocked", "blocked"),
                ("platform", "workflow stopped", "blocked", "blocked"),
            ],
            progress.summary(),
        )

    async def test_init_pre_apply_guard_passes_before_steps(self):
        progress = _RecordingProgress()
        guard = _PreflightAction(PreflightResult(()))
        step = _RecordingAction("init")

        result = await PlatformInitWorkflow(
            [step],
            pre_apply_guard=guard,
            progress=progress,
        ).run()

        self.assertEqual(["preflight"], guard.calls)
        self.assertEqual(["init"], step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(
            ("platform:init:preflight", "init"),
            tuple(item.target_id for item in result.verification_results),
        )
        self.assertEqual(
            (VerificationStatus.VERIFIED, VerificationStatus.VERIFIED),
            tuple(item.status for item in result.verification_results),
        )
        self.assertEqual(
            [
                ("pre_apply", "pre-apply guard", "started", "pending"),
                ("pre_apply", "pre-apply guard", "verified", "verified"),
                ("apply", "apply", "started", "pending"),
                ("apply", "apply", "completed", "completed"),
                ("verify", "verify", "started", "pending"),
                ("verify", "verify", "verified", "verified"),
                ("platform", "workflow completed", "completed", "completed"),
            ],
            progress.summary(),
        )

    async def test_reset_refuses_missing_or_wrong_confirmation_before_running_steps(self):
        destructive_step = _ForbiddenAction()
        workflow = PlatformResetWorkflow([destructive_step])

        missing_result = await workflow.run()
        wrong_result = await workflow.run("wrong")

        self.assertEqual(PlatformWorkflowStatus.REFUSED, missing_result.status)
        self.assertEqual(PlatformWorkflowStatus.REFUSED, wrong_result.status)
        self.assertFalse(missing_result.executed)
        self.assertFalse(wrong_result.executed)

    async def test_destroy_refuses_missing_or_wrong_confirmation_before_running_steps(self):
        destructive_step = _ForbiddenAction()
        workflow = PlatformDestroyWorkflow([destructive_step])

        missing_result = await workflow.run()
        wrong_result = await workflow.run("wrong")

        self.assertEqual(PlatformWorkflowStatus.REFUSED, missing_result.status)
        self.assertEqual(PlatformWorkflowStatus.REFUSED, wrong_result.status)
        self.assertFalse(missing_result.executed)
        self.assertFalse(wrong_result.executed)

    async def test_reset_and_destroy_confirmations_are_not_cross_accepted(self):
        reset_result = await PlatformResetWorkflow([_ForbiddenAction()]).run(
            DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION
        )
        destroy_result = await PlatformDestroyWorkflow([_ForbiddenAction()]).run(
            RESET_TINY_SWARM_PLATFORM_CONFIRMATION
        )

        self.assertEqual(PlatformWorkflowStatus.REFUSED, reset_result.status)
        self.assertEqual(PlatformWorkflowStatus.REFUSED, destroy_result.status)
        self.assertFalse(reset_result.executed)
        self.assertFalse(destroy_result.executed)

    async def test_reset_runs_steps_only_after_exact_confirmation(self):
        destructive_step = _RecordingAction("reset")

        result = await PlatformResetWorkflow([destructive_step]).run(
            RESET_TINY_SWARM_PLATFORM_CONFIRMATION
        )

        self.assertEqual(["reset"], destructive_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)

    async def test_destroy_runs_steps_only_after_exact_confirmation(self):
        destructive_step = _RecordingAction("destroy")

        result = await PlatformDestroyWorkflow([destructive_step]).run(
            DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION
        )

        self.assertEqual(["destroy"], destructive_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)

    async def test_confirmed_reset_without_steps_is_blocked_until_policy_exists(self):
        result = await PlatformResetWorkflow().run(RESET_TINY_SWARM_PLATFORM_CONFIRMATION)

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)

    async def test_mutating_workflow_without_verify_spec_is_blocked_before_apply(self):
        apply_only_step = _ApplyOnlyAction("apply-only")
        later_step = _RecordingAction("later")

        result = await PlatformInitWorkflow([apply_only_step, later_step]).run()

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertEqual([], apply_only_step.calls)
        self.assertEqual([], later_step.calls)
        self.assertEqual(VerificationStatus.BLOCKED, result.verification_results[0].status)
        self.assertIn(
            "command-backed verification is not configured",
            result.message,
        )
        self.assertEqual(
            "command-backed verification is not configured",
            result.verification_results[0].evidence["reason"],
        )

    async def test_pre_apply_verification_blocks_before_apply_and_later_steps(self):
        blocked_step = _PreApplyAction(
            "pre-apply-blocked",
            VerificationResult(
                target_id="pre-apply-blocked",
                status=VerificationStatus.BLOCKED,
                message="Command-backed verification is not configured.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "command_backed_verification_missing",
                },
            ),
        )
        later_step = _RecordingAction("later")

        result = await PlatformInitWorkflow([blocked_step, later_step]).run()

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertEqual([], blocked_step.calls)
        self.assertEqual([], blocked_step.verifications)
        self.assertEqual([], later_step.calls)
        self.assertEqual(VerificationStatus.BLOCKED, result.verification_results[0].status)
        self.assertEqual(
            "command_backed_verification_missing",
            result.verification_results[0].evidence["reason"],
        )

    async def test_pre_apply_verified_step_blocks_after_apply_without_observed_verification(self):
        step = _PreApplyAction(
            "pre-apply-verified",
            VerificationResult(
                target_id="pre-apply-verified",
                status=VerificationStatus.VERIFIED,
                message="Command-backed verification contract is configured.",
                evidence={"phase": "pre_apply"},
            ),
        )

        result = await PlatformInitWorkflow([step]).run()

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertEqual(["pre-apply-verified"], step.calls)
        self.assertEqual(
            ("pre_apply", "verify"),
            tuple(item.evidence["phase"] for item in result.verification_results),
        )
        self.assertEqual("Verification evidence is missing.", result.verification_results[1].message)

    async def test_verification_result_step_records_provider_lifecycle_result(self):
        progress = _RecordingProgress()
        step = _VerificationResultAction(
            VerificationResult(
                target_id="platform:node:swarm-manager",
                status=VerificationStatus.VERIFIED,
                message="Provider lifecycle reached the desired state.",
                evidence={
                    "phase": "verify",
                    "classification": "verified",
                    "provider": "lxc_native",
                    "node": "swarm-manager",
                    "backend": "incus",
                },
            )
        )

        result = await PlatformInitWorkflow([step], progress=progress).run()

        self.assertEqual(["platform:node:swarm-manager"], step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertEqual("platform:node:swarm-manager", result.verification_results[0].target_id)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual(
            [
                ("apply", "apply", "started", "pending"),
                ("apply", "apply", "completed", "completed"),
                ("verify", "direct verification", "verified", "verified"),
                ("platform", "workflow completed", "completed", "completed"),
            ],
            progress.summary(),
        )

    async def test_blocked_verification_result_step_stops_before_later_steps(self):
        progress = _RecordingProgress()
        blocked_step = _VerificationResultAction(
            VerificationResult(
                target_id="platform:node:swarm-manager",
                status=VerificationStatus.BLOCKED,
                message="Provider lifecycle is blocked before mutation.",
                evidence={
                    "phase": "pre_apply",
                    "classification": "live_mutation_consent_missing",
                    "provider": "lxc_native",
                    "node": "swarm-manager",
                },
            )
        )
        later_step = _RecordingAction("later")

        result = await PlatformInitWorkflow(
            [blocked_step, later_step],
            progress=progress,
        ).run()

        self.assertEqual(["platform:node:swarm-manager"], blocked_step.calls)
        self.assertEqual([], later_step.calls)
        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertEqual("platform:node:swarm-manager", result.verification_results[0].target_id)
        self.assertEqual(
            [
                ("apply", "apply", "started", "pending"),
                ("apply", "apply", "completed", "completed"),
                ("pre_apply", "direct verification", "blocked", "blocked"),
                ("platform", "workflow stopped", "blocked", "blocked"),
            ],
            progress.summary(),
        )

    async def test_pre_apply_verified_step_completes_with_observed_verification(self):
        step = _PreApplyVerifiableAction(
            "pre-apply-verified",
            VerificationResult(
                target_id="pre-apply-verified",
                status=VerificationStatus.VERIFIED,
                message="Command-backed verification contract is configured.",
                evidence={"phase": "pre_apply"},
            ),
        )

        result = await PlatformInitWorkflow([step]).run()

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(["pre-apply-verified"], step.calls)
        self.assertEqual(["pre-apply-verified"], step.verifications)
        self.assertEqual(
            ("pre_apply", "verify"),
            tuple(item.evidence["phase"] for item in result.verification_results),
        )

    async def test_failed_apply_stops_workflow_before_verify_and_later_steps(self):
        progress = _RecordingProgress()
        failing_step = _FailingApplyAction("failing")
        later_step = _RecordingAction("later")

        result = await PlatformInitWorkflow(
            [failing_step, later_step],
            progress=progress,
        ).run()

        self.assertEqual(PlatformWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(["failing"], failing_step.calls)
        self.assertEqual([], failing_step.verifications)
        self.assertEqual([], later_step.calls)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.verification_results[0].status)
        self.assertEqual(
            [
                ("apply", "apply", "started", "pending"),
                ("apply", "apply result", "failed_to_apply", "failed_to_apply"),
                ("platform", "workflow stopped", "failed_to_apply", "failed_to_apply"),
            ],
            progress.summary(),
        )

    async def test_failed_apply_result_is_not_treated_as_success(self):
        progress = _RecordingProgress()
        failing_step = _FailedApplyResultAction("failed-result")

        result = await PlatformInitWorkflow([failing_step], progress=progress).run()

        self.assertEqual(PlatformWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.verification_results[0].status)
        self.assertEqual([], failing_step.verifications)
        self.assertEqual(
            [
                ("apply", "apply", "started", "pending"),
                ("apply", "apply result", "failed_to_apply", "failed_to_apply"),
                ("platform", "workflow stopped", "failed_to_apply", "failed_to_apply"),
            ],
            progress.summary(),
        )

    async def test_failed_verify_stops_before_later_apply_steps(self):
        progress = _RecordingProgress()
        failing_verify = _FailingVerifyAction("verify-fails")
        later_step = _RecordingAction("later")

        result = await PlatformInitWorkflow(
            [failing_verify, later_step],
            progress=progress,
        ).run()

        self.assertEqual(PlatformWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(["verify-fails"], failing_verify.calls)
        self.assertEqual(["verify-fails"], failing_verify.verifications)
        self.assertEqual([], later_step.calls)
        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.verification_results[0].status)
        self.assertEqual(
            [
                ("apply", "apply", "started", "pending"),
                ("apply", "apply", "completed", "completed"),
                ("verify", "verify", "started", "pending"),
                ("verify", "verify", "failed_to_verify", "failed_to_verify"),
                ("platform", "workflow stopped", "failed_to_verify", "failed_to_verify"),
            ],
            progress.summary(),
        )

    async def test_lxc_aggregate_direct_verification_progress_uses_safe_counts(self):
        progress = _RecordingProgress()
        step = _VerificationResultAction(
            VerificationResult(
                target_id="platform:init:lxc-container-runtime",
                status=VerificationStatus.VERIFIED,
                message="Container runtime phase reached a terminal state.",
                evidence={
                    "phase": "verify",
                    "classification": "container_runtime_verified",
                    "result_count": "2",
                    "verified_count": "2",
                    "blocked_count": "0",
                    "failed_apply_count": "0",
                    "failed_verify_count": "0",
                    "node": "swarm-manager",
                },
            )
        )

        result = await PlatformInitWorkflow([step], progress=progress).run()

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        direct_event = progress.events[2]
        self.assertEqual("direct verification", direct_event.step)
        self.assertIn("result_count=2", direct_event.safe_message)
        self.assertIn("verified_count=2", direct_event.safe_message)
        self.assertIn("blocked_count=0", direct_event.safe_message)
        self.assertIn("failed_apply_count=0", direct_event.safe_message)
        self.assertIn("failed_verify_count=0", direct_event.safe_message)
        self.assertNotIn("swarm-manager", direct_event.safe_message)
        self.assertNotIn("incus", direct_event.safe_message)
        self.assertNotIn("container_runtime_verified", direct_event.safe_message)

    async def test_missing_verify_evidence_blocks_continuation(self):
        progress = _RecordingProgress()
        missing_evidence = _MissingEvidenceAction("missing-evidence")
        later_step = _RecordingAction("later")

        result = await PlatformInitWorkflow(
            [missing_evidence, later_step],
            progress=progress,
        ).run()

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertEqual(["missing-evidence"], missing_evidence.calls)
        self.assertEqual(["missing-evidence"], missing_evidence.verifications)
        self.assertEqual([], later_step.calls)
        self.assertEqual(
            [
                ("apply", "apply", "started", "pending"),
                ("apply", "apply", "completed", "completed"),
                ("verify", "verify", "started", "pending"),
                ("verify", "verify", "blocked", "blocked"),
                ("platform", "workflow stopped", "blocked", "blocked"),
            ],
            progress.summary(),
        )

    async def test_verified_steps_append_evidence_when_repository_is_configured(self):
        evidence_repository = _RecordingEvidenceRepository()
        step = _RecordingAction("init")

        result = await PlatformInitWorkflow(
            [step],
            verification_evidence_repository=evidence_repository,
        ).run()

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(("init",), tuple(item.target_id for item in evidence_repository.results))
        self.assertEqual(("init",), tuple(item.target_id for item in result.verification_results))

    async def test_missing_verify_evidence_appends_blocked_result_when_repository_is_configured(self):
        evidence_repository = _RecordingEvidenceRepository()
        missing_evidence = _MissingEvidenceAction("missing-evidence")

        result = await PlatformInitWorkflow(
            [missing_evidence],
            verification_evidence_repository=evidence_repository,
        ).run()

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertEqual(
            (VerificationStatus.BLOCKED,),
            tuple(item.status for item in evidence_repository.results),
        )


class _RecordingAction:
    def __init__(self, name: str):
        self.name = name
        self.calls: list[str] = []
        self.verifications: list[str] = []
        self.verification_target_id = name

    async def run(self) -> object:
        await async_checkpoint()
        self.calls.append(self.name)
        return self.name

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        self.verifications.append(self.name)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message="Step verified.",
            evidence={"phase": "verify"},
        )


class _PreApplyAction:
    def __init__(self, name: str, pre_apply_result: VerificationResult):
        self.name = name
        self.calls: list[str] = []
        self.verifications: list[str] = []
        self.verification_target_id = name
        self.pre_apply_result = pre_apply_result

    async def run(self) -> object:
        await async_checkpoint()
        self.calls.append(self.name)
        return self.name

    def verify_pre_apply(self) -> VerificationResult:
        return self.pre_apply_result

    async def verify(self) -> object:
        await async_checkpoint()
        return None


class _PreApplyVerifiableAction(_PreApplyAction):
    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        self.verifications.append(self.name)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message="Step verified.",
            evidence={"phase": "verify"},
        )


class _ApplyOnlyAction:
    def __init__(self, name: str):
        self.name = name
        self.calls: list[str] = []

    async def run(self) -> object:
        await async_checkpoint()
        self.calls.append(self.name)
        return self.name


class _FailingApplyAction(_RecordingAction):
    async def run(self) -> object:
        await async_checkpoint()
        self.calls.append(self.name)
        raise RuntimeError("apply failed")


class _FailedApplyResultAction(_RecordingAction):
    async def run(self) -> object:
        await async_checkpoint()
        self.calls.append(self.name)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_APPLY,
            message="Apply reported failure.",
            evidence={"phase": "apply"},
        )


class _FailingVerifyAction(_RecordingAction):
    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        self.verifications.append(self.name)
        raise RuntimeError("verify failed")


class _MissingEvidenceAction:
    def __init__(self, name: str):
        self.name = name
        self.calls: list[str] = []
        self.verifications: list[str] = []
        self.verification_target_id = name

    async def run(self) -> object:
        await async_checkpoint()
        self.calls.append(self.name)
        return self.name

    async def verify(self) -> object:
        await async_checkpoint()
        self.verifications.append(self.name)
        return None


class _ForbiddenAction:
    async def run(self) -> object:
        await async_checkpoint()
        raise AssertionError("destructive step must not run without confirmation")


class _PreflightAction:
    def __init__(self, result: PreflightResult):
        self.result = result
        self.calls: list[str] = []

    async def run(self) -> PreflightResult:
        await async_checkpoint()
        self.calls.append("preflight")
        return self.result


class _ProviderGuardAction:
    def __init__(self, result: VerificationResult):
        self.result = result
        self.calls: list[str] = []

    async def run(self) -> VerificationResult:
        await async_checkpoint()
        self.calls.append("provider")
        return self.result


class _VerificationResultAction:
    returns_verification_result = True

    def __init__(self, result: VerificationResult):
        self.result = result
        self.verification_target_id = result.target_id
        self.calls: list[str] = []

    async def run(self) -> VerificationResult:
        await async_checkpoint()
        self.calls.append(self.verification_target_id)
        return self.result


class _RecordingEvidenceRepository:
    def __init__(self) -> None:
        self.results: list[VerificationResult] = []

    def append(self, result: VerificationResult) -> None:
        self.results.append(result)

    def list_all(self) -> tuple[VerificationResult, ...]:
        return tuple(self.results)


class _RecordingProgress(PortWorkflowProgress):
    def __init__(self) -> None:
        self.events: list[WorkflowProgressEvent] = []

    def report(self, event: WorkflowProgressEvent) -> None:
        self.events.append(event)

    def summary(self) -> list[tuple[str, str, str, str]]:
        return [
            (event.phase, event.step, event.status, event.result)
            for event in self.events
        ]


class _RecordingMethodTrace(PortMethodTrace):
    def __init__(self) -> None:
        self.events: list[MethodTraceEvent] = []

    def report(self, event: MethodTraceEvent) -> None:
        self.events.append(event)

    def summary(self) -> list[tuple[str, str, str, str | None, str | None]]:
        return [
            (
                event.class_name,
                event.method_name,
                event.status,
                event.safe_result,
                event.exception_type,
            )
            for event in self.events
        ]


if __name__ == "__main__":
    unittest.main()

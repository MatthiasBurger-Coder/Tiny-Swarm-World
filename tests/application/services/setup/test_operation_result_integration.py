"""Cross-family result propagation using local fake ports only."""
import asyncio
from types import SimpleNamespace
import unittest

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome, OperationResult
from tiny_swarm_world.application.services.artifacts.workflows import ArtifactPrepareWorkflow, ArtifactWorkflowKind, ArtifactWorkflowResult, ArtifactWorkflowStatus
from tiny_swarm_world.application.services.deployment.workflows import DeploymentApplyWorkflow, DeploymentVerifyWorkflow, DeploymentWorkflowStatus, ValidationPlan
from tiny_swarm_world.application.services.shared.operation_results import failures_to_evidence
from tiny_swarm_world.application.services.setup.workflow import SetupWorkflow, SetupWorkflowPhase, SetupWorkflowStatus
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.preflight import InstallationPhase, InstallationPlan, LiveConsent, PreflightCheck, PreflightCategory, PreflightSeverity, PreflightStatus, PreflightResult


def consent():
    return LiveConsent(live_flag=True, confirmed=True)


def verified():
    return VerificationResult("test:target", VerificationStatus.VERIFIED, "Ready")


def step(error=None):
    def run():
        if error:
            raise error
    return SimpleNamespace(run=run, verify=verified)


class OperationResultIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_verification_exception_precedes_companion_and_fallback_retains_origin(self):
        caught = OperationFailure.for_cause("service.request", "nexus", "request_failed")
        companion = OperationFailure.for_cause("service.ready", "nexus", "dependency_unavailable")
        async def failing_verification():
            raise OperationError(caught)
        for workflow in (ArtifactPrepareWorkflow, DeploymentApplyWorkflow):
            with self.subTest(workflow=workflow.__name__):
                component = SimpleNamespace(run=lambda: None, verify=failing_verification, operation_failure=companion)
                result = await workflow((component,)).run()
                self.assertEqual((caught,), result.operation_result.failures)
                component.verify = lambda: VerificationResult("test:target", VerificationStatus.FAILED_TO_VERIFY, "Unavailable")
                result = await workflow((component,)).run()
                self.assertEqual((companion,), result.operation_result.failures)


    async def test_artifact_failure_origin_survives_setup_and_stops_dependents(self):
        failure = OperationFailure.for_cause("image.push", "image_runtime", "process_timeout")
        workflow = ArtifactPrepareWorkflow((step(), step(OperationError(failure))))
        calls = []
        result = await SetupWorkflow((SetupWorkflowPhase("artifacts", workflow.run), SetupWorkflowPhase("later", lambda: calls.append("later"))), live_consent=consent()).run()
        self.assertEqual([], calls)
        self.assertEqual(OperationOutcome.PARTIAL, result.operation_result.outcome)
        self.assertEqual((failure,), result.operation_result.failures)
        self.assertEqual(("setup.phase.1.artifacts.prepare.step.1.verify",), result.operation_result.completed_operations)
        self.assertIn("setup.phase.2", result.operation_result.pending_operations)
        self.assertEqual(("setup.phase.1.artifacts.prepare.step.2.apply",), result.operation_result.uncertain_operations)

    async def test_blocked_after_confirmed_work_preserves_partial_and_stops_mutation(self):
        for workflow in (ArtifactPrepareWorkflow, DeploymentApplyWorkflow):
            calls = []
            blocked = SimpleNamespace(run=lambda: calls.append("blocked"), verify=lambda: VerificationResult("test:blocked", VerificationStatus.BLOCKED, "Blocked"))
            later = SimpleNamespace(run=lambda: calls.append("later"), verify=verified)
            result = await workflow((step(), blocked, later)).run()
            self.assertEqual(["blocked"], calls)
            self.assertEqual("blocked", result.status.value)
            self.assertEqual(OperationOutcome.PARTIAL, result.operation_result.outcome)
            self.assertEqual(1, len(result.operation_result.completed_operations))
            self.assertEqual(2, len(result.operation_result.pending_operations))
            self.assertEqual(1, len(result.operation_result.uncertain_operations))

    async def test_first_failed_attempt_is_uncertain_not_partial(self):
        for workflow in (ArtifactPrepareWorkflow, DeploymentApplyWorkflow):
            result = await workflow((step(RuntimeError("private-marker")),)).run()
            self.assertEqual(OperationOutcome.FAILED, result.operation_result.outcome)
            self.assertEqual("unexpected_failure", result.operation_result.failures[0].cause)
            self.assertEqual((), result.operation_result.completed_operations)
            self.assertTrue(result.operation_result.uncertain_operations)
            self.assertNotIn("private-marker", repr(result.operation_result))

    async def test_preparation_return_confirms_work_but_failed_preparation_is_uncertain(self):
        result = await DeploymentApplyWorkflow((step(),), pre_apply_steps=(SimpleNamespace(run=lambda: None),)).run()
        self.assertEqual(OperationOutcome.SUCCESS, result.operation_result.outcome)
        self.assertIn("deployment.apply.prepare.1.apply", result.operation_result.completed_operations)
        failure = OperationFailure.for_cause("storage.write", "storage", "filesystem_error")
        failed = await DeploymentApplyWorkflow((step(),), pre_apply_steps=(step(OperationError(failure)),)).run()
        self.assertEqual((failure,), failed.operation_result.failures)
        self.assertEqual(("deployment.apply.prepare.1.apply",), failed.operation_result.uncertain_operations)

    async def test_partial_preparation_stops_deployment_before_apply(self):
        failure = OperationFailure.for_cause("storage.write", "storage", "filesystem_error")
        partial = OperationResult(OperationOutcome.PARTIAL, (failure,), ("saved",), ("remaining",))
        calls = []
        preparation = SimpleNamespace(run=lambda: None, operation_result=partial)
        result = await DeploymentApplyWorkflow((SimpleNamespace(run=lambda: calls.append("apply"), verify=verified),), pre_apply_steps=(preparation,)).run()
        self.assertEqual([], calls)
        self.assertEqual(OperationOutcome.PARTIAL, result.operation_result.outcome)
        self.assertEqual((failure,), result.operation_result.failures)

    async def test_legacy_completed_result_remains_compatible(self):
        legacy = ArtifactWorkflowResult(ArtifactWorkflowKind.PREPARE, ArtifactWorkflowStatus.COMPLETED, "Done", "Verified")
        result = await SetupWorkflow((SetupWorkflowPhase("legacy", lambda: legacy),), live_consent=consent()).run()
        self.assertEqual(SetupWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(OperationOutcome.SUCCESS, result.operation_result.outcome)

    async def test_contradictory_preflight_evidence_stops_setup(self):
        check = PreflightCheck("CHECK", PreflightCategory.DEPENDENCY, PreflightStatus.PASSED, PreflightSeverity.MANDATORY, "Ready", "", {"failure_cause": "process_timeout"})
        calls = []
        result = await SetupWorkflow((SetupWorkflowPhase("preflight", lambda: PreflightResult((check,))), SetupWorkflowPhase("later", lambda: calls.append("later"))), live_consent=consent()).run()
        self.assertEqual([], calls)
        self.assertNotEqual(SetupWorkflowStatus.COMPLETED, result.status)
        self.assertEqual("process_timeout", result.operation_result.failures[0].cause)

    async def test_timeouts_retain_prior_confirmed_work(self):
        async def hanging():
            await asyncio.Event().wait()
        deployment = await DeploymentVerifyWorkflow((step(), SimpleNamespace(verify=hanging)), timeout_seconds=0.2).run()
        self.assertEqual(DeploymentWorkflowStatus.TIMED_OUT, deployment.status)
        self.assertEqual(OperationOutcome.PARTIAL, deployment.operation_result.outcome)
        self.assertEqual(("deployment.verify.step.1.verify",), deployment.operation_result.completed_operations)
        setup = await SetupWorkflow((SetupWorkflowPhase("done", lambda: {"status": "completed"}), SetupWorkflowPhase("active", hanging), SetupWorkflowPhase("queued", hanging)), live_consent=consent(), timeout_seconds=0.2).run()
        self.assertEqual(OperationOutcome.PARTIAL, setup.operation_result.outcome)
        self.assertEqual(("setup.phase.1",), setup.operation_result.completed_operations)
        self.assertEqual(("setup.phase.2",), setup.operation_result.uncertain_operations)
        self.assertEqual(("setup.phase.3",), setup.operation_result.pending_operations)

    async def test_cancellation_propagates(self):
        async def cancelled():
            raise asyncio.CancelledError
        for workflow in (ArtifactPrepareWorkflow((SimpleNamespace(run=cancelled, verify=verified),)), DeploymentApplyWorkflow((SimpleNamespace(run=cancelled, verify=verified),)), SetupWorkflow((SetupWorkflowPhase("cancel", cancelled),), live_consent=consent())):
            with self.assertRaises(asyncio.CancelledError):
                await workflow.run()

    async def test_concurrent_aggregation_uses_plan_order(self):
        second_finished = asyncio.Event()
        async def first():
            await second_finished.wait()
            return {"status": "completed"}
        async def second():
            second_finished.set()
            return {"status": "completed"}
        plan = InstallationPlan(phases=(InstallationPhase("first", 1, workflow_phase_names=("first",), parallel_group="workers"), InstallationPhase("second", 1, workflow_phase_names=("second",), parallel_group="workers")))
        result = await SetupWorkflow((SetupWorkflowPhase("first", first), SetupWorkflowPhase("second", second)), installation_plan=plan, max_concurrency=2, live_consent=consent()).run()
        self.assertEqual(OperationOutcome.SUCCESS, result.operation_result.outcome)
        self.assertEqual(("setup.phase.1", "setup.phase.2"), result.operation_result.completed_operations)

    async def test_restored_child_history_is_nested_and_parent_tracks_current_failure(self):
        original = OperationFailure.for_cause("platform.update", "platform", "process_timeout")
        restored = OperationResult(OperationOutcome.ROLLED_BACK, (original,), ("restored",), rollback_verified=True)
        child = ArtifactWorkflowResult(ArtifactWorkflowKind.PREPARE, ArtifactWorkflowStatus.COMPLETED, "Restored", "Verified", operation_result=restored)
        result = await SetupWorkflow((SetupWorkflowPhase("recover", lambda: child),), live_consent=consent()).run()
        self.assertEqual(OperationOutcome.SUCCESS, result.operation_result.outcome)
        self.assertFalse(result.operation_result.rollback_verified)
        self.assertEqual((original,), result.phase_results[0].operation_result.failures)
        active = OperationFailure.for_cause("service.request", "portainer", "request_failed")
        def fail():
            raise OperationError(active)
        result = await SetupWorkflow((SetupWorkflowPhase("recover", lambda: child), SetupWorkflowPhase("next", fail)), live_consent=consent()).run()
        self.assertEqual(OperationOutcome.PARTIAL, result.operation_result.outcome)
        self.assertEqual((active,), result.operation_result.failures)
        self.assertEqual((original,), result.phase_results[0].operation_result.failures)

    async def test_untrusted_exception_attributes_are_redacted(self):
        error = RuntimeError("private-value-4827")
        error.diagnostic = "private-value-4827"
        error.operator_action = "private-value-4827"
        error.operation = "private-value-4827"
        error.reason = "private-value-4827"
        error.status_code = "private-value-4827"
        for workflow in (ArtifactPrepareWorkflow, DeploymentApplyWorkflow):
            with self.assertLogs(workflow.__name__, level="ERROR") as logs:
                result = await workflow((step(error),)).run()
            self.assertNotIn("private-value-4827", repr(result.to_dict()))
            self.assertNotIn("private-value-4827", repr(logs.output))

    def test_validation_preserves_declared_indexed_origin(self):
        failure = OperationFailure.for_cause("service.request", "portainer", "request_failed")
        item = VerificationResult("test:bad", VerificationStatus.FAILED_TO_VERIFY, "Failed", failures_to_evidence((failure,)))
        result = ValidationPlan("plan", ("test:bad",)).evaluate((item,))
        self.assertEqual((failure,), result.operation_result.failures)

    def test_validation_rejects_failure_evidence_and_retains_other_target(self):
        evidence = {"replicas": "1/1", "required_services": "service", "stack_name": "stack"}
        good = VerificationResult("test:good", VerificationStatus.VERIFIED, "Ready", evidence)
        bad = VerificationResult("test:bad", VerificationStatus.VERIFIED, "Ready", {**evidence, "failure_cause": "process_timeout"})
        result = ValidationPlan("plan", ("test:good", "test:bad")).evaluate((good, bad))
        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(OperationOutcome.PARTIAL, result.operation_result.outcome)
        self.assertEqual(("deployment.validation.target.1",), result.operation_result.completed_operations)

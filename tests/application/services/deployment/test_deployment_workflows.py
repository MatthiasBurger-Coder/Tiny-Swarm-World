import unittest
from types import SimpleNamespace
from tests.support.async_helpers import async_checkpoint
from tests.support.sonar_safe_literals import operator_credential, sensitive_assignment

from tiny_swarm_world.application.services.deployment.ensure_portainer_admin_access import (
    EnsurePortainerAdminAccess,
)
from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortainerAdminInitializationRejected,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentApplyWorkflow,
    DeploymentVerifyWorkflow,
    DeploymentWorkflowKind,
    DeploymentWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class TestDeploymentWorkflows(unittest.IsolatedAsyncioTestCase):
    async def test_apply_workflow_is_explicitly_blocked(self):
        result = await DeploymentApplyWorkflow().run()

        self.assertEqual(DeploymentWorkflowKind.APPLY, result.kind)
        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("deployment apply", result.workflow_name)
        self.assertIn("stack deployment contracts", result.message)
        self.assertIn("Portainer stack changes", result.reason)
        self.assertEqual("blocked", result.to_dict()["status"])

    async def test_apply_workflow_blocks_configured_step_without_verify_after_apply(self):
        step = SimpleNamespace(calls=0)

        async def run_step() -> None:
            await async_checkpoint()
            step.calls += 1

        step.run = run_step

        result = await DeploymentApplyWorkflow((step,)).run()

        self.assertEqual(DeploymentWorkflowKind.APPLY, result.kind)
        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(0, step.calls)
        self.assertIn("verify-after-apply", result.reason)

    async def test_apply_workflow_completes_only_after_verified_evidence(self):
        class VerifiedStep:
            verification_target_id = "deployment:portainer-stack"

            def __init__(self) -> None:
                self.calls = 0

            async def run(self) -> None:
                await async_checkpoint()
                self.calls += 1

            async def verify(self) -> VerificationResult:
                await async_checkpoint()
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.VERIFIED,
                    message="Portainer stack verified.",
                    evidence={"phase": "verify"},
                )

        step = VerifiedStep()

        result = await DeploymentApplyWorkflow((step,)).run()

        self.assertEqual(DeploymentWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(1, step.calls)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual(
            "verified",
            result.to_dict()["verification_results"][0]["status"],
        )

    async def test_apply_workflow_reports_apply_failures_without_raw_payloads(self):
        class FailingStep:
            verification_target_id = "deployment:portainer-stack"

            async def run(self) -> None:
                await async_checkpoint()
                raise RuntimeError("contains sensitive response body")

            async def verify(self) -> VerificationResult:
                await async_checkpoint()
                raise AssertionError("verify must not run after failed apply")

        result = await DeploymentApplyWorkflow((FailingStep(),)).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertTrue(result.executed)
        self.assertEqual("apply failed with RuntimeError", result.reason)
        self.assertNotIn("sensitive response", result.reason)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.verification_results[0].status)

    async def test_apply_workflow_preserves_actionable_safe_apply_failure_summary(self):
        class FailingStep:
            verification_target_id = "deployment:jenkins-stack"

            async def run(self) -> None:
                await async_checkpoint()
                raise RuntimeError("Failed to create Portainer stack 'jenkins'. HTTP 500.")

            async def verify(self) -> VerificationResult:
                await async_checkpoint()
                raise AssertionError("verify must not run after failed apply")

        with self.assertLogs("DeploymentApplyWorkflow", level="ERROR") as captured:
            result = await DeploymentApplyWorkflow((FailingStep(),)).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertIn(
            "RuntimeError. Failed to create Portainer stack 'jenkins'. HTTP 500.",
            captured.output[0],
        )
        self.assertIn(
            "RuntimeError. Failed to create Portainer stack 'jenkins'. HTTP 500.",
            result.verification_results[0].message,
        )

    async def test_apply_workflow_reports_portainer_admin_rejection_with_safe_diagnostics(self):
        class RejectedPortainerAdminStep:
            verification_target_id = "deployment:portainer-admin-access"

            async def run(self) -> None:
                await async_checkpoint()
                raise PortainerAdminInitializationRejected(
                    f"HTTP 409 {sensitive_assignment()}",
                    status_code=409,
                )

            async def verify(self) -> VerificationResult:
                await async_checkpoint()
                raise AssertionError("verify must not run after failed apply")

        with self.assertLogs("DeploymentApplyWorkflow", level="ERROR") as captured:
            result = await DeploymentApplyWorkflow(
                (RejectedPortainerAdminStep(),),
                kind=DeploymentWorkflowKind.BOOTSTRAP,
            ).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertIn("PortainerAdminInitializationRejected HTTP 409", result.reason)
        self.assertNotIn(sensitive_assignment(), result.reason)
        self.assertIn("PortainerAdminInitializationRejected HTTP 409", captured.output[0])
        self.assertNotIn(sensitive_assignment(), captured.output[0])
        verification = result.verification_results[0]
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, verification.status)
        self.assertEqual("http_status_409", verification.evidence["diagnostic"])
        self.assertIn("Portainer state", verification.evidence["operator_action"])

    async def test_apply_workflow_blocks_before_running_steps_when_pre_apply_check_blocks(self):
        pre_apply_check = _BlockedDeploymentCheck("deployment:service-access-external-input")
        step = _OrderedApplyStep("deployment:service-access-stack", VerificationStatus.VERIFIED)

        result = await DeploymentApplyWorkflow(
            (step,),
            pre_apply_checks=(pre_apply_check,),
        ).run()

        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertFalse(step.ran)
        self.assertEqual(
            "pre-apply verification is blocked for deployment:service-access-external-input",
            result.reason,
        )

    async def test_apply_workflow_reports_failed_pre_apply_verification_without_running_steps(self):
        pre_apply_check = _FailedDeploymentCheck("deployment:service-access-external-input")
        step = _OrderedApplyStep("deployment:service-access-stack", VerificationStatus.VERIFIED)

        result = await DeploymentApplyWorkflow(
            (step,),
            pre_apply_checks=(pre_apply_check,),
        ).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertFalse(result.executed)
        self.assertFalse(step.ran)
        self.assertEqual(
            "pre-apply verification failed for deployment:service-access-external-input",
            result.reason,
        )

    async def test_apply_workflow_prepares_external_inputs_before_pre_apply_checks(self):
        pre_apply_step = _PreApplyStep("deployment:service-access-external-input")
        pre_apply_check = _VerifiedDeploymentCheck("deployment:service-access-external-input")
        step = _OrderedApplyStep("deployment:service-access-stack", VerificationStatus.VERIFIED)

        result = await DeploymentApplyWorkflow(
            (step,),
            pre_apply_steps=(pre_apply_step,),
            pre_apply_checks=(pre_apply_check,),
        ).run()

        self.assertEqual(DeploymentWorkflowStatus.COMPLETED, result.status)
        self.assertTrue(pre_apply_step.ran)
        self.assertTrue(step.ran)
        self.assertEqual(
            ("deployment:service-access-external-input", "deployment:service-access-stack"),
            tuple(verification.target_id for verification in result.verification_results),
        )

    async def test_apply_workflow_reports_pre_apply_prepare_failures_without_raw_payloads(self):
        pre_apply_step = _PreApplyStep(
            "deployment:service-access-external-input",
            exception=RuntimeError(sensitive_assignment()),
        )
        pre_apply_check = _VerifiedDeploymentCheck("deployment:service-access-external-input")
        step = _OrderedApplyStep("deployment:service-access-stack", VerificationStatus.VERIFIED)

        result = await DeploymentApplyWorkflow(
            (step,),
            pre_apply_steps=(pre_apply_step,),
            pre_apply_checks=(pre_apply_check,),
        ).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_PREPARE, result.status)
        self.assertTrue(result.executed)
        self.assertFalse(step.ran)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.verification_results[0].status)
        self.assertNotIn(sensitive_assignment(), str(result.to_dict()))

    async def test_apply_workflow_reports_verify_failures(self):
        class FailedVerifyStep:
            verification_target_id = "deployment:portainer-stack"

            async def run(self) -> None:
                await async_checkpoint()
                # Test double; this step only exercises failed verification.
                pass

            async def verify(self) -> VerificationResult:
                await async_checkpoint()
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.FAILED_TO_VERIFY,
                    message="Portainer stack verification failed.",
                    evidence={"phase": "verify"},
                )

        result = await DeploymentApplyWorkflow((FailedVerifyStep(),)).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertTrue(result.executed)
        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.verification_results[0].status)

    async def test_bootstrap_workflow_stops_after_failed_admin_access_verification(self):
        portainer_stack = _OrderedApplyStep("deployment:portainer-stack", VerificationStatus.VERIFIED)
        admin_access = _OrderedApplyStep(
            "deployment:portainer-admin-access",
            VerificationStatus.FAILED_TO_VERIFY,
        )
        nexus_stack = _OrderedApplyStep("deployment:nexus-stack", VerificationStatus.VERIFIED)

        result = await DeploymentApplyWorkflow(
            (portainer_stack, admin_access, nexus_stack),
            kind=DeploymentWorkflowKind.BOOTSTRAP,
        ).run()

        self.assertEqual(DeploymentWorkflowKind.BOOTSTRAP, result.kind)
        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertTrue(portainer_stack.ran)
        self.assertTrue(admin_access.ran)
        self.assertFalse(nexus_stack.ran)
        self.assertEqual("verification failed for deployment:portainer-admin-access", result.reason)

    async def test_apply_workflow_accepts_portainer_admin_access_safe_evidence(self):
        admin_access = EnsurePortainerAdminAccess(
            _AlwaysActivePortainerAdminClient(),
            username="admin",
            password=operator_credential(),
            max_attempts=1,
            wait_seconds=0,
        )

        result = await DeploymentApplyWorkflow(
            (admin_access,),
            kind=DeploymentWorkflowKind.BOOTSTRAP,
        ).run()

        self.assertEqual(DeploymentWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual("active", result.verification_results[0].evidence["access_state"])

    async def test_apply_workflow_stops_later_stacks_when_verification_blocks(self):
        first_step = _OrderedApplyStep("deployment:nexus-stack", VerificationStatus.VERIFIED)
        second_step = _OrderedApplyStep("deployment:jenkins-service-readiness", VerificationStatus.BLOCKED)
        third_step = _OrderedApplyStep("deployment:rabbitmq-stack", VerificationStatus.VERIFIED)

        result = await DeploymentApplyWorkflow((first_step, second_step, third_step)).run()

        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertTrue(result.executed)
        self.assertTrue(first_step.ran)
        self.assertTrue(second_step.ran)
        self.assertFalse(third_step.ran)
        self.assertEqual(2, len(result.verification_results))

    async def test_verify_workflow_is_explicitly_blocked(self):
        result = await DeploymentVerifyWorkflow().run()

        self.assertEqual(DeploymentWorkflowKind.VERIFY, result.kind)
        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("deployment verify", result.workflow_name)
        self.assertIn("stack verification contracts", result.message)
        self.assertIn("observed-state verification", result.reason)
        self.assertEqual("deployment verify", result.to_dict()["workflow"])

    async def test_verify_workflow_completes_after_verified_stack_checks(self):
        check = _VerifiedDeploymentCheck("deployment:nexus-stack")

        result = await DeploymentVerifyWorkflow((check,)).run()

        self.assertEqual(DeploymentWorkflowStatus.COMPLETED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual("deployment:nexus-stack", result.verification_results[0].target_id)

    async def test_verify_workflow_reports_missing_stack_verification(self):
        check = _FailedDeploymentCheck("deployment:jenkins-stack")

        result = await DeploymentVerifyWorkflow((check,)).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("verification failed for deployment:jenkins-stack", result.reason)

    async def test_verify_workflow_reports_blocked_service_readiness(self):
        check = _BlockedDeploymentCheck("deployment:nexus-service-readiness")

        result = await DeploymentVerifyWorkflow((check,)).run()

        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("verification is blocked for deployment:nexus-service-readiness", result.reason)

    async def test_verify_workflow_sanitizes_check_exceptions(self):
        check = _ExceptionDeploymentCheck("deployment:rabbitmq-stack")

        result = await DeploymentVerifyWorkflow((check,)).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertNotIn("secret", result.verification_results[0].message)


class _VerifiedDeploymentCheck:
    def __init__(self, target_id: str):
        self.verification_target_id = target_id

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.VERIFIED)


class _FailedDeploymentCheck:
    def __init__(self, target_id: str):
        self.verification_target_id = target_id

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.FAILED_TO_VERIFY)


class _ExceptionDeploymentCheck:
    def __init__(self, target_id: str):
        self.verification_target_id = target_id

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        raise RuntimeError(sensitive_assignment())


class _BlockedDeploymentCheck:
    def __init__(self, target_id: str):
        self.verification_target_id = target_id

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.BLOCKED)


class _PreApplyStep:
    def __init__(self, target_id: str, exception: Exception | None = None):
        self.verification_target_id = target_id
        self.exception = exception
        self.ran = False

    async def run(self) -> None:
        await async_checkpoint()
        self.ran = True
        if self.exception is not None:
            raise self.exception


class _AlwaysActivePortainerAdminClient:
    def can_authenticate(self, username: str, password: str) -> bool:
        return True

    def initialize_admin_user(self, username: str, password: str) -> None:
        raise AssertionError("active credentials should not require initialization")


class _OrderedApplyStep:
    def __init__(self, target_id: str, verification_status: VerificationStatus):
        self.verification_target_id = target_id
        self.verification_status = verification_status
        self.ran = False

    async def run(self) -> None:
        await async_checkpoint()
        self.ran = True

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, self.verification_status)


def _verification_result(target_id: str, status: VerificationStatus) -> VerificationResult:
    return VerificationResult(
        target_id=target_id,
        status=status,
        message="Deployment stack verification summary.",
        evidence={"phase": "verify"},
    )

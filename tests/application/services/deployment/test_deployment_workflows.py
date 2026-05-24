import unittest
from types import SimpleNamespace

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
                self.calls += 1

            async def verify(self) -> VerificationResult:
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
                raise RuntimeError("contains sensitive response body")

            async def verify(self) -> VerificationResult:
                raise AssertionError("verify must not run after failed apply")

        result = await DeploymentApplyWorkflow((FailingStep(),)).run()

        self.assertEqual(DeploymentWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertTrue(result.executed)
        self.assertEqual("apply failed with RuntimeError", result.reason)
        self.assertNotIn("sensitive response", result.reason)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.verification_results[0].status)

    async def test_apply_workflow_reports_verify_failures(self):
        class FailedVerifyStep:
            verification_target_id = "deployment:portainer-stack"

            async def run(self) -> None:
                pass

            async def verify(self) -> VerificationResult:
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

    async def test_verify_workflow_is_explicitly_blocked(self):
        result = await DeploymentVerifyWorkflow().run()

        self.assertEqual(DeploymentWorkflowKind.VERIFY, result.kind)
        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("deployment verify", result.workflow_name)
        self.assertIn("stack verification contracts", result.message)
        self.assertIn("observed-state verification", result.reason)
        self.assertEqual("deployment verify", result.to_dict()["workflow"])

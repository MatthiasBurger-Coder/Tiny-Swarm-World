import unittest
from tests.support.async_helpers import async_checkpoint
from tests.support.sonar_safe_literals import sensitive_assignment

from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactPrepareWorkflow,
    ArtifactVerifyWorkflow,
    ArtifactWorkflowKind,
    ArtifactWorkflowStatus,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access import (
    NexusAdminAccessRecoveryBlocked,
)


class TestArtifactWorkflows(unittest.IsolatedAsyncioTestCase):
    async def test_prepare_workflow_is_explicitly_blocked(self):
        result = await ArtifactPrepareWorkflow().run()

        self.assertEqual(ArtifactWorkflowKind.PREPARE, result.kind)
        self.assertEqual(ArtifactWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("artifacts prepare", result.workflow_name)
        self.assertIn("artifact preparation contracts", result.message)
        self.assertIn("verified artifact contracts", result.reason)
        self.assertEqual("blocked", result.to_dict()["status"])
        self.assertEqual([], result.to_dict()["verification_results"])

    async def test_verify_workflow_is_explicitly_blocked(self):
        result = await ArtifactVerifyWorkflow().run()

        self.assertEqual(ArtifactWorkflowKind.VERIFY, result.kind)
        self.assertEqual(ArtifactWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("artifacts verify", result.workflow_name)
        self.assertIn("artifact verification contracts", result.message)
        self.assertIn("observed-state verification", result.reason)
        self.assertEqual("artifacts verify", result.to_dict()["workflow"])

    async def test_prepare_workflow_completes_after_step_verification(self):
        step = _VerifiedPrepareStep("artifacts:nexus-docker-hosted-repository")

        result = await ArtifactPrepareWorkflow((step,)).run()

        self.assertEqual(ArtifactWorkflowStatus.COMPLETED, result.status)
        self.assertTrue(result.executed)
        self.assertTrue(step.ran)
        self.assertEqual(1, len(result.verification_results))
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)

    async def test_prepare_workflow_blocks_when_verify_after_prepare_is_missing(self):
        step = _PrepareStepWithoutVerification()

        result = await ArtifactPrepareWorkflow((step,)).run()

        self.assertEqual(ArtifactWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertFalse(step.ran)
        self.assertEqual("verify-after-prepare contract is missing for artifacts prepare", result.reason)
        self.assertEqual(VerificationStatus.BLOCKED, result.verification_results[0].status)

    async def test_prepare_workflow_sanitizes_prepare_failure(self):
        step = _FailingPrepareStep()

        result = await ArtifactPrepareWorkflow((step,)).run()

        self.assertEqual(ArtifactWorkflowStatus.FAILED_TO_PREPARE, result.status)
        self.assertTrue(result.executed)
        self.assertEqual("prepare failed with RuntimeError", result.reason)
        self.assertNotIn("secret", result.reason)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.verification_results[0].status)

    async def test_prepare_workflow_reports_safe_diagnostic_evidence(self):
        step = _DiagnosticFailingPrepareStep()

        result = await ArtifactPrepareWorkflow((step,)).run()

        self.assertEqual(ArtifactWorkflowStatus.FAILED_TO_PREPARE, result.status)
        self.assertIn("initial_admin_value_unavailable", result.reason)
        self.assertEqual("initial_admin_value_unavailable", result.verification_results[0].evidence["diagnostic"])
        self.assertEqual(
            "NexusAdminAccessRecoveryBlocked",
            result.verification_results[0].evidence["failure_class"],
        )
        self.assertEqual(
            "initial_admin_value_unavailable_recovery",
            result.verification_results[0].evidence["operator_action_code"],
        )

    async def test_prepare_workflow_reports_failed_verification(self):
        step = _FailedVerificationPrepareStep()

        result = await ArtifactPrepareWorkflow((step,)).run()

        self.assertEqual(ArtifactWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertTrue(result.executed)
        self.assertEqual("verification failed for artifacts:nexus-maven-proxy-repository", result.reason)

    async def test_verify_workflow_completes_with_verified_checks(self):
        check = _VerifiedCheck("artifacts:nexus-docker-hosted-repository")

        result = await ArtifactVerifyWorkflow((check,)).run()

        self.assertEqual(ArtifactWorkflowStatus.COMPLETED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)

    async def test_verify_workflow_reports_blocked_check(self):
        check = _BlockedCheck("artifacts:nexus-docker-hosted-repository")

        result = await ArtifactVerifyWorkflow((check,)).run()

        self.assertEqual(ArtifactWorkflowStatus.BLOCKED, result.status)
        self.assertEqual("verification is blocked for artifacts:nexus-docker-hosted-repository", result.reason)


class _VerifiedPrepareStep:
    def __init__(self, target_id: str):
        self.verification_target_id = target_id
        self.ran = False

    async def run(self) -> None:
        await async_checkpoint()
        self.ran = True

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.VERIFIED)


class _PrepareStepWithoutVerification:
    verification_target_id = "artifacts:nexus-docker-hosted-repository"

    def __init__(self) -> None:
        self.ran = False

    async def run(self) -> None:
        await async_checkpoint()
        self.ran = True


class _FailingPrepareStep:
    verification_target_id = "artifacts:nexus-docker-hosted-repository"

    async def run(self) -> None:
        await async_checkpoint()
        raise RuntimeError(sensitive_assignment())

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.VERIFIED)


class _DiagnosticFailingPrepareStep:
    verification_target_id = "artifacts:nexus-admin-access"

    async def run(self) -> None:
        await async_checkpoint()
        raise NexusAdminAccessRecoveryBlocked(
            "Could not read Nexus admin password from configured path.",
            diagnostic="initial_admin_value_unavailable",
            operator_action=(
                "Check configured Nexus admin access value or reset existing Nexus "
                "state before rerunning setup."
            ),
        )

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.VERIFIED)


class _FailedVerificationPrepareStep:
    verification_target_id = "artifacts:nexus-maven-proxy-repository"

    async def run(self) -> None:
        await async_checkpoint()
        return None

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.FAILED_TO_VERIFY)


class _VerifiedCheck:
    def __init__(self, target_id: str):
        self.verification_target_id = target_id

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.VERIFIED)


class _BlockedCheck:
    def __init__(self, target_id: str):
        self.verification_target_id = target_id

    async def verify(self) -> VerificationResult:
        await async_checkpoint()
        return _verification_result(self.verification_target_id, VerificationStatus.BLOCKED)


def _verification_result(target_id: str, status: VerificationStatus) -> VerificationResult:
    return VerificationResult(
        target_id=target_id,
        status=status,
        message="Artifact contract verification summary.",
        evidence={"phase": "verify"},
    )

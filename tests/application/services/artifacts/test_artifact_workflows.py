import unittest

from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactPrepareWorkflow,
    ArtifactVerifyWorkflow,
    ArtifactWorkflowKind,
    ArtifactWorkflowStatus,
)


class TestArtifactWorkflows(unittest.IsolatedAsyncioTestCase):
    async def test_prepare_workflow_is_explicitly_blocked(self):
        result = await ArtifactPrepareWorkflow().run()

        self.assertEqual(ArtifactWorkflowKind.PREPARE, result.kind)
        self.assertEqual(ArtifactWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("artifacts prepare", result.workflow_name)
        self.assertIn("artifact preparation contracts", result.message)
        self.assertIn("live registry and Nexus contracts", result.reason)
        self.assertEqual("blocked", result.to_dict()["status"])

    async def test_verify_workflow_is_explicitly_blocked(self):
        result = await ArtifactVerifyWorkflow().run()

        self.assertEqual(ArtifactWorkflowKind.VERIFY, result.kind)
        self.assertEqual(ArtifactWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("artifacts verify", result.workflow_name)
        self.assertIn("artifact verification contracts", result.message)
        self.assertIn("observed-state verification", result.reason)
        self.assertEqual("artifacts verify", result.to_dict()["workflow"])

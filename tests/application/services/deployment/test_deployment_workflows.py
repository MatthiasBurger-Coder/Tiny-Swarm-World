import unittest

from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentApplyWorkflow,
    DeploymentVerifyWorkflow,
    DeploymentWorkflowKind,
    DeploymentWorkflowStatus,
)


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

    async def test_verify_workflow_is_explicitly_blocked(self):
        result = await DeploymentVerifyWorkflow().run()

        self.assertEqual(DeploymentWorkflowKind.VERIFY, result.kind)
        self.assertEqual(DeploymentWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("deployment verify", result.workflow_name)
        self.assertIn("stack verification contracts", result.message)
        self.assertIn("observed-state verification", result.reason)
        self.assertEqual("deployment verify", result.to_dict()["workflow"])

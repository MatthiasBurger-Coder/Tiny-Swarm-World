import unittest

from tiny_swarm_world.application.services.deployment import (
    DeploymentApplyWorkflow,
    DeploymentVerifyWorkflow,
    DeploymentWorkflowKind,
    DeploymentWorkflowResult,
    DeploymentWorkflowStatus,
    EnsureNexusStack,
)
from tiny_swarm_world.application.services.deployment.ensure_nexus_stack import (
    EnsureNexusStack as DeploymentEnsureNexusStack,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentApplyWorkflow as ExistingDeploymentApplyWorkflow,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentVerifyWorkflow as ExistingDeploymentVerifyWorkflow,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentWorkflowKind as ExistingDeploymentWorkflowKind,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentWorkflowResult as ExistingDeploymentWorkflowResult,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentWorkflowStatus as ExistingDeploymentWorkflowStatus,
)


class TestDeploymentServiceExports(unittest.TestCase):
    def test_deployment_namespace_exports_workflow_contracts(self):
        self.assertIs(DeploymentApplyWorkflow, ExistingDeploymentApplyWorkflow)
        self.assertIs(DeploymentVerifyWorkflow, ExistingDeploymentVerifyWorkflow)
        self.assertIs(DeploymentWorkflowKind, ExistingDeploymentWorkflowKind)
        self.assertIs(DeploymentWorkflowResult, ExistingDeploymentWorkflowResult)
        self.assertIs(DeploymentWorkflowStatus, ExistingDeploymentWorkflowStatus)

    def test_deployment_namespace_exports_deployment_stack_service(self):
        self.assertIs(EnsureNexusStack, DeploymentEnsureNexusStack)

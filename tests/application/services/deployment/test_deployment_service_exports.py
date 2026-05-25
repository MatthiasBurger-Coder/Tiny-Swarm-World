import unittest

from tiny_swarm_world.application.services.deployment import (
    DeploymentApplyWorkflow,
    DeploymentVerifyCheck,
    DeploymentVerifyWorkflow,
    DeploymentWorkflowKind,
    DeploymentWorkflowResult,
    DeploymentWorkflowStatus,
    EnsureNexusStack,
    EnsurePortainerAdminAccess,
    EnsurePortainerStack,
    EnsureServiceStack,
    VerifyExternalSwarmInput,
    build_default_service_stack_steps,
)
from tiny_swarm_world.application.services.deployment.ensure_nexus_stack import (
    EnsureNexusStack as DeploymentEnsureNexusStack,
)
from tiny_swarm_world.application.services.deployment.ensure_portainer_stack import (
    EnsurePortainerStack as DeploymentEnsurePortainerStack,
)
from tiny_swarm_world.application.services.deployment.ensure_portainer_admin_access import (
    EnsurePortainerAdminAccess as DeploymentEnsurePortainerAdminAccess,
)
from tiny_swarm_world.application.services.deployment.ensure_service_stack import (
    EnsureServiceStack as DeploymentEnsureServiceStack,
)
from tiny_swarm_world.application.services.deployment.verify_external_swarm_input import (
    VerifyExternalSwarmInput as DeploymentVerifyExternalSwarmInput,
)
from tiny_swarm_world.application.services.deployment.service_stack_plan import (
    build_default_service_stack_steps as existing_build_default_service_stack_steps,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentApplyWorkflow as ExistingDeploymentApplyWorkflow,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentVerifyCheck as ExistingDeploymentVerifyCheck,
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
        self.assertIs(DeploymentVerifyCheck, ExistingDeploymentVerifyCheck)
        self.assertIs(DeploymentVerifyWorkflow, ExistingDeploymentVerifyWorkflow)
        self.assertIs(DeploymentWorkflowKind, ExistingDeploymentWorkflowKind)
        self.assertIs(DeploymentWorkflowResult, ExistingDeploymentWorkflowResult)
        self.assertIs(DeploymentWorkflowStatus, ExistingDeploymentWorkflowStatus)

    def test_deployment_namespace_exports_deployment_stack_service(self):
        self.assertIs(EnsureNexusStack, DeploymentEnsureNexusStack)
        self.assertIs(EnsurePortainerAdminAccess, DeploymentEnsurePortainerAdminAccess)
        self.assertIs(EnsurePortainerStack, DeploymentEnsurePortainerStack)
        self.assertIs(EnsureServiceStack, DeploymentEnsureServiceStack)
        self.assertIs(VerifyExternalSwarmInput, DeploymentVerifyExternalSwarmInput)
        self.assertIs(build_default_service_stack_steps, existing_build_default_service_stack_steps)

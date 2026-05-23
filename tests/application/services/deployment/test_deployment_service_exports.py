import unittest

from tiny_swarm_world.application.services.deployment import EnsureNexusStack
from tiny_swarm_world.application.services.deployment.ensure_nexus_stack import (
    EnsureNexusStack as DeploymentEnsureNexusStack,
)


class TestDeploymentServiceExports(unittest.TestCase):
    def test_deployment_namespace_exports_deployment_stack_service(self):
        self.assertIs(EnsureNexusStack, DeploymentEnsureNexusStack)

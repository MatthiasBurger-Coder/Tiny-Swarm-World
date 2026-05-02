import unittest

from tiny_swarm_world.application.services.deployment import EnsureNexusStack
from tiny_swarm_world.application.services.nexus.ensure_nexus_stack import (
    EnsureNexusStack as ExistingEnsureNexusStack,
)


class TestDeploymentServiceExports(unittest.TestCase):
    def test_deployment_namespace_exports_existing_stack_deployment_service(self):
        self.assertIs(EnsureNexusStack, ExistingEnsureNexusStack)

import unittest

from tiny_swarm_world.application.services.deployment.ensure_nexus_stack import (
    EnsureNexusStack as DeploymentEnsureNexusStack,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_stack import (
    EnsureNexusStack as LegacyEnsureNexusStack,
)


class TestEnsureNexusStackCompatibility(unittest.TestCase):
    def test_legacy_nexus_import_path_reexports_deployment_service(self):
        self.assertIs(LegacyEnsureNexusStack, DeploymentEnsureNexusStack)

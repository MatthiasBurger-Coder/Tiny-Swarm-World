import unittest

import tiny_swarm_world.application.services.artifacts as artifacts
from tiny_swarm_world.application.services.artifacts import (
    EnableNexusAnonymousAccess,
    EnsureNexusAdminAccess,
    NexusBootstrapConfiguration,
    WaitForNexusReady,
)
from tiny_swarm_world.application.services.nexus.enable_nexus_anonymous_access import (
    EnableNexusAnonymousAccess as ExistingEnableNexusAnonymousAccess,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access import (
    EnsureNexusAdminAccess as ExistingEnsureNexusAdminAccess,
)
from tiny_swarm_world.application.services.nexus.nexus_bootstrap_configuration import (
    NexusBootstrapConfiguration as ExistingNexusBootstrapConfiguration,
)
from tiny_swarm_world.application.services.nexus.wait_for_nexus_ready import (
    WaitForNexusReady as ExistingWaitForNexusReady,
)


class TestArtifactServiceExports(unittest.TestCase):
    def test_artifacts_namespace_exports_existing_artifact_services(self):
        self.assertIs(EnableNexusAnonymousAccess, ExistingEnableNexusAnonymousAccess)
        self.assertIs(EnsureNexusAdminAccess, ExistingEnsureNexusAdminAccess)
        self.assertIs(NexusBootstrapConfiguration, ExistingNexusBootstrapConfiguration)
        self.assertIs(WaitForNexusReady, ExistingWaitForNexusReady)

    def test_artifacts_namespace_does_not_export_stack_deployment_service(self):
        self.assertNotIn("EnsureNexusStack", artifacts.__all__)

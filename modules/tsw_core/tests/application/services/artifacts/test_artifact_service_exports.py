import unittest

import tiny_swarm_world.application.services.artifacts as artifacts
from tiny_swarm_world.application.services.artifacts import (
    ArtifactPrepareStep,
    ArtifactPrepareWorkflow,
    ArtifactVerifyCheck,
    ArtifactVerifyWorkflow,
    ArtifactWorkflowKind,
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
    EnableNexusAnonymousAccess,
    EnsureNexusAdminAccess,
    EnsureNexusDockerHostedRepository,
    EnsureNexusMavenProxyRepository,
    NexusBootstrapConfiguration,
    NexusDockerHostedRepositoryConfiguration,
    NexusMavenProxyRepositoryConfiguration,
    WaitForNexusReady,
)
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactPrepareStep as ExistingArtifactPrepareStep,
)
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactPrepareWorkflow as ExistingArtifactPrepareWorkflow,
)
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactVerifyCheck as ExistingArtifactVerifyCheck,
)
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactVerifyWorkflow as ExistingArtifactVerifyWorkflow,
)
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactWorkflowKind as ExistingArtifactWorkflowKind,
)
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactWorkflowResult as ExistingArtifactWorkflowResult,
)
from tiny_swarm_world.application.services.artifacts.workflows import (
    ArtifactWorkflowStatus as ExistingArtifactWorkflowStatus,
)
from tiny_swarm_world.application.services.nexus.enable_nexus_anonymous_access import (
    EnableNexusAnonymousAccess as ExistingEnableNexusAnonymousAccess,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access import (
    EnsureNexusAdminAccess as ExistingEnsureNexusAdminAccess,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_repository import (
    EnsureNexusDockerHostedRepository as ExistingEnsureNexusDockerHostedRepository,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_repository import (
    EnsureNexusMavenProxyRepository as ExistingEnsureNexusMavenProxyRepository,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_repository import (
    NexusDockerHostedRepositoryConfiguration as ExistingNexusDockerHostedRepositoryConfiguration,
)
from tiny_swarm_world.application.services.nexus.ensure_nexus_repository import (
    NexusMavenProxyRepositoryConfiguration as ExistingNexusMavenProxyRepositoryConfiguration,
)
from tiny_swarm_world.application.services.nexus.nexus_bootstrap_configuration import (
    NexusBootstrapConfiguration as ExistingNexusBootstrapConfiguration,
)
from tiny_swarm_world.application.services.nexus.wait_for_nexus_ready import (
    WaitForNexusReady as ExistingWaitForNexusReady,
)


class TestArtifactServiceExports(unittest.TestCase):
    def test_artifacts_namespace_exports_workflow_contracts(self):
        self.assertIs(ArtifactPrepareStep, ExistingArtifactPrepareStep)
        self.assertIs(ArtifactPrepareWorkflow, ExistingArtifactPrepareWorkflow)
        self.assertIs(ArtifactVerifyCheck, ExistingArtifactVerifyCheck)
        self.assertIs(ArtifactVerifyWorkflow, ExistingArtifactVerifyWorkflow)
        self.assertIs(ArtifactWorkflowKind, ExistingArtifactWorkflowKind)
        self.assertIs(ArtifactWorkflowResult, ExistingArtifactWorkflowResult)
        self.assertIs(ArtifactWorkflowStatus, ExistingArtifactWorkflowStatus)

    def test_artifacts_namespace_exports_existing_artifact_services(self):
        self.assertIs(EnableNexusAnonymousAccess, ExistingEnableNexusAnonymousAccess)
        self.assertIs(EnsureNexusAdminAccess, ExistingEnsureNexusAdminAccess)
        self.assertIs(EnsureNexusDockerHostedRepository, ExistingEnsureNexusDockerHostedRepository)
        self.assertIs(EnsureNexusMavenProxyRepository, ExistingEnsureNexusMavenProxyRepository)
        self.assertIs(
            NexusDockerHostedRepositoryConfiguration,
            ExistingNexusDockerHostedRepositoryConfiguration,
        )
        self.assertIs(NexusBootstrapConfiguration, ExistingNexusBootstrapConfiguration)
        self.assertIs(
            NexusMavenProxyRepositoryConfiguration,
            ExistingNexusMavenProxyRepositoryConfiguration,
        )
        self.assertIs(WaitForNexusReady, ExistingWaitForNexusReady)

    def test_artifacts_namespace_does_not_export_stack_deployment_service(self):
        self.assertNotIn("EnsureNexusStack", artifacts.__all__)

import unittest

from tiny_swarm_world.application.services.network.socat.socat_manager import (
    SocatManager as ExistingSocatManager,
)
from tiny_swarm_world.application.services.platform import (
    LxcDockerInstallService,
    LxcDockerInstallStep,
    LxcSwarmBootstrapService,
    LxcSwarmBootstrapStep,
    PlatformDestroyWorkflow,
    PlatformInitWorkflow,
    PlatformReconcileWorkflow,
    PlatformResetWorkflow,
    PlatformVerifyWorkflow,
    PreflightService,
    SocatManager,
)
from tiny_swarm_world.application.services.platform.lxc_docker_install import (
    LxcDockerInstallService as ExistingLxcDockerInstallService,
)
from tiny_swarm_world.application.services.platform.lxc_docker_install import (
    LxcDockerInstallStep as ExistingLxcDockerInstallStep,
)
from tiny_swarm_world.application.services.platform.lxc_swarm_bootstrap import (
    LxcSwarmBootstrapService as ExistingLxcSwarmBootstrapService,
)
from tiny_swarm_world.application.services.platform.lxc_swarm_bootstrap import (
    LxcSwarmBootstrapStep as ExistingLxcSwarmBootstrapStep,
)
from tiny_swarm_world.application.services.platform.workflows import (
    PlatformDestroyWorkflow as ExistingPlatformDestroyWorkflow,
)
from tiny_swarm_world.application.services.platform.workflows import (
    PlatformInitWorkflow as ExistingPlatformInitWorkflow,
)
from tiny_swarm_world.application.services.platform.workflows import (
    PlatformReconcileWorkflow as ExistingPlatformReconcileWorkflow,
)
from tiny_swarm_world.application.services.platform.workflows import (
    PlatformResetWorkflow as ExistingPlatformResetWorkflow,
)
from tiny_swarm_world.application.services.platform.workflows import (
    PlatformVerifyWorkflow as ExistingPlatformVerifyWorkflow,
)
from tiny_swarm_world.application.services.platform.preflight_service import (
    PreflightService as ExistingPreflightService,
)


class TestPlatformServiceExports(unittest.TestCase):
    def test_platform_namespace_exports_existing_services(self):
        self.assertIs(LxcDockerInstallService, ExistingLxcDockerInstallService)
        self.assertIs(LxcDockerInstallStep, ExistingLxcDockerInstallStep)
        self.assertIs(LxcSwarmBootstrapService, ExistingLxcSwarmBootstrapService)
        self.assertIs(LxcSwarmBootstrapStep, ExistingLxcSwarmBootstrapStep)
        self.assertIs(PlatformDestroyWorkflow, ExistingPlatformDestroyWorkflow)
        self.assertIs(PlatformInitWorkflow, ExistingPlatformInitWorkflow)
        self.assertIs(PlatformReconcileWorkflow, ExistingPlatformReconcileWorkflow)
        self.assertIs(PlatformResetWorkflow, ExistingPlatformResetWorkflow)
        self.assertIs(PlatformVerifyWorkflow, ExistingPlatformVerifyWorkflow)
        self.assertIs(PreflightService, ExistingPreflightService)
        self.assertIs(SocatManager, ExistingSocatManager)

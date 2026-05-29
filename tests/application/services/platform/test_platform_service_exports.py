import unittest

from tiny_swarm_world.application.services.multipass.multipass_docker_install import (
    MultipassDockerInstall as ExistingMultipassDockerInstall,
)
from tiny_swarm_world.application.services.multipass.multipass_docker_swarm_init import (
    MultipassDockerSwarmInit as ExistingMultipassDockerSwarmInit,
)
from tiny_swarm_world.application.services.multipass.multipass_init_vms import (
    MultipassInitVms as ExistingMultipassInitVms,
)
from tiny_swarm_world.application.services.multipass.multipass_restart_vms import (
    MultipassRestartVMs as ExistingMultipassRestartVMs,
)
from tiny_swarm_world.application.services.network.netplant.network_prepare_netplan import (
    NetworkPrepareNetplan as ExistingNetworkPrepareNetplan,
)
from tiny_swarm_world.application.services.network.netplant.network_setup_netplan import (
    NetworkSetupNetplan as ExistingNetworkSetupNetplan,
)
from tiny_swarm_world.application.services.network.socat.socat_manager import (
    SocatManager as ExistingSocatManager,
)
from tiny_swarm_world.application.services.platform import (
    LxcDockerInstallService,
    LxcDockerInstallStep,
    LxcSwarmBootstrapService,
    LxcSwarmBootstrapStep,
    MultipassDockerInstall,
    MultipassDockerSwarmInit,
    MultipassInitVms,
    MultipassRestartVMs,
    NetworkPrepareNetplan,
    NetworkSetupNetplan,
    PlatformDestroyWorkflow,
    PlatformInitWorkflow,
    PlatformReconcileWorkflow,
    PlatformResetWorkflow,
    PlatformVerifyWorkflow,
    PreflightService,
    SocatManager,
    VmIpList,
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
from tiny_swarm_world.application.services.vm.vm_ip_list import VmIpList as ExistingVmIpList


class TestPlatformServiceExports(unittest.TestCase):
    def test_platform_namespace_exports_existing_services(self):
        self.assertIs(MultipassDockerInstall, ExistingMultipassDockerInstall)
        self.assertIs(LxcDockerInstallService, ExistingLxcDockerInstallService)
        self.assertIs(LxcDockerInstallStep, ExistingLxcDockerInstallStep)
        self.assertIs(LxcSwarmBootstrapService, ExistingLxcSwarmBootstrapService)
        self.assertIs(LxcSwarmBootstrapStep, ExistingLxcSwarmBootstrapStep)
        self.assertIs(MultipassDockerSwarmInit, ExistingMultipassDockerSwarmInit)
        self.assertIs(MultipassInitVms, ExistingMultipassInitVms)
        self.assertIs(MultipassRestartVMs, ExistingMultipassRestartVMs)
        self.assertIs(NetworkPrepareNetplan, ExistingNetworkPrepareNetplan)
        self.assertIs(NetworkSetupNetplan, ExistingNetworkSetupNetplan)
        self.assertIs(PlatformDestroyWorkflow, ExistingPlatformDestroyWorkflow)
        self.assertIs(PlatformInitWorkflow, ExistingPlatformInitWorkflow)
        self.assertIs(PlatformReconcileWorkflow, ExistingPlatformReconcileWorkflow)
        self.assertIs(PlatformResetWorkflow, ExistingPlatformResetWorkflow)
        self.assertIs(PlatformVerifyWorkflow, ExistingPlatformVerifyWorkflow)
        self.assertIs(PreflightService, ExistingPreflightService)
        self.assertIs(SocatManager, ExistingSocatManager)
        self.assertIs(VmIpList, ExistingVmIpList)

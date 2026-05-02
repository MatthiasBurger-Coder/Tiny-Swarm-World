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
    MultipassDockerInstall,
    MultipassDockerSwarmInit,
    MultipassInitVms,
    MultipassRestartVMs,
    NetworkPrepareNetplan,
    NetworkSetupNetplan,
    SocatManager,
    VmIpList,
)
from tiny_swarm_world.application.services.vm.vm_ip_list import VmIpList as ExistingVmIpList


class TestPlatformServiceExports(unittest.TestCase):
    def test_platform_namespace_exports_existing_services(self):
        self.assertIs(MultipassDockerInstall, ExistingMultipassDockerInstall)
        self.assertIs(MultipassDockerSwarmInit, ExistingMultipassDockerSwarmInit)
        self.assertIs(MultipassInitVms, ExistingMultipassInitVms)
        self.assertIs(MultipassRestartVMs, ExistingMultipassRestartVMs)
        self.assertIs(NetworkPrepareNetplan, ExistingNetworkPrepareNetplan)
        self.assertIs(NetworkSetupNetplan, ExistingNetworkSetupNetplan)
        self.assertIs(SocatManager, ExistingSocatManager)
        self.assertIs(VmIpList, ExistingVmIpList)

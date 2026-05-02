"""Platform provisioning service namespace.

This module marks the target Platform boundary without moving the existing
service modules yet. Existing imports keep working while new code can depend on
the platform namespace during the incremental migration.
"""

from tiny_swarm_world.application.services.multipass.multipass_docker_install import (
    MultipassDockerInstall,
)
from tiny_swarm_world.application.services.multipass.multipass_docker_swarm_init import (
    MultipassDockerSwarmInit,
)
from tiny_swarm_world.application.services.multipass.multipass_init_vms import (
    MultipassInitVms,
)
from tiny_swarm_world.application.services.multipass.multipass_restart_vms import (
    MultipassRestartVMs,
)
from tiny_swarm_world.application.services.network.netplant.network_prepare_netplan import (
    NetworkPrepareNetplan,
)
from tiny_swarm_world.application.services.network.netplant.network_setup_netplan import (
    NetworkSetupNetplan,
)
from tiny_swarm_world.application.services.network.socat.socat_manager import SocatManager
from tiny_swarm_world.application.services.vm.vm_ip_list import VmIpList

__all__ = [
    "MultipassDockerInstall",
    "MultipassDockerSwarmInit",
    "MultipassInitVms",
    "MultipassRestartVMs",
    "NetworkPrepareNetplan",
    "NetworkSetupNetplan",
    "SocatManager",
    "VmIpList",
]

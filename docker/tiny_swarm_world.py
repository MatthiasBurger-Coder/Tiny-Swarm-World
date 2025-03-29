import asyncio

from application.services.multipass.multipass_docker_install import MultipassDockerInstall
from application.services.multipass.multipass_docker_swarm_init import MultipassDockerSwarmInit
from application.services.multipass.multipass_init_vms import MultipassInitVms
from application.services.multipass.multipass_restart_vms import MultipassRestartVMs
from application.services.network.netplant.network_prepare_netplan import NetworkPrepareNetplan
from application.services.network.netplant.network_setup_netplan import NetworkSetupNetplan
from application.services.network.socat.multipass_vm_ip_list import MultipassVmIpList
from infrastructure.adapters.file_management.file_manager import FileManager
from infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from infrastructure.dependency_injection.infra_core_di_container import infra_core_container
from infrastructure.logging.logger_factory import LoggerFactory


async def main():

    logger = LoggerFactory.get_logger("application")
    logger.info("Starting application")

    logger.info("Register FileManager explicitly")
    #infra_core_container.scan_module("docker")
    infra_core_container.register(PathFactory)
    infra_core_container.register(FileManager)

    logger.info("MultipassInitVms")
    multipass_init_vms = MultipassInitVms()
    await multipass_init_vms.run()

    logger.info("NetworkPrepareNetplan")
    network_prepare_netplan = NetworkPrepareNetplan()
    await network_prepare_netplan.run()

    logger.info("NetworkSetupNetplan")
    network = NetworkSetupNetplan()
    await network.run()

    logger.info("MultipassRestartVMs")
    multipass_restart_vms = MultipassRestartVMs()
    await multipass_restart_vms.run()

    logger.info("MultipassDockerInstall")
    multipass_docker_install = MultipassDockerInstall()
    await multipass_docker_install.run()

    logger.info("MultipassRestartVMs")
    multipass_restart_vms = MultipassRestartVMs()
    await multipass_restart_vms.run()

    logger.info("MultipassDockerSwarmInit")
    multipass_swarm_init = MultipassDockerSwarmInit()
    await multipass_swarm_init.run()

    logger.info("MultipassVmIpList")
    multipass_vm_ip_list = MultipassVmIpList()
    await multipass_vm_ip_list.run()

    logger.info("Done")
    print("Done")


if __name__ == "__main__":
    asyncio.run(main())

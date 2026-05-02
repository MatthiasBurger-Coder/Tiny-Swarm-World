import asyncio

from tiny_swarm_world.application.services.vm.vm_ip_list import VmIpList
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml import PortVmRepositoryYaml
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


async def main():

    logger = LoggerFactory.get_logger("application")
    logger.info("Starting application")

    logger.info("Register FileManager explicitly")
    # infra_core_container.scan_module("tiny_swarm_world")
    infra_core_container.register(PathFactory)
    infra_core_container.register(FileManager)
    command_workflow = CommandWorkflow()

    # logger.info("MultipassInitVms")
    # multipass_init_vms = MultipassInitVms(command_workflow)
    # await multipass_init_vms.run()
    #
    # logger.info("NetworkPrepareNetplan")
    # network_prepare_netplan = NetworkPrepareNetplan(command_workflow, PortVmRepositoryYaml(), PortNetplanRepositoryYaml())
    # await network_prepare_netplan.run()
    #
    # logger.info("NetworkSetupNetplan")
    # network = NetworkSetupNetplan(command_workflow)
    # await network.run()
    #
    # logger.info("MultipassRestartVMs")
    # multipass_restart_vms = MultipassRestartVMs(command_workflow)
    # await multipass_restart_vms.run()
    #
    # logger.info("MultipassDockerInstall")
    # multipass_docker_install = MultipassDockerInstall(command_workflow)
    # await multipass_docker_install.run()
    #
    # logger.info("MultipassRestartVMs")
    # multipass_restart_vms = MultipassRestartVMs(command_workflow)
    # await multipass_restart_vms.run()
    #
    # logger.info("MultipassDockerSwarmInit")
    # multipass_swarm_init = MultipassDockerSwarmInit(command_workflow)
    # await multipass_swarm_init.run()

    logger.info("VmIpList")
    vm_ip_list = VmIpList(command_workflow=command_workflow, vm_repository=PortVmRepositoryYaml())
    await vm_ip_list.run()

    logger.info("Done")
    print("Done")


if __name__ == "__main__":
    asyncio.run(main())

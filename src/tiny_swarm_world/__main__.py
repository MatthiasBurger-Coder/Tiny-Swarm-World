import asyncio

from tiny_swarm_world.infrastructure.composition import build_application_services
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


async def main():

    logger = LoggerFactory.get_logger("application")
    logger.info("Starting application")

    services = build_application_services()

    # logger.info("MultipassInitVms")
    # await services.multipass_init_vms.run()
    #
    # logger.info("NetworkPrepareNetplan")
    # await services.network_prepare_netplan.run()
    #
    # logger.info("NetworkSetupNetplan")
    # await services.network_setup_netplan.run()
    #
    # logger.info("MultipassRestartVMs")
    # await services.multipass_restart_vms.run()
    #
    # logger.info("MultipassDockerInstall")
    # await services.multipass_docker_install.run()
    #
    # logger.info("MultipassRestartVMs")
    # await services.multipass_restart_vms.run()
    #
    # logger.info("MultipassDockerSwarmInit")
    # await services.multipass_docker_swarm_init.run()

    logger.info("VmIpList")
    await services.vm_ip_list.run()

    logger.info("Done")
    print("Done")


if __name__ == "__main__":
    asyncio.run(main())

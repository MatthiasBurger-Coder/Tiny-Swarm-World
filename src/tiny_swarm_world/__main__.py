import asyncio
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence

from tiny_swarm_world.infrastructure.composition import (
    ApplicationServices,
    build_application_services,
)
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory

SERVICE_CHOICES = (
    "multipass-docker-install",
    "multipass-docker-swarm-init",
    "multipass-init-vms",
    "multipass-restart-vms",
    "network-prepare-netplan",
    "network-setup-netplan",
    "vm-ip-list",
)


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser(description="Tiny Swarm World automation entrypoint.")
    parser.add_argument(
        "--list-services",
        action="store_true",
        help="List explicit automation services without running infrastructure commands.",
    )
    parser.add_argument(
        "--run",
        choices=SERVICE_CHOICES,
        help="Run one explicit automation service. This may execute infrastructure commands.",
    )
    return parser.parse_args(argv)


async def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    logger = LoggerFactory.get_logger("application")
    logger.info("Starting application")

    if args.list_services:
        for service_name in SERVICE_CHOICES:
            print(service_name)
        return

    if args.run is None:
        print("No automation service selected. Use --list-services to inspect available services.")
        return

    services = build_application_services()
    logger.info("Running automation service: %s", args.run)
    await run_service(services, args.run)

    logger.info("Done")
    print("Done")


async def run_service(services: ApplicationServices, service_name: str) -> None:
    match service_name:
        case "multipass-docker-install":
            await services.multipass_docker_install.run()
        case "multipass-docker-swarm-init":
            await services.multipass_docker_swarm_init.run()
        case "multipass-init-vms":
            await services.multipass_init_vms.run()
        case "multipass-restart-vms":
            await services.multipass_restart_vms.run()
        case "network-prepare-netplan":
            await services.network_prepare_netplan.run()
        case "network-setup-netplan":
            await services.network_setup_netplan.run()
        case "vm-ip-list":
            await services.vm_ip_list.run()
        case _:
            raise ValueError(f"Unsupported automation service: {service_name}")


if __name__ == "__main__":
    asyncio.run(main())

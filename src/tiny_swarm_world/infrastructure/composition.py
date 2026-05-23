from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.services.platform import (
    MultipassDockerInstall,
    MultipassDockerSwarmInit,
    MultipassInitVms,
    MultipassRestartVMs,
    NetworkPrepareNetplan,
    NetworkSetupNetplan,
    PreflightService,
    SocatManager,
    VmIpList,
)
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe
from tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository import PortNetplanRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml import PortVmRepositoryYaml
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container


@dataclass(frozen=True)
class PlatformServices:
    command_workflow: CommandWorkflow
    vm_repository: PortVmRepositoryYaml
    netplan_repository: PortNetplanRepositoryYaml
    multipass_init_vms: MultipassInitVms
    network_prepare_netplan: NetworkPrepareNetplan
    network_setup_netplan: NetworkSetupNetplan
    multipass_restart_vms: MultipassRestartVMs
    multipass_docker_install: MultipassDockerInstall
    multipass_docker_swarm_init: MultipassDockerSwarmInit
    preflight: PreflightService
    vm_ip_list: VmIpList
    socat_manager: SocatManager


ApplicationServices = PlatformServices


def configure_infrastructure_container() -> None:
    infra_core_container.register(PathFactory)
    infra_core_container.register(FileManager)


def build_platform_services() -> PlatformServices:
    configure_infrastructure_container()

    vm_repository = PortVmRepositoryYaml()
    netplan_repository = PortNetplanRepositoryYaml()
    command_workflow = CommandWorkflow(vm_repository=vm_repository)
    preflight_probe = HostPreflightProbe()

    return PlatformServices(
        command_workflow=command_workflow,
        vm_repository=vm_repository,
        netplan_repository=netplan_repository,
        multipass_init_vms=MultipassInitVms(command_workflow),
        network_prepare_netplan=NetworkPrepareNetplan(
            command_workflow=command_workflow,
            vm_repository=vm_repository,
            netplan_repository=netplan_repository,
        ),
        network_setup_netplan=NetworkSetupNetplan(command_workflow),
        multipass_restart_vms=MultipassRestartVMs(command_workflow),
        multipass_docker_install=MultipassDockerInstall(command_workflow),
        multipass_docker_swarm_init=MultipassDockerSwarmInit(command_workflow),
        preflight=PreflightService(preflight_probe),
        vm_ip_list=VmIpList(command_workflow=command_workflow, vm_repository=vm_repository),
        socat_manager=SocatManager(),
    )


def build_application_services() -> ApplicationServices:
    return build_platform_services()

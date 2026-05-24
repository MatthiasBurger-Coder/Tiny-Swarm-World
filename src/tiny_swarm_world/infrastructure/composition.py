from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.services.artifacts import (
    ArtifactPrepareWorkflow,
    ArtifactVerifyWorkflow,
)
from tiny_swarm_world.application.services.deployment import (
    DeploymentApplyWorkflow,
    DeploymentVerifyWorkflow,
)
from tiny_swarm_world.application.services.platform import (
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
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe
from tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository import PortNetplanRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml import PortVmRepositoryYaml
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container


@dataclass(frozen=True)
class PlatformWorkflows:
    init: PlatformInitWorkflow
    reconcile: PlatformReconcileWorkflow
    reset: PlatformResetWorkflow
    destroy: PlatformDestroyWorkflow
    verify: PlatformVerifyWorkflow


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
    workflows: PlatformWorkflows


@dataclass(frozen=True)
class ArtifactWorkflows:
    prepare: ArtifactPrepareWorkflow
    verify: ArtifactVerifyWorkflow


@dataclass(frozen=True)
class ArtifactServices:
    workflows: ArtifactWorkflows


@dataclass(frozen=True)
class DeploymentWorkflows:
    apply: DeploymentApplyWorkflow
    verify: DeploymentVerifyWorkflow


@dataclass(frozen=True)
class DeploymentServices:
    workflows: DeploymentWorkflows


@dataclass(frozen=True)
class ApplicationServices:
    platform: PlatformServices
    artifacts: ArtifactServices
    deployment: DeploymentServices

    @property
    def multipass_init_vms(self) -> MultipassInitVms:
        return self.platform.multipass_init_vms

    @property
    def network_prepare_netplan(self) -> NetworkPrepareNetplan:
        return self.platform.network_prepare_netplan

    @property
    def network_setup_netplan(self) -> NetworkSetupNetplan:
        return self.platform.network_setup_netplan

    @property
    def multipass_restart_vms(self) -> MultipassRestartVMs:
        return self.platform.multipass_restart_vms

    @property
    def multipass_docker_install(self) -> MultipassDockerInstall:
        return self.platform.multipass_docker_install

    @property
    def multipass_docker_swarm_init(self) -> MultipassDockerSwarmInit:
        return self.platform.multipass_docker_swarm_init

    @property
    def preflight(self) -> PreflightService:
        return self.platform.preflight

    @property
    def vm_ip_list(self) -> VmIpList:
        return self.platform.vm_ip_list

    @property
    def socat_manager(self) -> SocatManager:
        return self.platform.socat_manager


def configure_infrastructure_container() -> None:
    infra_core_container.register(PathFactory)
    infra_core_container.register(FileManager)


def build_preflight_service() -> PreflightService:
    return PreflightService(HostPreflightProbe())


def build_platform_services() -> PlatformServices:
    configure_infrastructure_container()

    vm_repository = PortVmRepositoryYaml()
    netplan_repository = PortNetplanRepositoryYaml()
    command_workflow = CommandWorkflow(vm_repository=vm_repository)
    preflight = build_preflight_service()
    multipass_init_vms = MultipassInitVms(command_workflow)
    network_prepare_netplan = NetworkPrepareNetplan(
        command_workflow=command_workflow,
        vm_repository=vm_repository,
        netplan_repository=netplan_repository,
    )
    network_setup_netplan = NetworkSetupNetplan(command_workflow)
    multipass_restart_vms = MultipassRestartVMs(command_workflow)
    multipass_docker_install = MultipassDockerInstall(command_workflow)
    multipass_docker_swarm_init = MultipassDockerSwarmInit(command_workflow)
    vm_ip_list = VmIpList(command_workflow=command_workflow, vm_repository=vm_repository)
    socat_manager = SocatManager()
    workflows = PlatformWorkflows(
        init=PlatformInitWorkflow(
            (
                multipass_init_vms,
                network_prepare_netplan,
                network_setup_netplan,
                multipass_restart_vms,
                multipass_docker_install,
                multipass_docker_swarm_init,
            )
        ),
        reconcile=PlatformReconcileWorkflow((vm_ip_list,)),
        reset=PlatformResetWorkflow(),
        destroy=PlatformDestroyWorkflow(),
        verify=PlatformVerifyWorkflow((preflight,)),
    )

    return PlatformServices(
        command_workflow=command_workflow,
        vm_repository=vm_repository,
        netplan_repository=netplan_repository,
        multipass_init_vms=multipass_init_vms,
        network_prepare_netplan=network_prepare_netplan,
        network_setup_netplan=network_setup_netplan,
        multipass_restart_vms=multipass_restart_vms,
        multipass_docker_install=multipass_docker_install,
        multipass_docker_swarm_init=multipass_docker_swarm_init,
        preflight=preflight,
        vm_ip_list=vm_ip_list,
        socat_manager=socat_manager,
        workflows=workflows,
    )


def build_artifact_services() -> ArtifactServices:
    return ArtifactServices(
        workflows=ArtifactWorkflows(
            prepare=ArtifactPrepareWorkflow(),
            verify=ArtifactVerifyWorkflow(),
        )
    )


def build_deployment_services() -> DeploymentServices:
    return DeploymentServices(
        workflows=DeploymentWorkflows(
            apply=DeploymentApplyWorkflow(),
            verify=DeploymentVerifyWorkflow(),
        )
    )


def build_application_services() -> ApplicationServices:
    return ApplicationServices(
        platform=build_platform_services(),
        artifacts=build_artifact_services(),
        deployment=build_deployment_services(),
    )

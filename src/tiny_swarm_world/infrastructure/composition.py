from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from tiny_swarm_world.application.services.artifacts import (
    ArtifactPrepareStep,
    ArtifactPrepareWorkflow,
    ArtifactVerifyCheck,
    ArtifactVerifyWorkflow,
    EnsureContainerImage,
    EnsureNexusAdminAccess,
    EnsureNexusDockerHostedRepository,
    EnsureNexusMavenProxyRepository,
    NexusDockerHostedRepositoryConfiguration,
    NexusMavenProxyRepositoryConfiguration,
    WaitForNexusReady,
)
from tiny_swarm_world.application.services.deployment import (
    DeploymentApplyWorkflow,
    DeploymentWorkflowKind,
    DeploymentVerifyWorkflow,
    EnsurePortainerAdminAccess,
    EnsureSwarmStack,
    VerifySwarmServiceReadiness,
)
from tiny_swarm_world.application.services.deployment.service_stack_plan import build_service_stack_steps
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
from tiny_swarm_world.application.services.setup import SetupWorkflow, SetupWorkflowPhase
from tiny_swarm_world.domain.artifacts import DEFAULT_CONTAINER_IMAGE_CONTRACTS
from tiny_swarm_world.domain.deployment import (
    ServiceStackProfile,
    service_stack_contracts_for_profile,
)
from tiny_swarm_world.domain.preflight import LiveConsent, default_preflight_configuration
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.clients.multipass_container_image_publisher import (
    MultipassContainerImagePublisher,
)
from tiny_swarm_world.infrastructure.adapters.clients.multipass_container_runtime import (
    MultipassContainerRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.multipass_nexus_http_client import (
    MultipassNexusHttpClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.multipass_portainer_admin_client import (
    MultipassPortainerAdminClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.multipass_swarm_runtime import (
    MultipassSwarmRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml,
)
from tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository import PortNetplanRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.repositories.verification_evidence_local_repository import (
    VerificationEvidenceLocalRepository,
)
from tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml import PortVmRepositoryYaml
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container


DEFAULT_SETUP_SERVICE_PROFILE = ServiceStackProfile.SERVICE_ACCESS


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
    bootstrap: DeploymentApplyWorkflow
    apply: DeploymentApplyWorkflow
    verify: DeploymentVerifyWorkflow


@dataclass(frozen=True)
class DeploymentServices:
    workflows: DeploymentWorkflows


@dataclass(frozen=True)
class SetupWorkflows:
    run: SetupWorkflow


@dataclass(frozen=True)
class SetupServices:
    workflows: SetupWorkflows


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


def build_preflight_service(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
) -> PreflightService:
    return PreflightService(
        HostPreflightProbe(),
        default_preflight_configuration(service_profile=service_profile),
    )


def build_platform_services(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    live_consent: LiveConsent | None = None,
) -> PlatformServices:
    configure_infrastructure_container()

    vm_repository = PortVmRepositoryYaml()
    netplan_repository = PortNetplanRepositoryYaml()
    command_workflow = CommandWorkflow(vm_repository=vm_repository)
    verification_evidence_repository = VerificationEvidenceLocalRepository()
    preflight = build_preflight_service(service_profile=service_profile)
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
            ),
            verification_evidence_repository=verification_evidence_repository,
            pre_apply_guard=(
                SetupWorkflowPhase(
                    "platform init preflight",
                    lambda: preflight.run(live_consent),
                )
                if live_consent is not None
                else None
            ),
        ),
        reconcile=PlatformReconcileWorkflow(
            (vm_ip_list,),
            verification_evidence_repository=verification_evidence_repository,
        ),
        reset=PlatformResetWorkflow(
            verification_evidence_repository=verification_evidence_repository,
        ),
        destroy=PlatformDestroyWorkflow(
            verification_evidence_repository=verification_evidence_repository,
        ),
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
    nexus_admin_password = _static_secret_default("TSW_NEXUS_ADMIN_PASSWORD")
    nexus_client = MultipassNexusHttpClient()
    container_runtime = MultipassContainerRuntime()
    image_publisher = MultipassContainerImagePublisher(
        registry_username="admin",
        registry_password=nexus_admin_password,
    )
    wait_for_nexus_ready = WaitForNexusReady(
        nexus_client=nexus_client,
        max_attempts=60,
        wait_seconds=10,
    )
    ensure_nexus_admin_access = EnsureNexusAdminAccess(
        nexus_client=nexus_client,
        container_runtime=container_runtime,
        admin_username="admin",
        admin_password=nexus_admin_password,
        container_name_filter="nexus",
        initial_password_path="/nexus-data/admin.password",
        max_attempts=60,
        wait_seconds=10,
    )
    nexus_repository_steps = (
        EnsureNexusDockerHostedRepository(
            nexus_client=nexus_client,
            configuration=NexusDockerHostedRepositoryConfiguration(
                repository_name="docker-hosted",
                http_port=5000,
                admin_username="admin",
                admin_password=nexus_admin_password,
            ),
        ),
        EnsureNexusMavenProxyRepository(
            nexus_client=nexus_client,
            configuration=NexusMavenProxyRepositoryConfiguration(
                repository_name="maven-central-proxy",
                remote_url="https://repo1.maven.org/maven2/",
                admin_username="admin",
                admin_password=nexus_admin_password,
            ),
        ),
    )
    image_steps = tuple(
        EnsureContainerImage(image_publisher, contract)
        for contract in DEFAULT_CONTAINER_IMAGE_CONTRACTS
    )
    checks = cast(
        tuple[ArtifactPrepareStep, ...],
        (
            wait_for_nexus_ready,
            ensure_nexus_admin_access,
            *nexus_repository_steps,
            *image_steps,
        ),
    )
    verify_checks = cast(tuple[ArtifactVerifyCheck, ...], checks)
    return ArtifactServices(
        workflows=ArtifactWorkflows(
            prepare=ArtifactPrepareWorkflow(checks),
            verify=ArtifactVerifyWorkflow(verify_checks),
        )
    )


def build_deployment_services(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
) -> DeploymentServices:
    selected_service_profile = ServiceStackProfile(service_profile)
    service_stack_contracts = service_stack_contracts_for_profile(selected_service_profile)
    compose_repository = ComposeFileRepositoryYaml()
    swarm_runtime = MultipassSwarmRuntime()
    portainer_admin_client = MultipassPortainerAdminClient()
    portainer_client = PortainerHttpClient(
        "http://localhost:9000",
        "admin",
        _static_secret_default("TSW_PORTAINER_PASSWORD"),
    )
    stack_steps = {
        contract.stack_name: EnsureSwarmStack(
            compose_repository=compose_repository,
            swarm_runtime=swarm_runtime,
            service_stack=contract,
        )
        for contract in service_stack_contracts
    }
    bootstrap_steps = (
        stack_steps["portainer"],
        EnsurePortainerAdminAccess(
            portainer_admin_client=portainer_admin_client,
            username="admin",
            password=_static_secret_default("TSW_PORTAINER_PASSWORD"),
            max_attempts=60,
            wait_seconds=5,
        ),
        stack_steps["nexus"],
    )
    application_steps = build_service_stack_steps(
        compose_repository=compose_repository,
        portainer_client=portainer_client,
        endpoint_name="local",
        service_profile=selected_service_profile,
        excluded_stack_names=("nexus",),
    )
    readiness_checks = tuple(
        VerifySwarmServiceReadiness(
            swarm_runtime=swarm_runtime,
            service_stack=contract,
            max_attempts=60,
            wait_seconds=10,
        )
        for contract in service_stack_contracts
    )
    return DeploymentServices(
        workflows=DeploymentWorkflows(
            bootstrap=DeploymentApplyWorkflow(
                bootstrap_steps,
                kind=DeploymentWorkflowKind.BOOTSTRAP,
            ),
            apply=DeploymentApplyWorkflow(application_steps),
            verify=DeploymentVerifyWorkflow(readiness_checks),
        )
    )


def build_setup_services(
    live_consent: LiveConsent,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
) -> SetupServices:
    preflight = build_preflight_service(service_profile=service_profile)
    platform = build_platform_services(
        service_profile=service_profile,
        live_consent=live_consent,
    )
    artifacts = build_artifact_services()
    deployment = build_deployment_services(service_profile=service_profile)

    return SetupServices(
        workflows=SetupWorkflows(
            run=SetupWorkflow(
                (
                    SetupWorkflowPhase("preflight", lambda: preflight.run(live_consent)),
                    SetupWorkflowPhase("platform init", lambda: platform.workflows.init.run()),
                    SetupWorkflowPhase("platform reconcile", lambda: platform.workflows.reconcile.run()),
                    SetupWorkflowPhase("deployment bootstrap", lambda: deployment.workflows.bootstrap.run()),
                    SetupWorkflowPhase("artifacts prepare", lambda: artifacts.workflows.prepare.run()),
                    SetupWorkflowPhase("artifacts verify", lambda: artifacts.workflows.verify.run()),
                    SetupWorkflowPhase("deployment apply", lambda: deployment.workflows.apply.run()),
                    SetupWorkflowPhase("deployment verify", lambda: deployment.workflows.verify.run()),
                    SetupWorkflowPhase("platform verify", lambda: platform.workflows.verify.run()),
                ),
                live_consent=live_consent,
            )
        )
    )


def build_application_services(
    live_consent: LiveConsent | None = None,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
) -> ApplicationServices:
    return ApplicationServices(
        platform=build_platform_services(
            service_profile=service_profile,
            live_consent=live_consent,
        ),
        artifacts=build_artifact_services(),
        deployment=build_deployment_services(service_profile=service_profile),
    )


def _static_secret_default(name: str) -> str:
    for default in build_preflight_service().configuration.static_secret_defaults:
        if default.name == name:
            return default.value
    raise KeyError(f"Missing static secret default '{name}'.")

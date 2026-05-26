from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
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
    VerifyExternalSwarmInput,
    VerifySwarmServiceReadiness,
)
from tiny_swarm_world.application.services.deployment.service_stack_plan import (
    DEFAULT_PORTAINER_ENDPOINT_NAME,
    build_service_stack_steps,
)
from tiny_swarm_world.application.services.platform import (
    AsyncWorkflowStep,
    MultipassDockerInstall,
    MultipassDockerSwarmInit,
    MultipassInitVms,
    MultipassRestartVMs,
    NetworkPrepareNetplan,
    NetworkSetupNetplan,
    NodeProviderEnsureNodeStep,
    NodeProviderSelectionRequest,
    NodeProviderSelectionService,
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
from tiny_swarm_world.domain.node_provider import NodeProviderKind, NodeRole, NodeSpec
from tiny_swarm_world.domain.preflight import (
    LiveConsent,
    PreflightConfiguration,
    default_preflight_configuration,
)
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
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    AsyncLxcNodeCommandRunner,
    LxcNodeProvider,
)
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe, LxcProviderPreflightProbe
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml,
)
from tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository import PortNetplanRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfigYamlRepository,
)
from tiny_swarm_world.infrastructure.adapters.repositories.verification_evidence_local_repository import (
    VerificationEvidenceLocalRepository,
)
from tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml import PortVmRepositoryYaml
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container


DEFAULT_SETUP_SERVICE_PROFILE = ServiceStackProfile.SERVICE_ACCESS
DEFAULT_PORTAINER_API_URL = "http://localhost:9000"
VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT = "TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET"
DEFAULT_VAULTWARDEN_ADMIN_INPUT_NAME = "tsw_vaultwarden_admin_token"
DEFAULT_LXC_PLATFORM_NODES = (
    NodeSpec("swarm-manager", NodeRole.MANAGER, NodeProviderKind.LXC_NATIVE),
    NodeSpec("swarm-worker-1", NodeRole.WORKER, NodeProviderKind.LXC_NATIVE),
    NodeSpec("swarm-worker-2", NodeRole.WORKER, NodeProviderKind.LXC_NATIVE),
)


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
    lxc_node_provider: LxcNodeProvider
    node_provider_selection: NodeProviderSelectionService
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
    node_provider_request: NodeProviderSelectionRequest | None = None,
) -> PreflightService:
    return PreflightService(
        HostPreflightProbe(),
        _preflight_configuration_for_provider(service_profile, node_provider_request),
    )


def build_platform_services(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    live_consent: LiveConsent | None = None,
    node_provider_request: NodeProviderSelectionRequest | None = None,
) -> PlatformServices:
    configure_infrastructure_container()
    provider_request = node_provider_request or NodeProviderSelectionRequest()

    vm_repository = PortVmRepositoryYaml()
    netplan_repository = PortNetplanRepositoryYaml()
    command_workflow = CommandWorkflow(vm_repository=vm_repository)
    verification_evidence_repository = VerificationEvidenceLocalRepository()
    preflight = _build_preflight_service_for_request(service_profile, node_provider_request)
    lxc_node_provider = LxcNodeProvider(
        config_repository=NodeProviderConfigYamlRepository(),
        runner=AsyncLxcNodeCommandRunner(),
        allow_live_mutation=False if live_consent is None else live_consent.accepted
    )
    node_provider_selection = NodeProviderSelectionService(
        LxcProviderPreflightProbe(
            wsl_lxc_capability_available=_wsl_lxc_lifecycle_capability_available,
        ),
        lxc_node_provider,
    )
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
    init_steps = _platform_init_steps(
        provider_request=provider_request,
        node_provider_selection=node_provider_selection,
        live_consent=live_consent,
        multipass_steps=(
            multipass_init_vms,
            network_prepare_netplan,
            network_setup_netplan,
            multipass_restart_vms,
            multipass_docker_install,
            multipass_docker_swarm_init,
        ),
    )
    workflows = PlatformWorkflows(
        init=PlatformInitWorkflow(
            init_steps,
            verification_evidence_repository=verification_evidence_repository,
            pre_apply_guard=(
                SetupWorkflowPhase(
                    "platform init preflight",
                    lambda: _platform_init_pre_apply_guard(
                        preflight,
                        node_provider_selection,
                        provider_request,
                        live_consent,
                    ),
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
        lxc_node_provider=lxc_node_provider,
        node_provider_selection=node_provider_selection,
        vm_ip_list=vm_ip_list,
        socat_manager=socat_manager,
        workflows=workflows,
    )


def build_artifact_services() -> ArtifactServices:
    nexus_admin_password = _operator_secret_value("TSW_NEXUS_ADMIN_PASSWORD")
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
    swarm_runtime = MultipassSwarmRuntime()
    service_access_environment = _service_access_stack_environment(selected_service_profile)
    external_input_checks = _service_access_external_input_checks(
        selected_service_profile,
        swarm_runtime=swarm_runtime,
    )
    compose_repository = ComposeFileRepositoryYaml()
    portainer_admin_client = MultipassPortainerAdminClient()
    portainer_client = PortainerHttpClient(
        DEFAULT_PORTAINER_API_URL,
        "admin",
        _operator_secret_value("TSW_PORTAINER_PASSWORD"),
    )
    stack_steps = {
        contract.stack_name: EnsureSwarmStack(
            compose_repository=compose_repository,
            swarm_runtime=swarm_runtime,
            service_stack=contract,
            stack_environment=service_access_environment.get(contract.stack_name),
        )
        for contract in service_stack_contracts
    }
    bootstrap_steps = (
        stack_steps["portainer"],
        EnsurePortainerAdminAccess(
            portainer_admin_client=portainer_admin_client,
            username="admin",
            password=_operator_secret_value("TSW_PORTAINER_PASSWORD"),
            max_attempts=60,
            wait_seconds=5,
        ),
        stack_steps["nexus"],
    )
    application_steps = build_service_stack_steps(
        compose_repository=compose_repository,
        portainer_client=portainer_client,
        endpoint_name=DEFAULT_PORTAINER_ENDPOINT_NAME,
        service_profile=selected_service_profile,
        excluded_stack_names=("nexus",),
        stack_environments=service_access_environment,
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
            apply=DeploymentApplyWorkflow(
                application_steps,
                pre_apply_checks=external_input_checks,
            ),
            verify=DeploymentVerifyWorkflow((*external_input_checks, *readiness_checks)),
        )
    )


def build_setup_services(
    live_consent: LiveConsent,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
) -> SetupServices:
    preflight = _build_preflight_service_for_request(service_profile, node_provider_request)
    platform = _build_platform_services_for_request(
        service_profile,
        live_consent,
        node_provider_request,
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
    node_provider_request: NodeProviderSelectionRequest | None = None,
) -> ApplicationServices:
    return ApplicationServices(
        platform=_build_platform_services_for_request(
            service_profile,
            live_consent,
            node_provider_request,
        ),
        artifacts=build_artifact_services(),
        deployment=build_deployment_services(service_profile=service_profile),
    )


def _build_platform_services_for_request(
    service_profile: ServiceStackProfile | str,
    live_consent: LiveConsent | None,
    node_provider_request: NodeProviderSelectionRequest | None,
) -> PlatformServices:
    if node_provider_request is None:
        return build_platform_services(
            service_profile=service_profile,
            live_consent=live_consent,
        )
    return build_platform_services(
        service_profile=service_profile,
        live_consent=live_consent,
        node_provider_request=node_provider_request,
    )


def _build_preflight_service_for_request(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
) -> PreflightService:
    if node_provider_request is None:
        return build_preflight_service(service_profile=service_profile)
    return build_preflight_service(
        service_profile=service_profile,
        node_provider_request=node_provider_request,
    )


def _preflight_configuration_for_provider(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
) -> PreflightConfiguration:
    configuration = default_preflight_configuration(service_profile=service_profile)
    request = node_provider_request or NodeProviderSelectionRequest()
    if request.requested_provider != NodeProviderKind.LXC_NATIVE:
        return configuration
    return replace(
        configuration,
        required_dependencies=tuple(
            dependency
            for dependency in configuration.required_dependencies
            if dependency.name != "multipass"
        ),
        required_runtime_readiness=(),
    )


def _platform_init_steps(
    *,
    provider_request: NodeProviderSelectionRequest,
    node_provider_selection: NodeProviderSelectionService,
    live_consent: LiveConsent | None,
    multipass_steps: tuple[AsyncWorkflowStep, ...],
) -> tuple[AsyncWorkflowStep, ...]:
    if provider_request.requested_provider == NodeProviderKind.MULTIPASS_LEGACY:
        return multipass_steps
    if live_consent is None or not live_consent.accepted:
        return multipass_steps
    return tuple(
        NodeProviderEnsureNodeStep(node, node_provider_selection, provider_request)
        for node in DEFAULT_LXC_PLATFORM_NODES
    )


async def _platform_init_pre_apply_guard(
    preflight: PreflightService,
    node_provider_selection: NodeProviderSelectionService,
    provider_request: NodeProviderSelectionRequest,
    live_consent: LiveConsent | None,
) -> object:
    preflight_result = await preflight.run(live_consent)
    if not preflight_result.passed:
        return preflight_result
    return await node_provider_selection.verify_provider_selection(provider_request)


def _operator_secret_value(name: str) -> str:
    return os.environ.get(name) or f"<operator-supplied:{name}>"


def _wsl_lxc_lifecycle_capability_available() -> bool:
    return (
        _linux_text_file_equals(Path("/proc/sys/kernel/unprivileged_userns_clone"), "1")
        and Path("/sys/fs/cgroup/cgroup.controllers").exists()
        and Path("/proc/self/uid_map").exists()
    )


def _linux_text_file_equals(path: Path, expected: str) -> bool:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip() == expected
    except OSError:
        return False


def _operator_config_value(name: str, default: str) -> str:
    return os.environ.get(name) or default


def _operator_config_source_ref(name: str) -> str:
    if os.environ.get(name):
        return "operator_env"
    return "default"


def _service_access_stack_environment(
    service_profile: ServiceStackProfile,
) -> dict[str, dict[str, str]]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return {}
    return {
        "service-access": {
            VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT: _operator_config_value(
                VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT,
                DEFAULT_VAULTWARDEN_ADMIN_INPUT_NAME,
            )
        }
    }


def _service_access_external_input_checks(
    service_profile: ServiceStackProfile,
    *,
    swarm_runtime: MultipassSwarmRuntime,
) -> tuple[VerifyExternalSwarmInput, ...]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return ()
    return (
        VerifyExternalSwarmInput(
            swarm_runtime=swarm_runtime,
            resource_name=_operator_config_value(
                VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT,
                DEFAULT_VAULTWARDEN_ADMIN_INPUT_NAME,
            ),
            source_ref=_operator_config_source_ref(VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT),
        ),
    )

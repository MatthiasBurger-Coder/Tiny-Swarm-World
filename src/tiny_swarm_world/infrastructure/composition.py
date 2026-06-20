from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import cast
from uuid import uuid4

from tiny_swarm_world.application.ports.method_trace import PortMethodTrace
from tiny_swarm_world.application.services.artifacts import (
    ArtifactPrepareStep,
    ArtifactPrepareWorkflow,
    ArtifactVerifyCheck,
    ArtifactVerifyWorkflow,
    ArtifactWorkflowKind,
    EnsureContainerImage,
    EnsureNexusAdminAccess,
    EnsureNexusDockerHostedRepository,
    EnsureNexusDockerProxyRepository,
    EnsureNexusMavenProxyRepository,
    NexusDockerHostedRepositoryConfiguration,
    NexusDockerProxyRepositoryConfiguration,
    NexusMavenProxyRepositoryConfiguration,
    WaitForNexusReady,
)
from tiny_swarm_world.application.services.deployment import (
    DeploymentApplyWorkflow,
    DeploymentWorkflowKind,
    DeploymentVerifyWorkflow,
    EnsureInfisicalSilentInstall,
    EnsureInfisicalSecretItems,
    InfisicalSilentInstallConfig,
    EnsurePortainerEndpoint,
    EnsurePortainerAdminAccess,
    EnsureSonarqubeAdminAccess,
    EnsureSwarmStack,
    EnsureSwarmServiceReadiness,
    VerifySwarmServiceReadiness,
    InfisicalSecretItem,
    InfisicalSecretSyncStep,
    SecretConsumptionVerifier,
    SecretDiscoveryStep,
    SecretEvidenceWriter,
    SecretManifestRenderer,
)
from tiny_swarm_world.application.services.deployment.workflows import DeploymentApplyStep
from tiny_swarm_world.application.services.deployment.service_stack_plan import (
    DEFAULT_PORTAINER_ENDPOINT_NAME,
    build_service_stack_steps,
)
from tiny_swarm_world.application.ports.progress import PortWorkflowProgress
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    STATUS_ERROR,
    PortUI,
)
from tiny_swarm_world.application.services.platform import (
    AsyncWorkflowStep,
    LxcDockerInstallService,
    LxcDockerInstallStep,
    LxcDockerVerifyStep,
    LxcProxyDriftRepairService,
    LxcProxyDriftRepairStep,
    LxcServiceExposureService,
    LxcServiceExposureStep,
    LxcServiceExposureVerifyStep,
    LxcSwarmBootstrapService,
    LxcSwarmBootstrapStep,
    LxcSwarmVerifyStep,
    NodeProviderDestroyManagedNodesStep,
    NodeProviderEnsureNodeStep,
    NodeProviderResetManagedNodesStep,
    NodeProviderSelectionRequest,
    NodeProviderSelectionService,
    NodeProviderVerifyNodeStep,
    PlatformDestroyWorkflow,
    PlatformExposeWorkflow,
    PlatformInitWorkflow,
    PlatformRepairLxcProxyDriftWorkflow,
    PlatformReconcileWorkflow,
    PlatformResetWorkflow,
    PlatformVerifyWorkflow,
    PortainerEndpointVerifyStep,
    PreflightService,
    SocatManager,
)
from tiny_swarm_world.application.services.configuration import ConfigurationValidationService
from tiny_swarm_world.application.services.setup import (
    SetupWorkflow,
    SetupWorkflowPhase,
    SetupWorkflowResult,
)
from tiny_swarm_world.domain.artifacts import DEFAULT_CONTAINER_IMAGE_CONTRACTS, ContainerImageContract
from tiny_swarm_world.domain.deployment import (
    ServiceStackContract,
    ServiceStackProfile,
    service_stack_contracts_for_profile,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.network.port_forwarding_plan import (
    ForwardingStrategy,
    PortForwardingPlan,
)
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
)
from tiny_swarm_world.domain.preflight import (
    LiveConsent,
    PreflightConfiguration,
    ProviderPreflightMetadata,
    default_setup_manifest,
    default_preflight_configuration,
    RequiredDependency,
)
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    AsyncLxcNodeCommandRunner,
    LxcNodeProvider,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
    DockerRegistryMirrorConfiguration,
    LxcContainerDockerRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_proxy_device_runtime import (
    LxcProxyDeviceRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime import (
    LxcContainerImagePublisher,
    LxcContainerRuntime,
    LxcNexusHttpClient,
    LxcPortainerAdminClient,
    LxcPortainerHttpClient,
    LxcSwarmRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.infisical_playwright_client import (
    PlaywrightInfisicalClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.infisical_cli_client import (
    InfisicalCliClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.infisical_bootstrap_http_client import (
    InfisicalBootstrapHttpClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.sonarqube_http_client import (
    SonarqubeHttpClient,
)
from tiny_swarm_world.infrastructure.adapters.configuration import (
    CombinedConfigurationSource,
    EnvironmentConfigurationSource,
    ShellEnvFileConfigurationSource,
)
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.adapters.ui.progress_trace_ui import (
    TerminalMethodTrace,
    TerminalWorkflowProgress,
)
from tiny_swarm_world.infrastructure.adapters.ui.factory_ui import FactoryUI
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe, LxcProviderPreflightProbe
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfig,
    NodeProviderConfigYamlRepository,
)
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)
from tiny_swarm_world.infrastructure.os_types import OsTypes
from tiny_swarm_world.infrastructure.adapters.repositories.verification_evidence_local_repository import (
    VerificationEvidenceLocalRepository,
)
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.logging.progress_trace_logging import (
    CompositeMethodTrace,
    CompositeWorkflowProgress,
    LoggingMethodTrace,
    LoggingWorkflowProgress,
)
from tiny_swarm_world.infrastructure.composition_blocked_workflows import (
    BlockedArtifactWorkflow,
    BlockedDeploymentWorkflow,
)
from tiny_swarm_world.infrastructure.composition_lxc_runtimes import (
    PrepareLxcStackAssets,
    ProviderSelectedLxcDockerRuntime,
    ProviderSelectedLxcProxyDeviceRuntime,
    ProviderSelectedLxcSwarmRuntime,
    selected_lxc_backend,
)
from tiny_swarm_world.infrastructure.composition_models import (
    ApplicationServices,
    ArtifactServices,
    ArtifactWorkflows,
    DeploymentServices,
    DeploymentWorkflows,
    PlatformServices,
    PlatformWorkflows,
    SetupServices,
    SetupWorkflows,
)


DEFAULT_SETUP_SERVICE_PROFILE = ServiceStackProfile.SERVICE_ACCESS
DEFAULT_OPERATOR_CONFIGURATION_ENV_FILE = Path(".tiny-swarm-world/local/live-installation.env")
DEFAULT_PORTAINER_API_URL = "http://localhost:9000"
PORTAINER_STACK_REQUEST_TIMEOUT_ENVIRONMENT = "TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS"
DEFAULT_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS = 180
SEED_INFISICAL_ITEMS_ENVIRONMENT = "TSW_SEED_INFISICAL_ITEMS"
INFISICAL_LOGIN_EMAIL_ENVIRONMENT = "TSW_INFISICAL_LOGIN_EMAIL"
INFISICAL_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"
INFISICAL_READINESS_ATTEMPTS_ENVIRONMENT = "TSW_INFISICAL_READINESS_ATTEMPTS"
INFISICAL_READINESS_INTERVAL_ENVIRONMENT = "TSW_INFISICAL_READINESS_INTERVAL_SECONDS"
INFISICAL_URL_ENVIRONMENT = "TSW_INFISICAL_URL"
INFISICAL_INTERNAL_URL_ENVIRONMENT = "TSW_INFISICAL_INTERNAL_URL"
INFISICAL_ORGANIZATION_ENVIRONMENT = "TSW_INFISICAL_ORGANIZATION"
INFISICAL_ADMIN_FIRST_NAME_ENVIRONMENT = "TSW_INFISICAL_ADMIN_FIRST_NAME"
INFISICAL_ADMIN_LAST_NAME_ENVIRONMENT = "TSW_INFISICAL_ADMIN_LAST_NAME"
DEFAULT_INFISICAL_ORGANIZATION = "Tiny Swarm World"
DEFAULT_INFISICAL_READINESS_ATTEMPTS = 120
DEFAULT_INFISICAL_READINESS_INTERVAL_SECONDS = 5.0
SWARM_REGISTRY_ENDPOINT_ENVIRONMENT = "TSW_SWARM_REGISTRY_ENDPOINT"
DEFAULT_SWARM_REGISTRY_ENDPOINT = "127.0.0.1:5000"
LXC_PROXY_LISTEN_ADDRESS_ENVIRONMENT = "TSW_LXC_PROXY_LISTEN_ADDRESS"
DEFAULT_LXC_PROXY_LISTEN_ADDRESS = "0.0.0.0"
DEFAULT_NEXUS_CACHE_CONTAINER = "tiny-swarm-nexus-cache"
DEFAULT_NEXUS_CACHE_PROXY_PORT = "5001"
NEXUS_DOCKER_HUB_PROXY_REPOSITORY_ENVIRONMENT = "TSW_NEXUS_DOCKER_HUB_PROXY_REPOSITORY"
NEXUS_DOCKER_HUB_PROXY_PORT_ENVIRONMENT = "TSW_NEXUS_DOCKER_HUB_PROXY_PORT"
NEXUS_DOCKER_HUB_PROXY_REMOTE_URL_ENVIRONMENT = "TSW_NEXUS_DOCKER_HUB_PROXY_REMOTE_URL"
DEFAULT_NEXUS_DOCKER_HUB_PROXY_REPOSITORY = "docker-hub-proxy"
DEFAULT_NEXUS_DOCKER_HUB_PROXY_PORT = 5001
DEFAULT_NEXUS_DOCKER_HUB_PROXY_REMOTE_URL = "https://registry-1.docker.io"
DEFAULT_LXC_MANAGER_PROXY_PROFILE = "docker-swarm-manager"
NEXUS_IMAGE_ENVIRONMENT = "TSW_NEXUS_IMAGE"
JENKINS_IMAGE_ENVIRONMENT = "TSW_JENKINS_IMAGE"
SERVICE_ACCESS_DASHBOARD_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_DASHBOARD_IMAGE"
SERVICE_ACCESS_NGINX_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_NGINX_IMAGE"
INFISICAL_IMAGE_ENVIRONMENT = "TSW_INFISICAL_IMAGE"
INFISICAL_POSTGRES_IMAGE_ENVIRONMENT = "TSW_INFISICAL_POSTGRES_IMAGE"
INFISICAL_REDIS_IMAGE_ENVIRONMENT = "TSW_INFISICAL_REDIS_IMAGE"
INFISICAL_ENCRYPTION_KEY_ENVIRONMENT = "TSW_INFISICAL_ENCRYPTION_KEY"
INFISICAL_AUTH_SECRET_ENVIRONMENT = "TSW_INFISICAL_AUTH_SECRET"
INFISICAL_POSTGRES_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_POSTGRES_PASSWORD"
INFISICAL_REDIS_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_REDIS_PASSWORD"
REGISTRY_ENDPOINT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(?::\d{1,5})?$")
DEFAULT_LXC_PLATFORM_NODES = (
    NodeSpec("swarm-manager", NodeRole.MANAGER, NodeProviderKind.LXC_NATIVE),
    NodeSpec("swarm-worker-1", NodeRole.WORKER, NodeProviderKind.LXC_NATIVE),
    NodeSpec("swarm-worker-2", NodeRole.WORKER, NodeProviderKind.LXC_NATIVE),
)
LXC_BACKEND_REQUIRED_REASON = "lxc_backend_required"
_LXC_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
LXC_BACKEND_REQUIRED_MESSAGE = (
    "LXC-native workflows require an available or explicitly selected Incus or LXD backend."
)
_BlockedArtifactWorkflow = BlockedArtifactWorkflow
_BlockedDeploymentWorkflow = BlockedDeploymentWorkflow
_ProviderSelectedLxcDockerRuntime = ProviderSelectedLxcDockerRuntime
_ProviderSelectedLxcSwarmRuntime = ProviderSelectedLxcSwarmRuntime
_PrepareLxcStackAssets = PrepareLxcStackAssets
_ProviderSelectedLxcProxyDeviceRuntime = ProviderSelectedLxcProxyDeviceRuntime
_selected_lxc_backend = selected_lxc_backend


class _BlockedPlatformProviderStep:
    returns_verification_result = True

    def __init__(
        self,
        *,
        target_id: str,
        provider_request: NodeProviderSelectionRequest,
        message: str,
        reason: str,
    ):
        self.verification_target_id = target_id
        self.provider_request = provider_request
        self.message = message
        self.reason = reason

    async def run(self) -> VerificationResult:
        await asyncio.sleep(0)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message=self.message,
            evidence={
                "phase": "pre_apply",
                "reason": self.reason,
                "requested_provider": self.provider_request.requested_provider.value,
            },
        )


class _VerifiedPlatformProviderStep:
    returns_verification_result = True

    def __init__(
        self,
        *,
        target_id: str,
        provider_request: NodeProviderSelectionRequest,
        message: str,
        reason: str,
    ):
        self.verification_target_id = target_id
        self.provider_request = provider_request
        self.message = message
        self.reason = reason

    async def run(self) -> VerificationResult:
        await asyncio.sleep(0)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message=self.message,
            evidence={
                "phase": "verify",
                "reason": self.reason,
                "requested_provider": self.provider_request.requested_provider.value,
            },
        )


class _WslSocatExposeStep:
    returns_verification_result = True
    verification_target_id = "platform:expose:wsl-socat"

    def __init__(
        self,
        socat_manager: SocatManager,
        *,
        service_profile: ServiceStackProfile,
        live_consent: LiveConsent | None,
        os_type: OsTypes | None = None,
    ) -> None:
        self.socat_manager = socat_manager
        self.service_profile = service_profile
        self.live_consent = live_consent
        self.os_type = os_type

    async def run(self) -> VerificationResult:
        os_type = self.os_type or OsTypes.detect_current()
        plans = _wsl_socat_forwarding_plans(self.service_profile)
        commands = self.socat_manager.set_service_socat_ports(os_type, plans)
        if not commands:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="WSL port exposure is not required for this host type.",
                evidence={
                    "phase": "verify",
                    "classification": "not_required",
                    "os_type": str(getattr(os_type, "value", os_type)),
                },
            )
        if self.live_consent is None or not self.live_consent.accepted:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.BLOCKED,
                message="WSL port exposure requires accepted live infrastructure consent.",
                evidence={
                    "phase": "pre_apply",
                    "classification": "live_mutation_required",
                    "os_type": str(getattr(os_type, "value", os_type)),
                    "planned_forward_count": str(len(commands)),
                },
            )
        if shutil.which("socat") is None:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.BLOCKED,
                message="WSL port exposure requires the configured forwarding executable.",
                evidence={
                    "phase": "pre_apply",
                    "classification": "socat_missing",
                    "os_type": str(getattr(os_type, "value", os_type)),
                    "remediation_hint": "Install the WSL forwarding tool and rerun platform expose.",
                },
            )

        started_count = 0
        existing_count = 0
        failed_count = 0
        for command in commands:
            pattern = command.shell_command
            if await _wsl_socat_process_exists(pattern):
                existing_count += 1
                continue
            if await _start_wsl_socat_command(pattern):
                started_count += 1
            else:
                failed_count += 1
        status = (
            VerificationStatus.VERIFIED
            if failed_count == 0
            else VerificationStatus.FAILED_TO_APPLY
        )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=status,
            message=_wsl_socat_expose_message(status),
            evidence={
                "phase": "apply",
                "classification": (
                    "wsl_socat_exposed"
                    if status == VerificationStatus.VERIFIED
                    else "wsl_socat_expose_failed"
                ),
                "os_type": str(getattr(os_type, "value", os_type)),
                "planned_forward_count": str(len(commands)),
                "started_count": str(started_count),
                "existing_count": str(existing_count),
                "failed_count": str(failed_count),
            },
        )


def configure_infrastructure_container() -> None:
    infra_core_container.register(PathFactory)
    infra_core_container.register(FileManager)


def build_application_logger():
    return LoggerFactory.get_logger("application")


def build_preflight_service(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    configuration_validation: ConfigurationValidationService | None = None,
) -> PreflightService:
    port_registry = PortRegistryYamlRepository().load()
    return PreflightService(
        HostPreflightProbe(),
        _preflight_configuration_for_provider(service_profile, node_provider_request),
        configuration_validation=configuration_validation,
        port_registry=port_registry,
    )


def build_configuration_validation_service(
    env_file: Path | None = None,
) -> ConfigurationValidationService:
    resolved_env_file = env_file or Path(
        os.environ.get("TSW_INSTALL_ENV_FILE", DEFAULT_OPERATOR_CONFIGURATION_ENV_FILE)
    )
    return ConfigurationValidationService(
        CombinedConfigurationSource(
            (
                ShellEnvFileConfigurationSource(resolved_env_file),
                EnvironmentConfigurationSource(),
            )
        )
    )


def build_compose_file_repository() -> PortComposeFileRepository:
    return ComposeFileRepositoryYaml()


def build_post_install_preflight_service(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    configuration_validation: ConfigurationValidationService | None = None,
) -> PreflightService:
    configuration = _preflight_configuration_for_provider(service_profile, node_provider_request)
    return PreflightService(
        HostPreflightProbe(),
        replace(configuration, required_ports=()),
        configuration_validation=configuration_validation,
    )


def _build_workflow_progress_sink(ui: PortUI | None = None) -> PortWorkflowProgress:
    sinks: list[PortWorkflowProgress] = [
        LoggingWorkflowProgress(LoggerFactory.get_logger("WorkflowProgress"))
    ]
    if ui is not None:
        sinks.append(TerminalWorkflowProgress(ui))
    return CompositeWorkflowProgress(sinks)


def _build_method_trace_sink(ui: PortUI | None = None) -> PortMethodTrace:
    sinks: list[PortMethodTrace] = [
        LoggingMethodTrace(LoggerFactory.get_logger("MethodTrace"))
    ]
    if ui is not None:
        sinks.append(TerminalMethodTrace(ui))
    return CompositeMethodTrace(sinks)


def _new_installation_trace_correlation_id() -> str:
    return f"trace-installation-{uuid4().hex}"


def build_setup_ui(*, test_mode: bool = False) -> PortUI:
    return FactoryUI().get_ui(instances=(), test_mode=test_mode)


async def run_setup_with_terminal_status(
    live_consent: LiveConsent,
    action: str,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
) -> SetupWorkflowResult:
    if not live_consent.accepted:
        raise ValueError("setup run requires accepted live consent")

    ui = build_setup_ui()
    ui.start_in_thread()
    try:
        services = build_setup_services(
            live_consent,
            service_profile=service_profile,
            node_provider_request=node_provider_request,
            ui=ui,
            configuration_validation=build_configuration_validation_service(),
        )
        match action:
            case "run":
                result = await services.workflows.run.run()
            case _:
                raise ValueError(f"Unsupported setup workflow action: {action}")
        ui.update_status(
            AGGREGATE_INSTANCE,
            task="setup run",
            step="finished",
            result=_setup_result_status(result),
        )
        return result
    except Exception:
        ui.update_status(
            AGGREGATE_INSTANCE,
            task="setup run",
            step="exception",
            result=STATUS_ERROR,
        )
        raise
    finally:
        if ui.ui_thread is not None:
            await ui.ui_thread


def _setup_result_status(result: SetupWorkflowResult) -> str:
    return result.status.value


def build_platform_services(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    live_consent: LiveConsent | None = None,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
    trace_correlation_id: str | None = None,
) -> PlatformServices:
    configure_infrastructure_container()
    node_provider_config_repository = NodeProviderConfigYamlRepository()
    provider_config = node_provider_config_repository.load()
    provider_request = node_provider_request or _node_provider_request_from_config(provider_config)
    workflow_progress = _build_workflow_progress_sink(ui)
    method_trace = _build_method_trace_sink(ui)
    trace_correlation_id = trace_correlation_id or _new_installation_trace_correlation_id()

    command_workflow = CommandWorkflow()
    verification_evidence_repository = VerificationEvidenceLocalRepository()
    preflight = _build_preflight_service_for_request(service_profile, provider_request)
    post_install_preflight = _build_post_install_preflight_service_for_request(
        service_profile,
        provider_request,
    )
    lxc_runner = AsyncLxcNodeCommandRunner()
    lxc_node_provider = LxcNodeProvider(
        config_repository=node_provider_config_repository,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted
    )
    node_provider_selection = NodeProviderSelectionService(
        LxcProviderPreflightProbe(
            wsl_lxc_capability_available=_wsl_lxc_lifecycle_capability_available,
        ),
        lxc_node_provider,
        lxc_node_provider,
    )
    lxc_docker_runtime = _ProviderSelectedLxcDockerRuntime(
        provider_selection=node_provider_selection,
        provider_request=provider_request,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
        registry_mirror_configuration=_lxc_docker_registry_mirror_configuration,
        docker_runtime_factory=LxcContainerDockerRuntime,
    )
    lxc_docker_install = LxcDockerInstallService(lxc_docker_runtime)
    lxc_docker_verify = LxcDockerInstallService(
        _ProviderSelectedLxcDockerRuntime(
            provider_selection=node_provider_selection,
            provider_request=provider_request,
            runner=lxc_runner,
            allow_live_mutation=False,
            allow_live_inspection=True,
            registry_mirror_configuration=_lxc_docker_registry_mirror_configuration,
            docker_runtime_factory=LxcContainerDockerRuntime,
        )
    )
    lxc_swarm_runtime = _ProviderSelectedLxcSwarmRuntime(
        provider_selection=node_provider_selection,
        provider_request=provider_request,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
        proxy_runtime_factory=LxcProxyDeviceRuntime,
    )
    lxc_swarm_bootstrap = LxcSwarmBootstrapService(
        lxc_swarm_runtime,
        lxc_swarm_runtime,
    )
    lxc_swarm_verify = LxcSwarmBootstrapService(
        _ProviderSelectedLxcSwarmRuntime(
            provider_selection=node_provider_selection,
            provider_request=provider_request,
            runner=lxc_runner,
            allow_live_mutation=False,
            allow_live_inspection=True,
            proxy_runtime_factory=LxcProxyDeviceRuntime,
        ),
        lxc_swarm_runtime,
    )
    lxc_proxy_runtime = _ProviderSelectedLxcProxyDeviceRuntime(
        provider_selection=node_provider_selection,
        provider_request=provider_request,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
    )
    lxc_service_exposure = LxcServiceExposureService(
        lxc_proxy_runtime,
        gateway_node=_lxc_manager_node(),
        manager_profile_name=DEFAULT_LXC_MANAGER_PROXY_PROFILE,
        setup_manifest=default_setup_manifest(service_profile=service_profile),
        listen_address=_lxc_proxy_listen_address(),
    )
    lxc_service_exposure_verify = LxcServiceExposureService(
        _ProviderSelectedLxcProxyDeviceRuntime(
            provider_selection=node_provider_selection,
            provider_request=provider_request,
            runner=lxc_runner,
            allow_live_mutation=False,
            allow_live_inspection=True,
        ),
        gateway_node=_lxc_manager_node(),
        manager_profile_name=DEFAULT_LXC_MANAGER_PROXY_PROFILE,
        setup_manifest=default_setup_manifest(service_profile=service_profile),
        listen_address=_lxc_proxy_listen_address(),
    )
    lxc_proxy_drift_repair = LxcProxyDriftRepairService(
        lxc_proxy_runtime,
        gateway_node=_lxc_manager_node(),
        manager_profile_name=DEFAULT_LXC_MANAGER_PROXY_PROFILE,
        setup_manifest=default_setup_manifest(service_profile=service_profile),
        listen_address=_lxc_proxy_listen_address(),
    )
    socat_manager = SocatManager()
    init_steps = _platform_init_steps(
        provider_request=provider_request,
        node_provider_selection=node_provider_selection,
        lxc_steps=(
            LxcDockerInstallStep(lxc_docker_install, DEFAULT_LXC_PLATFORM_NODES),
            LxcSwarmBootstrapStep(lxc_swarm_bootstrap, DEFAULT_LXC_PLATFORM_NODES),
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
                    method_trace=method_trace,
                    trace_correlation_id=trace_correlation_id,
                )
                if live_consent is not None
                else None
            ),
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        reconcile=PlatformReconcileWorkflow(
            _platform_reconcile_steps(
                provider_request=provider_request,
                node_provider_selection=node_provider_selection,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        expose=PlatformExposeWorkflow(
            _platform_expose_steps(
                lxc_service_exposure,
                socat_manager,
                service_profile=ServiceStackProfile(service_profile),
                live_consent=live_consent,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        repair_lxc_proxy_drift=PlatformRepairLxcProxyDriftWorkflow(
            _platform_repair_lxc_proxy_drift_steps(lxc_proxy_drift_repair),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        reset=PlatformResetWorkflow(
            _platform_reset_steps(
                provider_request,
                node_provider_selection,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        destroy=PlatformDestroyWorkflow(
            _platform_destroy_steps(
                provider_request,
                node_provider_selection,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        verify=PlatformVerifyWorkflow(
            _platform_verify_steps(
                post_install_preflight,
                provider_request=provider_request,
                node_provider_selection=node_provider_selection,
                lxc_docker_install=lxc_docker_verify,
                lxc_swarm_bootstrap=lxc_swarm_verify,
                lxc_service_exposure=lxc_service_exposure_verify,
            ),
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
            verify_retry_attempts=6,
            verify_retry_delay_seconds=10.0,
        ),
    )

    return PlatformServices(
        command_workflow=command_workflow,
        lxc_docker_install=lxc_docker_install,
        lxc_proxy_drift_repair=lxc_proxy_drift_repair,
        lxc_service_exposure=lxc_service_exposure,
        lxc_swarm_bootstrap=lxc_swarm_bootstrap,
        preflight=preflight,
        lxc_node_provider=lxc_node_provider,
        node_provider_selection=node_provider_selection,
        socat_manager=socat_manager,
        workflows=workflows,
    )


def build_artifact_services_for_provider(
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
) -> ArtifactServices:
    provider_request = node_provider_request or _default_node_provider_request()
    backend = _lxc_backend_for_provider_request(provider_request)
    if backend is not None:
        return build_lxc_artifact_services(backend=backend, ui=ui)
    return ArtifactServices(
        workflows=ArtifactWorkflows(
            prepare=cast(
                ArtifactPrepareWorkflow,
                _BlockedArtifactWorkflow(
                    ArtifactWorkflowKind.PREPARE,
                    LXC_BACKEND_REQUIRED_REASON,
                ),
            ),
            verify=cast(
                ArtifactVerifyWorkflow,
                _BlockedArtifactWorkflow(
                    ArtifactWorkflowKind.VERIFY,
                    LXC_BACKEND_REQUIRED_REASON,
                ),
            ),
        )
    )


def build_lxc_artifact_services(
    *,
    backend: ManagedLxcBackend,
    ui: PortUI | None = None,
) -> ArtifactServices:
    nexus_admin_password = _operator_secret_value("TSW_NEXUS_ADMIN_PASSWORD")
    nexus_client = LxcNexusHttpClient(backend=backend)
    container_runtime = LxcContainerRuntime(backend=backend)
    image_publisher = LxcContainerImagePublisher(
        backend=backend,
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
        ui=ui,
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
        EnsureNexusDockerProxyRepository(
            nexus_client=nexus_client,
            configuration=NexusDockerProxyRepositoryConfiguration(
                repository_name=_nexus_docker_hub_proxy_repository_name(),
                http_port=_nexus_docker_hub_proxy_port(),
                remote_url=_nexus_docker_hub_proxy_remote_url(),
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
        for contract in _container_image_contracts_from_environment()
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


def build_deployment_services_for_provider(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
) -> DeploymentServices:
    provider_request = node_provider_request or _default_node_provider_request()
    backend = _lxc_backend_for_provider_request(provider_request)
    if backend is not None:
        return build_lxc_deployment_services(
            service_profile=service_profile,
            backend=backend,
            ui=ui,
        )
    return DeploymentServices(
        workflows=DeploymentWorkflows(
            bootstrap=cast(
                DeploymentApplyWorkflow,
                _BlockedDeploymentWorkflow(
                    DeploymentWorkflowKind.BOOTSTRAP,
                    LXC_BACKEND_REQUIRED_REASON,
                ),
            ),
            apply=cast(
                DeploymentApplyWorkflow,
                _BlockedDeploymentWorkflow(
                    DeploymentWorkflowKind.APPLY,
                    LXC_BACKEND_REQUIRED_REASON,
                ),
            ),
            verify=cast(
                DeploymentVerifyWorkflow,
                _BlockedDeploymentWorkflow(
                    DeploymentWorkflowKind.VERIFY,
                    LXC_BACKEND_REQUIRED_REASON,
                ),
            ),
        )
    )


def build_lxc_deployment_services(
    *,
    backend: ManagedLxcBackend,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    ui: PortUI | None = None,
) -> DeploymentServices:
    selected_service_profile = ServiceStackProfile(service_profile)
    service_stack_contracts = service_stack_contracts_for_profile(selected_service_profile)
    swarm_runtime = LxcSwarmRuntime(backend=backend)
    stack_environment = _deployment_stack_environment(selected_service_profile)
    secret_manifest_entries = SecretManifestRenderer().run()
    compose_repository = ComposeFileRepositoryYaml()
    portainer_admin_client = LxcPortainerAdminClient(backend=backend)
    portainer_client = LxcPortainerHttpClient(
        backend=backend,
        username="admin",
        password=_operator_secret_value("TSW_PORTAINER_ADMIN_PASSWORD"),
        stack_request_timeout_seconds=_operator_config_int(
            PORTAINER_STACK_REQUEST_TIMEOUT_ENVIRONMENT,
            DEFAULT_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS,
            minimum=1,
        ),
    )
    stack_steps = {
        contract.stack_name: EnsureSwarmStack(
            compose_repository=compose_repository,
            swarm_runtime=swarm_runtime,
            service_stack=contract,
            stack_environment=stack_environment.get(contract.stack_name),
        )
        for contract in service_stack_contracts
    }
    bootstrap_steps = (
        stack_steps["portainer"],
        EnsurePortainerAdminAccess(
            portainer_admin_client=portainer_admin_client,
            username="admin",
            password=_operator_secret_value("TSW_PORTAINER_ADMIN_PASSWORD"),
            max_attempts=60,
            wait_seconds=5,
            ui=ui,
        ),
        EnsurePortainerEndpoint(
            portainer_client=portainer_client,
            endpoint_name=DEFAULT_PORTAINER_ENDPOINT_NAME,
        ),
        stack_steps["nexus"],
    )
    application_steps: tuple[object, ...] = build_service_stack_steps(
        compose_repository=compose_repository,
        deployment_gateway=portainer_client,
        service_profile=selected_service_profile,
        excluded_stack_names=("nexus",),
        stack_environments=stack_environment,
    )
    application_steps = _with_post_stack_steps(
        application_steps,
        "sonarqube",
        (
            EnsureSonarqubeAdminAccess(
                sonarqube_client=SonarqubeHttpClient("http://localhost:9001"),
                username=_operator_config_value("TSW_SONARQUBE_ADMIN_USERNAME", "admin"),
                password=lambda: _required_operator_secret_value("TSW_SONARQUBE_ADMIN_PASSWORD"),
                max_attempts=120,
                wait_seconds=5,
            ),
        ),
    )
    infisical_cli_client = InfisicalCliClient()
    service_stack_by_name = {contract.stack_name: contract for contract in service_stack_contracts}
    infisical_apply_readiness_steps = _infisical_apply_readiness_steps(
        selected_service_profile,
        swarm_runtime=swarm_runtime,
        service_stack_by_name=service_stack_by_name,
    )
    infisical_bootstrap_steps = _infisical_bootstrap_steps(
        selected_service_profile,
        cli=infisical_cli_client,
    )
    secret_discovery_step = SecretDiscoveryStep(manifest_entries=secret_manifest_entries)
    infisical_secret_sync_step = InfisicalSecretSyncStep(
        cli=infisical_cli_client,
        manifest_entries=secret_manifest_entries,
    )
    secret_consumption_step = SecretConsumptionVerifier(
        manifest_entries=secret_manifest_entries,
        stack_environment=stack_environment,
    )
    secret_evidence_step = SecretEvidenceWriter(
        discovery=secret_discovery_step,
        sync=infisical_secret_sync_step,
        consumption=secret_consumption_step,
    )
    infisical_secret_management_steps = (
        secret_discovery_step,
        *infisical_bootstrap_steps,
        infisical_secret_sync_step,
        secret_consumption_step,
        secret_evidence_step,
    )
    infisical_seed_steps = _infisical_secret_seed_steps(selected_service_profile)
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
                cast(
                    tuple[DeploymentApplyStep, ...],
                    _with_infisical_post_apply_steps(
                        application_steps,
                        (
                            *infisical_apply_readiness_steps,
                            *infisical_secret_management_steps,
                            *infisical_seed_steps,
                        ),
                    ),
                ),
                pre_apply_steps=(
                    _PrepareLxcStackAssets(swarm_runtime, "swagger"),
                ),
            ),
            verify=DeploymentVerifyWorkflow(readiness_checks),
        )
    )


def build_setup_services(
    live_consent: LiveConsent,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
    configuration_validation: ConfigurationValidationService | None = None,
) -> SetupServices:
    preflight = _build_preflight_service_for_request(
        service_profile,
        node_provider_request,
        configuration_validation=configuration_validation,
    )
    trace_correlation_id = _new_installation_trace_correlation_id()
    platform = _build_platform_services_for_request(
        service_profile,
        live_consent,
        node_provider_request,
        ui=ui,
        trace_correlation_id=trace_correlation_id,
    )
    artifacts = build_artifact_services_for_provider(
        node_provider_request=node_provider_request,
        ui=ui,
    )
    deployment = _build_deployment_services_for_request(
        service_profile=service_profile,
        node_provider_request=node_provider_request,
        ui=ui,
    )
    workflow_progress = _build_workflow_progress_sink(ui)
    method_trace = _build_method_trace_sink(ui)

    def traced_phase(name: str, runner) -> SetupWorkflowPhase:
        return SetupWorkflowPhase(
            name,
            runner,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        )

    return SetupServices(
        workflows=SetupWorkflows(
            run=SetupWorkflow(
                (
                    traced_phase("preflight", lambda: preflight.run(live_consent)),
                    traced_phase("platform init", lambda: platform.workflows.init.run()),
                    traced_phase(
                        "platform reconcile",
                        lambda: platform.workflows.reconcile.run(),
                    ),
                    traced_phase(
                        "platform expose",
                        lambda: platform.workflows.expose.run(),
                    ),
                    traced_phase(
                        "deployment bootstrap",
                        lambda: deployment.workflows.bootstrap.run(),
                    ),
                    traced_phase(
                        "artifacts prepare",
                        lambda: artifacts.workflows.prepare.run(),
                    ),
                    traced_phase(
                        "artifacts verify",
                        lambda: artifacts.workflows.verify.run(),
                    ),
                    traced_phase(
                        "deployment apply",
                        lambda: deployment.workflows.apply.run(),
                    ),
                    traced_phase(
                        "deployment verify",
                        lambda: deployment.workflows.verify.run(),
                    ),
                    traced_phase("platform verify", lambda: platform.workflows.verify.run()),
                ),
                live_consent=live_consent,
                progress=workflow_progress,
                method_trace=method_trace,
                trace_correlation_id=trace_correlation_id,
            )
        )
    )


def build_application_services(
    live_consent: LiveConsent | None = None,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
) -> ApplicationServices:
    return ApplicationServices(
        platform=_build_platform_services_for_request(
            service_profile,
            live_consent,
            node_provider_request,
            ui=ui,
        ),
        artifacts=build_artifact_services_for_provider(
            node_provider_request=node_provider_request
        ),
        deployment=_build_deployment_services_for_request(
            service_profile=service_profile,
            node_provider_request=node_provider_request,
            ui=ui,
        ),
    )


def _build_platform_services_for_request(
    service_profile: ServiceStackProfile | str,
    live_consent: LiveConsent | None,
    node_provider_request: NodeProviderSelectionRequest | None,
    ui: PortUI | None = None,
    trace_correlation_id: str | None = None,
) -> PlatformServices:
    if node_provider_request is None:
        if ui is None and trace_correlation_id is None:
            return build_platform_services(
                service_profile=service_profile,
                live_consent=live_consent,
            )
        return build_platform_services(
            service_profile=service_profile,
            live_consent=live_consent,
            ui=ui,
            trace_correlation_id=trace_correlation_id,
        )
    if ui is None and trace_correlation_id is None:
        return build_platform_services(
            service_profile=service_profile,
            live_consent=live_consent,
            node_provider_request=node_provider_request,
        )
    return build_platform_services(
        service_profile=service_profile,
        live_consent=live_consent,
        node_provider_request=node_provider_request,
        ui=ui,
        trace_correlation_id=trace_correlation_id,
    )


def _build_deployment_services_for_request(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
    ui: PortUI | None = None,
) -> DeploymentServices:
    if ui is None:
        return build_deployment_services_for_provider(
            service_profile=service_profile,
            node_provider_request=node_provider_request,
        )
    return build_deployment_services_for_provider(
        service_profile=service_profile,
        node_provider_request=node_provider_request,
        ui=ui,
    )


def _build_preflight_service_for_request(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
    configuration_validation: ConfigurationValidationService | None = None,
) -> PreflightService:
    if node_provider_request is None:
        return build_preflight_service(
            service_profile=service_profile,
            configuration_validation=configuration_validation,
        )
    return build_preflight_service(
        service_profile=service_profile,
        node_provider_request=node_provider_request,
        configuration_validation=configuration_validation,
    )


def _build_post_install_preflight_service_for_request(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
    configuration_validation: ConfigurationValidationService | None = None,
) -> PreflightService:
    if node_provider_request is None:
        return build_post_install_preflight_service(
            service_profile=service_profile,
            configuration_validation=configuration_validation,
        )
    return build_post_install_preflight_service(
        service_profile=service_profile,
        node_provider_request=node_provider_request,
        configuration_validation=configuration_validation,
    )


def _lxc_backend_for_provider_request(
    provider_request: NodeProviderSelectionRequest,
) -> ManagedLxcBackend | None:
    if provider_request.requested_provider != NodeProviderKind.LXC_NATIVE:
        return None
    if provider_request.preferred_backend is not None:
        return provider_request.preferred_backend
    for backend in provider_request.backend_candidates:
        if shutil.which(_LXC_BACKEND_CLI[backend]):
            return backend
    return None


def _default_node_provider_request() -> NodeProviderSelectionRequest:
    provider_config = NodeProviderConfigYamlRepository().load()
    return _node_provider_request_from_config(provider_config)


def _node_provider_request_from_config(
    provider_config: NodeProviderConfig,
) -> NodeProviderSelectionRequest:
    return NodeProviderSelectionRequest(
        requested_provider=provider_config.default_provider,
        preferred_backend=provider_config.preferred_backend,
        backend_candidates=provider_config.backend_candidates,
    )


def _preflight_configuration_for_provider(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
) -> PreflightConfiguration:
    configuration = default_preflight_configuration(service_profile=service_profile)
    provider_request = node_provider_request or _default_node_provider_request()
    if provider_request.requested_provider is not NodeProviderKind.LXC_NATIVE:
        return replace(
            configuration,
            provider_metadata=ProviderPreflightMetadata(
                provider=provider_request.requested_provider.value,
                generic_checks=configuration.provider_metadata.generic_checks,
            ),
        )
    backend = _lxc_backend_for_provider_request(provider_request)
    if backend is None:
        if not provider_request.backend_candidates:
            raise ValueError(
                "LXC-native preflight requires at least one managed backend candidate."
            )
        provider_dependencies = tuple(
            RequiredDependency(_LXC_BACKEND_CLI[candidate])
            for candidate in provider_request.backend_candidates
        )
        backend_label = "auto"
        provider_checks = tuple(
            f"backend-cli:{_LXC_BACKEND_CLI[candidate]}"
            for candidate in provider_request.backend_candidates
        )
    else:
        provider_dependencies = (RequiredDependency(_LXC_BACKEND_CLI[backend]),)
        backend_label = backend.value
        provider_checks = (f"backend-cli:{_LXC_BACKEND_CLI[backend]}",)
    return replace(
        configuration,
        required_dependencies=(
            *configuration.required_dependencies,
            *provider_dependencies,
        ),
        provider_metadata=ProviderPreflightMetadata(
            provider=provider_request.requested_provider.value,
            backend=backend_label,
            generic_checks=configuration.provider_metadata.generic_checks,
            provider_checks=provider_checks,
            daemon_checks=(
                "managed-lxc-daemon-selected-backend",
            ),
            network_checks=(
                "selected-backend-control-network",
            ),
            resource_expectations=(
                "selected-backend-storage-pool",
                "docker-swarm-profile",
            ),
        ),
    )


def _platform_init_steps(
    *,
    provider_request: NodeProviderSelectionRequest,
    node_provider_selection: NodeProviderSelectionService,
    lxc_steps: tuple[AsyncWorkflowStep, ...],
) -> tuple[AsyncWorkflowStep, ...]:
    node_steps = tuple(
        NodeProviderEnsureNodeStep(node, node_provider_selection, provider_request)
        for node in DEFAULT_LXC_PLATFORM_NODES
    )
    return (*node_steps, *lxc_steps)


def _platform_reconcile_steps(
    *,
    provider_request: NodeProviderSelectionRequest,
    node_provider_selection: NodeProviderSelectionService,
) -> tuple[AsyncWorkflowStep, ...]:
    return tuple(
        NodeProviderEnsureNodeStep(node, node_provider_selection, provider_request)
        for node in DEFAULT_LXC_PLATFORM_NODES
    )


def _platform_expose_steps(
    lxc_service_exposure: LxcServiceExposureService,
    socat_manager: SocatManager,
    *,
    service_profile: ServiceStackProfile,
    live_consent: LiveConsent | None,
) -> tuple[AsyncWorkflowStep, ...]:
    return (
        LxcServiceExposureStep(lxc_service_exposure),
        _WslSocatExposeStep(
            socat_manager,
            service_profile=ServiceStackProfile(service_profile),
            live_consent=live_consent,
        ),
    )


def _platform_repair_lxc_proxy_drift_steps(
    lxc_proxy_drift_repair: LxcProxyDriftRepairService,
) -> tuple[AsyncWorkflowStep, ...]:
    return (LxcProxyDriftRepairStep(lxc_proxy_drift_repair),)


def _platform_verify_steps(
    post_install_preflight: PreflightService,
    *,
    provider_request: NodeProviderSelectionRequest,
    node_provider_selection: NodeProviderSelectionService,
    lxc_docker_install: LxcDockerInstallService,
    lxc_swarm_bootstrap: LxcSwarmBootstrapService,
    lxc_service_exposure: LxcServiceExposureService,
) -> tuple[AsyncWorkflowStep, ...]:
    node_steps = tuple(
        NodeProviderVerifyNodeStep(node, node_provider_selection, provider_request)
        for node in DEFAULT_LXC_PLATFORM_NODES
    )
    return (
        post_install_preflight,
        *node_steps,
        LxcDockerVerifyStep(lxc_docker_install, DEFAULT_LXC_PLATFORM_NODES),
        LxcSwarmVerifyStep(lxc_swarm_bootstrap, DEFAULT_LXC_PLATFORM_NODES),
        LxcServiceExposureVerifyStep(lxc_service_exposure),
        _portainer_endpoint_verify_step(provider_request),
    )


def _portainer_endpoint_verify_step(
    provider_request: NodeProviderSelectionRequest,
) -> AsyncWorkflowStep:
    backend = _lxc_backend_for_provider_request(provider_request)
    if backend is None:
        return _BlockedPlatformProviderStep(
            target_id=PortainerEndpointVerifyStep.verification_target_id,
            provider_request=provider_request,
            message="Portainer endpoint verification requires a selected LXC backend.",
            reason=LXC_BACKEND_REQUIRED_REASON,
        )
    return PortainerEndpointVerifyStep(
        EnsurePortainerEndpoint(
            portainer_client=LxcPortainerHttpClient(
                backend=backend,
                username="admin",
                password=_operator_secret_value("TSW_PORTAINER_ADMIN_PASSWORD"),
                stack_request_timeout_seconds=_operator_config_int(
                    PORTAINER_STACK_REQUEST_TIMEOUT_ENVIRONMENT,
                    DEFAULT_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS,
                    minimum=1,
                ),
            ),
            endpoint_name=DEFAULT_PORTAINER_ENDPOINT_NAME,
            max_attempts=1,
            wait_seconds=0,
        )
    )


def _wsl_socat_forwarding_plans(
    service_profile: ServiceStackProfile,
) -> tuple[PortForwardingPlan, ...]:
    return tuple(
        PortForwardingPlan(
            strategy=ForwardingStrategy.WSL2_SOCAT,
            service=requirement.service,
            listen_port=requirement.port,
            target_port=requirement.port,
            remediation=("Start WSL socat forwarding after live consent.",),
        )
        for requirement in default_setup_manifest(
            service_profile=service_profile
        ).required_ports
    )


async def _wsl_socat_process_exists(pattern: str) -> bool:
    process = await asyncio.create_subprocess_exec(
        "pgrep",
        "-f",
        pattern,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return await process.wait() == 0


async def _start_wsl_socat_command(command: str) -> bool:
    process = await asyncio.create_subprocess_exec(
        "sh",
        "-lc",
        f"nohup {command} >/dev/null 2>&1 &",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return await process.wait() == 0


def _wsl_socat_expose_message(status: VerificationStatus) -> str:
    if status == VerificationStatus.VERIFIED:
        return "WSL port exposure is configured for published service ports."
    return "WSL port exposure failed for one or more published service ports."


def _platform_reset_steps(
    provider_request: NodeProviderSelectionRequest,
    node_provider_selection: NodeProviderSelectionService,
) -> tuple[AsyncWorkflowStep, ...]:
    return (
        NodeProviderResetManagedNodesStep(
            DEFAULT_LXC_PLATFORM_NODES,
            node_provider_selection,
            provider_request,
        ),
    )


def _platform_destroy_steps(
    provider_request: NodeProviderSelectionRequest,
    node_provider_selection: NodeProviderSelectionService,
) -> tuple[AsyncWorkflowStep, ...]:
    return (
        NodeProviderDestroyManagedNodesStep(
            DEFAULT_LXC_PLATFORM_NODES,
            node_provider_selection,
            provider_request,
        ),
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
        _wsl_unprivileged_userns_clone_available()
        and Path("/sys/fs/cgroup/cgroup.controllers").exists()
        and Path("/proc/self/uid_map").exists()
    )


def _wsl_unprivileged_userns_clone_available(
    path: Path = Path("/proc/sys/kernel/unprivileged_userns_clone"),
) -> bool:
    if not path.exists():
        return True
    return _linux_text_file_equals(path, "1")


def _linux_text_file_equals(path: Path, expected: str) -> bool:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip() == expected
    except OSError:
        return False


def _operator_config_value(name: str, default: str) -> str:
    return os.environ.get(name) or default


def _operator_config_int(name: str, default: int, *, minimum: int) -> int:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value, 10)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return value


def _operator_config_float(name: str, default: float, *, minimum: float) -> float:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum:g}.")
    return value


def _lxc_proxy_listen_address() -> str:
    address = _operator_config_value(
        LXC_PROXY_LISTEN_ADDRESS_ENVIRONMENT,
        DEFAULT_LXC_PROXY_LISTEN_ADDRESS,
    ).strip()
    if address not in {"127.0.0.1", "0.0.0.0"}:
        raise ValueError("LXC proxy listen address must be 127.0.0.1 or 0.0.0.0.")
    return address


def _lxc_docker_registry_mirror_configuration() -> DockerRegistryMirrorConfiguration | None:
    mirror_url = os.getenv("TSW_LXC_DOCKER_REGISTRY_MIRROR", "").strip()
    if mirror_url:
        return DockerRegistryMirrorConfiguration(mirror_url)
    mirror_url = _auto_detect_nexus_cache_registry_mirror()
    if not mirror_url:
        return None
    return DockerRegistryMirrorConfiguration(mirror_url)


def _auto_detect_nexus_cache_registry_mirror() -> str:
    container_name = os.getenv("TSW_NEXUS_CACHE_CONTAINER", DEFAULT_NEXUS_CACHE_CONTAINER).strip()
    proxy_port = os.getenv("TSW_NEXUS_CACHE_DOCKER_PROXY_PORT", DEFAULT_NEXUS_CACHE_PROXY_PORT).strip()
    if not container_name or not proxy_port:
        return ""
    if not _local_docker_container_running(container_name):
        return ""
    host_ip = _lxc_reachable_host_ip()
    if not host_ip:
        return ""
    return f"http://{host_ip}:{proxy_port}"


def _local_docker_container_running(container_name: str) -> bool:
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"name=^/{container_name}$",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    return container_name in {line.strip() for line in result.stdout.splitlines()}


def _lxc_reachable_host_ip() -> str:
    for interface_name in ("lxdbr0", "incusbr0"):
        address = _host_ipv4_for_interface(interface_name)
        if address:
            return address
    return ""


def _host_ipv4_for_interface(interface_name: str) -> str:
    try:
        result = subprocess.run(
            [
                "ip",
                "-4",
                "-o",
                "addr",
                "show",
                "dev",
                interface_name,
            ],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    match = re.search(r"\binet\s+(?P<address>\d+\.\d+\.\d+\.\d+)/", result.stdout)
    return match.group("address") if match else ""


def _lxc_manager_node() -> NodeSpec:
    manager = next(
        (node for node in DEFAULT_LXC_PLATFORM_NODES if node.role == NodeRole.MANAGER),
        None,
    )
    if manager is None:
        raise ValueError("LXC platform node list must include a manager.")
    return manager


def _operator_config_source_ref(name: str) -> str:
    if os.environ.get(name):
        return "operator_env"
    return "default"


def _add_optional_config(environment: dict[str, str], name: str) -> None:
    value = os.environ.get(name, "").strip()
    if value:
        environment[name] = value


def _deployment_stack_environment(
    service_profile: ServiceStackProfile,
) -> dict[str, dict[str, str]]:
    registry_endpoint = _swarm_registry_endpoint()
    environment = {
        "nexus": {
            NEXUS_IMAGE_ENVIRONMENT: _operator_config_value(
                NEXUS_IMAGE_ENVIRONMENT,
                "sonatype/nexus3:3.75.1",
            ),
        },
        "jenkins": {
            JENKINS_IMAGE_ENVIRONMENT: _operator_config_value(
                JENKINS_IMAGE_ENVIRONMENT,
                f"{registry_endpoint}/jenkins:latest",
            ),
            "TSW_JENKINS_ADMIN_PASSWORD": _operator_secret_value("TSW_JENKINS_ADMIN_PASSWORD"),
        },
        "pulsar": {
            "TSW_PULSAR_TOKEN_SECRET_KEY": _operator_secret_value("TSW_PULSAR_TOKEN_SECRET_KEY"),
            "TSW_PULSAR_ADMIN_TOKEN": _operator_secret_value("TSW_PULSAR_ADMIN_TOKEN"),
            "TSW_PULSAR_MANAGER_ADMIN_PASSWORD": _operator_secret_value("TSW_PULSAR_MANAGER_ADMIN_PASSWORD"),
        },
        "sonarqube": {
            "TSW_SONARQUBE_POSTGRES_PASSWORD": _operator_secret_value("TSW_SONARQUBE_POSTGRES_PASSWORD"),
            "TSW_POSTGRES_PASSWORD": _operator_secret_value("TSW_POSTGRES_PASSWORD"),
        }
    }
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return environment

    environment["service-access"] = {
        SERVICE_ACCESS_DASHBOARD_IMAGE_ENVIRONMENT: _operator_config_value(
            SERVICE_ACCESS_DASHBOARD_IMAGE_ENVIRONMENT,
            f"{registry_endpoint}/service-access-dashboard:latest",
        ),
        SERVICE_ACCESS_NGINX_IMAGE_ENVIRONMENT: _operator_config_value(
            SERVICE_ACCESS_NGINX_IMAGE_ENVIRONMENT,
            f"{registry_endpoint}/service-access-nginx:latest",
        ),
    }
    environment["infisical"] = {
        INFISICAL_ENCRYPTION_KEY_ENVIRONMENT: _operator_secret_value(
            INFISICAL_ENCRYPTION_KEY_ENVIRONMENT,
        ),
        INFISICAL_AUTH_SECRET_ENVIRONMENT: _operator_secret_value(
            INFISICAL_AUTH_SECRET_ENVIRONMENT,
        ),
        INFISICAL_LOGIN_EMAIL_ENVIRONMENT: _operator_secret_value(
            INFISICAL_LOGIN_EMAIL_ENVIRONMENT,
        ),
        INFISICAL_PASSWORD_ENVIRONMENT: _operator_secret_value(
            INFISICAL_PASSWORD_ENVIRONMENT,
        ),
        INFISICAL_ADMIN_FIRST_NAME_ENVIRONMENT: _operator_config_value(
            INFISICAL_ADMIN_FIRST_NAME_ENVIRONMENT,
            "Tiny",
        ),
        INFISICAL_ADMIN_LAST_NAME_ENVIRONMENT: _operator_config_value(
            INFISICAL_ADMIN_LAST_NAME_ENVIRONMENT,
            "Admin",
        ),
        INFISICAL_POSTGRES_PASSWORD_ENVIRONMENT: _operator_secret_value(
            INFISICAL_POSTGRES_PASSWORD_ENVIRONMENT,
        ),
        INFISICAL_REDIS_PASSWORD_ENVIRONMENT: _operator_secret_value(
            INFISICAL_REDIS_PASSWORD_ENVIRONMENT,
        ),
    }
    _add_optional_config(
        environment["infisical"],
        INFISICAL_IMAGE_ENVIRONMENT,
    )
    _add_optional_config(
        environment["infisical"],
        INFISICAL_POSTGRES_IMAGE_ENVIRONMENT,
    )
    _add_optional_config(
        environment["infisical"],
        INFISICAL_REDIS_IMAGE_ENVIRONMENT,
    )
    return environment


def _container_image_contracts_from_environment() -> tuple[ContainerImageContract, ...]:
    overrides = {
        "infisical": INFISICAL_IMAGE_ENVIRONMENT,
        "infisical-postgres": INFISICAL_POSTGRES_IMAGE_ENVIRONMENT,
        "infisical-redis": INFISICAL_REDIS_IMAGE_ENVIRONMENT,
    }
    contracts = []
    for contract in DEFAULT_CONTAINER_IMAGE_CONTRACTS:
        env_name = overrides.get(contract.build_context)
        image_ref = ""
        if env_name:
            image_ref = _operator_config_value(env_name, "").strip()
        if image_ref:
            image_name, tag = _split_image_ref(image_ref)
            contracts.append(replace(contract, image_name=image_name, tag=tag))
            continue
        contracts.append(contract)
    return tuple(contracts)


def _split_image_ref(image_ref: str) -> tuple[str, str]:
    if ":" not in image_ref.rsplit("/", 1)[-1]:
        return image_ref, "latest"
    image_name, tag = image_ref.rsplit(":", 1)
    return image_name, tag


def _nexus_docker_hub_proxy_repository_name() -> str:
    repository_name = _operator_config_value(
        NEXUS_DOCKER_HUB_PROXY_REPOSITORY_ENVIRONMENT,
        DEFAULT_NEXUS_DOCKER_HUB_PROXY_REPOSITORY,
    ).strip()
    if not repository_name:
        raise ValueError("Nexus Docker Hub proxy repository name must not be empty.")
    return repository_name


def _nexus_docker_hub_proxy_port() -> int:
    raw_port = _operator_config_value(
        NEXUS_DOCKER_HUB_PROXY_PORT_ENVIRONMENT,
        str(DEFAULT_NEXUS_DOCKER_HUB_PROXY_PORT),
    ).strip()
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("Nexus Docker Hub proxy port must be an integer.") from exc
    if port <= 0 or port > 65535:
        raise ValueError("Nexus Docker Hub proxy port must be a valid TCP port.")
    return port


def _nexus_docker_hub_proxy_remote_url() -> str:
    remote_url = _operator_config_value(
        NEXUS_DOCKER_HUB_PROXY_REMOTE_URL_ENVIRONMENT,
        DEFAULT_NEXUS_DOCKER_HUB_PROXY_REMOTE_URL,
    ).strip()
    if not remote_url.startswith(("http://", "https://")):
        raise ValueError("Nexus Docker Hub proxy remote URL must be HTTP or HTTPS.")
    return remote_url


def _swarm_registry_endpoint() -> str:
    endpoint = _operator_config_value(
        SWARM_REGISTRY_ENDPOINT_ENVIRONMENT,
        DEFAULT_SWARM_REGISTRY_ENDPOINT,
    ).strip()
    if not REGISTRY_ENDPOINT_PATTERN.fullmatch(endpoint):
        raise ValueError(
            "Swarm registry endpoint must be host[:port] without scheme or credentials."
        )
    return endpoint


def _infisical_secret_seed_steps(
    service_profile: ServiceStackProfile,
) -> list[EnsureInfisicalSecretItems]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return []
    if os.environ.get(SEED_INFISICAL_ITEMS_ENVIRONMENT) != "1":
        return []
    return [
        EnsureInfisicalSecretItems(
            infisical_client=PlaywrightInfisicalClient(
                base_url=_operator_config_value(
                    INFISICAL_URL_ENVIRONMENT,
                    "https://localhost",
                ),
            ),
            login_email=_operator_secret_value(INFISICAL_LOGIN_EMAIL_ENVIRONMENT),
            password=_operator_secret_value(INFISICAL_PASSWORD_ENVIRONMENT),
            items=_infisical_seed_items(),
        ),
    ]


def _infisical_apply_readiness_steps(
    service_profile: ServiceStackProfile,
    *,
    swarm_runtime: LxcSwarmRuntime,
    service_stack_by_name: dict[str, ServiceStackContract],
) -> tuple[EnsureSwarmServiceReadiness, ...]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return ()
    attempts = _operator_config_int(
        INFISICAL_READINESS_ATTEMPTS_ENVIRONMENT,
        DEFAULT_INFISICAL_READINESS_ATTEMPTS,
        minimum=1,
    )
    interval = _operator_config_float(
        INFISICAL_READINESS_INTERVAL_ENVIRONMENT,
        DEFAULT_INFISICAL_READINESS_INTERVAL_SECONDS,
        minimum=0,
    )
    return (
        EnsureSwarmServiceReadiness(
            swarm_runtime,
            service_stack_by_name["infisical"],
            verification_target_id="deployment:infisical-bootstrap-service-readiness",
            max_attempts=attempts,
            wait_seconds=int(interval),
        ),
        EnsureSwarmServiceReadiness(
            swarm_runtime,
            service_stack_by_name["service-access"],
            verification_target_id="deployment:infisical-bootstrap-access-readiness",
            max_attempts=attempts,
            wait_seconds=int(interval),
        ),
    )


def _infisical_bootstrap_steps(
    service_profile: ServiceStackProfile,
    *,
    cli: InfisicalCliClient | None = None,
) -> list[EnsureInfisicalSilentInstall]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return []
    return [
        EnsureInfisicalSilentInstall(
            cli=cli or InfisicalCliClient(),
            bootstrap_client=InfisicalBootstrapHttpClient(
                base_url=_operator_config_value(
                    INFISICAL_URL_ENVIRONMENT,
                    "http://localhost:8086",
                ),
                verify_tls=False,
                readiness_attempts=_operator_config_int(
                    INFISICAL_READINESS_ATTEMPTS_ENVIRONMENT,
                    DEFAULT_INFISICAL_READINESS_ATTEMPTS,
                    minimum=1,
                ),
                readiness_interval_seconds=_operator_config_float(
                    INFISICAL_READINESS_INTERVAL_ENVIRONMENT,
                    DEFAULT_INFISICAL_READINESS_INTERVAL_SECONDS,
                    minimum=0,
                ),
            ),
            config=InfisicalSilentInstallConfig(
                external_url=_operator_config_value(
                    INFISICAL_URL_ENVIRONMENT,
                    "http://localhost:8086",
                ),
                internal_url=_operator_config_value(
                    INFISICAL_INTERNAL_URL_ENVIRONMENT,
                    "http://infisical:8080",
                ),
                admin_email=_required_operator_secret_value(
                    INFISICAL_LOGIN_EMAIL_ENVIRONMENT,
                ),
                admin_first_name=_operator_config_value(
                    INFISICAL_ADMIN_FIRST_NAME_ENVIRONMENT,
                    "Tiny",
                ),
                admin_last_name=_operator_config_value(
                    INFISICAL_ADMIN_LAST_NAME_ENVIRONMENT,
                    "Admin",
                ),
                admin_password=_required_operator_secret_value(
                    INFISICAL_PASSWORD_ENVIRONMENT,
                ),
                organization=_operator_config_value(
                    INFISICAL_ORGANIZATION_ENVIRONMENT,
                    DEFAULT_INFISICAL_ORGANIZATION,
                ),
                encryption_key=_required_operator_secret_value(
                    INFISICAL_ENCRYPTION_KEY_ENVIRONMENT,
                ),
                auth_secret=_required_operator_secret_value(
                    INFISICAL_AUTH_SECRET_ENVIRONMENT,
                ),
                postgres_password=_required_operator_secret_value(
                    INFISICAL_POSTGRES_PASSWORD_ENVIRONMENT,
                ),
                redis_password=_operator_secret_value(INFISICAL_REDIS_PASSWORD_ENVIRONMENT),
            ),
        ),
    ]


def _with_infisical_post_apply_steps(
    application_steps: tuple[object, ...],
    post_steps: tuple[object, ...],
) -> tuple[object, ...]:
    if not post_steps:
        return application_steps
    ordered_steps: list[object] = []
    inserted = False
    for step in application_steps:
        ordered_steps.append(step)
        service_stack = getattr(step, "service_stack", None)
        if getattr(service_stack, "stack_name", "") == "service-access":
            ordered_steps.extend(post_steps)
            inserted = True
    if not inserted:
        ordered_steps.extend(post_steps)
    return tuple(ordered_steps)


def _with_post_stack_steps(
    application_steps: tuple[object, ...],
    stack_name: str,
    post_steps: tuple[object, ...],
) -> tuple[object, ...]:
    if not post_steps:
        return application_steps
    ordered_steps: list[object] = []
    inserted = False
    for step in application_steps:
        ordered_steps.append(step)
        service_stack = getattr(step, "service_stack", None)
        if getattr(service_stack, "stack_name", "") == stack_name:
            ordered_steps.extend(post_steps)
            inserted = True
    if not inserted:
        ordered_steps.extend(post_steps)
    return tuple(ordered_steps)


def _infisical_seed_items() -> tuple[InfisicalSecretItem, ...]:
    return (
        InfisicalSecretItem(
            "platform/jenkins",
            _operator_config_value("TSW_JENKINS_ADMIN_USERNAME", "admin"),
            _required_operator_secret_value("TSW_JENKINS_ADMIN_PASSWORD"),
        ),
        InfisicalSecretItem(
            "platform/nexus",
            _operator_config_value("TSW_NEXUS_ADMIN_USERNAME", "admin"),
            _required_operator_secret_value("TSW_NEXUS_ADMIN_PASSWORD"),
        ),
        InfisicalSecretItem(
            "platform/portainer",
            _operator_config_value("TSW_PORTAINER_USERNAME", "admin"),
            _required_operator_secret_value("TSW_PORTAINER_ADMIN_PASSWORD"),
        ),
        InfisicalSecretItem(
            "platform/pulsar",
            "admin",
            _required_operator_secret_value("TSW_PULSAR_ADMIN_TOKEN"),
        ),
        InfisicalSecretItem(
            "platform/pulsar-manager",
            "admin",
            _required_operator_secret_value("TSW_PULSAR_MANAGER_ADMIN_PASSWORD"),
        ),
        InfisicalSecretItem(
            "platform/sonarqube",
            _operator_config_value("TSW_SONARQUBE_ADMIN_USERNAME", "admin"),
            _required_operator_secret_value("TSW_SONARQUBE_ADMIN_PASSWORD"),
        ),
    )


def _required_operator_secret_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Required operator secret is missing: {name}")
    return value

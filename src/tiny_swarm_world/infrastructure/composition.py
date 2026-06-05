from __future__ import annotations

import asyncio
import os
import re
import shutil
from dataclasses import dataclass
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
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
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
    DeploymentWorkflowResult,
    DeploymentWorkflowStatus,
    DeploymentVerifyWorkflow,
    EnsureExternalSwarmSecret,
    EnsurePortainerEndpoint,
    EnsurePortainerAdminAccess,
    EnsureSwarmStack,
    VerifyExternalSwarmInput,
    VerifySwarmServiceReadiness,
)
from tiny_swarm_world.application.services.deployment.service_stack_plan import (
    DEFAULT_PORTAINER_ENDPOINT_NAME,
    build_service_stack_steps,
)
from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDeviceState,
    PortContainerDockerRuntime,
    PortContainerNetworkIdentity,
    PortContainerSwarmBootstrap,
    PortLxcProxyDeviceRuntime,
)
from tiny_swarm_world.application.ports.progress import PortWorkflowProgress
from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
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
    LxcServiceExposureService,
    LxcServiceExposureStep,
    LxcSwarmBootstrapService,
    LxcSwarmBootstrapStep,
    NodeProviderDestroyManagedNodesStep,
    NodeProviderEnsureNodeStep,
    NodeProviderResetManagedNodesStep,
    NodeProviderSelectionRequest,
    NodeProviderSelectionService,
    PlatformDestroyWorkflow,
    PlatformExposeWorkflow,
    PlatformInitWorkflow,
    PlatformReconcileWorkflow,
    PlatformResetWorkflow,
    PlatformVerifyWorkflow,
    PreflightService,
    SocatManager,
)
from tiny_swarm_world.application.services.setup import (
    SetupWorkflow,
    SetupWorkflowPhase,
    SetupWorkflowResult,
)
from tiny_swarm_world.domain.artifacts import DEFAULT_CONTAINER_IMAGE_CONTRACTS
from tiny_swarm_world.domain.deployment import (
    ServiceStackProfile,
    service_stack_contracts_for_profile,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerEngineState,
    DockerInstallState,
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    SwarmManagerBootstrapOutcome,
    SwarmManagerState,
    SwarmWorkerJoinCredential,
    SwarmWorkerJoinOutcome,
    WorkerJoinState,
)
from tiny_swarm_world.domain.preflight import (
    LiveConsent,
    PreflightConfiguration,
    default_setup_manifest,
    default_preflight_configuration,
)
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    AsyncLxcNodeCommandRunner,
    LxcNodeCommandRunner,
    LxcNodeProvider,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
    LxcContainerDockerRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_swarm_bootstrap import (
    LxcContainerNetworkIdentity,
    LxcContainerSwarmBootstrap,
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
    NodeProviderConfigYamlRepository,
)
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


DEFAULT_SETUP_SERVICE_PROFILE = ServiceStackProfile.SERVICE_ACCESS
DEFAULT_PORTAINER_API_URL = "http://localhost:9000"
VAULTWARDEN_ADMIN_TOKEN_ENVIRONMENT = "TSW_VAULTWARDEN_ADMIN_TOKEN"
VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT = "TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET"
DEFAULT_VAULTWARDEN_ADMIN_INPUT_NAME = "tsw_vaultwarden_admin_token"
SWARM_REGISTRY_ENDPOINT_ENVIRONMENT = "TSW_SWARM_REGISTRY_ENDPOINT"
DEFAULT_SWARM_REGISTRY_ENDPOINT = "swarm-manager:5000"
LXC_PROXY_LISTEN_ADDRESS_ENVIRONMENT = "TSW_LXC_PROXY_LISTEN_ADDRESS"
DEFAULT_LXC_PROXY_LISTEN_ADDRESS = "0.0.0.0"
JENKINS_IMAGE_ENVIRONMENT = "TSW_JENKINS_IMAGE"
SERVICE_ACCESS_DASHBOARD_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_DASHBOARD_IMAGE"
SERVICE_ACCESS_NGINX_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_NGINX_IMAGE"
REGISTRY_ENDPOINT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(?::[0-9]{1,5})?$")
DEFAULT_LXC_PLATFORM_NODES = (
    NodeSpec("swarm-manager", NodeRole.MANAGER, NodeProviderKind.LXC_NATIVE),
    NodeSpec("swarm-worker-1", NodeRole.WORKER, NodeProviderKind.LXC_NATIVE),
    NodeSpec("swarm-worker-2", NodeRole.WORKER, NodeProviderKind.LXC_NATIVE),
)
LXC_BACKEND_REQUIRED_REASON = "lxc_backend_required"
LXC_BACKEND_REQUIRED_MESSAGE = (
    "LXC-native workflows require an available or explicitly selected Incus or LXD backend."
)
LXC_RECONCILE_VERIFIED_REASON = "lxc_native_reconcile_noop"
LXC_RECONCILE_VERIFIED_MESSAGE = (
    "platform reconcile is satisfied by LXC-native platform init boundaries."
)


@dataclass(frozen=True)
class PlatformWorkflows:
    init: PlatformInitWorkflow
    reconcile: PlatformReconcileWorkflow
    expose: PlatformExposeWorkflow
    reset: PlatformResetWorkflow
    destroy: PlatformDestroyWorkflow
    verify: PlatformVerifyWorkflow


@dataclass(frozen=True)
class PlatformServices:
    command_workflow: CommandWorkflow
    lxc_docker_install: LxcDockerInstallService
    lxc_service_exposure: LxcServiceExposureService
    lxc_swarm_bootstrap: LxcSwarmBootstrapService
    preflight: PreflightService
    lxc_node_provider: LxcNodeProvider
    node_provider_selection: NodeProviderSelectionService
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
    def preflight(self) -> PreflightService:
        return self.platform.preflight

    @property
    def socat_manager(self) -> SocatManager:
        return self.platform.socat_manager


class _BlockedArtifactWorkflow:
    def __init__(self, kind: ArtifactWorkflowKind, reason: str):
        self.kind = kind
        self.reason = reason
        self.steps = ()
        self.checks = ()

    async def run(self) -> ArtifactWorkflowResult:
        await asyncio.sleep(0)
        return ArtifactWorkflowResult(
            kind=self.kind,
            status=ArtifactWorkflowStatus.BLOCKED,
            message=(
                f"artifacts {self.kind.value} is blocked for the selected node provider."
            ),
            reason=self.reason,
        )


class _BlockedDeploymentWorkflow:
    def __init__(self, kind: DeploymentWorkflowKind, reason: str):
        self.kind = kind
        self.reason = reason
        self.steps = ()
        self.pre_apply_checks = ()
        self.checks = ()

    async def run(self) -> DeploymentWorkflowResult:
        await asyncio.sleep(0)
        return DeploymentWorkflowResult(
            kind=self.kind,
            status=DeploymentWorkflowStatus.BLOCKED,
            message=(
                f"deployment {self.kind.value} is blocked for the selected node provider."
            ),
            reason=self.reason,
        )


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


class _ProviderSelectedLxcDockerRuntime(PortContainerDockerRuntime):
    def __init__(
        self,
        *,
        provider_selection: NodeProviderSelectionService,
        provider_request: NodeProviderSelectionRequest,
        runner: LxcNodeCommandRunner,
        allow_live_mutation: bool,
    ) -> None:
        self.provider_selection = provider_selection
        self.provider_request = provider_request
        self.runner = runner
        self.allow_live_mutation = allow_live_mutation

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        if not self.allow_live_mutation:
            return ContainerDockerReadiness(
                node=node,
                observed=False,
                engine_state=DockerEngineState.UNKNOWN,
            )
        delegate = await self._delegate()
        if delegate is None:
            return ContainerDockerReadiness(
                node=node,
                observed=False,
                engine_state=DockerEngineState.UNKNOWN,
            )
        return await delegate.inspect_docker(node)

    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        if not self.allow_live_mutation:
            return ContainerDockerInstallOutcome(
                node=node,
                state=DockerInstallState.FAILED,
                verified=False,
            )
        delegate = await self._delegate()
        if delegate is None:
            return ContainerDockerInstallOutcome(
                node=node,
                state=DockerInstallState.FAILED,
                verified=False,
            )
        return await delegate.install_docker(node)

    async def verify_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        if not self.allow_live_mutation:
            return ContainerDockerReadiness(
                node=node,
                observed=False,
                engine_state=DockerEngineState.UNKNOWN,
            )
        delegate = await self._delegate()
        if delegate is None:
            return ContainerDockerReadiness(
                node=node,
                observed=False,
                engine_state=DockerEngineState.UNKNOWN,
            )
        return await delegate.verify_docker(node)

    async def _delegate(self) -> LxcContainerDockerRuntime | None:
        backend = await _selected_lxc_backend(
            self.provider_selection,
            self.provider_request,
        )
        if backend is None:
            return None
        return LxcContainerDockerRuntime(
            backend=backend,
            runner=self.runner,
            allow_live_mutation=self.allow_live_mutation,
        )


class _ProviderSelectedLxcSwarmRuntime(
    PortContainerNetworkIdentity,
    PortContainerSwarmBootstrap,
):
    def __init__(
        self,
        *,
        provider_selection: NodeProviderSelectionService,
        provider_request: NodeProviderSelectionRequest,
        runner: LxcNodeCommandRunner,
        allow_live_mutation: bool,
    ) -> None:
        self.provider_selection = provider_selection
        self.provider_request = provider_request
        self.runner = runner
        self.allow_live_mutation = allow_live_mutation

    async def manager_advertise_address(self, node: NodeSpec) -> str:
        if not self.allow_live_mutation:
            return ""
        backend = await _selected_lxc_backend(
            self.provider_selection,
            self.provider_request,
        )
        if backend is None:
            return ""
        return await LxcContainerNetworkIdentity(
            backend=backend,
            runner=self.runner,
        ).manager_advertise_address(node)

    async def inspect_manager(self, node: NodeSpec) -> SwarmManagerBootstrapOutcome:
        if not self.allow_live_mutation:
            return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.UNKNOWN)
        delegate = await self._delegate()
        if delegate is None:
            return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.UNKNOWN)
        return await delegate.inspect_manager(node)

    async def initialize_manager(
        self,
        node: NodeSpec,
        advertise_address: str,
    ) -> SwarmManagerBootstrapOutcome:
        if not self.allow_live_mutation:
            return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.ERROR)
        delegate = await self._delegate()
        if delegate is None:
            return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.ERROR)
        return await delegate.initialize_manager(node, advertise_address)

    async def worker_join_credential(self, node: NodeSpec) -> SwarmWorkerJoinCredential:
        if not self.allow_live_mutation:
            return SwarmWorkerJoinCredential("<unavailable>")
        delegate = await self._delegate()
        if delegate is None:
            return SwarmWorkerJoinCredential("<unavailable>")
        return await delegate.worker_join_credential(node)

    async def inspect_worker(self, node: NodeSpec) -> SwarmWorkerJoinOutcome:
        if not self.allow_live_mutation:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.UNKNOWN,
                verified=False,
            )
        delegate = await self._delegate()
        if delegate is None:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.UNKNOWN,
                verified=False,
            )
        return await delegate.inspect_worker(node)

    async def join_worker(
        self,
        node: NodeSpec,
        manager_address: str,
        credential: SwarmWorkerJoinCredential,
    ) -> SwarmWorkerJoinOutcome:
        if not self.allow_live_mutation:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.FAILED,
                verified=False,
            )
        delegate = await self._delegate()
        if delegate is None:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.FAILED,
                verified=False,
            )
        return await delegate.join_worker(node, manager_address, credential)

    async def _delegate(self) -> LxcContainerSwarmBootstrap | None:
        backend = await _selected_lxc_backend(
            self.provider_selection,
            self.provider_request,
        )
        if backend is None:
            return None
        return LxcContainerSwarmBootstrap(
            backend=backend,
            runner=self.runner,
            allow_live_mutation=self.allow_live_mutation,
        )


class _ProviderSelectedLxcProxyDeviceRuntime(PortLxcProxyDeviceRuntime):
    def __init__(
        self,
        *,
        provider_selection: NodeProviderSelectionService,
        provider_request: NodeProviderSelectionRequest,
        runner: LxcNodeCommandRunner,
        allow_live_mutation: bool,
    ) -> None:
        self.provider_selection = provider_selection
        self.provider_request = provider_request
        self.runner = runner
        self.allow_live_mutation = allow_live_mutation

    async def inspect_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        if not self.allow_live_mutation:
            return LxcProxyDeviceState.UNKNOWN
        delegate = await self._delegate()
        if delegate is None:
            return LxcProxyDeviceState.UNKNOWN
        return await delegate.inspect_proxy_device(node, plan)

    async def create_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        delegate = await self._delegate()
        if delegate is None:
            return False
        return await delegate.create_proxy_device(node, plan)

    async def update_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        delegate = await self._delegate()
        if delegate is None:
            return False
        return await delegate.update_proxy_device(node, plan)

    async def _delegate(self) -> LxcProxyDeviceRuntime | None:
        backend = await _selected_lxc_backend(
            self.provider_selection,
            self.provider_request,
        )
        if backend is None:
            return None
        return LxcProxyDeviceRuntime(
            backend=backend,
            runner=self.runner,
            allow_live_mutation=self.allow_live_mutation,
        )


async def _selected_lxc_backend(
    provider_selection: NodeProviderSelectionService,
    provider_request: NodeProviderSelectionRequest,
) -> ManagedLxcBackend | None:
    selection = await provider_selection.select_provider(provider_request)
    if selection.blocks_mutation or selection.backend_selection is None:
        return None
    return selection.backend_selection.backend


def configure_infrastructure_container() -> None:
    infra_core_container.register(PathFactory)
    infra_core_container.register(FileManager)


def build_application_logger():
    return LoggerFactory.get_logger("application")


def build_preflight_service(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
) -> PreflightService:
    return PreflightService(
        HostPreflightProbe(),
        _preflight_configuration_for_provider(service_profile, node_provider_request),
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
    provider_request = node_provider_request or NodeProviderSelectionRequest()
    workflow_progress = _build_workflow_progress_sink(ui)
    method_trace = _build_method_trace_sink(ui)
    trace_correlation_id = trace_correlation_id or _new_installation_trace_correlation_id()

    command_workflow = CommandWorkflow()
    verification_evidence_repository = VerificationEvidenceLocalRepository()
    preflight = _build_preflight_service_for_request(service_profile, node_provider_request)
    lxc_runner = AsyncLxcNodeCommandRunner()
    lxc_node_provider = LxcNodeProvider(
        config_repository=NodeProviderConfigYamlRepository(),
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
    )
    lxc_docker_install = LxcDockerInstallService(lxc_docker_runtime)
    lxc_swarm_runtime = _ProviderSelectedLxcSwarmRuntime(
        provider_selection=node_provider_selection,
        provider_request=provider_request,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
    )
    lxc_swarm_bootstrap = LxcSwarmBootstrapService(
        lxc_swarm_runtime,
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
            _platform_reconcile_steps(provider_request),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        expose=PlatformExposeWorkflow(
            _platform_expose_steps(lxc_service_exposure),
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
            (preflight,),
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
    )

    return PlatformServices(
        command_workflow=command_workflow,
        lxc_docker_install=lxc_docker_install,
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
    provider_request = node_provider_request or NodeProviderSelectionRequest()
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


def build_deployment_services_for_provider(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
) -> DeploymentServices:
    provider_request = node_provider_request or NodeProviderSelectionRequest()
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
    external_input_checks = _service_access_external_input_checks(
        selected_service_profile,
        swarm_runtime=swarm_runtime,
    )
    external_input_steps = _service_access_external_input_steps(
        selected_service_profile,
        swarm_runtime=swarm_runtime,
    )
    compose_repository = ComposeFileRepositoryYaml()
    portainer_admin_client = LxcPortainerAdminClient(backend=backend)
    portainer_client = LxcPortainerHttpClient(
        backend=backend,
        username="admin",
        password=_operator_secret_value("TSW_PORTAINER_PASSWORD"),
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
            password=_operator_secret_value("TSW_PORTAINER_PASSWORD"),
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
    application_steps = build_service_stack_steps(
        compose_repository=compose_repository,
        portainer_client=portainer_client,
        endpoint_name=DEFAULT_PORTAINER_ENDPOINT_NAME,
        service_profile=selected_service_profile,
        excluded_stack_names=("nexus",),
        stack_environments=stack_environment,
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
                pre_apply_steps=external_input_steps,
                pre_apply_checks=external_input_checks,
            ),
            verify=DeploymentVerifyWorkflow((*external_input_checks, *readiness_checks)),
        )
    )


def build_setup_services(
    live_consent: LiveConsent,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
) -> SetupServices:
    preflight = _build_preflight_service_for_request(service_profile, node_provider_request)
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
) -> PreflightService:
    if node_provider_request is None:
        return build_preflight_service(service_profile=service_profile)
    return build_preflight_service(
        service_profile=service_profile,
        node_provider_request=node_provider_request,
    )


def _lxc_backend_for_provider_request(
    provider_request: NodeProviderSelectionRequest,
) -> ManagedLxcBackend | None:
    if provider_request.requested_provider != NodeProviderKind.LXC_NATIVE:
        return None
    if provider_request.preferred_backend is not None:
        return provider_request.preferred_backend
    if shutil.which("lxc"):
        return ManagedLxcBackend.LXD
    if shutil.which("incus"):
        return ManagedLxcBackend.INCUS
    return None


def _preflight_configuration_for_provider(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
) -> PreflightConfiguration:
    return default_preflight_configuration(service_profile=service_profile)


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
    provider_request: NodeProviderSelectionRequest,
) -> tuple[AsyncWorkflowStep, ...]:
    return (
        _VerifiedPlatformProviderStep(
            target_id="platform:reconcile:lxc-native-provider-boundary",
            provider_request=provider_request,
            message=LXC_RECONCILE_VERIFIED_MESSAGE,
            reason=LXC_RECONCILE_VERIFIED_REASON,
        ),
    )


def _platform_expose_steps(
    lxc_service_exposure: LxcServiceExposureService,
) -> tuple[AsyncWorkflowStep, ...]:
    return (LxcServiceExposureStep(lxc_service_exposure),)


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


def _lxc_proxy_listen_address() -> str:
    address = _operator_config_value(
        LXC_PROXY_LISTEN_ADDRESS_ENVIRONMENT,
        DEFAULT_LXC_PROXY_LISTEN_ADDRESS,
    ).strip()
    if address not in {"127.0.0.1", "0.0.0.0"}:
        raise ValueError("LXC proxy listen address must be 127.0.0.1 or 0.0.0.0.")
    return address


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


def _deployment_stack_environment(
    service_profile: ServiceStackProfile,
) -> dict[str, dict[str, str]]:
    registry_endpoint = _swarm_registry_endpoint()
    environment = {
        "jenkins": {
            JENKINS_IMAGE_ENVIRONMENT: _operator_config_value(
                JENKINS_IMAGE_ENVIRONMENT,
                f"{registry_endpoint}/jenkins:latest",
            )
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
        VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT: _operator_config_value(
            VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT,
            DEFAULT_VAULTWARDEN_ADMIN_INPUT_NAME,
        ),
    }
    return environment


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


def _service_access_external_input_steps(
    service_profile: ServiceStackProfile,
    *,
    swarm_runtime: PortSwarmStackRuntime,
) -> tuple[EnsureExternalSwarmSecret, ...]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return ()
    resource_value = os.environ.get(VAULTWARDEN_ADMIN_TOKEN_ENVIRONMENT)
    if not resource_value:
        return ()
    return (
        EnsureExternalSwarmSecret(
            swarm_runtime=swarm_runtime,
            resource_name=_operator_config_value(
                VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT,
                DEFAULT_VAULTWARDEN_ADMIN_INPUT_NAME,
            ),
            resource_value=resource_value,
        ),
    )


def _service_access_external_input_checks(
    service_profile: ServiceStackProfile,
    *,
    swarm_runtime: PortSwarmStackRuntime,
) -> tuple[VerifyExternalSwarmInput, ...]:
    checks: list[VerifyExternalSwarmInput] = []
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return tuple(checks)
    checks.append(
        VerifyExternalSwarmInput(
            swarm_runtime=swarm_runtime,
            resource_name=_operator_config_value(
                VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT,
                DEFAULT_VAULTWARDEN_ADMIN_INPUT_NAME,
            ),
            source_ref=_operator_config_source_ref(VAULTWARDEN_ADMIN_INPUT_ENVIRONMENT),
        ),
    )
    return tuple(checks)

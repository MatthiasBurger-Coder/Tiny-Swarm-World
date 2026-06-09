from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, replace
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
    EnsureInfisicalSilentInstall,
    EnsureInfisicalSecretItems,
    InfisicalSilentInstallConfig,
    EnsurePortainerEndpoint,
    EnsurePortainerAdminAccess,
    EnsureSwarmStack,
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
from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDriftRepairOutcome,
    LxcProxyDeviceState,
    PortContainerDockerRuntime,
    PortContainerNetworkIdentity,
    PortContainerSwarmBootstrap,
    PortLxcProxyDeviceRuntime,
)
from tiny_swarm_world.application.ports.progress import PortWorkflowProgress
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    STATUS_ERROR,
    PortUI,
)
from tiny_swarm_world.application.services.platform import (
    AsyncWorkflowStep,
    LxcDockerInstallService,
    LxcDockerInstallStep,
    LxcProxyDriftRepairService,
    LxcProxyDriftRepairStep,
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
    PlatformRepairLxcProxyDriftWorkflow,
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
from tiny_swarm_world.domain.network.port_forwarding_plan import (
    ForwardingStrategy,
    PortForwardingPlan,
)
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
    DockerRegistryMirrorConfiguration,
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
from tiny_swarm_world.infrastructure.adapters.clients.infisical_playwright_client import (
    PlaywrightInfisicalClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.infisical_cli_client import (
    InfisicalCliClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.infisical_bootstrap_http_client import (
    InfisicalBootstrapHttpClient,
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


DEFAULT_SETUP_SERVICE_PROFILE = ServiceStackProfile.SERVICE_ACCESS
DEFAULT_PORTAINER_API_URL = "http://localhost:9000"
SEED_INFISICAL_ITEMS_ENVIRONMENT = "TSW_SEED_INFISICAL_ITEMS"
INFISICAL_LOGIN_EMAIL_ENVIRONMENT = "TSW_INFISICAL_LOGIN_EMAIL"
INFISICAL_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"
INFISICAL_URL_ENVIRONMENT = "TSW_INFISICAL_URL"
INFISICAL_INTERNAL_URL_ENVIRONMENT = "TSW_INFISICAL_INTERNAL_URL"
INFISICAL_ORGANIZATION_ENVIRONMENT = "TSW_INFISICAL_ORGANIZATION"
INFISICAL_ADMIN_FIRST_NAME_ENVIRONMENT = "TSW_INFISICAL_ADMIN_FIRST_NAME"
INFISICAL_ADMIN_LAST_NAME_ENVIRONMENT = "TSW_INFISICAL_ADMIN_LAST_NAME"
DEFAULT_INFISICAL_ORGANIZATION = "Tiny Swarm World"
SWARM_REGISTRY_ENDPOINT_ENVIRONMENT = "TSW_SWARM_REGISTRY_ENDPOINT"
DEFAULT_SWARM_REGISTRY_ENDPOINT = "127.0.0.1:5000"
LXC_PROXY_LISTEN_ADDRESS_ENVIRONMENT = "TSW_LXC_PROXY_LISTEN_ADDRESS"
DEFAULT_LXC_PROXY_LISTEN_ADDRESS = "0.0.0.0"
DEFAULT_NEXUS_CACHE_CONTAINER = "tiny-swarm-nexus-cache"
DEFAULT_NEXUS_CACHE_PROXY_PORT = "5001"
DEFAULT_LXC_MANAGER_PROXY_PROFILE = "docker-swarm-manager"
JENKINS_IMAGE_ENVIRONMENT = "TSW_JENKINS_IMAGE"
SERVICE_ACCESS_DASHBOARD_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_DASHBOARD_IMAGE"
SERVICE_ACCESS_NGINX_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_NGINX_IMAGE"
INFISICAL_ENCRYPTION_KEY_ENVIRONMENT = "TSW_INFISICAL_ENCRYPTION_KEY"
INFISICAL_AUTH_SECRET_ENVIRONMENT = "TSW_INFISICAL_AUTH_SECRET"
INFISICAL_POSTGRES_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_POSTGRES_PASSWORD"
INFISICAL_REDIS_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_REDIS_PASSWORD"
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
    repair_lxc_proxy_drift: PlatformRepairLxcProxyDriftWorkflow
    reset: PlatformResetWorkflow
    destroy: PlatformDestroyWorkflow
    verify: PlatformVerifyWorkflow


@dataclass(frozen=True)
class PlatformServices:
    command_workflow: CommandWorkflow
    lxc_docker_install: LxcDockerInstallService
    lxc_proxy_drift_repair: LxcProxyDriftRepairService
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
            registry_mirror=_lxc_docker_registry_mirror_configuration(),
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


class _PrepareLxcStackAssets:
    def __init__(self, swarm_runtime: LxcSwarmRuntime, stack_name: str) -> None:
        self.swarm_runtime = swarm_runtime
        self.stack_name = stack_name
        self.deployment_target_id = f"deployment:{stack_name}-stack-assets"

    def run(self) -> None:
        self.swarm_runtime.prepare_stack_assets(self.stack_name)


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
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        if not self.allow_live_mutation:
            return LxcProxyDeviceState.UNKNOWN
        delegate = await self._delegate()
        if delegate is None:
            return LxcProxyDeviceState.UNKNOWN
        return await delegate.inspect_proxy_device(profile_name, plan)

    async def create_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        delegate = await self._delegate()
        if delegate is None:
            return False
        return await delegate.create_proxy_device(profile_name, plan)

    async def update_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        delegate = await self._delegate()
        if delegate is None:
            return False
        return await delegate.update_proxy_device(profile_name, plan)

    async def repair_stale_proxy_devices(
        self,
        profile_name: str,
        gateway_node: NodeSpec,
        plans: tuple[LxcProxyDevicePlan, ...],
    ) -> LxcProxyDriftRepairOutcome:
        if not self.allow_live_mutation:
            return LxcProxyDriftRepairOutcome(
                expected_profile_device_count=len(plans),
                mutation_allowed=False,
            )
        delegate = await self._delegate()
        if delegate is None:
            return LxcProxyDriftRepairOutcome(
                expected_profile_device_count=len(plans),
                lookup_failure_count=len(plans),
                failed_devices=tuple(plan.device_name for plan in plans),
            )
        return await delegate.repair_stale_proxy_devices(
            profile_name,
            gateway_node,
            plans,
        )

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


def build_post_install_preflight_service(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
) -> PreflightService:
    configuration = _preflight_configuration_for_provider(service_profile, node_provider_request)
    return PreflightService(
        HostPreflightProbe(),
        replace(configuration, required_ports=()),
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
    post_install_preflight = _build_post_install_preflight_service_for_request(
        service_profile,
        node_provider_request,
    )
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
            _platform_reconcile_steps(provider_request),
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
            (post_install_preflight,),
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
    secret_manifest_entries = SecretManifestRenderer().run()
    compose_repository = ComposeFileRepositoryYaml()
    portainer_admin_client = LxcPortainerAdminClient(backend=backend)
    portainer_client = LxcPortainerHttpClient(
        backend=backend,
        username="admin",
        password=_operator_secret_value("TSW_PORTAINER_ADMIN_PASSWORD"),
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
    application_steps = build_service_stack_steps(
        compose_repository=compose_repository,
        portainer_client=portainer_client,
        endpoint_name=DEFAULT_PORTAINER_ENDPOINT_NAME,
        service_profile=selected_service_profile,
        excluded_stack_names=("nexus",),
        stack_environments=stack_environment,
    )
    infisical_cli_client = InfisicalCliClient()
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
                        (*infisical_secret_management_steps, *infisical_seed_steps),
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


def _build_post_install_preflight_service_for_request(
    service_profile: ServiceStackProfile | str,
    node_provider_request: NodeProviderSelectionRequest | None,
) -> PreflightService:
    if node_provider_request is None:
        return build_post_install_preflight_service(service_profile=service_profile)
    return build_post_install_preflight_service(
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


def _deployment_stack_environment(
    service_profile: ServiceStackProfile,
) -> dict[str, dict[str, str]]:
    registry_endpoint = _swarm_registry_endpoint()
    environment = {
        "jenkins": {
            JENKINS_IMAGE_ENVIRONMENT: _operator_config_value(
                JENKINS_IMAGE_ENVIRONMENT,
                f"{registry_endpoint}/jenkins:latest",
            ),
            "TSW_JENKINS_ADMIN_PASSWORD": _operator_secret_value("TSW_JENKINS_ADMIN_PASSWORD"),
        },
        "rabbitmq": {
            "TSW_RABBITMQ_PASSWORD": _operator_secret_value("TSW_RABBITMQ_PASSWORD"),
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


def _infisical_secret_seed_steps(
    service_profile: ServiceStackProfile,
) -> tuple[EnsureInfisicalSecretItems, ...]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return ()
    if os.environ.get(SEED_INFISICAL_ITEMS_ENVIRONMENT) != "1":
        return ()
    return (
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
    )


def _infisical_bootstrap_steps(
    service_profile: ServiceStackProfile,
    *,
    cli: InfisicalCliClient | None = None,
) -> tuple[EnsureInfisicalSilentInstall, ...]:
    if service_profile is not ServiceStackProfile.SERVICE_ACCESS:
        return ()
    return (
        EnsureInfisicalSilentInstall(
            cli=cli or InfisicalCliClient(),
            bootstrap_client=InfisicalBootstrapHttpClient(
                base_url=_operator_config_value(
                    INFISICAL_URL_ENVIRONMENT,
                    "http://localhost:8086",
                ),
                verify_tls=False,
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
    )


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
            "platform/rabbitmq",
            _operator_config_value("TSW_RABBITMQ_USERNAME", "admin"),
            _required_operator_secret_value("TSW_RABBITMQ_PASSWORD"),
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

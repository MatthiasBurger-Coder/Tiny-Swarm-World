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
    LxcDockerInstallService,
    LxcProxyDriftRepairService,
    LxcServiceExposureService,
    LxcSwarmBootstrapService,
    PlatformDestroyWorkflow,
    PlatformExposeWorkflow,
    PlatformInitWorkflow,
    PlatformReconcileWorkflow,
    PlatformRepairLxcProxyDriftWorkflow,
    PlatformResetWorkflow,
    PlatformVerifyWorkflow,
    PreflightService,
    SocatManager,
)
from tiny_swarm_world.application.services.setup import SetupWorkflow
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import LxcNodeProvider
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.application.services.platform import NodeProviderSelectionService


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

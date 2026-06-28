from __future__ import annotations

from collections.abc import Callable

from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDriftRepairOutcome,
    LxcProxyDeviceState,
    PortContainerDockerRuntime,
    PortContainerNetworkIdentity,
    PortContainerSwarmBootstrap,
    PortLxcProxyDeviceRuntime,
)
from tiny_swarm_world.application.services.platform import (
    NodeProviderSelectionRequest,
    NodeProviderSelectionService,
)
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerEngineState,
    DockerInstallState,
    ManagedLxcBackend,
    NodeSpec,
    SwarmManagerBootstrapOutcome,
    SwarmManagerState,
    SwarmWorkerJoinCredential,
    SwarmWorkerJoinOutcome,
    WorkerJoinState,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
    DockerAptMirrorConfiguration,
    DockerRegistryMirrorConfiguration,
    LxcContainerDockerRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_swarm_bootstrap import (
    LxcContainerNetworkIdentity,
    LxcContainerSwarmBootstrap,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import LxcNodeCommandRunner
from tiny_swarm_world.infrastructure.adapters.clients.lxc_proxy_device_runtime import (
    LxcProxyDeviceRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime import LxcSwarmRuntime


class ProviderSelectedLxcDockerRuntime(PortContainerDockerRuntime):
    def __init__(
        self,
        *,
        provider_selection: NodeProviderSelectionService,
        provider_request: NodeProviderSelectionRequest,
        runner: LxcNodeCommandRunner,
        allow_live_mutation: bool,
        allow_live_inspection: bool = False,
        registry_mirror_configuration: Callable[
            [],
            DockerRegistryMirrorConfiguration | None,
        ]
        | None = None,
        apt_mirror_configuration: Callable[
            [],
            DockerAptMirrorConfiguration | None,
        ]
        | None = None,
        docker_runtime_factory: type[LxcContainerDockerRuntime] = LxcContainerDockerRuntime,
    ) -> None:
        self.provider_selection = provider_selection
        self.provider_request = provider_request
        self.runner = runner
        self.allow_live_mutation = allow_live_mutation
        self.allow_live_inspection = allow_live_inspection
        self.registry_mirror_configuration = registry_mirror_configuration
        self.apt_mirror_configuration = apt_mirror_configuration
        self.docker_runtime_factory = docker_runtime_factory

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        if not self.allow_live_mutation and not self.allow_live_inspection:
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
        if not self.allow_live_mutation and not self.allow_live_inspection:
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
        backend = await selected_lxc_backend(
            self.provider_selection,
            self.provider_request,
        )
        if backend is None:
            return None
        registry_mirror = (
            self.registry_mirror_configuration()
            if self.registry_mirror_configuration is not None
            else None
        )
        apt_mirror = (
            self.apt_mirror_configuration()
            if self.apt_mirror_configuration is not None
            else None
        )
        return self.docker_runtime_factory(
            backend=backend,
            runner=self.runner,
            allow_live_mutation=self.allow_live_mutation,
            registry_mirror=registry_mirror,
            apt_mirror=apt_mirror,
        )


class ProviderSelectedLxcSwarmRuntime(
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
        allow_live_inspection: bool = False,
        proxy_runtime_factory: type[LxcProxyDeviceRuntime] = LxcProxyDeviceRuntime,
    ) -> None:
        self.provider_selection = provider_selection
        self.provider_request = provider_request
        self.runner = runner
        self.allow_live_mutation = allow_live_mutation
        self.allow_live_inspection = allow_live_inspection
        self.proxy_runtime_factory = proxy_runtime_factory

    async def manager_advertise_address(self, node: NodeSpec) -> str:
        if not self.allow_live_mutation:
            return ""
        backend = await selected_lxc_backend(
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
        if not self.allow_live_mutation and not self.allow_live_inspection:
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
        if not self.allow_live_mutation and not self.allow_live_inspection:
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
        backend = await selected_lxc_backend(
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


class PrepareLxcStackAssets:
    def __init__(self, swarm_runtime: LxcSwarmRuntime, stack_name: str) -> None:
        self.swarm_runtime = swarm_runtime
        self.stack_name = stack_name
        self.deployment_target_id = f"deployment:{stack_name}-stack-assets"

    def run(self) -> None:
        self.swarm_runtime.prepare_stack_assets(self.stack_name)


class ProviderSelectedLxcProxyDeviceRuntime(PortLxcProxyDeviceRuntime):
    def __init__(
        self,
        *,
        provider_selection: NodeProviderSelectionService,
        provider_request: NodeProviderSelectionRequest,
        runner: LxcNodeCommandRunner,
        allow_live_mutation: bool,
        allow_live_inspection: bool = False,
        proxy_runtime_factory: type[LxcProxyDeviceRuntime] = LxcProxyDeviceRuntime,
    ) -> None:
        self.provider_selection = provider_selection
        self.provider_request = provider_request
        self.runner = runner
        self.allow_live_mutation = allow_live_mutation
        self.allow_live_inspection = allow_live_inspection
        self.proxy_runtime_factory = proxy_runtime_factory

    async def inspect_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        if not self.allow_live_mutation and not self.allow_live_inspection:
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
        backend = await selected_lxc_backend(
            self.provider_selection,
            self.provider_request,
        )
        if backend is None:
            return None
        return self.proxy_runtime_factory(
            backend=backend,
            runner=self.runner,
            allow_live_mutation=self.allow_live_mutation,
        )


async def selected_lxc_backend(
    provider_selection: NodeProviderSelectionService,
    provider_request: NodeProviderSelectionRequest,
) -> ManagedLxcBackend | None:
    selection = await provider_selection.select_provider(provider_request)
    if selection.blocks_mutation or selection.backend_selection is None:
        return None
    return selection.backend_selection.backend

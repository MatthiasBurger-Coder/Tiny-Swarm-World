import unittest

from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.ports.node_provider import LxcProxyDeviceState
from tiny_swarm_world.application.services.platform import (
    LxcDockerInstallService,
    LxcDockerVerifyStep,
    LxcServiceExposureService,
    LxcServiceExposureVerifyStep,
    LxcSwarmBootstrapService,
    LxcSwarmVerifyStep,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerEngineState,
    DockerInstallState,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    SwarmManagerBootstrapOutcome,
    SwarmManagerState,
    SwarmWorkerJoinCredential,
    SwarmWorkerJoinOutcome,
    WorkerJoinState,
)
from tiny_swarm_world.domain.preflight import default_setup_manifest


class TestPlatformVerifyChecks(unittest.IsolatedAsyncioTestCase):
    async def test_docker_verify_uses_inspect_only(self):
        runtime = _DockerRuntime(
            readiness=ContainerDockerReadiness(
                node=_manager(),
                observed=True,
                engine_state=DockerEngineState.READY,
            )
        )
        step = LxcDockerVerifyStep(
            LxcDockerInstallService(runtime),
            (_manager(),),
        )

        result = await step.run()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("container_runtime_verified", result.evidence["classification"])
        self.assertEqual(["swarm-manager"], runtime.inspect_calls)
        self.assertEqual(0, runtime.install_calls)
        self.assertEqual(0, runtime.verify_calls)

    async def test_docker_verify_reports_unready_node(self):
        runtime = _DockerRuntime(
            readiness=ContainerDockerReadiness(
                node=_manager(),
                observed=True,
                engine_state=DockerEngineState.MISSING,
            )
        )
        step = LxcDockerVerifyStep(LxcDockerInstallService(runtime), (_manager(),))

        result = await step.run()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("one_or_more_nodes_not_ready", result.evidence["observed"])
        self.assertEqual("swarm-manager", result.evidence["failed_nodes"])

    async def test_swarm_verify_uses_inspect_only(self):
        swarm = _SwarmRuntime(
            manager=SwarmManagerBootstrapOutcome(
                node=_manager(),
                state=SwarmManagerState.ACTIVE,
                manager_count=1,
            ),
            worker=SwarmWorkerJoinOutcome(
                node=_worker(),
                state=WorkerJoinState.ALREADY_JOINED,
                verified=True,
            ),
        )
        step = LxcSwarmVerifyStep(
            LxcSwarmBootstrapService(swarm, _NetworkIdentity()),
            (_manager(), _worker()),
        )

        result = await step.run()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("swarm_membership_verified", result.evidence["classification"])
        self.assertEqual(["swarm-manager"], swarm.manager_inspections)
        self.assertEqual(["swarm-worker-1"], swarm.worker_inspections)
        self.assertEqual(0, swarm.init_calls)
        self.assertEqual(0, swarm.credential_calls)
        self.assertEqual(0, swarm.join_calls)

    async def test_swarm_verify_reports_worker_not_joined(self):
        swarm = _SwarmRuntime(
            manager=SwarmManagerBootstrapOutcome(
                node=_manager(),
                state=SwarmManagerState.ACTIVE,
                manager_count=1,
            ),
            worker=SwarmWorkerJoinOutcome(
                node=_worker(),
                state=WorkerJoinState.UNKNOWN,
                verified=False,
            ),
        )
        step = LxcSwarmVerifyStep(
            LxcSwarmBootstrapService(swarm, _NetworkIdentity()),
            (_manager(), _worker()),
        )

        result = await step.run()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("one_or_more_nodes_not_joined", result.evidence["observed"])
        self.assertEqual("swarm-worker-1", result.evidence["failed_nodes"])

    async def test_proxy_verify_uses_inspect_only(self):
        runtime = _ProxyRuntime(default_state=LxcProxyDeviceState.PRESENT)
        step = LxcServiceExposureVerifyStep(
            LxcServiceExposureService(
                runtime,
                gateway_node=_manager(),
                manager_profile_name="docker-swarm-manager",
                setup_manifest=default_setup_manifest(
                    service_profile=ServiceStackProfile.SERVICE_ACCESS
                ),
                listen_address="0.0.0.0",
            )
        )

        result = await step.run()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("lxc_proxy_devices_verified", result.evidence["classification"])
        self.assertEqual("18", result.evidence["present_count"])
        self.assertEqual(0, runtime.create_calls)
        self.assertEqual(0, runtime.update_calls)

    async def test_proxy_verify_reports_missing_or_drifted_devices(self):
        runtime = _ProxyRuntime(
            states={
                10080: LxcProxyDeviceState.MISSING,
                10443: LxcProxyDeviceState.DRIFTED,
            },
            default_state=LxcProxyDeviceState.PRESENT,
        )
        step = LxcServiceExposureVerifyStep(
            LxcServiceExposureService(
                runtime,
                gateway_node=_manager(),
                manager_profile_name="docker-swarm-manager",
                setup_manifest=default_setup_manifest(
                    service_profile=ServiceStackProfile.SERVICE_ACCESS
                ),
                listen_address="0.0.0.0",
            )
        )

        result = await step.run()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(
            "one_or_more_proxy_devices_missing_or_drifted",
            result.evidence["observed"],
        )
        self.assertEqual("1", result.evidence["missing_count"])
        self.assertEqual("1", result.evidence["drifted_count"])
        self.assertEqual(0, runtime.create_calls)
        self.assertEqual(0, runtime.update_calls)


class _DockerRuntime:
    def __init__(self, *, readiness: ContainerDockerReadiness) -> None:
        self.readiness = readiness
        self.inspect_calls: list[str] = []
        self.install_calls = 0
        self.verify_calls = 0

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        await async_checkpoint()
        self.inspect_calls.append(node.name)
        return self.readiness

    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        await async_checkpoint()
        self.install_calls += 1
        return ContainerDockerInstallOutcome(
            node=node,
            state=DockerInstallState.FAILED,
            verified=False,
        )

    async def verify_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        await async_checkpoint()
        self.verify_calls += 1
        return self.readiness


class _NetworkIdentity:
    async def manager_advertise_address(self, node: NodeSpec) -> str:
        await async_checkpoint()
        return "manager-address"


class _SwarmRuntime:
    def __init__(
        self,
        *,
        manager: SwarmManagerBootstrapOutcome,
        worker: SwarmWorkerJoinOutcome,
    ) -> None:
        self.manager = manager
        self.worker = worker
        self.manager_inspections: list[str] = []
        self.worker_inspections: list[str] = []
        self.init_calls = 0
        self.credential_calls = 0
        self.join_calls = 0

    async def inspect_manager(self, node: NodeSpec) -> SwarmManagerBootstrapOutcome:
        await async_checkpoint()
        self.manager_inspections.append(node.name)
        return self.manager

    async def initialize_manager(
        self,
        node: NodeSpec,
        advertise_address: str,
    ) -> SwarmManagerBootstrapOutcome:
        await async_checkpoint()
        self.init_calls += 1
        return self.manager

    async def worker_join_credential(self, node: NodeSpec) -> SwarmWorkerJoinCredential:
        await async_checkpoint()
        self.credential_calls += 1
        return SwarmWorkerJoinCredential("unused")

    async def inspect_worker(self, node: NodeSpec) -> SwarmWorkerJoinOutcome:
        await async_checkpoint()
        self.worker_inspections.append(node.name)
        return self.worker

    async def join_worker(
        self,
        node: NodeSpec,
        manager_address: str,
        credential: SwarmWorkerJoinCredential,
    ) -> SwarmWorkerJoinOutcome:
        await async_checkpoint()
        self.join_calls += 1
        return self.worker


class _ProxyRuntime:
    def __init__(
        self,
        *,
        default_state: LxcProxyDeviceState,
        states: dict[int, LxcProxyDeviceState] | None = None,
    ) -> None:
        self.default_state = default_state
        self.states = states or {}
        self.inspect_calls: list[tuple[str, int]] = []
        self.create_calls = 0
        self.update_calls = 0

    async def inspect_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        await async_checkpoint()
        self.inspect_calls.append((profile_name, plan.listen_port))
        return self.states.get(plan.listen_port, self.default_state)

    async def create_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        await async_checkpoint()
        self.create_calls += 1
        return False

    async def update_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        await async_checkpoint()
        self.update_calls += 1
        return False

    async def repair_stale_proxy_devices(self, *_args) -> object:
        await async_checkpoint()
        raise AssertionError("repair_stale_proxy_devices was not expected")


def _manager() -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


def _worker() -> NodeSpec:
    return NodeSpec(
        name="swarm-worker-1",
        role=NodeRole.WORKER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


if __name__ == "__main__":
    unittest.main()

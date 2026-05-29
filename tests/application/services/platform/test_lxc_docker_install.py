import unittest
from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.services.platform.lxc_docker_install import (
    LxcDockerInstallService,
    LxcDockerInstallStep,
)
from tiny_swarm_world.application.services.platform.workflows import PlatformInitWorkflow
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerEngineState,
    DockerInstallState,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
)


class TestLxcDockerInstallService(unittest.IsolatedAsyncioTestCase):
    async def test_already_ready_node_does_not_run_install(self):
        runtime = _DockerRuntime(
            initial=ContainerDockerReadiness(
                node=_node(),
                observed=True,
                engine_state=DockerEngineState.READY,
            ),
        )

        results = await LxcDockerInstallService(runtime).ensure_docker_installed(
            (_node(),),
        )

        self.assertEqual(VerificationStatus.VERIFIED, results[0].status)
        self.assertEqual([], runtime.installed_nodes)

    async def test_missing_docker_installs_and_verifies_node(self):
        runtime = _DockerRuntime(
            initial=ContainerDockerReadiness(
                node=_node(),
                observed=True,
                engine_state=DockerEngineState.MISSING,
            ),
            install=ContainerDockerInstallOutcome(
                node=_node(),
                state=DockerInstallState.INSTALLED,
                verified=True,
            ),
            verified=ContainerDockerReadiness(
                node=_node(),
                observed=True,
                engine_state=DockerEngineState.READY,
            ),
        )

        results = await LxcDockerInstallService(runtime).ensure_docker_installed(
            (_node(),),
        )

        self.assertEqual(
            [
                VerificationStatus.VERIFIED,
                VerificationStatus.VERIFIED,
            ],
            [result.status for result in results],
        )
        self.assertEqual(["swarm-manager"], runtime.installed_nodes)

    async def test_failed_install_stops_before_verify(self):
        runtime = _DockerRuntime(
            initial=ContainerDockerReadiness(
                node=_node(),
                observed=True,
                engine_state=DockerEngineState.MISSING,
            ),
            install=ContainerDockerInstallOutcome(
                node=_node(),
                state=DockerInstallState.FAILED,
                verified=False,
            ),
        )

        results = await LxcDockerInstallService(runtime).ensure_docker_installed(
            (_node(),),
        )

        self.assertEqual(1, len(results))
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, results[0].status)
        self.assertEqual(0, runtime.verify_calls)

    async def test_unobserved_runtime_state_blocks_before_install(self):
        runtime = _DockerRuntime(
            initial=ContainerDockerReadiness(
                node=_node(),
                observed=False,
                engine_state=DockerEngineState.UNKNOWN,
            ),
        )

        results = await LxcDockerInstallService(runtime).ensure_docker_installed(
            (_node(),),
        )

        self.assertEqual(1, len(results))
        self.assertEqual(VerificationStatus.BLOCKED, results[0].status)
        self.assertEqual([], runtime.installed_nodes)

    async def test_install_step_aggregates_node_results_for_platform_workflow(self):
        runtime = _DockerRuntime(
            initial=ContainerDockerReadiness(
                node=_node(),
                observed=True,
                engine_state=DockerEngineState.READY,
            ),
        )
        step = LxcDockerInstallStep(
            LxcDockerInstallService(runtime),
            (_node(),),
        )

        result = await PlatformInitWorkflow([step]).run()

        self.assertEqual("completed", result.status.value)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual(
            "container_runtime_verified",
            result.verification_results[0].evidence["classification"],
        )


class _DockerRuntime:
    def __init__(
        self,
        *,
        initial: ContainerDockerReadiness,
        install: ContainerDockerInstallOutcome | None = None,
        verified: ContainerDockerReadiness | None = None,
    ) -> None:
        self.initial = initial
        self.install = install
        self.verified = verified
        self.installed_nodes: list[str] = []
        self.verify_calls = 0

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        await async_checkpoint()
        return self.initial

    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        await async_checkpoint()
        self.installed_nodes.append(node.name)
        if self.install is None:
            raise AssertionError("install_docker was not expected")
        return self.install

    async def verify_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        await async_checkpoint()
        self.verify_calls += 1
        if self.verified is None:
            raise AssertionError("verify_docker was not expected")
        return self.verified


def _node() -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


if __name__ == "__main__":
    unittest.main()

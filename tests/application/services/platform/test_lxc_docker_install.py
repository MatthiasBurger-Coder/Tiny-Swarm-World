import asyncio
import unittest
from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.services.platform.incus.lxc_docker_install import (
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
    async def test_one_node_failure_is_isolated_and_results_keep_configured_order(self):
        runtime = _OutOfOrderFailureRuntime()

        results = await LxcDockerInstallService(
            runtime,
            max_concurrency=3,
        ).ensure_docker_installed(
            (_node(), _worker(), _worker_2()),
        )

        self.assertEqual(
            [result.evidence["node"] for result in results],
            [
                "swarm-manager",
                "swarm-manager",
                "swarm-worker-1",
                "swarm-worker-2",
                "swarm-worker-2",
            ],
        )
        result_groups = [
            [result for result in results if result.evidence["node"] == node_name]
            for node_name in ("swarm-manager", "swarm-worker-1", "swarm-worker-2")
        ]
        self.assertEqual(
            [result.status for result in result_groups[0]],
            [VerificationStatus.VERIFIED, VerificationStatus.VERIFIED],
        )
        self.assertEqual(len(result_groups[1]), 1)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result_groups[1][0].status)
        self.assertEqual(result_groups[1][0].evidence["role"], NodeRole.WORKER.value)
        self.assertEqual(result_groups[1][0].evidence["operation_phase"], "install")
        self.assertIn("RuntimeError", result_groups[1][0].evidence["failure_reason"])
        self.assertEqual(
            [result.status for result in result_groups[2]],
            [VerificationStatus.VERIFIED, VerificationStatus.VERIFIED],
        )

    async def test_node_lifecycles_are_bounded_by_configured_concurrency(self):
        runtime = _ConcurrencyRuntime()
        service = LxcDockerInstallService(runtime, max_concurrency=2)

        results = await service.ensure_docker_installed(
            (_node(), _worker(), _worker_2()),
        )

        self.assertEqual(
            [result.evidence["node"] for result in results],
            ["swarm-manager", "swarm-worker-1", "swarm-worker-2"],
        )
        self.assertEqual(runtime.max_active, 2)

    def test_node_concurrency_must_be_positive(self):
        with self.assertRaises(ValueError):
            LxcDockerInstallService(_ConcurrencyRuntime(), max_concurrency=0)

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
        self.assertEqual(runtime.installed_nodes, [])

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
            [result.status for result in results],
            [
                VerificationStatus.VERIFIED,
                VerificationStatus.VERIFIED,
            ],
        )
        self.assertEqual(runtime.installed_nodes, ["swarm-manager"])

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
                failure_reason="apt_repository_unreachable",
            ),
        )

        results = await LxcDockerInstallService(runtime).ensure_docker_installed(
            (_node(),),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, results[0].status)
        self.assertEqual(results[0].evidence["failure_reason"], "apt_repository_unreachable")
        self.assertEqual(runtime.verify_calls, 0)

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

        self.assertEqual(len(results), 1)
        self.assertEqual(VerificationStatus.BLOCKED, results[0].status)
        self.assertEqual(runtime.installed_nodes, [])

    async def test_verify_docker_runtime_checks_every_expected_node(self):
        runtime = _DockerRuntime(
            initial=ContainerDockerReadiness(
                node=_node(),
                observed=True,
                engine_state=DockerEngineState.READY,
            ),
        )

        results = await LxcDockerInstallService(runtime).verify_docker_runtime(
            (_node(), _worker(), _worker_2()),
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(
            runtime.inspected_nodes,
            ["swarm-manager", "swarm-worker-1", "swarm-worker-2"],
        )

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

        self.assertEqual(result.status.value, "completed")
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual(
            result.verification_results[0].evidence["classification"],
            "container_runtime_verified",
        )

    async def test_install_step_reports_first_failed_node_and_reason(self):
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
                failure_reason="apt_repository_unreachable",
            ),
        )
        step = LxcDockerInstallStep(
            LxcDockerInstallService(runtime),
            (_node(),),
        )

        result = await step.run()

        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(result.evidence["failed_nodes"], "swarm-manager")
        self.assertEqual(result.evidence["first_failure_node"], "swarm-manager")
        self.assertEqual(
            result.evidence["first_failure_classification"],
            "docker_install_failed",
        )
        self.assertEqual(
            result.evidence["first_failure_reason"],
            "apt_repository_unreachable",
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
        self.inspected_nodes: list[str] = []

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        await async_checkpoint()
        self.inspected_nodes.append(node.name)
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


class _ConcurrencyRuntime:
    def __init__(self) -> None:
        self.active = 0
        self.max_active = 0

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        await self._checkpoint()
        return ContainerDockerReadiness(
            node=node,
            observed=True,
            engine_state=DockerEngineState.READY,
        )

    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        raise AssertionError(f"install_docker was not expected for {node.name}")

    async def verify_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        raise AssertionError(f"verify_docker was not expected for {node.name}")

    async def _checkpoint(self) -> None:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        await async_checkpoint()
        self.active -= 1


class _OutOfOrderFailureRuntime:
    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        if node.name == "swarm-manager":
            await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(0)
        return ContainerDockerReadiness(
            node=node,
            observed=True,
            engine_state=DockerEngineState.MISSING,
        )

    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        await asyncio.sleep(0)
        if node.name == "swarm-worker-1":
            raise RuntimeError("node operation failed")
        return ContainerDockerInstallOutcome(
            node=node,
            state=DockerInstallState.INSTALLED,
            verified=True,
        )

    async def verify_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        await asyncio.sleep(0)
        return ContainerDockerReadiness(
            node=node,
            observed=True,
            engine_state=DockerEngineState.READY,
        )


def _node() -> NodeSpec:
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


def _worker_2() -> NodeSpec:
    return NodeSpec(
        name="swarm-worker-2",
        role=NodeRole.WORKER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


if __name__ == "__main__":
    unittest.main()

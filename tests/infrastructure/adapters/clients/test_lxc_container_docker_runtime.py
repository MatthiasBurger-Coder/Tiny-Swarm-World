import unittest

from tests.support.sonar_safe_literals import ipv4_address
from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.domain.node_provider import (
    DockerEngineState,
    DockerInstallState,
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
    DockerRegistryMirrorConfiguration,
    LxcContainerDockerRuntime,
    redact_argv_for_test,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
)


class TestLxcContainerDockerRuntime(unittest.IsolatedAsyncioTestCase):
    async def test_lxd_inspect_uses_backend_exec_and_reports_ready(self):
        runner = _FakeRunner(LxcNodeCommandResult(returncode=0, stdout="24.0.0"))
        runtime = _runtime(runner, backend=ManagedLxcBackend.LXD)

        readiness = await runtime.inspect_docker(_node())

        self.assertTrue(readiness.ready)
        self.assertEqual(DockerEngineState.READY, readiness.engine_state)
        self.assertEqual(
            (
                "lxc",
                "exec",
                "swarm-manager",
                "--",
                "docker",
                "info",
                "--format",
                "{{json .ServerVersion}}",
            ),
            runner.calls[0][0],
        )

    async def test_incus_install_uses_structured_exec_and_verifies_after_apply(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(returncode=0, stdout="token=secret"),
            LxcNodeCommandResult(returncode=0, stdout="24.0.0"),
        )
        runtime = _runtime(runner, allow_live_mutation=True)

        outcome = await runtime.install_docker(_node())

        self.assertEqual(DockerInstallState.INSTALLED, outcome.state)
        self.assertTrue(outcome.verified)
        self.assertEqual("incus", runner.calls[0][0][0])
        self.assertEqual(("incus", "exec", "swarm-manager", "--", "bash", "-lc", "<script>"), runner.redacted_calls[0][0])
        self.assertNotIn("token=secret", repr(outcome))

    async def test_install_writes_lxc_reachable_registry_mirror_when_configured(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(returncode=0),
            LxcNodeCommandResult(returncode=0, stdout="24.0.0"),
        )
        runtime = _runtime(
            runner,
            registry_mirror=DockerRegistryMirrorConfiguration(f"http://{ipv4_address(10, 0, 3, 1)}:5001"),
        )

        await runtime.install_docker(_node())

        script = runner.calls[0][0][-1]
        self.assertIn('"registry-mirrors": [', script)
        self.assertIn('"http://10.0.3.1:5001"', script)
        self.assertIn('"insecure-registries": [', script)
        self.assertIn('"10.0.3.1:5001"', script)
        self.assertIn("cat > /etc/docker/daemon.json", script)
        self.assertIn("systemctl restart docker || service docker restart || true", script)

    def test_rejects_localhost_registry_mirror_for_lxc_nodes(self):
        with self.assertRaises(ValueError):
            DockerRegistryMirrorConfiguration("http://127.0.0.1:5001")

    async def test_install_blocks_without_live_mutation_consent(self):
        runner = _FakeRunner()
        runtime = _runtime(runner, allow_live_mutation=False)

        outcome = await runtime.install_docker(_node())

        self.assertEqual(DockerInstallState.FAILED, outcome.state)
        self.assertFalse(outcome.verified)
        self.assertEqual([], runner.calls)

    async def test_failed_inspect_classifies_missing_engine_without_raw_output(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(
                returncode=127,
                stderr="docker: not found token=secret /home/alice",
            )
        )
        runtime = _runtime(runner)

        readiness = await runtime.inspect_docker(_node())

        self.assertFalse(readiness.ready)
        self.assertEqual(DockerEngineState.MISSING, readiness.engine_state)
        self.assertNotIn("token=secret", repr(readiness))
        self.assertNotIn("/home/alice", repr(readiness))


class _FakeRunner:
    def __init__(self, *results: LxcNodeCommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[tuple[str, ...], float]] = []
        self.redacted_calls: list[tuple[tuple[str, ...], float]] = []

    async def run(
        self,
        args,
        timeout_seconds,
    ) -> LxcNodeCommandResult:
        await async_checkpoint()
        self.calls.append((tuple(args), timeout_seconds))
        self.redacted_calls.append((redact_argv_for_test(args), timeout_seconds))
        if not self.results:
            raise AssertionError("unexpected LXC Docker runtime call")
        return self.results.pop(0)


def _runtime(
    runner: _FakeRunner,
    *,
    backend: ManagedLxcBackend = ManagedLxcBackend.INCUS,
    allow_live_mutation: bool = True,
    registry_mirror: DockerRegistryMirrorConfiguration | None = None,
) -> LxcContainerDockerRuntime:
    return LxcContainerDockerRuntime(
        backend=backend,
        runner=runner,
        allow_live_mutation=allow_live_mutation,
        registry_mirror=registry_mirror,
    )


def _node() -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


if __name__ == "__main__":
    unittest.main()

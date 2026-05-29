import unittest

from tiny_swarm_world.domain.node_provider import (
    DockerEngineState,
    DockerInstallState,
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
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
) -> LxcContainerDockerRuntime:
    return LxcContainerDockerRuntime(
        backend=backend,
        runner=runner,
        allow_live_mutation=allow_live_mutation,
    )


def _node() -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


if __name__ == "__main__":
    unittest.main()

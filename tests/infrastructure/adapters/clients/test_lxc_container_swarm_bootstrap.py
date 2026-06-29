import unittest
from tests.support.async_helpers import async_checkpoint
from tests.support.sonar_safe_literals import ipv4_address

from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    SwarmManagerState,
    SwarmWorkerJoinCredential,
    WorkerJoinState,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_swarm_bootstrap import (
    LxcContainerNetworkIdentity,
    LxcContainerSwarmBootstrap,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
)


class TestLxcContainerSwarmBootstrap(unittest.IsolatedAsyncioTestCase):
    async def test_manager_identity_uses_selected_backend_exec(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(
                returncode=0,
                stdout=f"{ipv4_address(10, 10, 0, 5)} fd00::1",
            )
        )
        identity = LxcContainerNetworkIdentity(
            backend=ManagedLxcBackend.LXD,
            runner=runner,
        )

        address = await identity.manager_advertise_address(_manager())

        self.assertEqual(ipv4_address(10, 10, 0, 5), address)
        self.assertEqual(
            (
                "lxc",
                "exec",
                "swarm-manager",
                "--",
                "sh",
                "-lc",
                "ip -4 -o addr show dev eth0 | awk '{print $4}' | cut -d/ -f1",
            ),
            runner.calls[0][0],
        )

    async def test_active_manager_is_observed_without_mutation(self):
        runner = _FakeRunner(LxcNodeCommandResult(returncode=0, stdout="active true"))
        swarm = _swarm(runner, allow_live_mutation=False)

        outcome = await swarm.inspect_manager(_manager())

        self.assertEqual(SwarmManagerState.ACTIVE, outcome.state)
        self.assertEqual(1, outcome.manager_count)
        self.assertEqual(1, len(runner.calls))

    async def test_manager_init_requires_live_mutation_consent(self):
        runner = _FakeRunner()
        swarm = _swarm(runner, allow_live_mutation=False)

        outcome = await swarm.initialize_manager(_manager(), ipv4_address(10, 10, 0, 5))

        self.assertEqual(SwarmManagerState.ERROR, outcome.state)
        self.assertEqual([], runner.calls)

    async def test_manager_init_uses_structured_argv(self):
        runner = _FakeRunner(LxcNodeCommandResult(returncode=0))
        swarm = _swarm(runner, allow_live_mutation=True)

        outcome = await swarm.initialize_manager(_manager(), ipv4_address(10, 10, 0, 5))

        self.assertEqual(SwarmManagerState.INITIALIZED, outcome.state)
        self.assertEqual(
            (
                "incus",
                "exec",
                "swarm-manager",
                "--",
                "docker",
                "swarm",
                "init",
                "--advertise-addr",
                ipv4_address(10, 10, 0, 5),
                "--default-addr-pool",
                "10.240.0.0/16",
                "--default-addr-pool-mask-length",
                "24",
            ),
            runner.calls[0][0],
        )

    async def test_worker_join_token_is_memory_only_outcome(self):
        runner = _FakeRunner(LxcNodeCommandResult(returncode=0, stdout="sensitive-token"))
        swarm = _swarm(runner)

        credential = await swarm.worker_join_credential(_manager())

        self.assertEqual("<redacted>", str(credential))
        self.assertNotIn("sensitive-token", repr(credential))

    async def test_worker_join_uses_token_without_persisting_it_in_outcome(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(returncode=0, stdout="left"),
            LxcNodeCommandResult(returncode=0, stdout="joined"),
            LxcNodeCommandResult(returncode=0, stdout="active false"),
        )
        swarm = _swarm(runner, allow_live_mutation=True)

        outcome = await swarm.join_worker(
            _worker(),
            ipv4_address(10, 10, 0, 5),
            SwarmWorkerJoinCredential("sensitive-token"),
        )

        self.assertEqual(WorkerJoinState.JOINED, outcome.state)
        self.assertTrue(outcome.verified)
        self.assertEqual("leave", runner.calls[0][0][6])
        self.assertEqual("--force", runner.calls[0][0][7])
        self.assertIn("sensitive-token", runner.calls[1][0])
        self.assertNotIn("sensitive-token", repr(outcome))
        self.assertEqual("docker", runner.calls[2][0][4])
        self.assertEqual("info", runner.calls[2][0][5])

    async def test_worker_join_fails_when_post_join_state_is_inactive(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(returncode=1, stdout="not part of a swarm"),
            LxcNodeCommandResult(returncode=0, stdout="joined"),
            LxcNodeCommandResult(returncode=0, stdout="inactive false"),
        )
        swarm = _swarm(runner, allow_live_mutation=True)

        outcome = await swarm.join_worker(
            _worker(),
            ipv4_address(10, 10, 0, 5),
            SwarmWorkerJoinCredential("sensitive-token"),
        )

        self.assertEqual(WorkerJoinState.FAILED, outcome.state)
        self.assertFalse(outcome.verified)

    async def test_worker_join_timeout_can_verify_after_background_join_completes(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(returncode=0, stdout="left"),
            LxcNodeCommandResult(returncode=1, stderr="join continues in the background"),
            LxcNodeCommandResult(returncode=0, stdout="pending false"),
            LxcNodeCommandResult(returncode=0, stdout="active false"),
        )
        swarm = _swarm(
            runner,
            allow_live_mutation=True,
            verify_attempts=2,
            verify_delay_seconds=0,
        )

        outcome = await swarm.join_worker(
            _worker(),
            ipv4_address(10, 10, 0, 5),
            SwarmWorkerJoinCredential("sensitive-token"),
        )

        self.assertEqual(WorkerJoinState.JOINED, outcome.state)
        self.assertTrue(outcome.verified)
        self.assertEqual(4, len(runner.calls))


class _FakeRunner:
    def __init__(self, *results: LxcNodeCommandResult) -> None:
        self.results = list(results)
        self.calls: list[tuple[tuple[str, ...], float]] = []

    async def run(
        self,
        args,
        timeout_seconds,
    ) -> LxcNodeCommandResult:
        await async_checkpoint()
        self.calls.append((tuple(args), timeout_seconds))
        if not self.results:
            raise AssertionError("unexpected LXC Swarm call")
        return self.results.pop(0)


def _swarm(
    runner: _FakeRunner,
    *,
    allow_live_mutation: bool = True,
    verify_attempts: int = 1,
    verify_delay_seconds: float = 0,
) -> LxcContainerSwarmBootstrap:
    return LxcContainerSwarmBootstrap(
        backend=ManagedLxcBackend.INCUS,
        runner=runner,
        allow_live_mutation=allow_live_mutation,
        verify_attempts=verify_attempts,
        verify_delay_seconds=verify_delay_seconds,
    )


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

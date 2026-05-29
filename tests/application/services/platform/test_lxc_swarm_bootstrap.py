import unittest

from tiny_swarm_world.application.services.platform.lxc_swarm_bootstrap import (
    LxcSwarmBootstrapService,
)
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    SwarmManagerBootstrapOutcome,
    SwarmManagerState,
    SwarmWorkerJoinCredential,
    SwarmWorkerJoinOutcome,
    WorkerJoinState,
)


class TestLxcSwarmBootstrapService(unittest.IsolatedAsyncioTestCase):
    async def test_active_manager_and_joined_worker_do_not_mutate(self):
        swarm = _SwarmBootstrap(
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

        results = await LxcSwarmBootstrapService(swarm, _NetworkIdentity()).bootstrap_swarm(
            _manager(),
            (_worker(),),
        )

        self.assertEqual(
            [VerificationStatus.VERIFIED, VerificationStatus.VERIFIED],
            [result.status for result in results],
        )
        self.assertEqual(0, swarm.init_calls)
        self.assertEqual(0, swarm.join_calls)

    async def test_pending_manager_is_initialized_before_workers_join(self):
        swarm = _SwarmBootstrap(
            manager=SwarmManagerBootstrapOutcome(
                node=_manager(),
                state=SwarmManagerState.PENDING,
            ),
            initialized_manager=SwarmManagerBootstrapOutcome(
                node=_manager(),
                state=SwarmManagerState.INITIALIZED,
                manager_count=1,
            ),
            worker=SwarmWorkerJoinOutcome(
                node=_worker(),
                state=WorkerJoinState.UNKNOWN,
                verified=False,
            ),
            joined_worker=SwarmWorkerJoinOutcome(
                node=_worker(),
                state=WorkerJoinState.JOINED,
                verified=True,
            ),
        )

        results = await LxcSwarmBootstrapService(swarm, _NetworkIdentity()).bootstrap_swarm(
            _manager(),
            (_worker(),),
        )

        self.assertEqual(
            [VerificationStatus.VERIFIED, VerificationStatus.VERIFIED],
            [result.status for result in results],
        )
        self.assertEqual(1, swarm.init_calls)
        self.assertEqual(1, swarm.join_calls)
        self.assertNotIn("sensitive-value", repr(swarm.credentials_seen[0]))

    async def test_failed_worker_join_does_not_persist_credential_in_results(self):
        swarm = _SwarmBootstrap(
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
            joined_worker=SwarmWorkerJoinOutcome(
                node=_worker(),
                state=WorkerJoinState.FAILED,
                verified=False,
            ),
        )

        results = await LxcSwarmBootstrapService(swarm, _NetworkIdentity()).bootstrap_swarm(
            _manager(),
            (_worker(),),
        )

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, results[-1].status)
        self.assertNotIn("sensitive-value", repr([result.to_dict() for result in results]))


class _NetworkIdentity:
    async def manager_advertise_address(self, node: NodeSpec) -> str:
        return "manager-address"


class _SwarmBootstrap:
    def __init__(
        self,
        *,
        manager: SwarmManagerBootstrapOutcome,
        worker: SwarmWorkerJoinOutcome,
        initialized_manager: SwarmManagerBootstrapOutcome | None = None,
        joined_worker: SwarmWorkerJoinOutcome | None = None,
    ) -> None:
        self.manager = manager
        self.initialized_manager = initialized_manager
        self.worker = worker
        self.joined_worker = joined_worker
        self.init_calls = 0
        self.join_calls = 0
        self.credentials_seen: list[SwarmWorkerJoinCredential] = []

    async def inspect_manager(self, node: NodeSpec) -> SwarmManagerBootstrapOutcome:
        return self.manager

    async def initialize_manager(
        self,
        node: NodeSpec,
        advertise_address: str,
    ) -> SwarmManagerBootstrapOutcome:
        self.init_calls += 1
        if self.initialized_manager is None:
            raise AssertionError("initialize_manager was not expected")
        return self.initialized_manager

    async def worker_join_credential(self, node: NodeSpec) -> SwarmWorkerJoinCredential:
        return SwarmWorkerJoinCredential("sensitive-value")

    async def inspect_worker(self, node: NodeSpec) -> SwarmWorkerJoinOutcome:
        return self.worker

    async def join_worker(
        self,
        node: NodeSpec,
        manager_address: str,
        credential: SwarmWorkerJoinCredential,
    ) -> SwarmWorkerJoinOutcome:
        self.join_calls += 1
        self.credentials_seen.append(credential)
        if self.joined_worker is None:
            raise AssertionError("join_worker was not expected")
        return self.joined_worker


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

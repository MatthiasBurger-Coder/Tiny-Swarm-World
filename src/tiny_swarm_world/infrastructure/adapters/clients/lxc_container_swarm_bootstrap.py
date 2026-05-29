from __future__ import annotations

from tiny_swarm_world.application.ports.node_provider import (
    PortContainerNetworkIdentity,
    PortContainerSwarmBootstrap,
)
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeSpec,
    SwarmManagerBootstrapOutcome,
    SwarmManagerState,
    SwarmWorkerJoinCredential,
    SwarmWorkerJoinOutcome,
    WorkerJoinState,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
    LxcNodeCommandRunner,
)


DEFAULT_SWARM_COMMAND_TIMEOUT_SECONDS = 120.0

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}


class LxcContainerNetworkIdentity(PortContainerNetworkIdentity):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        runner: LxcNodeCommandRunner,
        timeout_seconds: float = DEFAULT_SWARM_COMMAND_TIMEOUT_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Network identity timeout must be positive.")
        self.backend = backend
        self.runner = runner
        self.timeout_seconds = timeout_seconds

    async def manager_advertise_address(self, node: NodeSpec) -> str:
        result = await self.runner.run(
            _hostname_ip_args(self.backend, node),
            self.timeout_seconds,
        )
        if result.returncode != 0 or result.timed_out:
            return ""
        return (result.stdout.strip().split() or [""])[0]


class LxcContainerSwarmBootstrap(PortContainerSwarmBootstrap):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        runner: LxcNodeCommandRunner,
        timeout_seconds: float = DEFAULT_SWARM_COMMAND_TIMEOUT_SECONDS,
        allow_live_mutation: bool = False,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Swarm command timeout must be positive.")
        self.backend = backend
        self.runner = runner
        self.timeout_seconds = timeout_seconds
        self.allow_live_mutation = allow_live_mutation

    async def inspect_manager(self, node: NodeSpec) -> SwarmManagerBootstrapOutcome:
        result = await self.runner.run(
            _swarm_state_args(self.backend, node),
            self.timeout_seconds,
        )
        return _manager_outcome(node, result)

    async def initialize_manager(
        self,
        node: NodeSpec,
        advertise_address: str,
    ) -> SwarmManagerBootstrapOutcome:
        if not self.allow_live_mutation or not advertise_address:
            return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.ERROR)
        result = await self.runner.run(
            _manager_init_args(self.backend, node, advertise_address),
            self.timeout_seconds,
        )
        if result.returncode != 0 or result.timed_out:
            return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.ERROR)
        return SwarmManagerBootstrapOutcome(
            node=node,
            state=SwarmManagerState.INITIALIZED,
            manager_count=1,
        )

    async def worker_join_credential(self, node: NodeSpec) -> SwarmWorkerJoinCredential:
        result = await self.runner.run(
            _worker_token_args(self.backend, node),
            self.timeout_seconds,
        )
        if result.returncode != 0 or result.timed_out:
            return SwarmWorkerJoinCredential("<unavailable>")
        return SwarmWorkerJoinCredential(result.stdout.strip())

    async def inspect_worker(self, node: NodeSpec) -> SwarmWorkerJoinOutcome:
        result = await self.runner.run(
            _swarm_state_args(self.backend, node),
            self.timeout_seconds,
        )
        return _worker_outcome(node, result)

    async def join_worker(
        self,
        node: NodeSpec,
        manager_address: str,
        credential: SwarmWorkerJoinCredential,
    ) -> SwarmWorkerJoinOutcome:
        if not self.allow_live_mutation or not manager_address:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.FAILED,
                verified=False,
            )
        result = await self.runner.run(
            _worker_join_args(self.backend, node, manager_address, credential.value),
            self.timeout_seconds,
        )
        if result.returncode != 0 or result.timed_out:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.FAILED,
                verified=False,
            )
        return SwarmWorkerJoinOutcome(
            node=node,
            state=WorkerJoinState.JOINED,
            verified=True,
        )


def _hostname_ip_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "exec", node.name, "--", "hostname", "-I")


def _swarm_state_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "docker",
        "info",
        "--format",
        "{{.Swarm.LocalNodeState}} {{.Swarm.ControlAvailable}}",
    )


def _manager_init_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
    advertise_address: str,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "docker",
        "swarm",
        "init",
        "--advertise-addr",
        advertise_address,
    )


def _worker_token_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "docker",
        "swarm",
        "join-token",
        "-q",
        "worker",
    )


def _worker_join_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
    manager_address: str,
    token: str,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "docker",
        "swarm",
        "join",
        "--token",
        token,
        f"{manager_address}:2377",
    )


def _manager_outcome(
    node: NodeSpec,
    result: LxcNodeCommandResult,
) -> SwarmManagerBootstrapOutcome:
    if result.returncode != 0 or result.timed_out:
        return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.UNKNOWN)
    output = result.stdout.casefold()
    if "active" in output and "true" in output:
        return SwarmManagerBootstrapOutcome(
            node=node,
            state=SwarmManagerState.ACTIVE,
            manager_count=1,
        )
    if "active" in output:
        return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.ERROR)
    return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.PENDING)


def _worker_outcome(
    node: NodeSpec,
    result: LxcNodeCommandResult,
) -> SwarmWorkerJoinOutcome:
    if result.returncode != 0 or result.timed_out:
        return SwarmWorkerJoinOutcome(
            node=node,
            state=WorkerJoinState.UNKNOWN,
            verified=False,
        )
    if "active" in result.stdout.casefold():
        return SwarmWorkerJoinOutcome(
            node=node,
            state=WorkerJoinState.ALREADY_JOINED,
            verified=True,
        )
    return SwarmWorkerJoinOutcome(
        node=node,
        state=WorkerJoinState.UNKNOWN,
        verified=False,
    )

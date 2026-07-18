from __future__ import annotations

import asyncio
import os

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
DEFAULT_SWARM_OVERLAY_ADDRESS_POOL = os.getenv(
    "TSW_SWARM_OVERLAY_ADDRESS_POOL",
    "10.240.0.0/16",
)
DEFAULT_SWARM_OVERLAY_ADDRESS_POOL_MASK_LENGTH = os.getenv(
    "TSW_SWARM_OVERLAY_ADDRESS_POOL_MASK_LENGTH",
    "24",
)

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
        verify_attempts: int = 6,
        verify_delay_seconds: float = 5.0,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Swarm command timeout must be positive.")
        if verify_attempts <= 0:
            raise ValueError("Swarm verify attempts must be positive.")
        if verify_delay_seconds < 0:
            raise ValueError("Swarm verify delay must not be negative.")
        self.backend = backend
        self.runner = runner
        self.timeout_seconds = timeout_seconds
        self.allow_live_mutation = allow_live_mutation
        self.verify_attempts = verify_attempts
        self.verify_delay_seconds = verify_delay_seconds

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
        await self.runner.run(
            _worker_leave_args(self.backend, node),
            self.timeout_seconds,
        )
        result = await self.runner.run(
            _worker_join_args(self.backend, node, manager_address, credential.value),
            self.timeout_seconds,
        )
        verified_outcome = await self._verify_worker_join(node)
        if verified_outcome.verified:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.JOINED,
                verified=True,
            )
        if result.returncode != 0 or result.timed_out:
            return SwarmWorkerJoinOutcome(
                node=node,
                state=WorkerJoinState.FAILED,
                verified=False,
            )
        return SwarmWorkerJoinOutcome(
            node=node,
            state=WorkerJoinState.FAILED,
            verified=False,
        )

    async def _verify_worker_join(self, node: NodeSpec) -> SwarmWorkerJoinOutcome:
        verified_outcome = SwarmWorkerJoinOutcome(
            node=node,
            state=WorkerJoinState.FAILED,
            verified=False,
        )
        for attempt in range(self.verify_attempts):
            verify_result = await self.runner.run(
                _swarm_state_args(self.backend, node),
                self.timeout_seconds,
            )
            verified_outcome = _worker_outcome(node, verify_result)
            if verified_outcome.verified:
                return verified_outcome
            if attempt + 1 < self.verify_attempts:
                await asyncio.sleep(self.verify_delay_seconds)
        return verified_outcome


def _hostname_ip_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "sh",
        "-lc",
        "ip -4 -o addr show dev eth0 | awk '{print $4}' | cut -d/ -f1",
    )


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
        "--default-addr-pool",
        DEFAULT_SWARM_OVERLAY_ADDRESS_POOL,
        "--default-addr-pool-mask-length",
        DEFAULT_SWARM_OVERLAY_ADDRESS_POOL_MASK_LENGTH,
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


def _worker_leave_args(
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
        "leave",
        "--force",
    )


def _manager_outcome(
    node: NodeSpec,
    result: LxcNodeCommandResult,
) -> SwarmManagerBootstrapOutcome:
    if result.returncode != 0 or result.timed_out:
        return SwarmManagerBootstrapOutcome(node=node, state=SwarmManagerState.UNKNOWN)
    state, control_available = _swarm_info_tokens(result.stdout)
    if state == "active" and control_available == "true":
        return SwarmManagerBootstrapOutcome(
            node=node,
            state=SwarmManagerState.ACTIVE,
            manager_count=1,
        )
    if state == "active":
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
    state, control_available = _swarm_info_tokens(result.stdout)
    if state == "active" and control_available == "false":
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


def _swarm_info_tokens(output: str) -> tuple[str, str]:
    parts = output.casefold().strip().split()
    state = parts[0] if parts else ""
    control_available = parts[1] if len(parts) > 1 else ""
    return state, control_available

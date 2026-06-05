from __future__ import annotations

from collections.abc import Sequence

from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDeviceState,
    PortLxcProxyDeviceRuntime,
)
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeSpec
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
    LxcNodeCommandRunner,
)


DEFAULT_LXC_PROXY_DEVICE_TIMEOUT_SECONDS = 30.0

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
_MISSING_DEVICE_MARKERS = (
    "not found",
    "does not exist",
    "doesn't exist",
    "not exist",
    "no such device",
    "not available",
)


class LxcProxyDeviceRuntime(PortLxcProxyDeviceRuntime):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        runner: LxcNodeCommandRunner,
        timeout_seconds: float = DEFAULT_LXC_PROXY_DEVICE_TIMEOUT_SECONDS,
        allow_live_mutation: bool = False,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("LXC proxy device timeout must be positive.")
        self.backend = backend
        self.runner = runner
        self.timeout_seconds = timeout_seconds
        self.allow_live_mutation = allow_live_mutation

    async def inspect_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        listen = await self.runner.run(
            _device_get_args(self.backend, node, plan, "listen"),
            self.timeout_seconds,
        )
        if _command_missing_device(listen):
            return LxcProxyDeviceState.MISSING
        if _command_failed(listen):
            return LxcProxyDeviceState.UNKNOWN

        connect = await self.runner.run(
            _device_get_args(self.backend, node, plan, "connect"),
            self.timeout_seconds,
        )
        if _command_missing_device(connect):
            return LxcProxyDeviceState.DRIFTED
        if _command_failed(connect):
            return LxcProxyDeviceState.UNKNOWN
        if (
            listen.stdout.strip() == plan.listen_endpoint
            and connect.stdout.strip() == plan.target_endpoint
        ):
            return LxcProxyDeviceState.PRESENT
        return LxcProxyDeviceState.DRIFTED

    async def create_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        if not self.allow_live_mutation:
            return False
        result = await self.runner.run(
            _device_add_args(self.backend, node, plan),
            self.timeout_seconds,
        )
        return not _command_failed(result)

    async def update_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        if not self.allow_live_mutation:
            return False
        listen_result = await self.runner.run(
            _device_set_args(self.backend, node, plan, "listen", plan.listen_endpoint),
            self.timeout_seconds,
        )
        if _command_failed(listen_result):
            return False
        connect_result = await self.runner.run(
            _device_set_args(self.backend, node, plan, "connect", plan.target_endpoint),
            self.timeout_seconds,
        )
        return not _command_failed(connect_result)


def _device_get_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
    plan: LxcProxyDevicePlan,
    key: str,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "config",
        "device",
        "get",
        node.name,
        plan.device_name,
        key,
    )


def _device_add_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
    plan: LxcProxyDevicePlan,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "config",
        "device",
        "add",
        node.name,
        plan.device_name,
        "proxy",
        f"listen={plan.listen_endpoint}",
        f"connect={plan.target_endpoint}",
    )


def _device_set_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
    plan: LxcProxyDevicePlan,
    key: str,
    value: str,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "config",
        "device",
        "set",
        node.name,
        plan.device_name,
        key,
        value,
    )


def _command_failed(result: LxcNodeCommandResult) -> bool:
    return result.timed_out or result.returncode != 0


def _command_missing_device(result: LxcNodeCommandResult) -> bool:
    if result.timed_out or result.returncode == 0:
        return False
    output = _combined_output(result)
    return any(marker in output for marker in _MISSING_DEVICE_MARKERS)


def _combined_output(result: LxcNodeCommandResult) -> str:
    return f"{result.stdout}\n{result.stderr}".lower()

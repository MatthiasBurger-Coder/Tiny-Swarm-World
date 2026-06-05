import unittest

from tiny_swarm_world.application.ports.node_provider import LxcProxyDeviceState
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_proxy_device_runtime import (
    LxcProxyDeviceRuntime,
)


class TestLxcProxyDeviceRuntime(unittest.IsolatedAsyncioTestCase):
    async def test_inspect_reports_present_when_listen_and_connect_match(self):
        runner = _RecordingRunner(
            results=(
                LxcNodeCommandResult(0, stdout="tcp:0.0.0.0:8080\n"),
                LxcNodeCommandResult(0, stdout="tcp:127.0.0.1:8080\n"),
            )
        )
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.LXD,
            runner=runner,
            allow_live_mutation=True,
        )

        state = await runtime.inspect_proxy_device(_manager(), _plan())

        self.assertEqual(LxcProxyDeviceState.PRESENT, state)
        self.assertEqual(
            [
                (
                    "lxc",
                    "config",
                    "device",
                    "get",
                    "swarm-manager",
                    "tsw-proxy-8080",
                    "listen",
                ),
                (
                    "lxc",
                    "config",
                    "device",
                    "get",
                    "swarm-manager",
                    "tsw-proxy-8080",
                    "connect",
                ),
            ],
            runner.calls,
        )

    async def test_inspect_distinguishes_missing_drifted_and_unknown(self):
        missing = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=_RecordingRunner(
                results=(LxcNodeCommandResult(1, stderr="Device not found"),)
            ),
        )
        drifted = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=_RecordingRunner(
                results=(
                    LxcNodeCommandResult(0, stdout="tcp:127.0.0.1:8080"),
                    LxcNodeCommandResult(0, stdout="tcp:127.0.0.1:8080"),
                )
            ),
        )
        unknown = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=_RecordingRunner(results=(LxcNodeCommandResult(2, stderr="daemon down"),)),
        )

        self.assertEqual(
            LxcProxyDeviceState.MISSING,
            await missing.inspect_proxy_device(_manager(), _plan()),
        )
        self.assertEqual(
            LxcProxyDeviceState.DRIFTED,
            await drifted.inspect_proxy_device(_manager(), _plan()),
        )
        self.assertEqual(
            LxcProxyDeviceState.UNKNOWN,
            await unknown.inspect_proxy_device(_manager(), _plan()),
        )

    async def test_inspect_treats_existing_device_with_missing_connect_key_as_drifted(self):
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=_RecordingRunner(
                results=(
                    LxcNodeCommandResult(0, stdout="tcp:0.0.0.0:8080"),
                    LxcNodeCommandResult(1, stderr="Device not found"),
                )
            ),
        )

        self.assertEqual(
            LxcProxyDeviceState.DRIFTED,
            await runtime.inspect_proxy_device(_manager(), _plan()),
        )

    async def test_create_uses_proxy_device_arguments(self):
        runner = _RecordingRunner(results=(LxcNodeCommandResult(0),))
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            allow_live_mutation=True,
        )

        created = await runtime.create_proxy_device(_manager(), _plan())

        self.assertTrue(created)
        self.assertEqual(
            (
                "incus",
                "config",
                "device",
                "add",
                "swarm-manager",
                "tsw-proxy-8080",
                "proxy",
                "listen=tcp:0.0.0.0:8080",
                "connect=tcp:127.0.0.1:8080",
            ),
            runner.calls[0],
        )

    async def test_update_sets_listen_and_connect_without_live_output(self):
        runner = _RecordingRunner(
            results=(LxcNodeCommandResult(0), LxcNodeCommandResult(0))
        )
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.LXD,
            runner=runner,
            allow_live_mutation=True,
        )

        updated = await runtime.update_proxy_device(_manager(), _plan())

        self.assertTrue(updated)
        self.assertEqual(
            (
                "lxc",
                "config",
                "device",
                "set",
                "swarm-manager",
                "tsw-proxy-8080",
                "listen",
                "tcp:0.0.0.0:8080",
            ),
            runner.calls[0],
        )
        self.assertEqual("connect", runner.calls[1][6])

    async def test_mutating_methods_refuse_when_live_mutation_is_disabled(self):
        runner = _RecordingRunner(results=(LxcNodeCommandResult(0),))
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.LXD,
            runner=runner,
            allow_live_mutation=False,
        )

        self.assertFalse(await runtime.create_proxy_device(_manager(), _plan()))
        self.assertFalse(await runtime.update_proxy_device(_manager(), _plan()))
        self.assertEqual([], runner.calls)


class _RecordingRunner:
    def __init__(self, *, results: tuple[LxcNodeCommandResult, ...]) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    async def run(
        self,
        args: tuple[str, ...],
        timeout_seconds: float,
    ) -> LxcNodeCommandResult:
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError("No fake command result configured.")
        return self.results.pop(0)


def _manager() -> NodeSpec:
    return NodeSpec("swarm-manager", NodeRole.MANAGER, NodeProviderKind.LXC_NATIVE)


def _plan() -> LxcProxyDevicePlan:
    return LxcProxyDevicePlan(
        service="Jenkins",
        listen_port=8080,
        target_port=8080,
        listen_address="0.0.0.0",
    )

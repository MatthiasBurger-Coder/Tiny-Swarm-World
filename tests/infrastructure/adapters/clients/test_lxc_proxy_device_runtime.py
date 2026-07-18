import unittest

from tests.support.async_helpers import async_checkpoint

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

        state = await runtime.inspect_proxy_device(_manager_profile(), _plan())

        self.assertEqual(LxcProxyDeviceState.PRESENT, state)
        self.assertEqual(
            runner.calls,
            [
                (
                    "lxc",
                    "profile",
                    "device",
                    "get",
                    "docker-swarm-manager",
                    "tsw-proxy-8080",
                    "listen",
                ),
                (
                    "lxc",
                    "profile",
                    "device",
                    "get",
                    "docker-swarm-manager",
                    "tsw-proxy-8080",
                    "connect",
                ),
            ],
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
            await missing.inspect_proxy_device(_manager_profile(), _plan()),
        )
        self.assertEqual(
            LxcProxyDeviceState.DRIFTED,
            await drifted.inspect_proxy_device(_manager_profile(), _plan()),
        )
        self.assertEqual(
            LxcProxyDeviceState.UNKNOWN,
            await unknown.inspect_proxy_device(_manager_profile(), _plan()),
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
            await runtime.inspect_proxy_device(_manager_profile(), _plan()),
        )

    async def test_create_uses_profile_proxy_device_arguments(self):
        runner = _RecordingRunner(results=(LxcNodeCommandResult(0),))
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            allow_live_mutation=True,
        )

        created = await runtime.create_proxy_device(_manager_profile(), _plan())

        self.assertTrue(created)
        self.assertEqual(
            runner.calls,
            [
                (
                    "incus",
                    "profile",
                    "device",
                    "add",
                    "docker-swarm-manager",
                    "tsw-proxy-8080",
                    "proxy",
                    "listen=tcp:0.0.0.0:8080",
                    "connect=tcp:127.0.0.1:8080",
                )
            ],
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

        updated = await runtime.update_proxy_device(_manager_profile(), _plan())

        self.assertTrue(updated)
        self.assertEqual(len(runner.calls), 2)
        listen_call, connect_call = runner.calls
        self.assertEqual(
            listen_call,
            (
                "lxc",
                "profile",
                "device",
                "set",
                "docker-swarm-manager",
                "tsw-proxy-8080",
                "listen",
                "tcp:0.0.0.0:8080",
            ),
        )
        _, _, _, _, _, _, device_field, *_ = connect_call
        self.assertEqual(device_field, "connect")

    async def test_mutating_methods_refuse_when_live_mutation_is_disabled(self):
        runner = _RecordingRunner(results=(LxcNodeCommandResult(0),))
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.LXD,
            runner=runner,
            allow_live_mutation=False,
        )

        self.assertFalse(await runtime.create_proxy_device(_manager_profile(), _plan()))
        self.assertFalse(await runtime.update_proxy_device(_manager_profile(), _plan()))
        self.assertEqual(runner.calls, [])

    async def test_repair_removes_direct_project_proxy_after_profile_equivalent_is_present(
        self,
    ):
        runner = _RecordingRunner(
            results=(
                LxcNodeCommandResult(
                    0,
                    stdout=(
                        "tsw-proxy-8080:\n"
                        "  type: proxy\n"
                        "  listen: tcp:0.0.0.0:8080\n"
                        "  connect: tcp:127.0.0.1:8080\n"
                        "operator-proxy:\n"
                        "  type: proxy\n"
                    ),
                ),
                LxcNodeCommandResult(0, stdout="tcp:0.0.0.0:8080\n"),
                LxcNodeCommandResult(0, stdout="tcp:127.0.0.1:8080\n"),
                LxcNodeCommandResult(0),
            )
        )
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            allow_live_mutation=True,
        )

        outcome = await runtime.repair_stale_proxy_devices(
            _manager_profile(),
            _manager(),
            (_plan(),),
        )

        self.assertEqual(outcome.stale_direct_device_count, 1)
        self.assertEqual(outcome.removed_count, 1)
        self.assertEqual(outcome.removed_devices, ("tsw-proxy-8080",))
        self.assertEqual(outcome.refused_count, 0)
        self.assertEqual(
            runner.calls,
            [
                ("incus", "config", "device", "show", "swarm-manager"),
                (
                    "incus",
                    "profile",
                    "device",
                    "get",
                    "docker-swarm-manager",
                    "tsw-proxy-8080",
                    "listen",
                ),
                (
                    "incus",
                    "profile",
                    "device",
                    "get",
                    "docker-swarm-manager",
                    "tsw-proxy-8080",
                    "connect",
                ),
                (
                    "incus",
                    "config",
                    "device",
                    "remove",
                    "swarm-manager",
                    "tsw-proxy-8080",
                ),
            ],
        )

    async def test_repair_refuses_when_profile_equivalent_is_not_present(self):
        runner = _RecordingRunner(
            results=(
                LxcNodeCommandResult(0, stdout="tsw-proxy-8080:\n  type: proxy\n"),
                LxcNodeCommandResult(1, stderr="Device not found"),
            )
        )
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.LXD,
            runner=runner,
            allow_live_mutation=True,
        )

        outcome = await runtime.repair_stale_proxy_devices(
            _manager_profile(),
            _manager(),
            (_plan(),),
        )

        self.assertEqual(outcome.stale_direct_device_count, 1)
        self.assertEqual(outcome.removed_count, 0)
        self.assertEqual(outcome.refused_count, 1)
        self.assertEqual(outcome.refused_devices, ("tsw-proxy-8080",))
        self.assertNotIn("remove", tuple(item for call in runner.calls for item in call))

    async def test_repair_refuses_unknown_project_proxy_without_expected_plan(self):
        runner = _RecordingRunner(
            results=(
                LxcNodeCommandResult(0, stdout="tsw-proxy-9999:\n  type: proxy\n"),
            )
        )
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            allow_live_mutation=True,
        )

        outcome = await runtime.repair_stale_proxy_devices(
            _manager_profile(),
            _manager(),
            (_plan(),),
        )

        self.assertEqual(outcome.stale_direct_device_count, 1)
        self.assertEqual(outcome.removed_count, 0)
        self.assertEqual(outcome.refused_count, 1)
        self.assertEqual(outcome.refused_devices, ("tsw-proxy-9999",))
        self.assertEqual(runner.calls, [("incus", "config", "device", "show", "swarm-manager")])

    async def test_repair_refuses_without_live_mutation_before_reading_devices(self):
        runner = _RecordingRunner(results=(LxcNodeCommandResult(0),))
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            allow_live_mutation=False,
        )

        outcome = await runtime.repair_stale_proxy_devices(
            _manager_profile(),
            _manager(),
            (_plan(),),
        )

        self.assertFalse(outcome.mutation_allowed)
        self.assertEqual(outcome.expected_profile_device_count, 1)
        self.assertEqual(runner.calls, [])


class _RecordingRunner:
    def __init__(self, *, results: tuple[LxcNodeCommandResult, ...]) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, ...]] = []

    async def run(
        self,
        args: tuple[str, ...],
        timeout_seconds: float,
    ) -> LxcNodeCommandResult:
        await async_checkpoint()
        self.calls.append(tuple(args))
        if not self.results:
            raise AssertionError("No fake command result configured.")
        return self.results.pop(0)


def _manager_profile() -> str:
    return "docker-swarm-manager"


def _manager() -> NodeSpec:
    return NodeSpec("swarm-manager", NodeRole.MANAGER, NodeProviderKind.LXC_NATIVE)


def _plan() -> LxcProxyDevicePlan:
    return LxcProxyDevicePlan(
        service="Jenkins",
        listen_port=8080,
        target_port=8080,
        listen_address="0.0.0.0",
    )

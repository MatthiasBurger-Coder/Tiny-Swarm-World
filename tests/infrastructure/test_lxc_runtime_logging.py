import logging
import subprocess
import unittest
from unittest.mock import patch

from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.ports.node_provider import LxcProxyDeviceState
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
    LxcContainerDockerRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
    LxcNodeProvider,
)
from tiny_swarm_world.infrastructure.adapters.clients import lxc_node_provider
from tiny_swarm_world.infrastructure.adapters.clients.lxc_proxy_device_runtime import (
    LxcProxyDeviceRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime import (
    LxcSwarmRuntime,
)


class TestLxcRuntimeLogging(unittest.IsolatedAsyncioTestCase):
    async def test_container_docker_runtime_logs_bounded_failed_output(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(
                returncode=1,
                stdout=("ready\n" * 120),
                stderr=("failure\n" * 120),
            )
        )
        runtime = LxcContainerDockerRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            logger=logging.getLogger("test.lxc_container_docker_runtime"),
        )

        with self.assertLogs("test.lxc_container_docker_runtime", level="WARNING") as captured:
            await runtime.inspect_docker(_node())

        logged = "\n".join(captured.output)
        self.assertIn("action=inspect_docker", logged)
        self.assertIn("returncode=1", logged)
        self.assertIn("ready ready", logged)
        self.assertIn("failure failure", logged)
        self.assertIn("...", logged)

    async def test_container_docker_runtime_logs_install_paths(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(returncode=0, stdout="installed"),
            LxcNodeCommandResult(returncode=0, stdout="24.0.0"),
        )
        runtime = LxcContainerDockerRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            allow_live_mutation=True,
            logger=logging.getLogger("test.lxc_container_docker_runtime.install"),
        )

        with self.assertLogs("test.lxc_container_docker_runtime.install", level="INFO") as captured:
            outcome = await runtime.install_docker(_node())

        self.assertTrue(outcome.verified)
        logged = "\n".join(captured.output)
        self.assertIn("install_start", logged)
        self.assertIn("action=install_docker", logged)

        refused_runtime = LxcContainerDockerRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=_FakeRunner(),
            allow_live_mutation=False,
            logger=logging.getLogger("test.lxc_container_docker_runtime.refused"),
        )
        with self.assertLogs("test.lxc_container_docker_runtime.refused", level="WARNING") as refused:
            refused_outcome = await refused_runtime.install_docker(_node())

        self.assertFalse(refused_outcome.verified)
        self.assertIn("mutation_refused action=install", "\n".join(refused.output))

    async def test_proxy_device_runtime_logs_bounded_failed_output(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(
                returncode=2,
                stdout=("ready\n" * 120),
                stderr=("daemon down\n" * 120),
            )
        )
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            logger=logging.getLogger("test.lxc_proxy_device_runtime"),
        )

        with self.assertLogs("test.lxc_proxy_device_runtime", level="WARNING") as captured:
            state = await runtime.inspect_proxy_device(_manager_profile(), _plan())

        self.assertEqual(LxcProxyDeviceState.UNKNOWN, state)
        logged = "\n".join(captured.output)
        self.assertIn("action=inspect_listen", logged)
        self.assertIn("returncode=2", logged)
        self.assertIn("ready ready", logged)
        self.assertIn("daemon down", logged)
        self.assertIn("...", logged)

    async def test_proxy_device_runtime_logs_mutation_and_repair_paths(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(returncode=0, stdout="created"),
            LxcNodeCommandResult(returncode=0, stdout="listen updated"),
            LxcNodeCommandResult(returncode=0, stdout="connect updated"),
            LxcNodeCommandResult(
                returncode=0,
                stdout=(
                    "tsw-proxy-8080:\n"
                    "  type: proxy\n"
                    "  listen: tcp:0.0.0.0:8080\n"
                    "  connect: tcp:127.0.0.1:8080\n"
                ),
            ),
            LxcNodeCommandResult(returncode=0, stdout="tcp:0.0.0.0:8080"),
            LxcNodeCommandResult(returncode=0, stdout="tcp:127.0.0.1:8080"),
            LxcNodeCommandResult(returncode=0, stdout="removed"),
        )
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=runner,
            allow_live_mutation=True,
            logger=logging.getLogger("test.lxc_proxy_device_runtime.mutate"),
        )

        with self.assertLogs("test.lxc_proxy_device_runtime.mutate", level="INFO") as captured:
            self.assertTrue(await runtime.create_proxy_device(_manager_profile(), _plan()))
            self.assertTrue(await runtime.update_proxy_device(_manager_profile(), _plan()))
            outcome = await runtime.repair_stale_proxy_devices(
                _manager_profile(),
                _node(),
                (_plan(),),
            )

        self.assertEqual(outcome.removed_count, 1)
        logged = "\n".join(captured.output)
        self.assertIn("action=create", logged)
        self.assertIn("action=update_listen", logged)
        self.assertIn("action=update_connect", logged)
        self.assertIn("action=repair_show_instance_devices", logged)
        self.assertIn("action=repair_remove_instance_device", logged)

    async def test_proxy_device_runtime_logs_refused_mutations(self):
        runtime = LxcProxyDeviceRuntime(
            backend=ManagedLxcBackend.INCUS,
            runner=_FakeRunner(),
            allow_live_mutation=False,
            logger=logging.getLogger("test.lxc_proxy_device_runtime.refused"),
        )

        with self.assertLogs("test.lxc_proxy_device_runtime.refused", level="WARNING") as captured:
            self.assertFalse(await runtime.create_proxy_device(_manager_profile(), _plan()))
            self.assertFalse(await runtime.update_proxy_device(_manager_profile(), _plan()))

        logged = "\n".join(captured.output)
        self.assertIn("mutation_refused action=create", logged)
        self.assertIn("mutation_refused action=update", logged)

    async def test_node_provider_logs_bounded_failed_output(self):
        provider = LxcNodeProvider(
            config_repository=_UnusedConfigRepository(),
            runner=_FakeRunner(),
            logger=logging.getLogger("test.lxc_node_provider"),
        )

        with self.assertLogs("test.lxc_node_provider", level="WARNING") as captured:
            provider._log_command_result(
                "launch",
                _node(),
                ManagedLxcBackend.INCUS,
                LxcNodeCommandResult(
                    returncode=1,
                    stdout=("ready\n" * 120),
                    stderr=("launch failed\n" * 120),
                ),
            )

        logged = "\n".join(captured.output)
        self.assertIn("action=launch", logged)
        self.assertIn("returncode=1", logged)
        self.assertIn("ready ready", logged)
        self.assertIn("launch failed", logged)
        self.assertIn("...", logged)
        self.assertEqual(lxc_node_provider._safe_log_text("short"), "short")

    async def test_swarm_runtime_logs_bounded_manager_shell_output(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime.subprocess.run",
            return_value=subprocess.CompletedProcess(
                [],
                1,
                stdout=("ready\n" * 140),
                stderr=("failed\n" * 140),
            ),
        ):
            with self.assertLogs("LxcSwarmRuntime", level=logging.INFO) as captured:
                result = runtime._run_manager_shell("echo ready && " * 80, check=False)

        self.assertEqual(result.returncode, 1)
        logged = "\n".join(captured.output)
        self.assertIn("Running LXC manager shell operation", logged)
        self.assertIn("manager_shell_result returncode=1", logged)
        self.assertIn("ready ready", logged)
        self.assertIn("failed failed", logged)
        self.assertIn("...", logged)


class _FakeRunner:
    def __init__(self, *results: LxcNodeCommandResult) -> None:
        self.results = list(results)

    async def run(
        self,
        args,
        timeout_seconds,
    ) -> LxcNodeCommandResult:
        await async_checkpoint()
        if not self.results:
            raise AssertionError("unexpected LXC command")
        return self.results.pop(0)


class _UnusedConfigRepository:
    async def load_config(self):
        raise AssertionError("config repository should not be used")


def _node() -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


def _manager_profile() -> str:
    return "docker-swarm-manager"


def _plan() -> LxcProxyDevicePlan:
    return LxcProxyDevicePlan(
        service="Jenkins",
        listen_port=8080,
        target_port=8080,
        listen_address="0.0.0.0",
    )


if __name__ == "__main__":
    unittest.main()

import subprocess
import unittest
from unittest.mock import patch

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.docker.lxc_container_runtime import (
    LxcContainerRuntime,
)


class TestLxcContainerRuntime(unittest.TestCase):
    def test_constructor_rejects_invalid_configuration(self):
        with self.assertRaisesRegex(ValueError, "timeout"):
            LxcContainerRuntime(backend=ManagedLxcBackend.LXD, timeout_seconds=0)
        with self.assertRaisesRegex(ValueError, "node list"):
            LxcContainerRuntime(backend=ManagedLxcBackend.LXD, node_names=())

    def test_find_container_names_uses_node_qualified_refs(self):
        runtime = LxcContainerRuntime(
            backend=ManagedLxcBackend.LXD,
            node_names=("swarm-worker-1",),
        )
        with patch(
            "tiny_swarm_world.infrastructure.process.runner.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout="nexus.1\n"),
        ) as run:
            self.assertEqual(runtime.find_container_names("nexus"), ["swarm-worker-1::nexus.1"])

        self.assertEqual(run.call_args.args[0][:5], ["lxc", "exec", "swarm-worker-1", "--", "docker"])

    def test_file_exists_and_read_file_support_node_qualified_references(self):
        runtime = LxcContainerRuntime(backend=ManagedLxcBackend.INCUS)
        with patch(
            "tiny_swarm_world.infrastructure.process.runner.subprocess.run",
            side_effect=(
                subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                subprocess.CompletedProcess([], 0, stdout="contents", stderr=""),
            ),
        ) as run:
            self.assertTrue(runtime.file_exists("worker-1::app", "/tmp/ready"))
            self.assertEqual(runtime.read_file("worker-1::app", "/tmp/config"), "contents")

        self.assertEqual(run.call_args_list[0].args[0][0:3], ["incus", "exec", "worker-1"])

    def test_checked_docker_operation_rejects_failure_and_timeout(self):
        runtime = LxcContainerRuntime(backend=ManagedLxcBackend.LXD)
        with patch(
            "tiny_swarm_world.infrastructure.process.runner.subprocess.run",
            return_value=subprocess.CompletedProcess([], 17, stdout="", stderr="failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "exit code 17"):
                runtime.read_file("app", "/tmp/config")

        with patch(
            "tiny_swarm_world.infrastructure.process.runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired("lxc", 120),
        ):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                runtime.file_exists("app", "/tmp/ready")

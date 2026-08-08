import subprocess
import unittest
from unittest.mock import patch

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.docker.lxc_container_runtime import (
    LxcContainerRuntime,
)


class TestLxcContainerRuntime(unittest.TestCase):
    def test_find_container_names_uses_node_qualified_refs(self):
        runtime = LxcContainerRuntime(
            backend=ManagedLxcBackend.LXD,
            node_names=("swarm-worker-1",),
        )
        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc.docker."
            "lxc_container_runtime.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout="nexus.1\n"),
        ) as run:
            self.assertEqual(runtime.find_container_names("nexus"), ["swarm-worker-1::nexus.1"])

        self.assertEqual(run.call_args.args[0][:5], ["lxc", "exec", "swarm-worker-1", "--", "docker"])

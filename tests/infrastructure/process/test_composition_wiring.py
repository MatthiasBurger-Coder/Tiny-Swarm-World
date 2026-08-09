import unittest
from unittest.mock import MagicMock, patch

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure import composition


class TestProcessRunnerComposition(unittest.TestCase):
    @patch("tiny_swarm_world.infrastructure.composition._operator_secret_value", return_value="safe")
    @patch("tiny_swarm_world.infrastructure.composition.LxcNexusHttpClient")
    @patch("tiny_swarm_world.infrastructure.composition.LxcContainerImagePublisher")
    @patch("tiny_swarm_world.infrastructure.composition.LxcContainerRuntime")
    @patch("tiny_swarm_world.infrastructure.composition.build_process_runner")
    def test_lxc_artifact_adapters_share_composed_process_runner(
        self,
        build_process_runner,
        container_runtime,
        image_publisher,
        _nexus_client,
        _secret_value,
    ):
        runner = MagicMock(name="process_runner")
        build_process_runner.return_value = runner

        composition.build_lxc_artifact_services(backend=ManagedLxcBackend.LXD)

        self.assertIs(container_runtime.call_args.kwargs["process_runner"], runner)
        self.assertIs(image_publisher.call_args.kwargs["process_runner"], runner)


if __name__ == "__main__":
    unittest.main()

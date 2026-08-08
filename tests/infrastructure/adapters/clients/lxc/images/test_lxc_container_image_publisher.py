import subprocess
import unittest
from unittest.mock import Mock

from tiny_swarm_world.domain.artifacts import ContainerImageContract
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.images.errors import (
    PublicImagePullRejected,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.images.lxc_container_image_publisher import (
    LxcContainerImagePublisher,
)


class TestLxcContainerImagePublisher(unittest.TestCase):
    def test_rate_limited_public_pull_uses_typed_redacted_error(self):
        publisher = LxcContainerImagePublisher(
            backend=ManagedLxcBackend.LXD,
            registry_username="admin",
            registry_password="secret",
        )
        publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess(
                [],
                1,
                stdout="",
                stderr="toomanyrequests: pull rate limit",
            )
        )
        publisher._load_host_cached_image = Mock(return_value=False)

        with self.assertRaises(PublicImagePullRejected) as raised:
            publisher.publish_image(
                ContainerImageContract("redis", "7", "redis", source="pull")
            )

        self.assertEqual(raised.exception.diagnostic, "registry_rate_limited")
        self.assertNotIn("toomanyrequests", str(raised.exception).lower())

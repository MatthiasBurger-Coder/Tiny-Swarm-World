import unittest

from tiny_swarm_world.infrastructure.adapters.clients.lxc.node.models import ObservedNode


class TestObservedNode(unittest.TestCase):
    def test_running_is_case_insensitive(self):
        self.assertTrue(
            ObservedNode(
                name="node",
                status="RUNNING",
                instance_type="container",
                profiles=(),
                config={},
                devices={},
            ).running
        )

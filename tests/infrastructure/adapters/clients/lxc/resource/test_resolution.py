import unittest

from tiny_swarm_world.infrastructure.adapters.clients.lxc.resource.resolution import (
    resource_cpu,
    resource_memory_bytes,
    resources_supported,
)


class TestLxcResourceResolution(unittest.TestCase):
    def test_resource_values_are_bounded_and_typed(self):
        self.assertEqual(4, resource_cpu("4"))
        self.assertEqual(0, resource_cpu("invalid"))
        self.assertEqual(2 * 1024**3, resource_memory_bytes("2GiB"))
        self.assertEqual(0, resource_memory_bytes("invalid"))

    def test_only_supported_resource_keys_and_formats_are_accepted(self):
        self.assertTrue(resources_supported({"cpu": "2", "memory": "2GiB"}))
        self.assertFalse(resources_supported({"unknown": "value"}))

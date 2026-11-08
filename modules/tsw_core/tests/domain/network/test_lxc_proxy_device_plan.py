import unittest

from tiny_swarm_world.domain.network import LxcProxyDevicePlan


class TestLxcProxyDevicePlan(unittest.TestCase):
    def test_describes_manager_proxy_without_host_specific_ips(self):
        plan = LxcProxyDevicePlan(
            service="Jenkins",
            listen_port=8080,
            target_port=8080,
            listen_address="0.0.0.0",
            gateway_node="swarm-manager",
        )

        self.assertEqual(plan.device_name, "tsw-proxy-8080")
        self.assertEqual(plan.listen_endpoint, "tcp:0.0.0.0:8080")
        self.assertEqual(plan.target_endpoint, "tcp:127.0.0.1:8080")
        payload = plan.to_dict()
        self.assertEqual(payload["gateway_node"], "swarm-manager")
        self.assertNotIn("worker", repr(payload).lower())
        self.assertNotIn("container_id", payload)

    def test_supports_local_only_listen_address(self):
        plan = LxcProxyDevicePlan(
            service="Portainer",
            listen_port=9000,
            target_port=9000,
            listen_address="127.0.0.1",
        )

        self.assertEqual(plan.listen_endpoint, "tcp:127.0.0.1:9000")

    def test_rejects_invalid_addresses_ports_and_names(self):
        with self.assertRaises(ValueError):
            LxcProxyDevicePlan(
                service="Jenkins",
                listen_port=8080,
                target_port=8080,
                listen_address="192.0.2.1",
            )

        with self.assertRaises(ValueError):
            LxcProxyDevicePlan(
                service="Jenkins",
                listen_port=0,
                target_port=8080,
            )

        with self.assertRaises(ValueError):
            LxcProxyDevicePlan(
                service="Jenkins",
                listen_port=8080,
                target_port=8080,
                device_name="bad device",
            )

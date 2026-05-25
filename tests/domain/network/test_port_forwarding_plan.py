import unittest

from tiny_swarm_world.domain.network.port_forwarding_plan import (
    ForwardingStrategy,
    PortForwardingPlan,
)


class TestPortForwardingPlan(unittest.TestCase):
    def test_wsl2_socat_plan_describes_ports_without_addresses(self):
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.WSL2_SOCAT,
            service="Portainer",
            listen_port=9000,
            target_port=9000,
            remediation=("Start forwarding only after operator approval.",),
        )

        self.assertTrue(plan.requires_operator_action)
        self.assertFalse(plan.supported_without_operator_action)
        payload = plan.to_dict()
        self.assertEqual("wsl2_socat", payload["strategy"])
        self.assertNotIn("host_ip", payload)
        self.assertNotIn("vm_ip", payload)

    def test_native_linux_direct_plan_is_supported_without_operator_action(self):
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.NATIVE_LINUX_DIRECT,
            service="Nexus",
            listen_port=8081,
            target_port=8081,
            remediation=("Use the published service port.",),
        )

        self.assertFalse(plan.requires_operator_action)
        self.assertTrue(plan.supported_without_operator_action)

    def test_unsupported_plan_is_blocked(self):
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.UNSUPPORTED,
            service="Unknown host",
            listen_port=9000,
            target_port=9000,
            remediation=("Use native Linux or WSL2.",),
        )

        self.assertFalse(plan.requires_operator_action)
        self.assertFalse(plan.supported_without_operator_action)

    def test_rejects_invalid_ports_and_empty_service_names(self):
        with self.assertRaises(ValueError):
            PortForwardingPlan(
                strategy=ForwardingStrategy.WSL2_SOCAT,
                service="Portainer",
                listen_port=0,
                target_port=9000,
                remediation=("Fix the port.",),
            )

        with self.assertRaises(ValueError):
            PortForwardingPlan(
                strategy=ForwardingStrategy.WSL2_SOCAT,
                service=" ",
                listen_port=9000,
                target_port=9000,
                remediation=("Fix the service name.",),
            )

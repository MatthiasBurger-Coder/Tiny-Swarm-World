import unittest

from tiny_swarm_world.domain.network import ContainerNetworkPlan, ContainerNetworkPurpose


class TestContainerNetworkPlan(unittest.TestCase):
    def test_provider_managed_control_network_uses_symbolic_name_only(self):
        plan = ContainerNetworkPlan.provider_managed_control()

        self.assertTrue(plan.safe_for_static_config)
        self.assertEqual("control", plan.name)
        self.assertEqual(ContainerNetworkPurpose.CONTROL, plan.purpose)
        self.assertEqual((), plan.host_addresses)
        self.assertIsNone(plan.host_bridge)
        self.assertFalse(plan.firewall_mutation)

    def test_network_plan_rejects_host_addresses_and_gateways(self):
        plan = ContainerNetworkPlan(
            name="control",
            purpose=ContainerNetworkPurpose.CONTROL,
            host_addresses=("10.0.0.2",),
            host_gateways=("10.0.0.1/24",),
        )

        self.assertFalse(plan.safe_for_static_config)
        self.assertIn("host_address_forbidden", plan.validation_errors())
        self.assertIn("host_specific_value_forbidden", plan.validation_errors())

    def test_network_plan_blocks_host_bridge_firewall_and_ports(self):
        plan = ContainerNetworkPlan(
            name="service",
            purpose=ContainerNetworkPurpose.SERVICE,
            provider_managed=False,
            host_network=True,
            host_bridge="br0",
            firewall_mutation=True,
            published_host_ports=(8080,),
        )

        self.assertIn("network_not_provider_managed", plan.validation_errors())
        self.assertIn("host_network_forbidden", plan.validation_errors())
        self.assertIn("host_bridge_forbidden", plan.validation_errors())
        self.assertIn("firewall_mutation_forbidden", plan.validation_errors())
        self.assertIn("host_port_publication_requires_approval", plan.validation_errors())

    def test_network_plan_rejects_invalid_names_and_ports(self):
        with self.assertRaises(ValueError):
            ContainerNetworkPlan(name="Control Net", purpose=ContainerNetworkPurpose.CONTROL)

        with self.assertRaises(ValueError):
            ContainerNetworkPlan(name="10.0.0.2", purpose=ContainerNetworkPurpose.CONTROL)

        with self.assertRaises(ValueError):
            ContainerNetworkPlan(
                name="published",
                purpose=ContainerNetworkPurpose.PUBLISHED_PORTS,
                published_host_ports=(70000,),
            )


if __name__ == "__main__":
    unittest.main()

import unittest

from tiny_swarm_world.domain.deployment import (
    DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS,
    DEFAULT_SERVICE_STACK_CONTRACTS,
    ServiceStackContract,
)


class TestServiceStackContract(unittest.TestCase):
    def test_default_service_stack_contracts_cover_runnable_profile(self):
        stack_names = tuple(contract.stack_name for contract in DEFAULT_SERVICE_STACK_CONTRACTS)

        self.assertEqual(
            ("portainer", "nexus", "jenkins", "rabbitmq", "sonarqube", "swagger"),
            stack_names,
        )

    def test_default_service_stack_contracts_have_valid_verification_targets(self):
        readiness_targets = {
            contract.service_readiness_target_id for contract in DEFAULT_SERVICE_STACK_CONTRACTS
        }

        self.assertEqual(
            {
                "deployment:portainer-service-readiness",
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:rabbitmq-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
            },
            readiness_targets,
        )

    def test_portainer_managed_stack_contracts_exclude_portainer_bootstrap_cycle(self):
        stack_names = tuple(
            contract.stack_name for contract in DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS
        )

        self.assertEqual(("nexus", "jenkins", "rabbitmq", "sonarqube", "swagger"), stack_names)

    def test_rejects_invalid_stack_name(self):
        with self.assertRaises(ValueError):
            ServiceStackContract("../nexus", ("nexus",))

    def test_rejects_empty_service_list(self):
        with self.assertRaises(ValueError):
            ServiceStackContract("nexus", ())

    def test_rejects_invalid_service_name(self):
        with self.assertRaises(ValueError):
            ServiceStackContract("nexus", ("Nexus Service",))

    def test_serializes_summary_without_runtime_payloads(self):
        contract = ServiceStackContract("nexus", ("nexus",))

        self.assertEqual(
            {
                "required_services": ["nexus"],
                "service_readiness_target_id": "deployment:nexus-service-readiness",
                "stack_target_id": "deployment:nexus-stack",
                "stack_name": "nexus",
            },
            contract.to_dict(),
        )

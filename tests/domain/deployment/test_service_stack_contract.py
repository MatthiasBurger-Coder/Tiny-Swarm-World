import unittest

from tests.support.sonar_safe_literals import ipv4_address

from tiny_swarm_world.domain.deployment import (
    DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS,
    DEFAULT_SERVICE_STACK_CONTRACTS,
    SERVICE_ACCESS_STACK_CONTRACT,
    ServiceEndpoint,
    ServiceStackProfile,
    ServiceStackContract,
    portainer_managed_service_stack_contracts_for_profile,
    service_stack_contracts_for_profile,
)


class TestServiceStackContract(unittest.TestCase):
    def test_default_service_stack_contracts_cover_runnable_profile(self):
        stack_names = tuple(contract.stack_name for contract in DEFAULT_SERVICE_STACK_CONTRACTS)

        self.assertEqual(
            ("portainer", "nexus", "jenkins", "rabbitmq", "sonarqube", "swagger"),
            stack_names,
        )
        self.assertNotIn("service-access", stack_names)

    def test_service_access_profile_adds_selected_stack_contract(self):
        selected = service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        selected_by_name = {contract.stack_name: contract for contract in selected}

        self.assertEqual(
            ("portainer", "nexus", "jenkins", "rabbitmq", "sonarqube", "swagger", "service-access"),
            tuple(contract.stack_name for contract in selected),
        )
        self.assertEqual(SERVICE_ACCESS_STACK_CONTRACT, selected_by_name["service-access"])
        self.assertEqual(
            ("service-access-dashboard", "vaultwarden", "service-access-nginx"),
            selected_by_name["service-access"].required_services,
        )
        self.assertEqual(
            "deployment:service-access-service-readiness",
            selected_by_name["service-access"].service_readiness_target_id,
        )
        self.assertEqual(
            ("http://localhost", "https://localhost"),
            tuple(endpoint.url for endpoint in selected_by_name["service-access"].endpoints),
        )

    def test_service_stack_contracts_publish_localhost_endpoint_defaults(self):
        endpoints_by_stack = {
            contract.stack_name: contract.endpoints
            for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        }

        self.assertEqual(("http://localhost:9000",), _endpoint_urls(endpoints_by_stack["portainer"]))
        self.assertEqual(
            ("http://localhost:8081", "http://localhost:5000"),
            _endpoint_urls(endpoints_by_stack["nexus"]),
        )
        self.assertEqual(("http://localhost:8080",), _endpoint_urls(endpoints_by_stack["jenkins"]))
        self.assertEqual(
            ("http://localhost:15672",),
            _endpoint_urls(endpoints_by_stack["rabbitmq"]),
        )
        self.assertEqual(
            ("http://localhost:9001",),
            _endpoint_urls(endpoints_by_stack["sonarqube"]),
        )
        self.assertEqual(("http://localhost:8084",), _endpoint_urls(endpoints_by_stack["swagger"]))
        self.assertEqual(
            ("http://localhost", "https://localhost"),
            _endpoint_urls(endpoints_by_stack["service-access"]),
        )
        all_endpoints = tuple(
            endpoint
            for endpoints in endpoints_by_stack.values()
            for endpoint in endpoints
        )
        self.assertTrue(all(endpoint.localhost_forwarding_required for endpoint in all_endpoints))
        self.assertFalse(any(endpoint.readiness_claimed for endpoint in all_endpoints))

    def test_endpoint_configuration_is_not_a_readiness_claim(self):
        endpoint = ServiceEndpoint("portainer", "http://localhost:9000")

        self.assertTrue(endpoint.localhost_forwarding_required)
        self.assertFalse(endpoint.readiness_claimed)
        self.assertEqual(
            {
                "localhost_forwarding_required": True,
                "name": "portainer",
                "readiness_claimed": False,
                "url": "http://localhost:9000",
            },
            endpoint.to_dict(),
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

    def test_selected_portainer_managed_stack_contracts_include_service_access(self):
        stack_names = tuple(
            contract.stack_name
            for contract in portainer_managed_service_stack_contracts_for_profile(
                ServiceStackProfile.SERVICE_ACCESS
            )
        )

        self.assertEqual(
            ("nexus", "jenkins", "rabbitmq", "sonarqube", "swagger", "service-access"),
            stack_names,
        )
        self.assertNotIn("portainer", stack_names)

    def test_rejects_invalid_stack_name(self):
        with self.assertRaises(ValueError):
            ServiceStackContract("../nexus", ("nexus",))

    def test_rejects_empty_service_list(self):
        with self.assertRaises(ValueError):
            ServiceStackContract("nexus", ())

    def test_rejects_invalid_service_name(self):
        with self.assertRaises(ValueError):
            ServiceStackContract("nexus", ("Nexus Service",))

    def test_rejects_host_specific_endpoint_url(self):
        with self.assertRaises(ValueError):
            ServiceEndpoint("service", f"http://{ipv4_address(10, 157, 2, 182)}:8080")

    def test_accepts_localhost_https_endpoint_url(self):
        endpoint = ServiceEndpoint("vaultwarden", "https://localhost")

        self.assertEqual("https://localhost", endpoint.url)

    def test_rejects_endpoint_with_credentials_or_query(self):
        with self.assertRaises(ValueError):
            ServiceEndpoint("service", "http://user@localhost:8080")

        with self.assertRaises(ValueError):
            ServiceEndpoint("service", "http://localhost:8080/?token=secret")

    def test_rejects_endpoint_readiness_claims(self):
        with self.assertRaises(ValueError):
            ServiceEndpoint("service", "http://localhost:8080", readiness_claimed=True)

    def test_serializes_summary_without_runtime_payloads(self):
        contract = ServiceStackContract("nexus", ("nexus",))

        self.assertEqual(
            {
                "endpoints": [],
                "required_services": ["nexus"],
                "service_readiness_target_id": "deployment:nexus-service-readiness",
                "stack_target_id": "deployment:nexus-stack",
                "stack_name": "nexus",
            },
            contract.to_dict(),
        )


def _endpoint_urls(endpoints: tuple[ServiceEndpoint, ...]) -> tuple[str, ...]:
    return tuple(endpoint.url for endpoint in endpoints)

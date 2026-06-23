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
            ("portainer", "traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger"),
            stack_names,
        )
        self.assertNotIn("service-access", stack_names)

    def test_service_access_profile_adds_selected_stack_contract(self):
        selected = service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        selected_by_name = {contract.stack_name: contract for contract in selected}

        self.assertEqual(
            (
                "portainer",
                "traefik",
                "nexus",
                "jenkins",
                "pulsar",
                "sonarqube",
                "swagger",
                "infisical",
                "service-access",
            ),
            tuple(contract.stack_name for contract in selected),
        )
        self.assertEqual(SERVICE_ACCESS_STACK_CONTRACT, selected_by_name["service-access"])
        self.assertEqual(
            ("service-access-dashboard", "service-access-nginx"),
            selected_by_name["service-access"].required_services,
        )
        self.assertEqual(
            ("infisical", "infisical-db", "infisical-redis"),
            selected_by_name["infisical"].required_services,
        )
        self.assertEqual(
            ("pulsar", "pulsar-manager"),
            selected_by_name["pulsar"].required_services,
        )
        self.assertEqual(
            "deployment:service-access-service-readiness",
            selected_by_name["service-access"].service_readiness_target_id,
        )
        self.assertEqual(
            ("http://localhost:10000",),
            tuple(endpoint.url for endpoint in selected_by_name["service-access"].endpoints),
        )
        self.assertEqual(
            ("http://localhost:17080",),
            tuple(endpoint.url for endpoint in selected_by_name["infisical"].endpoints),
        )

    def test_contracts_expose_phase_and_port_ids_without_readiness_claims(self):
        nexus = _contract_by_stack("nexus")

        self.assertEqual("artifacts", nexus.phase_id)
        self.assertEqual(
            ("nexus-http", "nexus-docker-http", "nexus-docker-https"),
            nexus.port_ids,
        )
        self.assertEqual("deployment:nexus-service-readiness", nexus.service_readiness_target_id)
        self.assertNotEqual(nexus.stack_target_id, nexus.service_readiness_target_id)
        self.assertFalse(any(endpoint.readiness_claimed for endpoint in nexus.endpoints))

    def test_service_stack_contracts_publish_localhost_endpoint_defaults(self):
        endpoints_by_stack = {
            contract.stack_name: contract.endpoints
            for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        }

        self.assertEqual(("http://localhost:10001",), _endpoint_urls(endpoints_by_stack["portainer"]))
        self.assertEqual(("https://localhost",), _endpoint_urls(endpoints_by_stack["traefik"]))
        self.assertEqual(
            ("http://localhost:13081", "http://localhost:13500"),
            _endpoint_urls(endpoints_by_stack["nexus"]),
        )
        self.assertEqual(("http://localhost:11080",), _endpoint_urls(endpoints_by_stack["jenkins"]))
        self.assertEqual(
            ("http://localhost:14080", "http://localhost:14081"),
            _endpoint_urls(endpoints_by_stack["pulsar"]),
        )
        self.assertEqual(
            ("http://localhost:12000",),
            _endpoint_urls(endpoints_by_stack["sonarqube"]),
        )
        self.assertEqual(("http://localhost:16081",), _endpoint_urls(endpoints_by_stack["swagger"]))
        self.assertEqual(
            ("http://localhost:10000",),
            _endpoint_urls(endpoints_by_stack["service-access"]),
        )
        self.assertEqual(("http://localhost:17080",), _endpoint_urls(endpoints_by_stack["infisical"]))
        all_endpoints = tuple(
            endpoint
            for endpoints in endpoints_by_stack.values()
            for endpoint in endpoints
        )
        self.assertTrue(all(endpoint.localhost_forwarding_required for endpoint in all_endpoints))
        self.assertFalse(any(endpoint.readiness_claimed for endpoint in all_endpoints))

    def test_endpoint_configuration_is_not_a_readiness_claim(self):
        endpoint = ServiceEndpoint("portainer", "http://localhost:10001")

        self.assertTrue(endpoint.localhost_forwarding_required)
        self.assertFalse(endpoint.readiness_claimed)
        self.assertEqual(
            {
                "localhost_forwarding_required": True,
                "name": "portainer",
                "readiness_claimed": False,
                "url": "http://localhost:10001",
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
                "deployment:traefik-service-readiness",
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:pulsar-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
            },
            readiness_targets,
        )

    def test_portainer_managed_stack_contracts_exclude_portainer_bootstrap_cycle(self):
        stack_names = tuple(
            contract.stack_name for contract in DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS
        )

        self.assertEqual(("traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger"), stack_names)

    def test_selected_portainer_managed_stack_contracts_include_service_access(self):
        stack_names = tuple(
            contract.stack_name
            for contract in portainer_managed_service_stack_contracts_for_profile(
                ServiceStackProfile.SERVICE_ACCESS
            )
        )

        self.assertEqual(
            (
                "traefik",
                "nexus",
                "jenkins",
                "pulsar",
                "sonarqube",
                "swagger",
                "infisical",
                "service-access",
            ),
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

    def test_rejects_invalid_phase_or_port_ids(self):
        with self.assertRaises(ValueError):
            ServiceStackContract("nexus", ("nexus",), phase_id="../artifacts")

        with self.assertRaises(ValueError):
            ServiceStackContract("nexus", ("nexus",), port_ids=("Nexus HTTP",))

    def test_rejects_host_specific_endpoint_url(self):
        with self.assertRaises(ValueError):
            ServiceEndpoint("service", f"http://{ipv4_address(10, 157, 2, 182)}:8080")

    def test_accepts_localhost_https_endpoint_url(self):
        endpoint = ServiceEndpoint("infisical", "http://localhost:17080")

        self.assertEqual("http://localhost:17080", endpoint.url)

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
                "phase_id": None,
                "port_ids": [],
                "required_services": ["nexus"],
                "service_readiness_target_id": "deployment:nexus-service-readiness",
                "stack_target_id": "deployment:nexus-stack",
                "stack_name": "nexus",
            },
            contract.to_dict(),
        )


def _endpoint_urls(endpoints: tuple[ServiceEndpoint, ...]) -> tuple[str, ...]:
    return tuple(endpoint.url for endpoint in endpoints)


def _contract_by_stack(stack_name: str) -> ServiceStackContract:
    return next(
        contract
        for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        if contract.stack_name == stack_name
    )

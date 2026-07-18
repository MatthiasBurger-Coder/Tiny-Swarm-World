import unittest

from tests.support.sonar_safe_literals import ipv4_address, sample_http_url

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
            stack_names,
            ("portainer", "traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger"),
        )
        self.assertNotIn("service-access", stack_names)

    def test_service_access_profile_adds_selected_stack_contract(self):
        selected = service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        selected_by_name = {contract.stack_name: contract for contract in selected}

        self.assertEqual(
            tuple(contract.stack_name for contract in selected),
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
        )
        self.assertEqual(SERVICE_ACCESS_STACK_CONTRACT, selected_by_name["service-access"])
        self.assertEqual(
            selected_by_name["service-access"].required_services,
            ("service-access-dashboard", "service-access-nginx"),
        )
        self.assertEqual(
            selected_by_name["infisical"].required_services,
            ("infisical", "infisical-db", "infisical-redis"),
        )
        self.assertEqual(
            selected_by_name["pulsar"].required_services,
            ("pulsar", "pulsar-manager"),
        )
        self.assertEqual(
            selected_by_name["service-access"].service_readiness_target_id,
            "deployment:service-access-service-readiness",
        )
        self.assertEqual(
            tuple(endpoint.url for endpoint in selected_by_name["service-access"].endpoints),
            ("http://localhost:10000",),
        )
        self.assertEqual(
            tuple(endpoint.url for endpoint in selected_by_name["infisical"].endpoints),
            ("http://localhost:17080",),
        )

    def test_contracts_expose_phase_and_port_ids_without_readiness_claims(self):
        nexus = _contract_by_stack("nexus")

        self.assertEqual(nexus.phase_id, "artifacts")
        self.assertEqual(
            nexus.port_ids,
            ("nexus-http", "nexus-docker-http", "nexus-docker-https"),
        )
        self.assertEqual(nexus.service_readiness_target_id, "deployment:nexus-service-readiness")
        self.assertNotEqual(nexus.stack_target_id, nexus.service_readiness_target_id)
        self.assertFalse(any(endpoint.readiness_claimed for endpoint in nexus.endpoints))

    def test_service_stack_contracts_publish_localhost_endpoint_defaults(self):
        endpoints_by_stack = {
            contract.stack_name: contract.endpoints
            for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        }

        self.assertEqual(_endpoint_urls(endpoints_by_stack["portainer"]), ("http://localhost:10001",))
        self.assertEqual(_endpoint_urls(endpoints_by_stack["traefik"]), ("http://localhost",))
        self.assertEqual(
            _endpoint_urls(endpoints_by_stack["nexus"]),
            ("http://localhost:13081", "http://localhost:13500"),
        )
        self.assertEqual(_endpoint_urls(endpoints_by_stack["jenkins"]), ("http://localhost:11080",))
        self.assertEqual(
            _endpoint_urls(endpoints_by_stack["pulsar"]),
            ("http://localhost:14080", "http://localhost:14081"),
        )
        self.assertEqual(
            _endpoint_urls(endpoints_by_stack["sonarqube"]),
            ("http://localhost:12000",),
        )
        self.assertEqual(_endpoint_urls(endpoints_by_stack["swagger"]), ("http://localhost:16081",))
        self.assertEqual(
            _endpoint_urls(endpoints_by_stack["service-access"]),
            ("http://localhost:10000",),
        )
        self.assertEqual(_endpoint_urls(endpoints_by_stack["infisical"]), ("http://localhost:17080",))
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
            endpoint.to_dict(),
            {
                "localhost_forwarding_required": True,
                "name": "portainer",
                "readiness_claimed": False,
                "url": "http://localhost:10001",
            },
        )

    def test_default_service_stack_contracts_have_valid_verification_targets(self):
        readiness_targets = {
            contract.service_readiness_target_id for contract in DEFAULT_SERVICE_STACK_CONTRACTS
        }

        self.assertEqual(
            readiness_targets,
            {
                "deployment:portainer-service-readiness",
                "deployment:traefik-service-readiness",
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:pulsar-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
            },
        )

    def test_portainer_managed_stack_contracts_exclude_portainer_bootstrap_cycle(self):
        stack_names = tuple(
            contract.stack_name for contract in DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS
        )

        self.assertEqual(stack_names, ("traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger"))

    def test_selected_portainer_managed_stack_contracts_include_service_access(self):
        stack_names = tuple(
            contract.stack_name
            for contract in portainer_managed_service_stack_contracts_for_profile(
                ServiceStackProfile.SERVICE_ACCESS
            )
        )

        self.assertEqual(
            stack_names,
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
            ServiceEndpoint("service", sample_http_url(ipv4_address(10, 157, 2, 182), 8080))

    def test_accepts_localhost_https_endpoint_url(self):
        endpoint = ServiceEndpoint("infisical", "http://localhost:17080")

        self.assertEqual(endpoint.url, "http://localhost:17080")

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
            contract.to_dict(),
            {
                "endpoints": [],
                "phase_id": None,
                "port_ids": [],
                "required_services": ["nexus"],
                "service_readiness_target_id": "deployment:nexus-service-readiness",
                "stack_target_id": "deployment:nexus-stack",
                "stack_name": "nexus",
            },
        )


def _endpoint_urls(endpoints: tuple[ServiceEndpoint, ...]) -> tuple[str, ...]:
    return tuple(endpoint.url for endpoint in endpoints)


def _contract_by_stack(stack_name: str) -> ServiceStackContract:
    return next(
        contract
        for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        if contract.stack_name == stack_name
    )

import unittest
from typing import Any, cast

from ruamel.yaml import YAML

from tiny_swarm_world.application.services.deployment.write_effective_access_model_evidence import (
    build_effective_access_model_evidence,
)
from tiny_swarm_world.domain.network import PortExposureClass, PortRegistry, ServicePortMapping
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml,
)
from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_route_contract,
    traefik_labels,
    route_expectation,
)


class TestInfisicalRouting(unittest.TestCase):
    def test_infisical_route_uses_internal_http_target(self) -> None:
        assert_route_contract(self, "infisical")

    def test_infisical_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "infisical")

    def test_infisical_route_uses_preferred_host_without_localhost_fallback(self) -> None:
        labels = traefik_labels(route_expectation("infisical"))

        self.assertIn(
            "traefik.http.routers.infisical.rule=Host(`infisical.tsw.local`)",
            labels,
        )
        self.assertNotIn("Host(`localhost`)", repr(labels))

    def test_infisical_registry_mapping_feeds_compose_urls_health_and_evidence(self) -> None:
        repository = ComposeFileRepositoryYaml(
            port_registry=PortRegistry(
                ranges=(),
                mappings=(
                    ServicePortMapping(
                        service_id="infisical",
                        port_id="infisical-http",
                        internal_port=8080,
                        external_port=27080,
                        exposure=PortExposureClass.DIAGNOSTIC,
                        route_host="infisical.tsw.local",
                        metadata={
                            "route_enabled_by_default": "true",
                            "upstream_service": "infisical",
                        },
                    ),
                ),
            )
        )
        compose = cast(
            dict[str, Any],
            YAML(typ="safe").load(
                repository.get_compose_of("infisical").compose_content
            ),
        )
        model = repository.get_effective_access_model()
        evidence = cast(
            dict[str, Any],
            build_effective_access_model_evidence(
                model,
                service_profile="service-access",
                generated_at="2026-08-11T00:00:00Z",
            ).to_dict(),
        )

        infisical_port = compose["services"]["infisical"]["ports"][0]
        self.assertEqual(infisical_port["published"], 27080)
        self.assertEqual(infisical_port["target"], 8080)
        route = next(
            route for route in evidence["routes"] if route["service_name"] == "infisical"
        )
        self.assertEqual(route["service_access_url"], "https://infisical.tsw.local")
        self.assertEqual(route["health_check_url"], "https://infisical.tsw.local")
        self.assertEqual(route["upstream_port"], 8080)
        fallback = next(
            fallback
            for fallback in evidence["diagnostic_fallback_ports"]
            if fallback["port_id"] == "infisical-http"
        )
        self.assertEqual(fallback["port"], 27080)


if __name__ == "__main__":
    unittest.main()

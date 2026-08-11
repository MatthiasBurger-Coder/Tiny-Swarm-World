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
)


class TestSonarQubeRouting(unittest.TestCase):
    def test_sonarqube_route_uses_internal_ui_target(self) -> None:
        assert_route_contract(self, "sonarqube")

    def test_sonarqube_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "sonarqube")

    def test_sonarqube_registry_mapping_feeds_compose_urls_health_and_evidence(self) -> None:
        repository = ComposeFileRepositoryYaml(
            port_registry=PortRegistry(
                ranges=(),
                mappings=(
                    ServicePortMapping(
                        service_id="sonarqube",
                        port_id="sonarqube-http",
                        internal_port=9000,
                        external_port=23000,
                        exposure=PortExposureClass.DIAGNOSTIC,
                        route_host="sonarqube.tsw.local",
                        metadata={
                            "route_enabled_by_default": "true",
                            "upstream_service": "sonarqube",
                        },
                    ),
                ),
            )
        )
        compose = cast(
            dict[str, Any],
            YAML(typ="safe").load(
                repository.get_compose_of("sonarqube").compose_content
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

        sonarqube_port = compose["services"]["sonarqube"]["ports"][0]
        self.assertEqual(sonarqube_port["published"], 23000)
        self.assertEqual(sonarqube_port["target"], 9000)
        route = next(
            route for route in evidence["routes"] if route["service_name"] == "sonarqube"
        )
        self.assertEqual(route["service_access_url"], "https://sonarqube.tsw.local")
        self.assertEqual(route["health_check_url"], "https://sonarqube.tsw.local")
        self.assertEqual(route["upstream_port"], 9000)
        fallback = next(
            fallback
            for fallback in evidence["diagnostic_fallback_ports"]
            if fallback["port_id"] == "sonarqube-http"
        )
        self.assertEqual(fallback["port"], 23000)


if __name__ == "__main__":
    unittest.main()

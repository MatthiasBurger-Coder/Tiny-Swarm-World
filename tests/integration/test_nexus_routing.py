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


class TestNexusRouting(unittest.TestCase):
    def test_nexus_route_uses_internal_ui_target(self) -> None:
        assert_route_contract(self, "nexus")

    def test_nexus_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "nexus")

    def test_nexus_registry_mapping_feeds_compose_urls_health_and_evidence(self) -> None:
        repository = ComposeFileRepositoryYaml(
            port_registry=PortRegistry(
                ranges=(),
                mappings=(
                    ServicePortMapping(
                        service_id="nexus",
                        port_id="nexus-http",
                        internal_port=8081,
                        external_port=23081,
                        exposure=PortExposureClass.DIAGNOSTIC,
                        route_host="nexus.tsw.local",
                        metadata={
                            "route_enabled_by_default": "true",
                            "upstream_service": "nexus",
                        },
                    ),
                    ServicePortMapping(
                        service_id="nexus",
                        port_id="nexus-docker-http",
                        internal_port=5000,
                        external_port=None,
                        exposure=PortExposureClass.DIAGNOSTIC,
                    ),
                    ServicePortMapping(
                        service_id="nexus",
                        port_id="nexus-docker-https",
                        internal_port=5001,
                        external_port=None,
                        exposure=PortExposureClass.DIAGNOSTIC,
                    ),
                ),
            )
        )
        compose = cast(
            dict[str, Any],
            YAML(typ="safe").load(repository.get_compose_of("nexus").compose_content),
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

        nexus_ports = compose["services"]["nexus"]["ports"]
        self.assertEqual(nexus_ports[0]["published"], 23081)
        self.assertEqual(nexus_ports[0]["target"], 8081)
        route = next(route for route in evidence["routes"] if route["service_name"] == "nexus")
        self.assertEqual(route["service_access_url"], "https://nexus.tsw.local")
        self.assertEqual(route["health_check_url"], "https://nexus.tsw.local")
        self.assertEqual(route["upstream_port"], 8081)
        fallback = next(
            fallback
            for fallback in evidence["diagnostic_fallback_ports"]
            if fallback["port_id"] == "nexus-http"
        )
        self.assertEqual(fallback["port"], 23081)


if __name__ == "__main__":
    unittest.main()

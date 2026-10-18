import unittest
from dataclasses import replace

from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.ingress import (
    DesiredHttpsIngress,
    DesiredHttpsRoute,
    desired_https_ingress_for_profile,
)
from tiny_swarm_world.domain.network import PortExposureClass, PortRegistry, ServicePortMapping
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)


class TestDesiredHttpsIngress(unittest.TestCase):
    def test_service_access_profile_routes_required_https_hosts(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            port_registry=_committed_port_registry(),
        )

        self.assertEqual(desired.public_ports, (80, 443))
        self.assertTrue(desired.http_redirect_to_https)
        self.assertFalse(desired.exposed_by_default)
        self.assertFalse(desired.api_insecure)
        self.assertEqual(
            desired.hostnames,
            (
                "portainer.tsw.local",
                "nexus.tsw.local",
                "jenkins.tsw.local",
                "pulsar-api.tsw.local",
                "pulsar.tsw.local",
                "sonarqube.tsw.local",
                "swagger.tsw.local",
                "infisical.tsw.local",
                "service-access.tsw.local",
            ),
        )
        self.assertNotIn("grafana.tsw.local", desired.hostnames)

    def test_minimal_selection_omits_unselected_routes_health_links_and_ports(self):
        desired = desired_https_ingress_for_profile(
            port_registry=_committed_port_registry(),
            resolved_services=("incus", "portainer"),
            conditional_service_names=("api", "app", "grafana", "prometheus"),
        )

        self.assertEqual(desired.hostnames, ())
        self.assertEqual(desired.public_ports, ())
        self.assertFalse(desired.gateway_enabled)
        self.assertFalse(desired.http_redirect_to_https)
        self.assertEqual(desired.direct_endpoints[0].service_access_url, "http://localhost:10001")
        payload = desired.to_dict()
        self.assertEqual([link["service"] for link in payload["service_access_links"]], ["portainer"])
        self.assertEqual([target["service"] for target in payload["health_check_targets"]], ["portainer"])
        self.assertEqual({port.service_name for port in desired.diagnostic_fallback_ports}, {"portainer"})
        self.assertEqual(desired.skipped_routes, ())

    def test_swagger_and_sonarqube_selection_uses_stack_ids(self):
        desired = desired_https_ingress_for_profile(
            port_registry=_committed_port_registry(),
            resolved_services=("incus", "portainer", "swagger", "sonarqube"),
        )

        self.assertEqual(desired.hostnames, ())
        self.assertEqual(
            {endpoint.service_access_url for endpoint in desired.direct_endpoints},
            {"http://localhost:10001", "http://localhost:12000", "http://localhost:16081"},
        )
        self.assertEqual(
            {port.service_name for port in desired.diagnostic_fallback_ports},
            {"portainer", "swagger", "sonarqube"},
        )
        self.assertEqual(desired.skipped_routes, ())

    def test_selected_conditional_route_remains_available(self):
        desired = desired_https_ingress_for_profile(
            port_registry=_committed_port_registry(),
            resolved_services=("portainer", "traefik", "grafana"),
            conditional_service_names=("grafana", "prometheus"),
        )
        self.assertEqual(desired.hostnames, ("portainer.tsw.local", "grafana.tsw.local"))

    def test_direct_selection_honors_registry_port_overrides(self):
        registry = _committed_port_registry()
        registry = replace(registry, mappings=tuple(
            replace(mapping, external_port=10002) if mapping.port_id == "portainer-http" else mapping
            for mapping in registry.mappings
        ))
        desired = desired_https_ingress_for_profile(
            resolved_services=("incus", "portainer"), port_registry=registry,
        )
        self.assertEqual(desired.direct_endpoints[0].service_access_url, "http://localhost:10002")

    def test_direct_endpoint_rejects_unsafe_urls_and_gateway_conflicts(self):
        from tiny_swarm_world.domain.ingress.desired_state import DirectServiceEndpoint

        endpoint = DirectServiceEndpoint("portainer", "http://localhost:10001", "http://localhost:10001", "portainer", 9000)
        for url in ("https://localhost:10001", "http://example.org:10001", "http://user@localhost:10001", "http://localhost:0", "http://localhost:10001?secret=value"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                replace(endpoint, service_access_url=url)
        with self.assertRaises(ValueError):
            DesiredHttpsIngress(routes=(), gateway_enabled=False, direct_endpoints=(endpoint,))
        with self.assertRaises(ValueError):
            DesiredHttpsIngress(routes=())

    def test_conditional_grafana_route_is_explicit(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            conditional_service_names=("grafana",),
            port_registry=_committed_port_registry(),
        )

        self.assertIn("grafana.tsw.local", desired.hostnames)
        grafana_route = next(
            route for route in desired.routes if route.service_name == "grafana"
        )
        self.assertEqual(grafana_route.upstream_service, "grafana")
        self.assertEqual(grafana_route.upstream_port, 3000)

    def test_conditional_route_candidates_cover_observability_app_and_api(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            conditional_service_names=("api", "app", "grafana", "prometheus"),
            port_registry=_committed_port_registry(),
        )
        routes = {route.service_name: route for route in desired.routes}

        self.assertEqual(routes["api"].hostname, "api.tsw.local")
        self.assertEqual(routes["api"].upstream_service, "tiny-swarm")
        self.assertEqual(routes["api"].upstream_port, 8081)
        self.assertEqual(routes["app"].hostname, "app.tsw.local")
        self.assertEqual(routes["app"].upstream_service, "tiny-swarm")
        self.assertEqual(routes["app"].upstream_port, 8080)
        self.assertEqual(routes["prometheus"].hostname, "prometheus.tsw.local")
        self.assertEqual(routes["prometheus"].upstream_service, "prometheus")
        self.assertEqual(routes["prometheus"].upstream_port, 9090)
        self.assertFalse(
            {"api", "app", "grafana", "prometheus"}
            & {skipped.service_name for skipped in desired.skipped_routes}
        )

    def test_default_profile_reports_default_enabled_routes_outside_profile(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.DEFAULT,
            port_registry=_committed_port_registry(),
        )

        self.assertLessEqual(
            {
                ("infisical", "service_not_in_active_profile"),
                ("service-access", "service_not_in_active_profile"),
            },
            {
                (skipped.service_name, skipped.reason)
                for skipped in desired.skipped_routes
            },
        )

    def test_effective_access_model_exports_links_health_fallbacks_and_skips(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            port_registry=_committed_port_registry(),
        )
        evidence = desired.to_dict()

        self.assertEqual(evidence["gateway_public_ingress_ports"], [80, 443])
        self.assertIn(
            {
                "classification": "diagnostic",
                "port": 10080,
                "port_id": "api-gateway-http",
                "service": "api-gateway",
            },
            evidence["diagnostic_fallback_ports"],
        )
        jenkins_link = next(
            link
            for link in evidence["service_access_links"]
            if link["service"] == "jenkins"
        )
        self.assertEqual(jenkins_link["url"], "https://jenkins.tsw.local")
        self.assertEqual(
            jenkins_link["credential"],
            {
                "item_reference": "platform/jenkins",
                "note": "Open Infisical item",
                "username_label": "admin",
            },
        )
        self.assertIn(
            {
                "service": "pulsar-admin-api",
                "target": "https://pulsar-api.tsw.local/admin/v2/clusters",
                "upstream_port": 8080,
                "upstream_service": "pulsar",
            },
            evidence["health_check_targets"],
        )
        self.assertIn(
            {"reason": "service_not_enabled", "service": "prometheus"},
            evidence["skipped_routes"],
        )

    def test_unsupported_route_metadata_is_reported_without_route_generation(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            port_registry=PortRegistry(
                ranges=_committed_port_registry().ranges,
                mappings=_committed_port_registry().mappings,
                metadata={"unsupported_routes": "legacy-broker"},
            ),
        )

        self.assertIn(
            {"reason": "service_not_supported", "service": "legacy-broker"},
            desired.to_dict()["skipped_routes"],
        )

    def test_route_hosts_and_diagnostic_fallbacks_can_come_from_port_registry(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            port_registry=_committed_port_registry(),
        )
        routes = {route.service_name: route for route in desired.routes}

        self.assertEqual(routes["jenkins"].hostname, "jenkins.tsw.local")
        self.assertEqual(routes["jenkins"].upstream_port, 8080)
        self.assertIn(
            {
                "classification": "diagnostic",
                "port": 10080,
                "port_id": "api-gateway-http",
                "service": "api-gateway",
            },
            [fallback.to_dict() for fallback in desired.diagnostic_fallback_ports],
        )

    def test_rejects_forbidden_ingress_policy(self):
        route = DesiredHttpsRoute(
            service_name="jenkins",
            hostname="jenkins.tsw.local",
            upstream_service="jenkins",
            upstream_port=8080,
        )

        for kwargs in (
            {"public_ports": (10080, 10443)},
            {"http_redirect_to_https": False},
            {"exposed_by_default": True},
            {"api_insecure": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    DesiredHttpsIngress(routes=(route,), **kwargs)

    def test_routes_use_internal_service_targets(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            port_registry=_committed_port_registry(),
        )
        routes = {route.service_name: route for route in desired.routes}

        self.assertEqual(routes["service-access"].upstream_service, "service-access-dashboard")
        self.assertEqual(routes["service-access"].upstream_port, 80)
        self.assertEqual(routes["pulsar-admin-api"].upstream_service, "pulsar")
        self.assertEqual(routes["pulsar-admin-api"].upstream_port, 8080)
        self.assertEqual(routes["pulsar-manager"].upstream_service, "pulsar-manager")
        self.assertEqual(routes["pulsar-manager"].upstream_port, 9527)
        self.assertEqual(routes["swagger"].upstream_service, "swagger-nginx")
        self.assertEqual(routes["swagger"].upstream_port, 8084)

    def test_route_rejects_local_topology_and_invalid_hostnames(self):
        with self.assertRaises(ValueError):
            DesiredHttpsRoute(
                service_name="jenkins",
                hostname="jenkins.127.0.0.1",
                upstream_service="jenkins",
                upstream_port=8080,
            )

        with self.assertRaises(ValueError):
            DesiredHttpsRoute(
                service_name="jenkins",
                hostname="Jenkins.tsw.local",
                upstream_service="jenkins",
                upstream_port=8080,
            )


def _sample_port_registry() -> PortRegistry:
    return PortRegistry(
        ranges=(),
        mappings=(
            ServicePortMapping(
                service_id="api-gateway",
                port_id="api-gateway-http",
                internal_port=80,
                external_port=10080,
                exposure=PortExposureClass.DIAGNOSTIC,
                route_host="gateway.tsw.local",
            ),
            ServicePortMapping(
                service_id="jenkins",
                port_id="jenkins-http",
                internal_port=8080,
                external_port=11080,
                exposure=PortExposureClass.DIAGNOSTIC,
                route_host="jenkins.tsw.local",
            ),
        ),
    )


def _committed_port_registry() -> PortRegistry:
    return PortRegistryYamlRepository().load()


if __name__ == "__main__":
    unittest.main()

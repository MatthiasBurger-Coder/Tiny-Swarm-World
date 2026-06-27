import unittest

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

        self.assertEqual((80, 443), desired.public_ports)
        self.assertTrue(desired.http_redirect_to_https)
        self.assertFalse(desired.exposed_by_default)
        self.assertFalse(desired.api_insecure)
        self.assertEqual(
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
            desired.hostnames,
        )
        self.assertNotIn("grafana.tsw.local", desired.hostnames)

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
        self.assertEqual("grafana", grafana_route.upstream_service)
        self.assertEqual(3000, grafana_route.upstream_port)

    def test_conditional_route_candidates_cover_observability_app_and_api(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            conditional_service_names=("api", "app", "grafana", "prometheus"),
            port_registry=_committed_port_registry(),
        )
        routes = {route.service_name: route for route in desired.routes}

        self.assertEqual("api.tsw.local", routes["api"].hostname)
        self.assertEqual("tiny-swarm", routes["api"].upstream_service)
        self.assertEqual(8081, routes["api"].upstream_port)
        self.assertEqual("app.tsw.local", routes["app"].hostname)
        self.assertEqual("tiny-swarm", routes["app"].upstream_service)
        self.assertEqual(8080, routes["app"].upstream_port)
        self.assertEqual("prometheus.tsw.local", routes["prometheus"].hostname)
        self.assertEqual("prometheus", routes["prometheus"].upstream_service)
        self.assertEqual(9090, routes["prometheus"].upstream_port)

    def test_effective_access_model_exports_links_health_fallbacks_and_skips(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            port_registry=_committed_port_registry(),
        )
        evidence = desired.to_dict()

        self.assertEqual([80, 443], evidence["gateway_public_ingress_ports"])
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
        self.assertEqual("https://jenkins.tsw.local", jenkins_link["url"])
        self.assertEqual(
            {
                "item_reference": "platform/jenkins",
                "note": "Open Infisical item",
                "username_label": "admin",
            },
            jenkins_link["credential"],
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

        self.assertEqual("jenkins.tsw.local", routes["jenkins"].hostname)
        self.assertEqual(8080, routes["jenkins"].upstream_port)
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

        self.assertEqual("service-access-dashboard", routes["service-access"].upstream_service)
        self.assertEqual(80, routes["service-access"].upstream_port)
        self.assertEqual("pulsar", routes["pulsar-admin-api"].upstream_service)
        self.assertEqual(8080, routes["pulsar-admin-api"].upstream_port)
        self.assertEqual("pulsar-manager", routes["pulsar-manager"].upstream_service)
        self.assertEqual(9527, routes["pulsar-manager"].upstream_port)
        self.assertEqual("swagger-nginx", routes["swagger"].upstream_service)
        self.assertEqual(8084, routes["swagger"].upstream_port)

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

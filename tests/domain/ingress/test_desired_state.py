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

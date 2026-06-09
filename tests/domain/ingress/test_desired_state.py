import unittest

from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.ingress import (
    DesiredHttpsIngress,
    DesiredHttpsRoute,
    desired_https_ingress_for_profile,
)


class TestDesiredHttpsIngress(unittest.TestCase):
    def test_service_access_profile_routes_required_https_hosts(self):
        desired = desired_https_ingress_for_profile(ServiceStackProfile.SERVICE_ACCESS)

        self.assertEqual((80, 443), desired.public_ports)
        self.assertTrue(desired.http_redirect_to_https)
        self.assertFalse(desired.exposed_by_default)
        self.assertFalse(desired.api_insecure)
        self.assertEqual(
            (
                "portainer.tsw.local",
                "nexus.tsw.local",
                "jenkins.tsw.local",
                "sonarqube.tsw.local",
                "infisical.tsw.local",
            ),
            desired.hostnames,
        )
        self.assertNotIn("grafana.tsw.local", desired.hostnames)

    def test_conditional_grafana_route_is_explicit(self):
        desired = desired_https_ingress_for_profile(
            ServiceStackProfile.SERVICE_ACCESS,
            conditional_service_names=("grafana",),
        )

        self.assertIn("grafana.tsw.local", desired.hostnames)
        grafana_route = next(
            route for route in desired.routes if route.service_name == "grafana"
        )
        self.assertEqual("grafana", grafana_route.upstream_service)
        self.assertEqual(3000, grafana_route.upstream_port)

    def test_rejects_forbidden_ingress_policy(self):
        route = DesiredHttpsRoute(
            service_name="jenkins",
            hostname="jenkins.tsw.local",
            upstream_service="jenkins",
            upstream_port=8080,
        )

        for kwargs in (
            {"public_ports": (80, 8080)},
            {"http_redirect_to_https": False},
            {"exposed_by_default": True},
            {"api_insecure": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    DesiredHttpsIngress(routes=(route,), **kwargs)

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


if __name__ == "__main__":
    unittest.main()

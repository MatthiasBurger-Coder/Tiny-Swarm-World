import unittest

from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_evidence_safe,
    assert_route_contract,
    route_evidence,
)


class TestServiceAccessRouting(unittest.TestCase):
    def test_service_access_route_uses_traefik_dashboard_target(self) -> None:
        assert_route_contract(self, "service-access")

    def test_service_access_link_prefers_routed_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "service-access")

    def test_effective_route_evidence_is_redacted_and_lists_fallbacks(self) -> None:
        evidence = route_evidence()

        self.assertEqual((80, 443), evidence["gateway_public_ingress_ports"])
        self.assertIn(
            {"classification": "diagnostic", "port": 10080},
            evidence["diagnostic_fallback_ports"],
        )
        self.assertIn(
            {"classification": "diagnostic", "port": 10443},
            evidence["diagnostic_fallback_ports"],
        )
        self.assertEqual("traefik_host_route", evidence["service_access_preferred_url_source"])
        self.assertIn(
            {"reason": "service_not_supported", "service": "rabbitmq"},
            evidence["skipped_routes"],
        )
        assert_evidence_safe(self, evidence)


if __name__ == "__main__":
    unittest.main()

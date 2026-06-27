import unittest

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

    def test_infisical_route_keeps_localhost_as_compatibility_host_only(self) -> None:
        labels = traefik_labels(route_expectation("infisical"))

        self.assertIn(
            "traefik.http.routers.infisical.rule=Host(`infisical.tsw.local`) || Host(`localhost`)",
            labels,
        )


if __name__ == "__main__":
    unittest.main()

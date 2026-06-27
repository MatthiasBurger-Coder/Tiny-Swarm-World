import unittest

from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_route_contract,
)


class TestSonarQubeRouting(unittest.TestCase):
    def test_sonarqube_route_uses_internal_ui_target(self) -> None:
        assert_route_contract(self, "sonarqube")

    def test_sonarqube_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "sonarqube")


if __name__ == "__main__":
    unittest.main()

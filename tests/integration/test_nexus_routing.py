import unittest

from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_route_contract,
)


class TestNexusRouting(unittest.TestCase):
    def test_nexus_route_uses_internal_ui_target(self) -> None:
        assert_route_contract(self, "nexus")

    def test_nexus_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "nexus")


if __name__ == "__main__":
    unittest.main()

import unittest

from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_route_contract,
)


class TestPortainerRouting(unittest.TestCase):
    def test_portainer_route_uses_internal_ui_target(self) -> None:
        assert_route_contract(self, "portainer")

    def test_portainer_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "portainer")


if __name__ == "__main__":
    unittest.main()

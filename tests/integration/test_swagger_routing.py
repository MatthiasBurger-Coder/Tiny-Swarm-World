import unittest

from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_route_contract,
)


class TestSwaggerRouting(unittest.TestCase):
    def test_swagger_route_uses_internal_nginx_target(self) -> None:
        assert_route_contract(self, "swagger")

    def test_swagger_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "swagger")


if __name__ == "__main__":
    unittest.main()

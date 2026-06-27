import unittest

from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_route_contract,
    compose_service,
    route_expectation,
)


class TestPulsarRouting(unittest.TestCase):
    def test_pulsar_manager_route_uses_gui_target_not_broker_port(self) -> None:
        assert_route_contract(self, "pulsar-manager")

    def test_pulsar_admin_api_route_uses_http_admin_target(self) -> None:
        assert_route_contract(self, "pulsar-admin-api")

    def test_pulsar_dashboard_links_prefer_traefik_hostnames(self) -> None:
        assert_dashboard_prefers_route(self, "pulsar-manager")
        assert_dashboard_prefers_route(self, "pulsar-admin-api")

    def test_pulsar_broker_tcp_port_is_not_http_route_target(self) -> None:
        manager = compose_service(route_expectation("pulsar-manager"))
        admin = compose_service(route_expectation("pulsar-admin-api"))

        self.assertNotIn(
            "traefik.http.services.pulsar.loadbalancer.server.port=6650",
            manager["deploy"]["labels"],
        )
        self.assertNotIn(
            "traefik.http.services.pulsar-api.loadbalancer.server.port=6650",
            admin["deploy"]["labels"],
        )


if __name__ == "__main__":
    unittest.main()

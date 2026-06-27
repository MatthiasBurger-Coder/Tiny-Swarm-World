import unittest

from tests.integration.routing_contract import (
    assert_dashboard_prefers_route,
    assert_route_contract,
)


class TestJenkinsRouting(unittest.TestCase):
    def test_jenkins_route_uses_internal_http_target(self) -> None:
        assert_route_contract(self, "jenkins")

    def test_jenkins_dashboard_link_prefers_traefik_hostname(self) -> None:
        assert_dashboard_prefers_route(self, "jenkins")


if __name__ == "__main__":
    unittest.main()

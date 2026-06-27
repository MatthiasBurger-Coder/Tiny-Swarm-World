import unittest

from tests.integration.routing_contract import route_evidence


class TestTinySwarmAppRouting(unittest.TestCase):
    def test_app_and_api_routes_are_skipped_without_configured_route_hosts(self) -> None:
        evidence = route_evidence()
        hostnames = {route["hostname"] for route in evidence["routes"]}

        self.assertNotIn("app.tsw.local", hostnames)
        self.assertNotIn("api.tsw.local", hostnames)
        self.assertIn(
            {"reason": "route_host_not_configured", "service": "app"},
            evidence["skipped_routes"],
        )
        self.assertIn(
            {"reason": "route_host_not_configured", "service": "api"},
            evidence["skipped_routes"],
        )


if __name__ == "__main__":
    unittest.main()

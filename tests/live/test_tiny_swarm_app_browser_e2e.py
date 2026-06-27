import unittest

from tests.integration.routing_contract import route_evidence


class TestTinySwarmAppBrowserE2E(unittest.TestCase):
    def test_app_and_api_routes_are_explicitly_skipped_without_route_hosts(self) -> None:
        evidence = route_evidence()

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

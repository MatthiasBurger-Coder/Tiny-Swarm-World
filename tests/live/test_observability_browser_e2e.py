import unittest

from tests.integration.routing_contract import route_evidence


class TestObservabilityBrowserE2E(unittest.TestCase):
    def test_observability_routes_are_explicitly_skipped_without_enabled_services(self) -> None:
        evidence = route_evidence()

        self.assertIn(
            {"reason": "service_not_enabled", "service": "prometheus"},
            evidence["skipped_routes"],
        )
        self.assertIn(
            {"reason": "service_not_enabled", "service": "grafana"},
            evidence["skipped_routes"],
        )


if __name__ == "__main__":
    unittest.main()

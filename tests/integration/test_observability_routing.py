import unittest

from tests.integration.routing_contract import route_evidence


class TestObservabilityRouting(unittest.TestCase):
    def test_prometheus_and_grafana_routes_are_skipped_when_not_enabled(self) -> None:
        evidence = route_evidence()

        self.assertNotIn("prometheus.tsw.local", repr(evidence["routes"]))
        self.assertNotIn("grafana.tsw.local", repr(evidence["routes"]))
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

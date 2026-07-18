import unittest
from typing import cast

from tests.live.browser_e2e_contract import (
    browser_route_expectations,
    build_suite_summary,
)
from tests.support.effective_access_model_fixture import effective_access_model_fixture


class TestObservabilityBrowserE2E(unittest.TestCase):
    def test_observability_routes_are_explicitly_skipped_without_enabled_services(self) -> None:
        with effective_access_model_fixture() as fixture:
            model = fixture.repository.get_effective_access_model()
            expectations = browser_route_expectations(fixture.repository)

        evidence = model.to_dict()
        skipped_routes = cast(list[dict[str, str]], evidence["skipped_routes"])
        expected_routes = {expectation.route_name for expectation in expectations}

        self.assertIn(
            {"reason": "service_not_enabled", "service": "prometheus"},
            skipped_routes,
        )
        self.assertIn(
            {"reason": "service_not_enabled", "service": "grafana"},
            skipped_routes,
        )
        self.assertNotIn("prometheus", expected_routes)
        self.assertNotIn("grafana", expected_routes)

    def test_enabled_observability_routes_enter_dynamic_suite_summary(self) -> None:
        with effective_access_model_fixture(
            enabled_services=("prometheus", "grafana")
        ) as fixture:
            expectations = browser_route_expectations(fixture.repository)

        summary = build_suite_summary(expectations, {})
        status_matrix = cast(dict[str, list[str]], summary["status_matrix"])
        self.assertIn("prometheus", status_matrix["missing"])
        self.assertIn("grafana", status_matrix["missing"])
        self.assertEqual(summary["result"], "failed")


if __name__ == "__main__":
    unittest.main()

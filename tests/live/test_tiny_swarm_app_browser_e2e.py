import unittest
from typing import cast

from tests.live.browser_e2e_contract import (
    browser_route_expectations,
    build_suite_summary,
)
from tests.support.effective_access_model_fixture import effective_access_model_fixture


class TestTinySwarmAppBrowserE2E(unittest.TestCase):
    def test_app_and_api_routes_are_explicitly_skipped_without_route_hosts(self) -> None:
        with effective_access_model_fixture() as fixture:
            model = fixture.repository.get_effective_access_model()
            expectations = browser_route_expectations(fixture.repository)

        evidence = model.to_dict()
        skipped_routes = cast(list[dict[str, str]], evidence["skipped_routes"])
        expected_routes = {expectation.route_name for expectation in expectations}

        self.assertIn(
            {"reason": "service_not_enabled", "service": "app"},
            skipped_routes,
        )
        self.assertIn(
            {"reason": "service_not_enabled", "service": "api"},
            skipped_routes,
        )
        self.assertNotIn("app", expected_routes)
        self.assertNotIn("api", expected_routes)

    def test_enabled_app_and_api_routes_enter_dynamic_suite_summary(self) -> None:
        with effective_access_model_fixture(enabled_services=("tiny-swarm",)) as fixture:
            expectations = browser_route_expectations(fixture.repository)

        summary = build_suite_summary(expectations, {})
        status_matrix = cast(dict[str, list[str]], summary["status_matrix"])
        self.assertIn("app", status_matrix["missing"])
        self.assertIn("api", status_matrix["missing"])
        self.assertEqual(summary["result"], "failed")


if __name__ == "__main__":
    unittest.main()

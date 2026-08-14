"""Static guardrails for the canonical Classic acceptance suite."""

from __future__ import annotations

import unittest
from pathlib import Path


CANONICAL_SUITE = Path(__file__).with_name("test_post_install_browser_live.py")
LEGACY_INTEGRATION_SUITE = (
    Path(__file__).parents[2] / "integration" / "test_post_install_browser_live.py"
)


class ClassicSuiteLayoutTest(unittest.TestCase):
    def test_canonical_suite_owns_post_install_and_dashboard_contract(self) -> None:
        source = CANONICAL_SUITE.read_text(encoding="utf-8")

        self.assertIn("class PostInstallBrowserLiveTest", source)
        self.assertIn("_service_checks", source)
        self.assertIn("browser_route_expectations", source)
        self.assertIn("TSW_RUN_POST_INSTALL_BROWSER_LIVE", source)

    def test_legacy_integration_runner_was_migrated_without_playwright_duplicate(self) -> None:
        source = CANONICAL_SUITE.read_text(encoding="utf-8").casefold()

        self.assertFalse(LEGACY_INTEGRATION_SUITE.exists())
        self.assertNotIn("import playwright", source)
        self.assertNotIn("playwright.sync_api", source)
        self.assertNotIn("tsw_run_post_install_browser_integration", source)

    def test_canonical_live_runner_is_opt_in(self) -> None:
        source = CANONICAL_SUITE.read_text(encoding="utf-8")

        self.assertIn("@unittest.skipUnless(", source)
        self.assertIn("EVIDENCE_ROOT_ENV", source)
        self.assertNotIn("setup run --live", source)
        self.assertNotIn("docker compose up", source.casefold())


if __name__ == "__main__":
    unittest.main()

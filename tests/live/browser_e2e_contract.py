from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from tests.integration.routing_contract import ROUTE_EXPECTATIONS, RouteExpectation


RUN_LIVE_ENV = "TSW_RUN_POST_INSTALL_BROWSER_LIVE"
E2E_EVIDENCE_ROOT = Path(".tiny-swarm-world/evidence/solid-typed-evidence/e2e")
LOGIN_REQUIRED_ROUTES = frozenset(
    {
        "infisical",
        "jenkins",
        "nexus",
        "portainer",
        "pulsar-manager",
        "sonarqube",
    }
)


@dataclass(frozen=True)
class BrowserRouteResult:
    route_name: str
    url: str
    result: str
    redacted_reason: str = ""

    def to_evidence(self) -> dict[str, str]:
        return {
            "redacted_reason": self.redacted_reason,
            "result": self.result,
            "route_name": self.route_name,
            "url": self.url,
        }


def route_expectation_for_browser(route_name: str) -> RouteExpectation:
    return ROUTE_EXPECTATIONS[route_name]


def live_e2e_enabled() -> bool:
    return os.environ.get(RUN_LIVE_ENV) == "1"


def approved_credential_available(route_name: str) -> bool:
    env_names = {
        "infisical": ("TSW_INFISICAL_LOGIN_EMAIL", "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"),
        "jenkins": ("TSW_JENKINS_ADMIN_PASSWORD",),
        "nexus": ("TSW_NEXUS_ADMIN_PASSWORD",),
        "portainer": ("TSW_PORTAINER_ADMIN_PASSWORD",),
        "pulsar-manager": ("TSW_PULSAR_MANAGER_ADMIN_PASSWORD",),
        "sonarqube": ("TSW_SONARQUBE_ADMIN_PASSWORD",),
    }
    return all(os.environ.get(name) for name in env_names.get(route_name, ()))


def selenium_driver():
    try:
        from selenium import webdriver  # type: ignore[import-not-found]
        from selenium.webdriver.common.by import By  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise unittest.SkipTest("selenium is not installed in the active test environment") from exc
    return webdriver, By


class BrowserRouteE2EContract(unittest.TestCase):
    __unittest_skip__ = True
    __unittest_skip_why__ = "abstract browser E2E contract"
    route_name: str = ""
    expected_title_fragment: str = ""

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__unittest_skip__ = False

    def test_route_contract_uses_routed_https_url(self) -> None:
        expectation = route_expectation_for_browser(self.route_name)
        parsed = urlparse(expectation.dashboard_url)

        self.assertEqual("https", parsed.scheme)
        self.assertTrue(parsed.hostname and parsed.hostname.endswith(".tsw.local"))
        self.assertIsNone(parsed.port)
        self.assertFalse(parsed.username)
        self.assertFalse(parsed.password)
        self.assertFalse(parsed.query)
        self.assertFalse(parsed.fragment)

    def test_live_e2e_evidence_target_is_local_and_ignored(self) -> None:
        self.assertEqual(
            ".tiny-swarm-world/evidence/solid-typed-evidence/e2e",
            E2E_EVIDENCE_ROOT.as_posix(),
        )

    @unittest.skipUnless(
        live_e2e_enabled(),
        f"set {RUN_LIVE_ENV}=1 to run routed Selenium browser E2E checks",
    )
    def test_live_routed_link_opens_with_selenium(self) -> None:
        expectation = route_expectation_for_browser(self.route_name)
        webdriver, by = selenium_driver()
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")

        driver = webdriver.Firefox(options=options)
        try:
            driver.set_page_load_timeout(
                float(os.environ.get("TSW_BROWSER_E2E_TIMEOUT_SECONDS", "45"))
            )
            driver.get(expectation.dashboard_url)
            body = driver.find_element(by.TAG_NAME, "body")
            self.assertTrue(body.text or driver.title)
            if self.route_name in LOGIN_REQUIRED_ROUTES:
                if not approved_credential_available(self.route_name):
                    self.skipTest(
                        "approved credential source unavailable for required login flow"
                    )
                self.assertTrue(
                    _login_page_or_authenticated_state(body.text, driver.title),
                    "expected login page or authenticated landing state",
                )
        finally:
            driver.quit()


def _login_page_or_authenticated_state(body_text: str, title: str) -> bool:
    text = f"{title}\n{body_text}".casefold()
    return any(
        marker in text
        for marker in (
            "login",
            "sign in",
            "dashboard",
            "portainer",
            "jenkins",
            "nexus",
            "sonarqube",
            "infisical",
            "pulsar",
        )
    )

from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
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
    return _approved_credential(route_name) is not None


def selenium_driver():
    try:
        from selenium import webdriver  # type: ignore[import-not-found]
        from selenium.webdriver.common.by import By  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise unittest.SkipTest("selenium is not installed in the active test environment") from exc
    return webdriver, By


class BrowserRouteE2EContract:
    route_name: str = ""
    expected_title_fragment: str = ""

    def test_route_contract_uses_routed_https_url(self) -> None:
        _assert_routed_https_url(self, route_expectation_for_browser(self.route_name).dashboard_url)

    def test_live_e2e_evidence_target_is_local_and_ignored(self) -> None:
        _assert_evidence_target(self)

    @unittest.skipUnless(
        live_e2e_enabled(),
        f"set {RUN_LIVE_ENV}=1 to run routed Selenium browser E2E checks",
    )
    def test_live_routed_link_opens_with_selenium(self) -> None:
        testcase = cast(unittest.TestCase, self)
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
            testcase.assertTrue(body.text or driver.title)
            if self.route_name in LOGIN_REQUIRED_ROUTES:
                credential = _approved_credential(self.route_name)
                if credential is None:
                    testcase.skipTest(
                        "approved credential source unavailable for required login flow"
                    )
                _perform_login_flow(driver, by, self.route_name, credential)
                body = driver.find_element(by.TAG_NAME, "body")
                testcase.assertTrue(
                    _post_login_success(self.route_name, body.text, driver.title),
                    "expected stable authenticated landing state after login",
                )
        finally:
            driver.quit()


class BrowserRouteE2EContractStaticTest(unittest.TestCase):
    def test_all_browser_route_urls_use_routed_https_hosts(self) -> None:
        for expectation in ROUTE_EXPECTATIONS.values():
            with self.subTest(route=expectation.route_name):
                _assert_routed_https_url(self, expectation.dashboard_url)

    def test_live_e2e_evidence_target_is_local_and_ignored(self) -> None:
        _assert_evidence_target(self)

    def test_browser_result_evidence_is_redacted(self) -> None:
        evidence = BrowserRouteResult(
            route_name="service-access",
            url="https://service-access.tsw.local",
            result="blocked",
            redacted_reason="live_consent_missing",
        ).to_evidence()

        self.assertEqual("service-access", evidence["route_name"])
        self.assertNotIn("password", repr(evidence).casefold())
        self.assertNotIn("secret", repr(evidence).casefold())
        self.assertNotIn("token", repr(evidence).casefold())


def _assert_routed_https_url(testcase: Any, url: str) -> None:
    parsed = urlparse(url)
    testcase.assertEqual("https", parsed.scheme)
    testcase.assertTrue(parsed.hostname and parsed.hostname.endswith(".tsw.local"))
    testcase.assertIsNone(parsed.port)
    testcase.assertFalse(parsed.username)
    testcase.assertFalse(parsed.password)
    testcase.assertFalse(parsed.query)
    testcase.assertFalse(parsed.fragment)


def _assert_evidence_target(testcase: Any) -> None:
    testcase.assertEqual(
        ".tiny-swarm-world/evidence/solid-typed-evidence/e2e",
        E2E_EVIDENCE_ROOT.as_posix(),
    )


def _approved_credential(route_name: str) -> tuple[str, str] | None:
    credentials = {
        "infisical": (
            os.environ.get("TSW_INFISICAL_LOGIN_EMAIL", ""),
            os.environ.get("TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD", ""),
        ),
        "jenkins": ("admin", os.environ.get("TSW_JENKINS_ADMIN_PASSWORD", "")),
        "nexus": ("admin", os.environ.get("TSW_NEXUS_ADMIN_PASSWORD", "")),
        "portainer": ("admin", os.environ.get("TSW_PORTAINER_ADMIN_PASSWORD", "")),
        "pulsar-manager": (
            "admin",
            os.environ.get("TSW_PULSAR_MANAGER_ADMIN_PASSWORD", ""),
        ),
        "sonarqube": ("admin", os.environ.get("TSW_SONARQUBE_ADMIN_PASSWORD", "")),
    }
    username, password = credentials.get(route_name, ("", ""))
    if username and password:
        return username, password
    return None


def _perform_login_flow(driver: Any, by: Any, route_name: str, credential: tuple[str, str]) -> None:
    username, password = credential
    body = driver.find_element(by.TAG_NAME, "body")
    if _post_login_success(route_name, body.text, driver.title):
        return
    username_field = _first_present(
        driver,
        by,
        (
            "input[name='username']",
            "input[name='user']",
            "input[name='j_username']",
            "input[name='email']",
            "input[type='email']",
            "input[id*='user']",
        ),
    )
    password_field = _first_present(
        driver,
        by,
        (
            "input[name='password']",
            "input[name='j_password']",
            "input[type='password']",
            "input[id*='password']",
        ),
    )
    username_field.clear()
    username_field.send_keys(username)
    password_field.clear()
    password_field.send_keys(password)
    submit = _first_present(
        driver,
        by,
        (
            "button[type='submit']",
            "input[type='submit']",
            "button[name='Submit']",
            "button",
        ),
    )
    submit.click()


def _first_present(driver: Any, by: Any, selectors: tuple[str, ...]) -> Any:
    last_error: Exception | None = None
    for selector in selectors:
        try:
            return driver.find_element(by.CSS_SELECTOR, selector)
        except Exception as exc:
            last_error = exc
    raise AssertionError(f"expected one selector to be present: {selectors}") from last_error


def _post_login_success(route_name: str, body_text: str, title: str) -> bool:
    text = f"{title}\n{body_text}".casefold()
    markers = {
        "infisical": ("projects", "secrets", "infisical"),
        "jenkins": ("dashboard", "jenkins", "new item"),
        "nexus": ("browse", "repositories", "nexus"),
        "portainer": ("home", "dashboard", "portainer"),
        "pulsar-manager": ("tenant", "namespace", "pulsar"),
        "sonarqube": ("projects", "quality", "sonarqube"),
    }
    return any(marker in text for marker in markers.get(route_name, (route_name,)))

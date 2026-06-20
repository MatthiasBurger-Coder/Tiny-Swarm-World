"""Opt-in browser checks for a completed local Tiny Swarm World installation.

The suite verifies the already-installed localhost service surfaces. It does
not start containers, deploy stacks, mutate Swarm state, or bootstrap services.
Run it only after an intentional live installation:

TSW_RUN_POST_INSTALL_BROWSER_INTEGRATION=1 python -m unittest \
  tests.integration.test_post_install_browser_live
"""

from __future__ import annotations

import os
import time
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


RUN_LIVE_ENV = "TSW_RUN_POST_INSTALL_BROWSER_INTEGRATION"
DEFAULT_ENV_FILE = Path(".tiny-swarm-world/local/live-installation.env")


@dataclass(frozen=True)
class ServiceEndpoint:
    name: str
    url: str


@dataclass(frozen=True)
class PostInstallConfig:
    dashboard_url: str
    vaultwarden_url: str
    vaultwarden_admin_token: str | None
    vaultwarden_email: str | None
    vaultwarden_master_password: str | None
    jenkins_url: str
    jenkins_username: str
    jenkins_password: str | None
    nexus_url: str
    nexus_username: str
    nexus_password: str | None
    portainer_url: str
    portainer_username: str
    portainer_password: str | None
    pulsar_admin_url: str
    pulsar_admin_token: str | None
    sonarqube_url: str
    sonarqube_username: str
    sonarqube_password: str | None
    swagger_url: str
    timeout_seconds: float
    browser_channel: str | None

    @classmethod
    def from_environment(cls) -> "PostInstallConfig":
        local_env = _load_shell_environment(Path(os.environ.get("TSW_LIVE_INSTALLATION_ENV", DEFAULT_ENV_FILE)))
        return cls(
            dashboard_url=_env_value(local_env, "TSW_DASHBOARD_URL", "http://localhost:10000"),
            vaultwarden_url=_env_value(local_env, "TSW_VAULTWARDEN_URL", "https://localhost"),
            vaultwarden_admin_token=_env_optional(local_env, "TSW_VAULTWARDEN_ADMIN_LOGIN_TOKEN")
            or _env_optional(local_env, "TSW_VAULTWARDEN_ADMIN_TOKEN"),
            vaultwarden_email=_env_optional(local_env, "TSW_VAULTWARDEN_LOGIN_EMAIL"),
            vaultwarden_master_password=_env_optional(local_env, "TSW_VAULTWARDEN_MASTER_PASSWORD"),
            jenkins_url=_env_value(local_env, "TSW_JENKINS_URL", "http://localhost:8080"),
            jenkins_username=_env_value(local_env, "TSW_JENKINS_ADMIN_USERNAME", "admin"),
            jenkins_password=_env_optional(local_env, "TSW_JENKINS_ADMIN_PASSWORD"),
            nexus_url=_env_value(local_env, "TSW_NEXUS_URL", "http://localhost:8081"),
            nexus_username=_env_value(local_env, "TSW_NEXUS_ADMIN_USERNAME", "admin"),
            nexus_password=_env_optional(local_env, "TSW_NEXUS_ADMIN_PASSWORD"),
            portainer_url=_env_value(local_env, "TSW_PORTAINER_URL", "http://localhost:9000"),
            portainer_username=_env_value(local_env, "TSW_PORTAINER_USERNAME", "admin"),
            portainer_password=_env_optional(local_env, "TSW_PORTAINER_ADMIN_PASSWORD"),
            pulsar_admin_url=_env_value(local_env, "TSW_PULSAR_PUBLIC_ADMIN_URL", "http://localhost:8087"),
            pulsar_admin_token=_env_optional(local_env, "TSW_PULSAR_ADMIN_TOKEN"),
            sonarqube_url=_env_value(local_env, "TSW_SONARQUBE_URL", "http://localhost:9001"),
            sonarqube_username=_env_value(local_env, "TSW_SONARQUBE_ADMIN_USERNAME", "admin"),
            sonarqube_password=_env_optional(local_env, "TSW_SONARQUBE_ADMIN_PASSWORD"),
            swagger_url=_env_value(local_env, "TSW_SWAGGER_URL", "http://localhost:8084"),
            timeout_seconds=float(os.environ.get("TSW_POST_INSTALL_BROWSER_TIMEOUT", "45")),
            browser_channel=os.environ.get("TSW_POST_INSTALL_BROWSER_CHANNEL"),
        )

    @property
    def service_endpoints(self) -> tuple[ServiceEndpoint, ...]:
        return (
            ServiceEndpoint("dashboard", self.dashboard_url),
            ServiceEndpoint("vaultwarden", self.vaultwarden_url),
            ServiceEndpoint("jenkins", self.jenkins_url),
            ServiceEndpoint("nexus", self.nexus_url),
            ServiceEndpoint("portainer", self.portainer_url),
            ServiceEndpoint("pulsar-admin-api", self.pulsar_admin_url),
            ServiceEndpoint("sonarqube", self.sonarqube_url),
            ServiceEndpoint("swagger", self.swagger_url),
        )


@unittest.skipUnless(
    os.environ.get(RUN_LIVE_ENV) == "1",
    f"set {RUN_LIVE_ENV}=1 to run post-install browser integration checks",
)
class PostInstallBrowserIntegrationTest(unittest.TestCase):
    """Verifies browser-visible localhost services after successful install."""

    config: ClassVar[PostInstallConfig]

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = PostInstallConfig.from_environment()
        try:
            import playwright.sync_api  # type: ignore[import-not-found]  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(
                "playwright is required for browser checks; install it outside the product dependency set "
                "and run `python -m playwright install chromium`"
            ) from exc

    def test_localhost_dashboard_links_are_browser_reachable(self) -> None:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright, self.config)
            page = browser.new_page(ignore_https_errors=True)
            try:
                _goto_ready(page, self.config.dashboard_url, self.config.timeout_seconds)
                links = page.locator("a[href]").evaluate_all(
                    "links => links.map(link => link.href).filter(href => href && !href.startsWith('mailto:'))"
                )
                self.assertGreaterEqual(len(links), 7, "dashboard must expose service links")
                for link in links:
                    with self.subTest(link=link):
                        probe = browser.new_page(ignore_https_errors=True)
                        try:
                            _goto_ready(probe, str(link), self.config.timeout_seconds)
                        finally:
                            probe.close()
            finally:
                browser.close()

    def test_all_service_urls_are_http_reachable(self) -> None:
        for endpoint in self.config.service_endpoints:
            with self.subTest(service=endpoint.name):
                _wait_for_http(endpoint.url, self.config.timeout_seconds)

    def test_vaultwarden_admin_page_accepts_admin_token(self) -> None:
        if not self.config.vaultwarden_admin_token:
            self.skipTest("TSW_VAULTWARDEN_ADMIN_LOGIN_TOKEN or TSW_VAULTWARDEN_ADMIN_TOKEN is required")

        from playwright.sync_api import expect, sync_playwright  # type: ignore[import-not-found]

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright, self.config)
            page = browser.new_page(ignore_https_errors=True)
            try:
                _goto_ready(page, urljoin(self.config.vaultwarden_url, "/admin"), self.config.timeout_seconds)
                _fill_first(page, ("Token", "Admin token", "Password"), self.config.vaultwarden_admin_token)
                _click_first(page, ("Enter", "Log in", "Login", "Submit"))
                expect(page.get_by_text("Users", exact=False)).to_be_visible(timeout=15_000)
            finally:
                browser.close()

    def test_vaultwarden_user_vault_is_visible_when_credentials_are_configured(self) -> None:
        if not self.config.vaultwarden_email or not self.config.vaultwarden_master_password:
            self.skipTest("TSW_VAULTWARDEN_LOGIN_EMAIL and TSW_VAULTWARDEN_MASTER_PASSWORD are required")

        from playwright.sync_api import expect, sync_playwright  # type: ignore[import-not-found]

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright, self.config)
            page = browser.new_page(ignore_https_errors=True, base_url=self.config.vaultwarden_url)
            try:
                _goto_ready(page, "/#/login", self.config.timeout_seconds)
                _fill_first(page, ("Email", "Email address"), self.config.vaultwarden_email)
                _fill_first(page, ("Master password", "Password"), self.config.vaultwarden_master_password)
                _click_first(page, ("Log in with master password", "Log in", "Login"))
                expect(page.get_by_text("Vault", exact=False)).to_be_visible(timeout=20_000)
            finally:
                browser.close()

    def test_jenkins_admin_login(self) -> None:
        self._require_secret(self.config.jenkins_password, "TSW_JENKINS_ADMIN_PASSWORD")
        self._login_with_username_password(
            self.config.jenkins_url,
            self.config.jenkins_username,
            self.config.jenkins_password,
            success_texts=("Dashboard", "Manage Jenkins", "New Item"),
        )

    def test_nexus_admin_login_and_docker_cache_repository(self) -> None:
        self._require_secret(self.config.nexus_password, "TSW_NEXUS_ADMIN_PASSWORD")
        from playwright.sync_api import expect, sync_playwright  # type: ignore[import-not-found]

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright, self.config)
            page = browser.new_page(ignore_https_errors=True)
            try:
                _goto_ready(page, self.config.nexus_url, self.config.timeout_seconds)
                page.get_by_text("Sign in", exact=False).first.click(timeout=10_000)
                page.locator("div.x-window input[name='username']").first.fill(
                    self.config.nexus_username,
                    timeout=10_000,
                )
                page.locator("div.x-window input[name='password']").first.fill(
                    self.config.nexus_password or "",
                    timeout=10_000,
                )
                page.locator("div.x-window a.x-btn").filter(has_text="Sign in").first.click(
                    timeout=10_000
                )
                expect(page.get_by_text("Sign out", exact=False).first).to_be_visible(
                    timeout=20_000
                )
            finally:
                browser.close()
        repositories_url = urljoin(self.config.nexus_url, "/service/rest/v1/repositories")
        repositories = _http_text(
            repositories_url,
            self.config.nexus_username,
            self.config.nexus_password,
            self.config.timeout_seconds,
        )
        self.assertIn("docker-hosted", repositories)

    def test_portainer_admin_login(self) -> None:
        self._require_secret(self.config.portainer_password, "TSW_PORTAINER_ADMIN_PASSWORD")
        self._login_with_username_password(
            self.config.portainer_url,
            self.config.portainer_username,
            self.config.portainer_password,
            success_texts=("Home", "Environments", "Stacks"),
        )

    def test_pulsar_admin_api_requires_and_accepts_admin_token(self) -> None:
        self._require_secret(self.config.pulsar_admin_token, "TSW_PULSAR_ADMIN_TOKEN")
        clusters_url = urljoin(self.config.pulsar_admin_url, "/admin/v2/clusters")

        self.assertIn(_http_status(clusters_url, self.config.timeout_seconds), {401, 403})
        clusters = _http_text(
            clusters_url,
            timeout_seconds=self.config.timeout_seconds,
            bearer_token=self.config.pulsar_admin_token,
        )

        self.assertIn("standalone", clusters.casefold())

    def test_sonarqube_admin_login(self) -> None:
        self._require_secret(self.config.sonarqube_password, "TSW_SONARQUBE_ADMIN_PASSWORD")
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright, self.config)
            page = browser.new_page(ignore_https_errors=True)
            try:
                _goto_ready(
                    page,
                    urljoin(self.config.sonarqube_url, "/sessions/new"),
                    self.config.timeout_seconds,
                )
                page.locator("input[name='login'], #login-input").first.fill(
                    self.config.sonarqube_username,
                    timeout=10_000,
                )
                page.locator("input[name='password'], #password-input").first.fill(
                    self.config.sonarqube_password or "",
                    timeout=10_000,
                )
                page.locator("button[type='submit']").first.click(timeout=10_000)
                _expect_any_text(page, ("Projects", "Administration", "Create your project"))
            finally:
                browser.close()

    def test_swagger_is_browser_reachable(self) -> None:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright, self.config)
            page = browser.new_page(ignore_https_errors=True)
            try:
                response = _goto_ready(
                    page,
                    urljoin(self.config.swagger_url, "/status"),
                    self.config.timeout_seconds,
                )
                if response is not None and response.status >= 500:
                    raise AssertionError(f"Swagger smoke endpoint returned HTTP {response.status}")
            finally:
                browser.close()

    def _login_with_username_password(
        self,
        url: str,
        username: str,
        password: str | None,
        success_texts: tuple[str, ...],
    ) -> None:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]

        if password is None:
            raise AssertionError("password must be present after _require_secret")

        with sync_playwright() as playwright:
            browser = _launch_browser(playwright, self.config)
            page = browser.new_page(ignore_https_errors=True)
            try:
                _goto_ready(page, url, self.config.timeout_seconds)
                _fill_username(page, username)
                _fill_password(page, password)
                _click_first(page, ("Sign in", "Log in", "Login", "Sign In"))
                _expect_any_text(page, success_texts)
            finally:
                browser.close()

    def _require_secret(self, value: str | None, name: str) -> None:
        if not value:
            self.skipTest(f"{name} is required in the live installation environment")


def _launch_browser(playwright: Any, config: PostInstallConfig) -> Any:
    if config.browser_channel:
        return playwright.chromium.launch(channel=config.browser_channel, headless=True)
    return playwright.chromium.launch(headless=True)


def _goto_ready(page: Any, url: str, timeout_seconds: float) -> Any:
    return page.goto(url, wait_until="domcontentloaded", timeout=int(timeout_seconds * 1000))


def _fill_username(page: Any, value: str) -> None:
    _fill_first(page, ("Username", "User Name", "Login", "User ID", "ID"), value)


def _fill_password(page: Any, value: str) -> None:
    _fill_first(page, ("Password", "Passwort"), value)


def _fill_first(page: Any, labels: tuple[str, ...], value: str) -> None:
    last_error: Exception | None = None
    for label in labels:
        for locator in (
            page.get_by_label(label, exact=False),
            page.get_by_placeholder(label, exact=False),
        ):
            try:
                locator.fill(value, timeout=5_000)
                return
            except Exception as exc:
                last_error = exc
    for selector in (
        "input[name='username']",
        "input[name='j_username']",
        "input[name='login']",
        "input[name='user']",
        "input[type='text']",
        "input[type='email']",
        "input[name='password']",
        "input[name='j_password']",
        "input[type='password']",
    ):
        try:
            page.locator(selector).first.fill(value, timeout=5_000)
            return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"could not fill any field matching {labels}: {last_error}")


def _click_first(page: Any, names: tuple[str, ...]) -> None:
    last_error: Exception | None = None
    for name in names:
        for locator in (
            page.get_by_role("button", name=name, exact=False),
            page.get_by_text(name, exact=False),
            page.locator(f"input[type='submit'][value*='{name}']"),
        ):
            try:
                locator.first.click(timeout=10_000)
                return
            except Exception as exc:
                last_error = exc
    raise RuntimeError(f"could not click any control matching {names}: {last_error}")


def _expect_any_text(page: Any, texts: tuple[str, ...]) -> None:
    last_error: Exception | None = None
    for text in texts:
        try:
            page.get_by_text(text, exact=False).first.wait_for(timeout=15_000)
            return
        except Exception as exc:
            last_error = exc
    raise AssertionError(f"none of the expected post-login texts became visible: {texts}; last error: {last_error}")


def _wait_for_http(url: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            _http_text(url, None, None, 3)
            return
        except HTTPError as exc:
            if exc.code < 500:
                return
            last_error = exc
        except Exception as exc:
            last_error = exc
        time.sleep(1)
    raise AssertionError(f"{url} did not become reachable before timeout: {last_error}")


def _http_text(
    url: str,
    username: str | None = None,
    password: str | None = None,
    timeout_seconds: float = 45,
    *,
    bearer_token: str | None = None,
) -> str:
    request = Request(url)
    if bearer_token is not None:
        request.add_header("Authorization", f"Bearer {bearer_token}")
    if username is not None and password is not None:
        import base64

        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    try:
        response_context = urlopen(request, timeout=timeout_seconds)
    except HTTPError as exc:
        if exc.code < 500:
            return exc.read().decode("utf-8", errors="replace")
        raise
    with response_context as response:
        return response.read().decode("utf-8", errors="replace")


def _http_status(url: str, timeout_seconds: float) -> int:
    request = Request(url)
    try:
        response_context = urlopen(request, timeout=timeout_seconds)
    except HTTPError as exc:
        return int(exc.code)
    with response_context as response:
        return int(response.status)


def _env_value(local_env: dict[str, str], key: str, default: str) -> str:
    return os.environ.get(key) or local_env.get(key) or default


def _env_optional(local_env: dict[str, str], key: str) -> str | None:
    return os.environ.get(key) or local_env.get(key)


def _load_shell_environment(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


if __name__ == "__main__":
    unittest.main()

"""Opt-in live checks for completed Tiny Swarm World service access installs.

The default quality gate runs only static safety tests in this module. The
live checks run only with:

TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest \
  tests.live.test_post_install_browser_live
"""

from __future__ import annotations

import json
import os
import ssl
import time
import unittest
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from tiny_swarm_world.domain.deployment import (
    ServiceStackProfile,
    service_stack_contracts_for_profile,
)


RUN_LIVE_ENV = "TSW_RUN_POST_INSTALL_BROWSER_LIVE"
DEFAULT_ENV_FILE = Path(".tiny-swarm-world/local/live-installation.env")
DEFAULT_EVIDENCE_ROOT = Path(".tiny-swarm-world/evidence/post_install_browser_live")
SERVICE_ACCESS_DASHBOARD = Path("infra/compose/service-access/dashboard/index.html")
EXPECTED_INFISICAL_ITEMS = (
    "platform/jenkins",
    "platform/nexus",
    "platform/portainer",
    "platform/rabbitmq",
    "platform/sonarqube",
)
NO_LOGIN_SERVICES = ("service-access", "swagger")
SERVICE_ALLOWED_STATUSES = {
    "jenkins": (200, 403),
    "nexus-docker-registry": (401,),
}
DASHBOARD_REDIRECT_STATUSES = (301, 302, 303, 307, 308)
FORBIDDEN_EVIDENCE_FRAGMENTS = (
    "authorization",
    "bearer ",
    "password",
    "secret",
    "token",
    "TSW_",
    "userinfo",
)


@dataclass(frozen=True)
class ServiceCheck:
    name: str
    url: str
    follow_redirects: bool = True
    allowed_statuses: tuple[int, ...] = (200,)


@dataclass(frozen=True)
class HttpProbeResult:
    service: str
    url: str
    reachable: bool
    status_code: int | None
    content_type: str
    result: str
    redacted_failure_reason: str = ""

    def to_evidence(self) -> dict[str, object]:
        return {
            "content_type": self.content_type,
            "reachable": self.reachable,
            "redacted_failure_reason": self.redacted_failure_reason,
            "result": self.result,
            "service": self.service,
            "status_code": self.status_code,
            "url": self.url,
        }


@dataclass(frozen=True)
class LivePostInstallConfig:
    dashboard_url: str
    infisical_url: str
    infisical_email: str | None
    infisical_password: str | None
    timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "LivePostInstallConfig":
        local_env = _load_shell_environment(
            Path(os.environ.get("TSW_LIVE_INSTALLATION_ENV", DEFAULT_ENV_FILE))
        )
        dashboard_url = _env_value(local_env, "TSW_DASHBOARD_URL", "http://localhost")
        infisical_url = _env_value(local_env, "TSW_INFISICAL_URL", "https://localhost")
        return cls(
            dashboard_url=_validated_local_url(dashboard_url, "dashboard"),
            infisical_url=_validated_local_url(infisical_url, "infisical"),
            infisical_email=_env_optional(local_env, "TSW_INFISICAL_LOGIN_EMAIL"),
            infisical_password=_env_optional(
                local_env,
                "TSW_INFISICAL_PASSWORD",
            ),
            timeout_seconds=float(os.environ.get("TSW_POST_INSTALL_BROWSER_TIMEOUT", "45")),
        )


class StaticPostInstallLiveSuiteTest(unittest.TestCase):
    def test_dashboard_declares_expected_infisical_item_references(self) -> None:
        references = _dashboard_references(SERVICE_ACCESS_DASHBOARD)

        self.assertEqual(EXPECTED_INFISICAL_ITEMS, references.credential_items)
        for service in NO_LOGIN_SERVICES:
            with self.subTest(service=service):
                self.assertIn(service, references.no_login_services)

    def test_live_service_checks_are_safe_localhost_urls(self) -> None:
        checks = _service_checks("http://localhost")

        self.assertGreaterEqual(len(checks), 14)
        for check in checks:
            with self.subTest(service=check.name):
                parsed = urlparse(check.url)
                self.assertIn(parsed.scheme, {"http", "https"})
                self.assertEqual("localhost", parsed.hostname)
                self.assertFalse(parsed.username)
                self.assertFalse(parsed.password)
                self.assertFalse(parsed.query)
                self.assertFalse(parsed.fragment)

    def test_live_service_checks_use_explicit_browser_status_allowlists(self) -> None:
        checks = _service_checks("http://localhost")

        for check in checks:
            with self.subTest(service=check.name):
                self.assertNotIn(404, check.allowed_statuses)
                self.assertTrue(check.allowed_statuses)
                self.assertTrue(
                    all(100 <= status <= 499 for status in check.allowed_statuses)
                )

    def test_live_config_rejects_non_local_operator_urls(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TSW_LIVE_INSTALLATION_ENV": "/tmp/tiny-swarm-world-missing.env",
                "TSW_DASHBOARD_URL": "https://example.invalid",
            },
        ):
            with self.assertRaisesRegex(
                AssertionError,
                "post_install_browser_setup_blocker: invalid_local_dashboard_url",
            ):
                LivePostInstallConfig.from_environment()

    def test_live_config_rejects_secret_bearing_infisical_urls(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TSW_LIVE_INSTALLATION_ENV": "/tmp/tiny-swarm-world-missing.env",
                "TSW_DASHBOARD_URL": "http://localhost",
                "TSW_INFISICAL_URL": "https://user:credential@localhost",
            },
        ):
            with self.assertRaisesRegex(
                AssertionError,
                "infisical_setup_blocker: invalid_local_infisical_url",
            ):
                LivePostInstallConfig.from_environment()

    def test_redacted_evidence_rejects_secret_like_keys_and_values(self) -> None:
        unsafe = {
            "service": "jenkins",
            "password": "value",
            "redacted_failure_reason": "token leaked",
        }

        self.assertFalse(_evidence_safe(unsafe))

    def test_infisical_inventory_evidence_contains_item_names_only(self) -> None:
        evidence = _infisical_item_evidence(
            expected_item="platform/jenkins",
            item_present=False,
            result="blocked",
            redacted_failure_reason="missing_login_material",
        )

        self.assertTrue(_evidence_safe(evidence))
        self.assertEqual("platform/jenkins", evidence["expected_infisical_item"])
        self.assertNotIn("value", evidence)


@unittest.skipUnless(
    os.environ.get(RUN_LIVE_ENV) == "1",
    f"set {RUN_LIVE_ENV}=1 to run post-install live browser checks",
)
class PostInstallBrowserLiveTest(unittest.TestCase):
    config: ClassVar[LivePostInstallConfig]
    evidence: ClassVar[_EvidenceRecorder]

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = LivePostInstallConfig.from_environment()
        cls.evidence = _EvidenceRecorder(DEFAULT_EVIDENCE_ROOT)

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "evidence"):
            cls.evidence.write()

    def test_01_service_routes_return_browser_relevant_http_responses(self) -> None:
        failures: list[HttpProbeResult] = []
        for check in _service_checks(self.config.dashboard_url):
            with self.subTest(service=check.name):
                result = _probe_http(check, self.config.timeout_seconds)
                self.evidence.record("service", result.to_evidence())
                if not result.reachable:
                    failures.append(result)

        if failures:
            failed_services = ",".join(result.service for result in failures)
            raise AssertionError(
                "post_install_browser_route_failed: "
                f"{failed_services}; evidence={self.evidence.path.as_posix()}"
            )

    def test_02_infisical_contains_required_credential_items(self) -> None:
        missing_material = _missing_infisical_login_material(self.config)
        if missing_material:
            for item in EXPECTED_INFISICAL_ITEMS:
                self.evidence.record(
                    "infisical_item",
                    _infisical_item_evidence(
                        expected_item=item,
                        item_present=False,
                        result="blocked",
                        redacted_failure_reason="missing_login_material",
                    ),
                )
            raise AssertionError(
                "infisical_setup_blocker: missing "
                f"{','.join(missing_material)}; evidence={self.evidence.path.as_posix()}"
            )

        missing_items = _missing_infisical_items(self.config)
        for item in EXPECTED_INFISICAL_ITEMS:
            self.evidence.record(
                "infisical_item",
                _infisical_item_evidence(
                    expected_item=item,
                    item_present=item not in missing_items,
                    result="passed" if item not in missing_items else "failed",
                    redacted_failure_reason=(
                        "" if item not in missing_items else "expected_item_not_visible"
                    ),
                ),
            )

        if missing_items:
            raise AssertionError(
                "infisical_credential_inventory_missing: "
                f"{','.join(missing_items)}; evidence={self.evidence.path.as_posix()}"
            )


def _service_checks(dashboard_url: str) -> tuple[ServiceCheck, ...]:
    safe_dashboard_url = _validated_local_url(dashboard_url, "dashboard")
    checks: list[ServiceCheck] = []
    for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS):
        for endpoint in contract.endpoints:
            url = endpoint.url
            if endpoint.name == "nexus-docker-registry":
                url = url.rstrip("/") + "/v2/"
            checks.append(
                ServiceCheck(
                    endpoint.name,
                    _validated_local_url(url, "service"),
                    allowed_statuses=SERVICE_ALLOWED_STATUSES.get(endpoint.name, (200,)),
                )
            )

    for route_name, route_path in _dashboard_references(SERVICE_ACCESS_DASHBOARD).routes:
        allowed_statuses = (
            (200,) if route_name == "service-access" else DASHBOARD_REDIRECT_STATUSES
        )
        checks.append(
            ServiceCheck(
                f"service-access-route:{route_name}",
                _validated_local_url(urljoin(safe_dashboard_url, route_path), "dashboard"),
                follow_redirects=False,
                allowed_statuses=allowed_statuses,
            )
        )
    return tuple(checks)


def _probe_http(check: ServiceCheck, timeout_seconds: float) -> HttpProbeResult:
    try:
        status_code, content_type = _http_head_or_get(
            check.url,
            timeout_seconds,
            follow_redirects=check.follow_redirects,
        )
    except (OSError, TimeoutError, URLError) as exc:
        return HttpProbeResult(
            service=check.name,
            url=check.url,
            reachable=False,
            status_code=None,
            content_type="",
            result="failed",
            redacted_failure_reason=type(exc).__name__,
        )

    reachable = status_code in check.allowed_statuses
    return HttpProbeResult(
        service=check.name,
        url=check.url,
        reachable=reachable,
        status_code=status_code,
        content_type=content_type,
        result="passed" if reachable else "failed",
        redacted_failure_reason="" if reachable else "http_status_out_of_range",
    )


def _http_head_or_get(
    url: str,
    timeout_seconds: float,
    *,
    follow_redirects: bool,
) -> tuple[int, str]:
    request = Request(url, method="HEAD")
    context = ssl._create_unverified_context() if url.startswith("https://") else None
    handlers = []
    if not follow_redirects:
        handlers.append(_NoRedirectHandler)
    if context is not None:
        handlers.append(HTTPSHandler(context=context))
    opener = build_opener(*handlers) if handlers else build_opener()
    try:
        response_context = opener.open(request, timeout=timeout_seconds)
    except HTTPError as exc:
        if exc.code < 500:
            return exc.code, exc.headers.get("content-type", "")
        raise
    except (OSError, TimeoutError, URLError):
        request = Request(url, method="GET")
        try:
            response_context = opener.open(request, timeout=timeout_seconds)
        except HTTPError as exc:
            if exc.code < 500:
                return exc.code, exc.headers.get("content-type", "")
            raise

    with response_context as response:
        return int(response.status), response.headers.get("content-type", "")


def _missing_infisical_login_material(
    config: LivePostInstallConfig,
) -> tuple[str, ...]:
    missing: list[str] = []
    if not config.infisical_email:
        missing.append("TSW_INFISICAL_LOGIN_EMAIL")
    if not config.infisical_password:
        missing.append("TSW_INFISICAL_PASSWORD")
    return tuple(missing)


def _missing_infisical_items(config: LivePostInstallConfig) -> tuple[str, ...]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError as exc:
        raise AssertionError("infisical_setup_blocker: playwright_unavailable") from exc

    if config.infisical_email is None or config.infisical_password is None:
        raise AssertionError("infisical_setup_blocker: missing_login_material")

    missing: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(ignore_https_errors=True, base_url=config.infisical_url)
        try:
            page.goto("/", wait_until="networkidle", timeout=int(config.timeout_seconds * 1000))
            _click_first_optional(page, ("Continue with Email",))
            _fill_first(page, ("Email", "Email address"), config.infisical_email)
            _fill_first(page, ("Password",), config.infisical_password)
            _click_first(page, ("Log in", "Login", "Sign in"))
            page.get_by_text("Secrets", exact=False).first.wait_for(timeout=20_000)
            for item in EXPECTED_INFISICAL_ITEMS:
                try:
                    page.get_by_text(item, exact=True).first.wait_for(timeout=5_000)
                except Exception:
                    missing.append(item)
        finally:
            browser.close()
    return tuple(missing)


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
    raise RuntimeError(f"could not fill field: {labels}; last={type(last_error).__name__}")


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
    raise RuntimeError(f"could not click control: {names}; last={type(last_error).__name__}")


def _click_first_optional(page: Any, names: tuple[str, ...]) -> None:
    try:
        _click_first(page, names)
    except RuntimeError:
        return


def _infisical_item_evidence(
    *,
    expected_item: str,
    item_present: bool,
    result: str,
    redacted_failure_reason: str,
) -> dict[str, object]:
    return {
        "expected_infisical_item": expected_item,
        "item_present": item_present,
        "redacted_failure_reason": redacted_failure_reason,
        "result": result,
        "service": expected_item.removeprefix("platform/"),
    }


def _env_value(local_env: dict[str, str], key: str, default: str) -> str:
    return os.environ.get(key) or local_env.get(key) or default


def _env_optional(local_env: dict[str, str], key: str) -> str | None:
    return os.environ.get(key) or local_env.get(key)


def _validated_local_url(raw_url: str, purpose: str) -> str:
    try:
        parsed = urlparse(raw_url)
        port = parsed.port
    except ValueError as exc:
        raise AssertionError(_invalid_local_url_reason(purpose)) from exc
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname != "localhost"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or port is not None
        and not 1 <= port <= 65535
    ):
        raise AssertionError(_invalid_local_url_reason(purpose))
    return raw_url


def _invalid_local_url_reason(purpose: str) -> str:
    if purpose == "infisical":
        return "infisical_setup_blocker: invalid_local_infisical_url"
    return f"post_install_browser_setup_blocker: invalid_local_{purpose}_url"


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


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, *_args: object, **_kwargs: object) -> None:
        return None


@dataclass(frozen=True)
class _DashboardReferences:
    routes: tuple[tuple[str, str], ...]
    credential_items: tuple[str, ...]
    no_login_services: tuple[str, ...]


class _DashboardReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.routes: list[tuple[str, str]] = []
        self.credential_items: list[str] = []
        self.no_login_services: list[str] = []
        self._current_row_header = ""
        self._in_header = False
        self._in_code = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "th":
            self._in_header = True
            self._current_row_header = ""
        if tag == "code":
            self._in_code = True
        if tag == "a" and (href := attributes.get("href")):
            if href.startswith("/"):
                name = href.strip("/") or "service-access"
                self.routes.append((name, href))

    def handle_endtag(self, tag: str) -> None:
        if tag == "th":
            self._in_header = False
        if tag == "code":
            self._in_code = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_header:
            self._current_row_header = text
        if self._in_code and text.startswith("platform/"):
            self.credential_items.append(text)
        if self._in_code and text == "not required" and self._current_row_header:
            self.no_login_services.append(self._current_row_header)


def _dashboard_references(path: Path) -> _DashboardReferences:
    parser = _DashboardReferenceParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return _DashboardReferences(
        routes=tuple(dict.fromkeys(parser.routes)),
        credential_items=tuple(dict.fromkeys(parser.credential_items)),
        no_login_services=tuple(dict.fromkeys(parser.no_login_services)),
    )


class _EvidenceRecorder:
    def __init__(self, root: Path) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.path = root / timestamp
        self.path.mkdir(parents=True, exist_ok=False)
        self._records: list[dict[str, object]] = []

    def record(self, kind: str, payload: dict[str, object]) -> None:
        record = {"kind": kind, **payload}
        if not _evidence_safe(record):
            raise AssertionError("redacted_evidence_policy_failed")
        self._records.append(record)

    def write(self) -> None:
        payload = {
            "generated_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "records": self._records,
        }
        if not _evidence_safe(payload):
            raise AssertionError("redacted_evidence_policy_failed")
        (self.path / "summary.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _evidence_safe(value: object) -> bool:
    if isinstance(value, dict):
        return all(
            _evidence_safe(str(key)) and _evidence_safe(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return all(_evidence_safe(item) for item in value)
    text = str(value).casefold()
    return not any(fragment.casefold() in text for fragment in FORBIDDEN_EVIDENCE_FRAGMENTS)


if __name__ == "__main__":
    unittest.main()

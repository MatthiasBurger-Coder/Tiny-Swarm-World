from __future__ import annotations

from typing import Any

from tiny_swarm_world.application.ports.clients.port_infisical_client import (
    PortInfisicalClient,
)


class PlaywrightInfisicalClient(PortInfisicalClient):
    def __init__(
        self,
        *,
        base_url: str = "https://localhost",
        timeout_seconds: float = 45.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def can_authenticate(self, email: str, password: str) -> bool:
        try:
            self._with_logged_in_page(email, password, lambda _page: None)
        except Exception:
            return False
        return True

    def secret_item_exists(self, email: str, password: str, item_name: str) -> bool:
        def check(page: Any) -> bool:
            try:
                page.get_by_text(item_name, exact=True).first.wait_for(timeout=5_000)
            except Exception:
                return False
            return True

        return bool(self._with_logged_in_page(email, password, check))

    def create_secret_item(
        self,
        email: str,
        password: str,
        item_name: str,
        username: str,
        secret_value: str,
    ) -> None:
        def create(page: Any) -> None:
            _click_first(page, ("Add Secret", "New Secret", "Create Secret"))
            _fill_first(page, ("Key", "Name"), item_name)
            _fill_first(page, ("Value", "Secret"), secret_value)
            _click_first(page, ("Save", "Create"))
            page.get_by_text(item_name, exact=True).first.wait_for(timeout=10_000)

        self._with_logged_in_page(email, password, create)

    def _with_logged_in_page(self, email: str, password: str, callback):
        try:
            from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Playwright is required for Infisical item seeding.") from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(ignore_https_errors=True, base_url=self.base_url)
            try:
                page.goto("/", wait_until="domcontentloaded", timeout=int(self.timeout_seconds * 1000))
                _fill_first(page, ("Email", "Email address"), email)
                _fill_first(page, ("Password",), password)
                _click_first(page, ("Log in", "Login", "Sign in"))
                page.get_by_text("Secrets", exact=False).first.wait_for(timeout=20_000)
                return callback(page)
            finally:
                browser.close()


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
        try:
            page.get_by_role("button", name=name, exact=False).first.click(timeout=5_000)
            return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"could not click button: {names}; last={type(last_error).__name__}")

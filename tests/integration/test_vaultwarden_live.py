"""Opt-in live integration test for Vaultwarden account and vault item flow.

This test intentionally starts a disposable Docker container. It is skipped by
normal quality gates and only runs when TSW_RUN_LIVE_VAULTWARDEN_INTEGRATION=1.
"""

from __future__ import annotations

import os
import secrets
import shutil
import subprocess
import tempfile
import time
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


RUN_LIVE_ENV = "TSW_RUN_LIVE_VAULTWARDEN_INTEGRATION"
DEFAULT_ENV_FILE = Path(".tiny-swarm-world/local/live-installation.env")


@dataclass(frozen=True)
class VaultwardenTestConfig:
    image: str
    host: str
    container_name: str
    signup_path: str
    timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "VaultwardenTestConfig":
        local_env = _load_shell_environment(Path(os.environ.get("TSW_LIVE_INSTALLATION_ENV", DEFAULT_ENV_FILE)))
        return cls(
            image=os.environ.get("TSW_VAULTWARDEN_IMAGE")
            or local_env.get("TSW_VAULTWARDEN_IMAGE")
            or "vaultwarden/server:latest",
            host="127.0.0.1",
            container_name=f"tsw-vaultwarden-it-{secrets.token_hex(6)}",
            signup_path=os.environ.get("TSW_VAULTWARDEN_SIGNUP_PATH", "/#/signup"),
            timeout_seconds=float(os.environ.get("TSW_VAULTWARDEN_IT_TIMEOUT", "90")),
        )


@unittest.skipUnless(
    os.environ.get(RUN_LIVE_ENV) == "1",
    f"set {RUN_LIVE_ENV}=1 to run the live Docker Vaultwarden integration test",
)
class VaultwardenLiveIntegrationTest(unittest.TestCase):
    """Verifies disposable Vaultwarden signup and password item visibility."""

    def test_signup_create_password_and_view_password(self) -> None:
        self._require_command("docker")
        self._require_playwright()
        config = VaultwardenTestConfig.from_environment()

        with tempfile.TemporaryDirectory(prefix="tsw-vaultwarden-it-") as data_dir:
            container = _VaultwardenContainer(config, Path(data_dir))
            workflow = _FailureWorkflow()
            try:
                workflow.step("create disposable Vaultwarden Docker container")
                base_url = container.start()

                workflow.step("wait for Vaultwarden HTTP readiness")
                _wait_for_http(base_url, timeout_seconds=config.timeout_seconds)

                workflow.step("create admin account through /signup")
                workflow.step("store password item in the authenticated web vault")
                workflow.step("open item again and verify the password is visible")
                _exercise_web_vault(base_url, config.signup_path)
            except Exception as exc:  # pragma: no cover - diagnostic path for live failures.
                raise AssertionError(workflow.render(exc)) from exc
            finally:
                container.stop()

    def _require_command(self, command: str) -> None:
        if shutil.which(command) is None:
            self.skipTest(f"required command not available: {command}")

    def _require_playwright(self) -> None:
        try:
            import playwright.sync_api  # type: ignore[import-not-found]  # noqa: F401
        except ImportError as exc:
            self.skipTest(
                "playwright is required for the browser-based /signup flow; "
                "install it outside the product dependency set and run `python -m playwright install chromium`"
            )
            raise exc


class _VaultwardenContainer:
    def __init__(self, config: VaultwardenTestConfig, data_dir: Path) -> None:
        self._config = config
        self._data_dir = data_dir
        self._base_url: str | None = None

    def start(self) -> str:
        subprocess.run(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                self._config.container_name,
                "--publish",
                f"{self._config.host}::80",
                "--env",
                "SIGNUPS_ALLOWED=true",
                "--env",
                "INVITATIONS_ALLOWED=true",
                "--env",
                "ROCKET_ADDRESS=0.0.0.0",
                "--volume",
                f"{self._data_dir.as_posix()}:/data",
                self._config.image,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        port = _docker_host_port(self._config.container_name)
        self._base_url = f"http://{self._config.host}:{port}"
        return self._base_url

    def stop(self) -> None:
        subprocess.run(
            ["docker", "rm", "--force", "--volumes", self._config.container_name],
            check=False,
            capture_output=True,
            text=True,
        )


def _docker_host_port(container_name: str) -> str:
    result = subprocess.run(
        ["docker", "port", container_name, "80/tcp"],
        check=True,
        capture_output=True,
        text=True,
    )
    endpoint = result.stdout.strip().splitlines()[0]
    return endpoint.rsplit(":", 1)[1]


def _wait_for_http(base_url: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(base_url, timeout=2) as response:
                if response.status < 500:
                    return
        except URLError as exc:
            last_error = exc
        except TimeoutError as exc:
            last_error = exc
        else:
            return
        time.sleep(1)
    if last_error is not None:
        raise RuntimeError(f"Vaultwarden did not become ready: {last_error}")
    raise RuntimeError("Vaultwarden did not become ready before timeout")


def _exercise_web_vault(base_url: str, signup_path: str) -> None:
    from playwright.sync_api import expect, sync_playwright  # type: ignore[import-not-found]

    email = f"admin-{secrets.token_hex(6)}@example.test"
    master_secret = f"TswMaster-{secrets.token_urlsafe(16)}1!"
    item_name = f"tsw-live-item-{secrets.token_hex(4)}"
    item_username = "service-admin"
    item_secret = f"TswSecret-{secrets.token_urlsafe(18)}1!"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(base_url=base_url)
        try:
            page.goto(signup_path, wait_until="networkidle")
            _fill_first(page, ("Name", "Your name"), "Tiny Swarm World Admin")
            _fill_first(page, ("Email", "Email address"), email)
            _fill_first(page, ("Master password", "Password"), master_secret)
            _fill_first(page, ("Re-type master password", "Confirm master password", "Confirm password"), master_secret)
            _click_first(page, ("Create account", "Submit"))

            page.goto("/#/login", wait_until="networkidle")
            _fill_first(page, ("Email", "Email address"), email)
            _fill_first(page, ("Master password", "Password"), master_secret)
            _click_first(page, ("Log in with master password", "Log in"))

            _click_first(page, ("New", "Add item", "New item"))
            _fill_first(page, ("Name",), item_name)
            _fill_first(page, ("Username",), item_username)
            _fill_first(page, ("Password",), item_secret)
            _click_first(page, ("Save",))

            page.get_by_text(item_name, exact=False).click(timeout=15_000)
            expect(page.get_by_text(item_username, exact=False)).to_be_visible(timeout=15_000)
            _reveal_password_if_hidden(page)
            expect(page.get_by_text(item_secret, exact=False)).to_be_visible(timeout=15_000)
        finally:
            browser.close()


def _fill_first(page: Any, labels: tuple[str, ...], value: str) -> None:
    last_error: Exception | None = None
    for label in labels:
        try:
            page.get_by_label(label, exact=False).fill(value, timeout=5_000)
            return
        except Exception as exc:  # Playwright selector fallback.
            last_error = exc
        try:
            page.get_by_placeholder(label, exact=False).fill(value, timeout=5_000)
            return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"could not fill any field matching {labels}: {last_error}")


def _click_first(page: Any, names: tuple[str, ...]) -> None:
    last_error: Exception | None = None
    for name in names:
        try:
            page.get_by_role("button", name=name, exact=False).click(timeout=10_000)
            return
        except Exception as exc:
            last_error = exc
        try:
            page.get_by_text(name, exact=False).click(timeout=10_000)
            return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"could not click any control matching {names}: {last_error}")


def _reveal_password_if_hidden(page: Any) -> None:
    for name in ("Show password", "View password", "Reveal password"):
        try:
            page.get_by_role("button", name=name, exact=False).click(timeout=2_000)
            return
        except Exception:
            continue


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


class _FailureWorkflow:
    def __init__(self) -> None:
        self._steps: list[str] = []

    def step(self, description: str) -> None:
        self._steps.append(description)

    def render(self, exc: Exception) -> str:
        completed = "\n".join(f"- {step}" for step in self._steps)
        return (
            "Vaultwarden live integration failed.\n\n"
            "Failure-derived workflow:\n"
            f"{completed}\n"
            "- inspect Docker container logs without exposing secrets\n"
            "- fix the first failing setup or browser step\n"
            "- rerun only this opt-in integration test\n\n"
            f"Original error: {type(exc).__name__}: {exc}"
        )


if __name__ == "__main__":
    unittest.main()

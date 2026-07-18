import importlib.util
import sys
import types
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "tiny_swarm_world"
    / "infrastructure"
    / "adapters"
    / "clients"
    / "infisical_playwright_client.py"
)


def _load_client_module():
    port_module = types.ModuleType(
        "tiny_swarm_world.application.ports.clients.port_infisical_client"
    )
    port_module.PortInfisicalClient = object
    sys.modules[port_module.__name__] = port_module
    spec = importlib.util.spec_from_file_location("infisical_playwright_client", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Infisical Playwright client module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_create_first_admin_if_required = _load_client_module()._create_first_admin_if_required


class TestInfisicalPlaywrightClient(unittest.TestCase):
    def test_create_first_admin_fills_setup_form_when_prompt_is_visible(self):
        page = _FakePage({"Create your first Super Admin Account", "Secrets"})

        _create_first_admin_if_required(
            page,
            "admin@tiny-swarm-world.local",
            "infisical-password",
        )

        self.assertEqual(
            page.filled,
            [
                ("First name", "Tiny"),
                ("Last name", "Swarm"),
                ("Email", "admin@tiny-swarm-world.local"),
                ("Password", "infisical-password"),
                ("Confirm password", "infisical-password"),
            ],
        )
        self.assertEqual(page.clicked, ["Continue"])

    def test_create_first_admin_skips_when_prompt_is_not_visible(self):
        page = _FakePage(set())

        _create_first_admin_if_required(
            page,
            "admin@tiny-swarm-world.local",
            "infisical-password",
        )

        self.assertEqual(page.filled, [])
        self.assertEqual(page.clicked, [])


class _FakePage:
    def __init__(self, visible_text: set[str]):
        self.visible_text = visible_text
        self.filled: list[tuple[str, str]] = []
        self.clicked: list[str] = []

    def get_by_text(self, text: str, exact: bool = False):
        return _FakeTextLocator(text in self.visible_text)

    def get_by_label(self, label: str, exact: bool = False):
        return _FakeFillLocator(self, label)

    def get_by_placeholder(self, label: str, exact: bool = False):
        return _FakeFillLocator(self, label)

    def get_by_role(self, role: str, name: str, exact: bool = False):
        return _FakeButtonLocator(self, name)


class _FakeTextLocator:
    def __init__(self, visible: bool):
        self.first = self
        self.visible = visible

    def wait_for(self, timeout: int) -> None:
        if not self.visible:
            raise RuntimeError("text not visible")


class _FakeFillLocator:
    def __init__(self, page: _FakePage, label: str):
        self.page = page
        self.label = label

    def fill(self, value: str, timeout: int) -> None:
        self.page.filled.append((self.label, value))


class _FakeButtonLocator:
    def __init__(self, page: _FakePage, name: str):
        self.first = self
        self.page = page
        self.name = name

    def click(self, timeout: int) -> None:
        self.page.clicked.append(self.name)


if __name__ == "__main__":
    unittest.main()

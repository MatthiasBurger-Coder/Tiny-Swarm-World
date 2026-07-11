import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = REPOSITORY_ROOT / "tools" / "windows" / "tws-wsl-bridge.ps1"
BRIDGE_GUIDE = REPOSITORY_ROOT / "tools" / "windows" / "README.windows-wsl-bridge.md"
NETWORK_GUIDE = REPOSITORY_ROOT / "documentation" / "system" / "network.adoc"


class TestWindowsWslBridgeAssets(unittest.TestCase):
    def test_bridge_script_exposes_read_only_prerequisite_action(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        self.assertIn(
            'ValidateSet("prerequisites", "install", "refresh", "verify", "status", "uninstall")',
            script,
        )
        self.assertIn('"prerequisites" {', script)
        self.assertIn("No bridge state was changed.", script)
        self.assertIn("function Get-BridgePrerequisiteResults", script)
        self.assertIn("function Assert-BridgePrerequisites", script)

    def test_install_and_refresh_gate_mutations_on_prerequisites(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        for action in ("install", "refresh"):
            with self.subTest(action=action):
                block = _switch_block(script, action)
                prerequisite_index = block.index("Assert-BridgePrerequisites")
                reconcile_index = block.index("Reconcile-PortProxy")
                self.assertLess(prerequisite_index, reconcile_index)

    def test_bridge_guides_document_reproducible_preparation(self):
        bridge_guide = BRIDGE_GUIDE.read_text(encoding="utf-8")
        network_guide = NETWORK_GUIDE.read_text(encoding="utf-8")

        for expected in (
            "-Action prerequisites",
            "-Action install",
            "systemd",
            "iphlpsvc",
            "Prepared-state contract",
            "infra/config/ports.yaml",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, bridge_guide)

        self.assertIn("-Action prerequisites", network_guide)
        self.assertIn("tools/windows/README.windows-wsl-bridge.md", network_guide)


def _switch_block(script: str, action: str) -> str:
    match = re.search(
        rf'^    "{re.escape(action)}" \{{(?P<body>.*?)^    \}}',
        script,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Missing PowerShell switch block for {action}")
    return match.group("body")


if __name__ == "__main__":
    unittest.main()

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = REPOSITORY_ROOT / "tools" / "windows" / "tws-wsl-bridge.ps1"
BRIDGE_GUIDE = REPOSITORY_ROOT / "tools" / "windows" / "README.windows-wsl-bridge.md"
BRIDGE_CONFIG = REPOSITORY_ROOT / "tools" / "windows" / "tws-wsl-bridge.config.json"
NETWORK_GUIDE = REPOSITORY_ROOT / "documentation" / "system" / "network.adoc"


class TestWindowsWslBridgeAssets(unittest.TestCase):
    def test_bridge_script_exposes_read_only_prerequisite_action(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        self.assertIn(
            'ValidateSet("prerequisites", "discover", "install", "reconcile", "refresh", "verify", "status", "uninstall")',
            script,
        )
        self.assertIn('"prerequisites" {', script)
        self.assertIn("No bridge state was changed.", script)
        self.assertIn("function Get-BridgePrerequisiteResults", script)
        self.assertIn("function Assert-BridgePrerequisites", script)

    def test_install_and_reconcile_gate_mutations_on_prerequisites(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        for action in ("install", "reconcile", "refresh"):
            with self.subTest(action=action):
                block = _switch_block(script, action)
                prerequisite_index = block.index("Assert-BridgePrerequisites")
                reconcile_index = block.index("Invoke-BridgeReconcile")
                self.assertLess(prerequisite_index, reconcile_index)

    def test_bridge_registers_periodic_discovery_reconcile_agent(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")
        config = BRIDGE_CONFIG.read_text(encoding="utf-8")
        install_block = _switch_block(script, "install")

        self.assertIn("function Get-BridgeDiscovery", script)
        self.assertIn("function Invoke-BridgeReconcile", script)
        self.assertIn("-Action reconcile", script)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn", script)
        self.assertIn("-RepetitionInterval", script)
        self.assertIn('contractVersion    = 2', script)
        self.assertIn('agentMode          = "scheduled-discovery"', script)
        self.assertLess(install_block.index("Register-BridgeTask"), install_block.index("Invoke-BridgeReconcile"))
        self.assertIn('"discoveryIntervalMinutes": 1', config)

    def test_resource_reconcile_paths_are_no_op_when_state_matches(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        for expected in (
            "Test-PortProxyMappingsReady",
            "PORTPROXY unchanged",
            "Test-FirewallRuleReady",
            "FIREWALL unchanged",
            "Test-HostsFileReady",
            "HOSTS unchanged",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, script)

    def test_reconcile_records_discovery_before_failing_on_remaining_drift(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")
        block = _function_block(script, "Invoke-BridgeReconcile")

        pending_state_index = block.index("reconcile_in_progress")
        mutation_index = block.index("Reconcile-PortProxy")
        discovery_index = block.index("Get-BridgeDiscovery")
        state_index = block.rindex("Write-StateFile")
        failure_index = block.index("if (-not $discovery.Ready)")
        self.assertLess(pending_state_index, mutation_index)
        self.assertLess(discovery_index, state_index)
        self.assertLess(state_index, failure_index)

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
            "scheduled discovery agent",
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


def _function_block(script: str, name: str) -> str:
    match = re.search(
        rf"^function {re.escape(name)} \{{(?P<body>.*?)^\}}",
        script,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Missing PowerShell function {name}")
    return match.group("body")


if __name__ == "__main__":
    unittest.main()

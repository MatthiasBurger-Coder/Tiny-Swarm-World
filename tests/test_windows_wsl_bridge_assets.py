import json
import os
import re
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = REPOSITORY_ROOT / "tools" / "windows" / "tws-wsl-bridge.ps1"
BRIDGE_SERVICE_RUNNER = REPOSITORY_ROOT / "tools" / "windows" / "tws-wsl-bridge-service.ps1"
BRIDGE_PESTER_TESTS = REPOSITORY_ROOT / "tests" / "windows" / "tws-wsl-bridge.Tests.ps1"
BRIDGE_GUIDE = REPOSITORY_ROOT / "tools" / "windows" / "README.windows-wsl-bridge.md"
BRIDGE_CONFIG = REPOSITORY_ROOT / "tools" / "windows" / "tws-wsl-bridge.config.json"
NETWORK_GUIDE = REPOSITORY_ROOT / "documentation" / "system" / "network.adoc"
INSTALLATION_GUIDE = REPOSITORY_ROOT / "documentation" / "user_guide" / "installation.adoc"
WINDOWS_POWERSHELL = Path(
    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
)


class TestWindowsWslBridgeAssets(unittest.TestCase):
    def test_bridge_script_exposes_read_only_prerequisite_action(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        self.assertIn(
            'ValidateSet("prerequisites", "inventory", "discover", "install", "reconcile", "refresh", "verify", "status", "uninstall")',
            script,
        )
        self.assertIn('"prerequisites" {', script)
        self.assertIn("No bridge state was changed.", script)
        self.assertIn("function Get-BridgePrerequisiteResults", script)
        self.assertIn("function Assert-BridgePrerequisites", script)

    def test_install_and_reconcile_gate_mutations_on_prerequisites(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        install_block = _switch_block(script, "install")
        self.assertLess(
            install_block.index("Assert-BridgePrerequisites"),
            install_block.index("Install-BridgeService"),
        )
        for action in ("reconcile", "refresh"):
            with self.subTest(action=action):
                block = _switch_block(script, action)
                prerequisite_index = block.index("Assert-BridgePrerequisites")
                reconcile_index = block.index("Invoke-BridgeReconcile")
                self.assertLess(prerequisite_index, reconcile_index)

    def test_bridge_registers_periodic_windows_service_agent(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")
        service_runner = BRIDGE_SERVICE_RUNNER.read_text(encoding="utf-8")
        config = BRIDGE_CONFIG.read_text(encoding="utf-8")
        definition_function = _function_block(script, "New-BridgeServiceDefinition")

        self.assertIn("function Get-BridgeDiscovery", script)
        self.assertIn("function Invoke-BridgeReconcile", script)
        self.assertIn("function Install-BridgeService", script)
        self.assertIn("function Test-BridgeServiceReady", script)
        self.assertIn("function Uninstall-BridgeService", script)
        self.assertIn("WinSW.NET461.exe", script)
        self.assertIn(
            '$WinSwSha256 = "B5066B7BBDFBA1293E5D15CDA3CAAEA88FBEAB35BD5B38C41C913D492AADFC4F"',
            script,
        )
        self.assertIn("<hidewindow>true</hidewindow>", script)
        self.assertIn("Get-Credential", script)
        self.assertIn("New-Service", script)
        self.assertIn("SeServiceLogonRight", script)
        self.assertIn("Test-BridgeServiceAccountMatchesCurrentIdentity", script)
        self.assertIn("SecurityIdentifier", script)
        self.assertIn('$normalizedAccount.StartsWith(".\\")', script)
        self.assertIn("Test-BridgeServicePathMatches", script)
        self.assertIn("Remove-BridgeServiceRegistration", script)
        self.assertIn("& sc.exe delete $ServiceName", script)
        self.assertIn("function Protect-BridgeServiceRoot", script)
        self.assertIn("[Environment+SpecialFolder]::CommonApplicationData", script)
        self.assertNotIn(
            'Join-Path $env:ProgramData "TinySwarmWorld\\WslBridge"',
            script,
        )
        self.assertIn("DeleteSubdirectoriesAndFiles", script)
        acl_function = _function_block(script, "Set-BridgeExactAcl")
        self.assertIn("Invoke-BridgeHandleAclHardening", acl_function)
        self.assertIn("FileFlagOpenReparsePoint", script)
        self.assertIn("SetSecurityInfo", script)
        self.assertNotIn("icacls.exe", script)
        self.assertIn("$InstalledBridgeScriptPath", script)
        self.assertIn("$InstalledServiceRunnerPath", script)
        self.assertIn("$InstalledConfigPath", script)
        self.assertIn("$InstalledPortRegistryPath", script)
        self.assertIn(
            "$escapedBridge = [Security.SecurityElement]::Escape($InstalledBridgeScriptPath)",
            definition_function,
        )
        self.assertIn(
            "$escapedRunner = [Security.SecurityElement]::Escape($InstalledServiceRunnerPath)",
            definition_function,
        )
        self.assertNotIn("Escape($PSCommandPath)", definition_function)
        self.assertIn("function Write-TextAtomically", script)
        self.assertIn('Global\\TinySwarmWorldWslBridgeReconcile', script)
        self.assertIn('Global\\TinySwarmWorldWslBridgeServiceUpdate', script)
        self.assertIn("function Get-FirewallRuleSnapshot", script)
        self.assertIn("function Get-ExactBridgeFirewallRules", script)
        self.assertIn("FiltersByRuleId", script)
        self.assertIn("Get-CimInstance -ClassName Win32_Service", script)
        self.assertNotIn("<password>", script)
        self.assertIn("while ($true)", service_runner)
        self.assertIn("-NoProfile", service_runner)
        self.assertIn("-NonInteractive", service_runner)
        self.assertIn("-Action refresh", service_runner)
        self.assertIn("-PortRegistryPath $PortRegistryPath", service_runner)
        self.assertNotIn("StateEvidencePath", service_runner)
        self.assertNotIn("StateEvidencePath", definition_function)
        self.assertNotIn(
            "StateEvidencePath",
            _function_block(script, "Write-StateFile"),
        )
        self.assertIn(
            "StateEvidencePath",
            _function_block(script, "Test-BridgeLegacyServiceDefinitionOwned"),
        )
        self.assertIn("$consecutiveFailures -ge 3", service_runner)
        self.assertLess(service_runner.index("while ($true)"), service_runner.index("Start-Sleep"))
        self.assertIn('contractVersion    = 2', script)
        self.assertIn("agentMode          = Get-BridgeAgentMode", script)
        self.assertIn("bundleId           = $bundleIdentity.BundleId", script)
        self.assertIn('"discoveryIntervalMinutes": 1', config)

    def test_service_upgrade_is_transactional_and_behavior_tested(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")
        tests = BRIDGE_PESTER_TESTS.read_text(encoding="utf-8")
        install_function = _function_block(script, "Install-BridgeService")

        for function_name in (
            "Get-BridgeServiceOwnership",
            "New-BridgeStagedPayload",
            "Test-BridgeStagedPayload",
            "Write-BridgeTransactionJournal",
            "Switch-BridgePayload",
            "Restore-BridgePayload",
            "Recover-BridgeInterruptedTransaction",
            "Wait-BridgeServiceHeartbeat",
        ):
            self.assertIn(f"function {function_name}", script)
        self.assertLess(
            install_function.index("Get-BridgeServiceOwnership"),
            install_function.index("Request-BridgeServiceCredential"),
        )
        self.assertLess(
            install_function.index("New-BridgeStagedPayload"),
            install_function.index("Stop-BridgeServiceChecked"),
        )
        self.assertLess(
            install_function.index("Stop-BridgeServiceChecked"),
            install_function.index("Switch-BridgePayload"),
        )
        self.assertIn("partial candidate move", tests)
        self.assertIn("ownership is a collision", tests)
        self.assertIn("credential dialog is cancelled", tests)
        self.assertIn("ACL hardening reports an error", tests)
        self.assertIn("bounded mutex timeout", tests)
        self.assertIn("three consecutive reconcile errors", tests)

    @unittest.skipUnless(
        os.name == "nt" or WINDOWS_POWERSHELL.exists(),
        "Windows PowerShell is unavailable on this Linux host.",
    )
    def test_windows_service_behavior_contract_with_pester(self):
        executable = "powershell.exe" if os.name == "nt" else str(WINDOWS_POWERSHELL)
        script_path = _as_windows_path(BRIDGE_PESTER_TESTS)
        command = _pester_command(script_path)

        completed = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-Command", command],
            cwd=REPOSITORY_ROOT,
            check=False,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)

    def test_service_is_the_only_new_agent_registration_path(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")

        self.assertIn('Name "service-management"', script)
        self.assertIn("Windows service management commands are available.", script)
        self.assertNotIn("function Register-BridgeTask", script)
        self.assertNotIn("function Repair-BridgeTaskAction", script)
        self.assertNotIn("New-ScheduledTaskAction", script)
        self.assertNotIn("tws-wsl-bridge-hidden.vbs", script)
        self.assertNotIn("function Test-BridgeTaskReady", script)
        self.assertIn("function Unregister-BridgeTask", script)

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

    def test_managed_hosts_block_writes_one_hostname_per_line(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")
        block = _function_block(script, "Get-ReconciledHostsContent")

        self.assertIn(
            '$hostNames | ForEach-Object { "$hostsAddress`t$_" }',
            block,
        )
        self.assertNotIn("$($hostNames -join ' ')", block)

    def test_windows_hosts_use_only_the_canonical_tsw_route_namespace(self):
        script = BRIDGE_SCRIPT.read_text(encoding="utf-8")
        config_text = BRIDGE_CONFIG.read_text(encoding="utf-8")
        guide = BRIDGE_GUIDE.read_text(encoding="utf-8")
        network_guide = NETWORK_GUIDE.read_text(encoding="utf-8")

        self.assertEqual(json.loads(config_text)["hostNames"], [])
        self.assertIn("Read-TswPortRegistry", script)
        self.assertIn("route_host", script)
        self.assertIn("*.tsw.local", guide)
        self.assertNotIn(".tws.local", script + config_text + guide + network_guide)

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
        installation_guide = INSTALLATION_GUIDE.read_text(encoding="utf-8")

        for expected in (
            "-Action prerequisites",
            "-Action install",
            "systemd",
            "iphlpsvc",
            "Prepared-state contract",
            "infra/config/ports.yaml",
            "Windows service",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, bridge_guide)

        self.assertIn("-Action prerequisites", network_guide)
        self.assertIn("tools/windows/README.windows-wsl-bridge.md", network_guide)
        for expected in (
            "Complete The Required Windows Prework For WSL2",
            "-Action prerequisites",
            "-Action install",
            "Get-Service -Name TinySwarmWorldWslBridge",
            "tws-wsl-bridge.config.json",
            "%ProgramData%\\TinySwarmWorld\\WslBridge",
            "TSW_WINDOWS_EXPOSURE=disabled",
        ):
            with self.subTest(installation_expected=expected):
                self.assertIn(expected, installation_guide)


class TestWslWindowsPathTranslation(unittest.TestCase):
    def test_mounted_drive_path_preserves_spaces_without_external_conversion(self):
        with patch("subprocess.run") as run:
            translated = _as_windows_path(Path("/mnt/d/test workspace/bridge.Tests.ps1"))

        self.assertEqual(translated, "D:\\test workspace\\bridge.Tests.ps1")
        run.assert_not_called()

    def test_linux_native_path_uses_bounded_wslpath_conversion(self):
        path = Path("/home/test user/bridge.Tests.ps1")
        converted = "\\\\wsl.localhost\\Ubuntu\\home\\test user\\bridge.Tests.ps1"
        with patch("subprocess.run", return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout=converted + "\n", stderr="",
        )) as run:
            translated = _as_windows_path(path)

        self.assertEqual(translated, converted)
        run.assert_called_once_with(
            ["wslpath", "-w", str(path.resolve())],
            check=True, capture_output=True, text=True, timeout=10,
        )

    def test_converter_failures_are_explicit_without_skipping(self):
        errors = (
            FileNotFoundError("wslpath is missing"),
            subprocess.CalledProcessError(1, ["wslpath"]),
            subprocess.TimeoutExpired(["wslpath"], 10),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with patch("subprocess.run", side_effect=error):
                    with self.assertRaisesRegex(AssertionError, "Cannot translate WSL path"):
                        _as_windows_path(Path("/home/test/bridge.Tests.ps1"))

    def test_converter_must_return_a_single_absolute_windows_path(self):
        for output in ("", "/home/test/bridge.Tests.ps1", "relative.ps1", "C:\\test.ps1\nextra"):
            with self.subTest(output=output):
                with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                    args=[], returncode=0, stdout=output, stderr="",
                )):
                    with self.assertRaisesRegex(AssertionError, "Cannot translate WSL path"):
                        _as_windows_path(Path("/home/test/bridge.Tests.ps1"))

    def test_pester_keeps_apostrophes_literal_and_failed_checks_nonzero(self):
        command = _pester_command("\\\\wsl.localhost\\Ubuntu\\home\\test user's folder\\bridge.Tests.ps1")

        self.assertIn("$testScript = '\\\\wsl.localhost\\Ubuntu\\home\\test user''s folder\\bridge.Tests.ps1'", command)
        self.assertIn("if ($result.FailedCount -ne 0 -or $result.PassedCount -eq 0) { exit 1 }", command)
        self.assertIn("[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding", command)
        self.assertIn("$testScript.StartsWith('\\\\')", command)
        self.assertIn("Copy-Item -LiteralPath", command)
        self.assertIn("} finally { if ($null -ne $stagingRoot)", command)
        self.assertIn("Remove-Item -LiteralPath $stagingRoot -Recurse -Force", command)
        self.assertNotIn("ExecutionPolicy", command)


def _switch_block(script: str, action: str) -> str:
    match = re.search(
        rf'^(?P<indent>[ \t]+)"{re.escape(action)}" \{{(?P<body>.*?)^(?P=indent)\}}',
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


def _as_windows_path(path: Path) -> str:
    if os.name == "nt":
        return str(path)
    parts = path.resolve().parts
    if len(parts) >= 4 and parts[1] == "mnt" and len(parts[2]) == 1:
        remainder = "\\".join(parts[3:])
        return f"{parts[2].upper()}:\\{remainder}"
    try:
        completed = subprocess.run(
            ["wslpath", "-w", str(path.resolve())],
            check=True, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        raise AssertionError(f"Cannot translate WSL path to Windows: {path}") from None
    translated = completed.stdout.strip()
    if "\n" in translated or "\r" in translated or not re.match(
        r"^(?:[A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)", translated,
    ):
        raise AssertionError(f"Cannot translate WSL path to Windows: {path}")
    return translated


def _pester_command(script_path: str) -> str:
    literal_path = script_path.replace("'", "''")
    return (
        "$ErrorActionPreference = 'Stop'; "
        "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding; "
        f"$testScript = '{literal_path}'; $stagingRoot = $null; "
        "try { "
        "if ($testScript.StartsWith('\\\\')) { "
        "$sourceRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $testScript)); "
        "$stagingRoot = Join-Path ([IO.Path]::GetTempPath()) ('tsw-pester-' + [guid]::NewGuid()); "
        "foreach ($directory in @('tests\\windows', 'tools\\windows', 'infra\\config')) { "
        "New-Item -ItemType Directory -Path (Join-Path $stagingRoot $directory) -Force | Out-Null }; "
        "foreach ($asset in @('tests\\windows\\tws-wsl-bridge.Tests.ps1', "
        "'tools\\windows\\tws-wsl-bridge.ps1', 'tools\\windows\\tws-wsl-bridge-service.ps1', "
        "'tools\\windows\\tws-wsl-bridge.config.json', 'infra\\config\\ports.yaml')) { "
        "Copy-Item -LiteralPath (Join-Path $sourceRoot $asset) -Destination (Join-Path $stagingRoot $asset) }; "
        "$testScript = Join-Path $stagingRoot 'tests\\windows\\tws-wsl-bridge.Tests.ps1' }; "
        "Import-Module Pester; "
        "$result = Invoke-Pester -Script $testScript -PassThru "
        "} finally { if ($null -ne $stagingRoot) { "
        "Remove-Item -LiteralPath $stagingRoot -Recurse -Force } }; "
        "if ($result.FailedCount -ne 0 -or $result.PassedCount -eq 0) { exit 1 }"
    )


if __name__ == "__main__":
    unittest.main()

"""Execute the exact production firewall query with fake NetSecurity cmdlets."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import unittest

from tests.test_prepare_windows import _powershell, _runtime_path
from tools.linux.qualification import incus_profile_listener_fixture as listener_fixture

ROOT = Path(__file__).resolve().parents[2]


class WslFirewallSnapshotTests(unittest.TestCase):
    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_shared_producer_is_exactly_equal_complete_fresh_and_bounded_on_both_consumers(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_firewall_snapshot.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable), "-CertificateContract"],
            check=False, capture_output=True, timeout=150,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="backslashreplace"))
        self.assertEqual(result.stderr, b"")
        report = json.loads(result.stdout.decode("utf-8", errors="strict"))
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 17)
        self.assertEqual(report["command_sha256"], hashlib.sha256(listener_fixture._windows_snapshot_wrapper().encode()).hexdigest())
        self.assertEqual(report["fresh_large_observations"], 8)
        self.assertGreater(report["full_windows_ram_bytes"], 64 * 1024 * 1024)
        self.assertLess(report["transport_bytes"], 32768)
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertFalse(report["live_capability_claim"])

    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_complete_snapshot_properties_failure_bounds_and_constant_calls(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_firewall_snapshot.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            check=False, capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="backslashreplace"))
        self.assertEqual(result.stderr, b"")
        report = json.loads(result.stdout.decode("utf-8", errors="strict"))
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 30)
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertFalse(report["live_capability_claim"])
        self.assertTrue(report["provider_calls_independent_of_rule_count"])

    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_real_child_unicode_snapshot_stdout_is_strict_utf8(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_firewall_snapshot.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable), "-EmitUnicodeSnapshot"],
            check=False, capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, f"Unicode child exit {result.returncode}")
        self.assertEqual(result.stderr, b"")
        text = result.stdout.decode("utf-8", errors="strict")
        self.assertNotIn("\ufffd", text)
        marker, payload = text.split("\n", 1)
        self.assertEqual(marker.rstrip("\r"), "\u00fc\u2603\u4e2d")
        value = json.loads(payload)
        self.assertEqual(value["filters"]["address"][0]["value"]["ForeignProperty"], "\u00fc\u2603\u4e2d")
        self.assertEqual(value["store"], "ActiveStore")

    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_real_cim_data_flags_alias_equivalence_and_identity_without_host_queries(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_firewall_snapshot.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable), "-NativeCimContract"],
            check=False, capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="backslashreplace"))
        self.assertEqual(result.stderr, b"")
        report = json.loads(result.stdout.decode("utf-8", errors="strict"))
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 20)
        self.assertTrue(report["genuine_cim_in_memory"])
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertFalse(report["live_capability_claim"])

    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_real_cim_exact_installed_dynamic_target_conversion_retains_native_data(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_firewall_snapshot.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable), "-DynamicTargetContract"],
            check=False, capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="backslashreplace"))
        self.assertEqual(result.stderr, b"")
        report = json.loads(result.stdout.decode("utf-8", errors="strict"))
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 13)
        self.assertTrue(report["genuine_cim_in_memory"])
        self.assertTrue(report["installed_getter_source_bound"])
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertFalse(report["live_capability_claim"])

    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_shared_source_getter_requires_exact_fixed_bounded_asset(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_firewall_snapshot.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable), "-SourceGuardContract"],
            check=False, capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="backslashreplace"))
        self.assertEqual(result.stderr, b"")
        report = json.loads(result.stdout.decode("utf-8", errors="strict"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["cases"], 5)
        self.assertTrue(report["fixed_source_hash_bound"])
        self.assertEqual(report["runtime_mutations"], 0)

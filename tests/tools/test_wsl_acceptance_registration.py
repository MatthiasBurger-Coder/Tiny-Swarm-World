"""Run the bounded registration state machine with fake Windows/WSL ports."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

from tests.test_prepare_windows import _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[2]


class WslAcceptanceRegistrationTests(unittest.TestCase):
    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_real_certificate_consumer_is_fresh_complete_bound_and_preserves_changed_hashes(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_acceptance_registration.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable), "-CertificateTransportContract"],
            check=False, capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="backslashreplace"))
        self.assertEqual(result.stderr, b"")
        report = json.loads(result.stdout.decode("utf-8", errors="strict"))
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 5)
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertEqual(report["provider_queries"], 0)
        self.assertFalse(report["live_capability_claim"])

    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_import_is_write_ahead_nonreplayable_and_preserves_originals(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_acceptance_registration.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            capture_output=True, text=True, check=False, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 35)
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertFalse(report["actual_import"])
        self.assertFalse(report["originals_touched"])
        self.assertFalse(report["services_verified"])

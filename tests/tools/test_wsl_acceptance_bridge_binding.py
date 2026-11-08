"""Bridge phase contracts and actual payload primitives; no live host effects."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

from tests.test_prepare_windows import _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[2]


class WslAcceptanceBridgeBindingTests(unittest.TestCase):
    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_phase_go_cas_and_actual_payload_rollback_preserve_original_archive(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_acceptance_bridge_binding.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            check=False, capture_output=True, text=True, timeout=90,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 55)
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertTrue(report["real_payload_primitives"])
        self.assertFalse(report["live_capability_claim"])

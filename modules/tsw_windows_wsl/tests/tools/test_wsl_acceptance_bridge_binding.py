"""Bridge phase contracts and actual payload primitives; no live host effects."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

from modules.tsw_windows_wsl.tests.test_prepare_windows import _windows_powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[4]


class WslAcceptanceBridgeBindingTests(unittest.TestCase):
    @unittest.skipUnless(_windows_powershell(), "Windows CIM/Win32 contract requires the Windows/WSL test host")
    def test_phase_go_cas_and_actual_payload_rollback_preserve_original_archive(self) -> None:
        executable = _windows_powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "modules/tsw_core/tests/fixtures/wsl_acceptance_bridge_binding.ps1", executable),
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

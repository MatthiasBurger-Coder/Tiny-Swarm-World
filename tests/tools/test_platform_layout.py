"""Verify execution and source-proof wiring after the tools directory migration."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.windows.build_windows_preparation_manifest import ASSETS


ROOT = Path(__file__).resolve().parents[2]


class PlatformLayoutTests(unittest.TestCase):
    def test_quality_entrypoint_runs_relocated_checker_in_isolated_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            for relative in (
                "tools/linux/quality_gate.py",
                "tools/linux/check_verification_policy_consistency.py",
                "documentation/process/verification-state-policy.md",
            ):
                target = checkout / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)

            result = subprocess.run(
                [sys.executable, "tools/linux/quality_gate.py", "verification-policy"],
                cwd=checkout,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_windows_handoff_and_release_proof_cover_same_relocated_assets(self):
        adapter = (ROOT / "bootstrap/windows/preparation/Adapters.ps1").read_text()
        asset_list = re.search(r"\$assets=@\(([^\n]+)\)", adapter)
        self.assertIsNotNone(asset_list)
        assert asset_list is not None
        self.assertEqual(set(re.findall(r"'([^']+)'", asset_list[1])), set(ASSETS))

        entrypoint = (ROOT / "bootstrap/windows/prepare_windows.ps1").read_text()
        required_list = entrypoint.split("$requiredAssets=@(", 1)[1].split(")", 1)[0]
        required_assets = set(re.findall(r"'([^']+)'", required_list))
        self.assertTrue(required_assets.issubset(ASSETS))
        self.assertIn("bootstrap/windows/preparation/linux-handoff.sh", required_assets)
        for relative in ASSETS:
            with self.subTest(asset=relative):
                self.assertTrue((ROOT / relative).is_file())

"""Guided entrypoint contracts use mocked ports, never a live WSL target."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from modules.tsw_windows_wsl.tests.test_prepare_windows import (
    ROOT,
    _powershell,
    _runtime_path,
)


@unittest.skipUnless(_powershell(), "PowerShell runtime unavailable.")
class GuidedWslSetupTests(unittest.TestCase):
    def test_guided_stages_with_mocked_ports(self) -> None:
        executable = _powershell()
        assert executable is not None
        completed = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", _runtime_path(ROOT / "modules/tsw_windows_wsl/tests/windows/setup-wsl.Tests.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            check=False, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS:", completed.stdout)

    def test_static_help_and_invalid_modes(self) -> None:
        executable = _powershell()
        assert executable is not None
        for arguments, expected in (
            (["-Help", "-Json"], 0),
            (["-Help", "-Preflight", "-Json"], 2),
            (["-DryRun", "-Resume", "-Json"], 2),
            (["-Profile", "classic", "-Json"], 2),
            (["-UnknownOption", "-Json"], 2),
        ):
            with self.subTest(arguments=arguments):
                with tempfile.TemporaryDirectory(prefix="tsw-static-help-") as directory:
                    entrypoint = Path(directory) / "setup_wsl.ps1"
                    shutil.copy2(ROOT / "setup_wsl.ps1", entrypoint)
                    completed = subprocess.run(
                        [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                         "-File", _runtime_path(entrypoint, executable), *arguments],
                        check=False, text=True, capture_output=True, timeout=15,
                    )
                    self.assertEqual(list(Path(directory).iterdir()), [entrypoint])
                self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
                envelope = json.loads(completed.stdout)
                self.assertEqual(envelope["result"]["exit_code"], expected)

"""Run the Windows controller contract against mocked host effects only."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.test_prepare_windows import WINDOWS_POWERSHELL, _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[2]


class WslResourceMaintenanceTests(unittest.TestCase):
    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_controller_preserves_boundaries_and_recovers_each_effect_failure(self) -> None:
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_resource_maintenance.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            check=False, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 23)
        self.assertEqual(report["runtime_mutations"], 0)
        self.assertFalse(report["live_capability_claim"])

    @unittest.skipUnless(os.name == "posix" and WINDOWS_POWERSHELL.exists(),
                         "Production adapter contracts require the approved Windows interop runtime")
    def test_real_adapter_routes_cas_and_foreign_families_with_mocked_host_io(self) -> None:
        executable = str(WINDOWS_POWERSHELL)
        query = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-Command", "[IO.Path]::GetTempPath()"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        converted = subprocess.run(["wslpath", "-u", query.stdout.strip()], check=True,
                                   capture_output=True, text=True, timeout=10)
        with tempfile.TemporaryDirectory(prefix="epic440-controller-contract-",
                                         dir=converted.stdout.strip()) as directory:
            root = Path(directory) / "native"
            # The production guard observes the real Windows actor as owner.
            native_root = _runtime_path(root, executable).replace("'", "''")
            native_source = _runtime_path(ROOT, executable).replace("'", "''")
            prepare = (
                "$ErrorActionPreference='Stop';"
                f"$root='{native_root}';$source='{native_source}';"
                "[IO.Directory]::CreateDirectory($root) | Out-Null;"
                "[IO.Directory]::CreateDirectory((Join-Path $root '.git')) | Out-Null;"
                "[IO.Directory]::CreateDirectory((Join-Path $root 'infra/config')) | Out-Null;"
                "$actor=[Security.Principal.WindowsIdentity]::GetCurrent().User;"
                "foreach($path in @($root,(Join-Path $root '.git'))){"
                "$acl=Get-Acl -LiteralPath $path;$acl.SetOwner($actor);"
                "Set-Acl -LiteralPath $path -AclObject $acl};"
                "Copy-Item -LiteralPath (Join-Path $source 'bootstrap') "
                "-Destination (Join-Path $root 'bootstrap') -Recurse;"
                "Copy-Item -LiteralPath (Join-Path $source 'infra/config/ports.yaml') "
                "-Destination (Join-Path $root 'infra/config/ports.yaml')"
            )
            subprocess.run(
                [executable, "-NoProfile", "-NonInteractive", "-EncodedCommand",
                 base64.b64encode(prepare.encode("utf-16-le")).decode("ascii")],
                check=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            result = subprocess.run(
                [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                 _runtime_path(ROOT / "tests/fixtures/wsl_resource_maintenance.ps1", executable),
                 "-RepositoryRoot", _runtime_path(ROOT, executable),
                 "-NativeFixtureRoot", _runtime_path(root, executable)],
                check=False, capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertGreaterEqual(report["cases"], 31)
            self.assertEqual(report["runtime_mutations"], 0)

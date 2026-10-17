"""Run mocked certificate-store behavior under the Windows PowerShell runtime."""
import os
import subprocess
import unittest

from tests.powershell_test_runtime import powershell_command
from tests.test_windows_wsl_bridge_assets import REPOSITORY_ROOT, WINDOWS_POWERSHELL, _as_windows_path


class TestWindowsTlsTrust(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt" or WINDOWS_POWERSHELL.exists(), "Windows PowerShell unavailable")
    def test_mocked_trust_behavior_with_pester(self):
        root = _as_windows_path(REPOSITORY_ROOT).replace("'", "''")
        command = (
            "$ErrorActionPreference='Stop'; "
            "$stage=Join-Path ([IO.Path]::GetTempPath()) ('tsw-trust-tests-'+[guid]::NewGuid()); "
            "try { foreach ($dir in @('tools/windows','tests/windows')) { "
            "New-Item -ItemType Directory -Path (Join-Path $stage $dir) -Force | Out-Null }; "
            "foreach ($file in @('tools/windows/tsw-tls-trust.ps1','tests/windows/tsw-tls-trust.Tests.ps1')) { "
            f"Copy-Item -LiteralPath (Join-Path '{root}' $file) -Destination (Join-Path $stage $file) }}; "
            "Import-Module Pester; $result=Invoke-Pester -Script (Join-Path $stage 'tests/windows/tsw-tls-trust.Tests.ps1') -PassThru; "
            "if ($result.FailedCount -ne 0 -or $result.PassedCount -eq 0) { exit 1 } "
            "} finally { Remove-Item -LiteralPath $stage -Recurse -Force }"
        )
        executable = "powershell.exe" if os.name == "nt" else str(WINDOWS_POWERSHELL)
        completed = subprocess.run(powershell_command(executable, command), cwd=REPOSITORY_ROOT,
                                   text=True, encoding="utf-8", stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, timeout=90, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout)

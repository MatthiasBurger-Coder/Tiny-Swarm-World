"""Run the Windows controller contract against mocked host effects only."""
from __future__ import annotations

import base64
from contextlib import redirect_stdout
import io
import re
import selectors
import stat
import sys
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
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
                "Copy-Item -LiteralPath (Join-Path $source 'modules/tsw_core/infra/config/ports.yaml') "
                "-Destination (Join-Path $root 'modules/tsw_core/infra/config/ports.yaml')"
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
            self.assertGreaterEqual(report["cases"], 34)
            self.assertEqual(report["runtime_mutations"], 0)


class WslMaintenanceLifetimeProtocolTests(unittest.TestCase):
    """Execute the fixed Linux child with actual pipes; no WSL/provider effects."""

    def program(self, name: str) -> str:
        text = (ROOT / "modules/tsw_windows_wsl/tools/windows/qualification/wsl_resource_maintenance.ps1").read_text()
        match = re.search(r"function " + re.escape(name) + r" \{.*?return @'\n(.*?)\n'@", text, re.S)
        self.assertIsNotNone(match)
        assert match is not None
        return match[1]

    @staticmethod
    def finish(process: subprocess.Popen[bytes]) -> None:
        if process.stdin is not None:
            process.stdin.close()
            process.stdin = None
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=2)

    def lease(self, seconds: int) -> subprocess.Popen[bytes]:
        process = subprocess.Popen([sys.executable, "-I", "-S", "-c",
                                    self.program("Get-WslMaintenanceLeaseProgram"), str(seconds)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.finish, process)
        assert process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            self.assertTrue(selector.select(3), "fixed child never acknowledged READY")
        self.assertEqual(process.stdout.readline(), b"READY\n")
        return process

    def test_real_child_eof_acknowledges_exit_without_input_payload(self) -> None:
        process = self.lease(3)
        self.assertIsNone(process.poll())
        output, error = process.communicate(b"", timeout=3)
        self.assertEqual((process.returncode, output, error), (0, b"CLOSED\n", b""))

    def test_real_child_refuses_any_input_and_never_claims_closed(self) -> None:
        process = self.lease(3)
        output, error = process.communicate(b"x", timeout=3)
        self.assertEqual((process.returncode, output, error), (4, b"", b""))

    def test_real_child_expiry_is_finite_nonzero_and_cleanup_closes_pipes(self) -> None:
        started = time.monotonic()
        process = self.lease(1)
        self.assertEqual(process.wait(timeout=3), 3)
        self.assertGreaterEqual(time.monotonic() - started, 0.8)
        output, error = process.communicate(b"", timeout=2)
        self.assertEqual((output, error), (b"", b""))

    def test_real_child_rejects_zero_negative_and_overbound_durations(self) -> None:
        code = self.program("Get-WslMaintenanceLeaseProgram")
        for seconds in (0, -1, 4801):
            with self.subTest(seconds=seconds):
                result = subprocess.run([sys.executable, "-I", "-S", "-c", code, str(seconds)],
                                        input=b"", capture_output=True, timeout=3)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (4, b"", b""))

    def test_ready_probe_keeps_activating_transient_and_denies_unknown_unit(self) -> None:
        code = compile(self.program("Get-WslMaintenanceReadyProgram"), "fixed-ready-probe", "exec")
        for active, substate, http_status, expected in (("activating", "start-post", 503, "WAIT"),
                                                         ("active", "running", 200, "READY"),
                                                         ("active", "running", 503, "WAIT"),
                                                         ("active", "running", 403, "REFUSE"),
                                                         ("failed", "failed", 503, "REFUSE"),
                                                         ("active", "unknown", 200, "REFUSE")):
            with self.subTest(active=active, substate=substate):
                raw = f"LoadState=loaded\nActiveState={active}\nSubState={substate}\nMainPID=123\n".encode()
                response = MagicMock()
                response.status = http_status
                response.read.return_value = b"{}"
                client = MagicMock()
                client.getresponse.return_value = response
                output = io.StringIO()
                with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=raw, stderr=b"")), \
                     patch("socket.socket"), patch("http.client.HTTPConnection", return_value=client), \
                     patch("os.path.exists", side_effect=lambda path: path == "/var/lib/incus/unix.socket"), \
                     patch("os.path.realpath", side_effect=lambda path: path), \
                     patch("os.stat", return_value=SimpleNamespace(st_mode=stat.S_IFSOCK)), redirect_stdout(output):
                    if expected == "REFUSE":
                        with self.assertRaises(SystemExit) as caught:
                            exec(code, {})
                        self.assertEqual(caught.exception.code, 4)
                    else:
                        exec(code, {})
                        self.assertEqual(output.getvalue().strip(), expected)

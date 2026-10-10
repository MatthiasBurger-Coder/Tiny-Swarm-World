"""Execute Windows preparation contracts with mocked ports, never live actions."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_POWERSHELL = Path(
    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
)


def _powershell() -> str | None:
    """Use a local runtime for deterministic PowerShell tests only."""
    candidate = shutil.which("pwsh") or shutil.which("powershell.exe")
    if candidate:
        return candidate
    return str(WINDOWS_POWERSHELL) if WINDOWS_POWERSHELL.exists() else None


def _runtime_path(path: Path, executable: str) -> str:
    if os.name != "nt" and executable.lower().endswith(".exe"):
        translated = subprocess.run(
            ["wslpath", "-w", str(path)],
            check=True,
            text=True,
            capture_output=True,
            timeout=10,
        )
        return translated.stdout.strip()
    return str(path)


class TestWindowsPreparation(unittest.TestCase):
    @unittest.skipUnless(
        os.name == "nt" or WINDOWS_POWERSHELL.exists(),
        "Windows PowerShell native bridge behavior unavailable.",
    )
    def test_read_only_bridge_inventory_and_existing_address_owner(self) -> None:
        executable = "powershell.exe" if os.name == "nt" else str(WINDOWS_POWERSHELL)
        completed = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/windows/bridge-preparation.Tests.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            check=False, text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS", completed.stdout)

    @unittest.skipUnless(
        _powershell(),
        "PowerShell runtime unavailable: W04 core behavior remains unverified.",
    )
    def test_mocked_pre_linux_lifecycle_and_preservation_contract(self) -> None:
        executable = _powershell()
        assert executable is not None
        completed = subprocess.run(
            [
                executable,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                _runtime_path(
                    ROOT / "tests" / "windows" / "prepare-windows.Tests.ps1",
                    executable,
                ),
                "-RepositoryRoot",
                _runtime_path(ROOT, executable),
            ],
            cwd=ROOT,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        self.assertEqual(
            completed.returncode, 0, completed.stdout + completed.stderr
        )
        self.assertIn("PASS", completed.stdout)


    @unittest.skipUnless(_powershell(), "PowerShell entrypoint remains unverified.")
    def test_help_and_invalid_cli_modes_emit_single_json_without_host_probes(self) -> None:
        executable = _powershell()
        assert executable is not None
        cases = (
            (["-Help", "-Json"], 0),
            (["-Help", "-Preflight", "-Json"], 2),
            (["-Preflight", "-DryRun", "-Json"], 2),
            (["-Preflight", "-ApproveApply", "-Json"], 2),
            (["-Preflight", "-Json"], 2),
        )
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                completed = subprocess.run(
                    [
                        executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                        _runtime_path(ROOT / "prepare_windows.ps1", executable),
                        *arguments,
                    ],
                    check=False,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=15,
                )
                self.assertEqual(
                    completed.returncode, expected, completed.stdout + completed.stderr
                )
                envelope = json.loads(completed.stdout)
                self.assertEqual(envelope["result"]["exit_code"], expected)
                self.assertEqual(
                    envelope["result"]["status"], "HELP" if expected == 0 else "BLOCKED"
                )
                self.assertFalse(envelope["result"]["preparation_ready"])
                self.assertFalse(envelope["result"]["services_verified"])


@unittest.skipUnless(os.name == "posix", "Linux helper requires a POSIX test runtime.")
class TestWindowsLinuxConfiguration(unittest.TestCase):
    """Exercise the real helper in a disposable filesystem, without root."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="tsw-w04-", dir="/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.sandbox = Path(self.temporary.name)
        (self.sandbox / "os-release").write_text('ID=ubuntu\nVERSION_ID="24.04"\n')
        self.config = self.sandbox / "wsl.conf"

    def _run(
        self, mode: str, expected: str = "", metadata: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        helper = ROOT / "tools/windows/preparation/linux-config.sh"
        script = helper.read_text()
        # Map only privileged paths/identity to this account's disposable fixture.
        # Configuration parsing, safety predicates and CAS/merge logic stay intact.
        identity = f"{os.getuid()}:{os.getgid()}"
        script = script.replace("/etc/", f"{self.sandbox}/")
        script = script.replace("0:0", identity).replace(
            "chown 0:0", f"chown {identity}"
        )
        self.assertNotIn("/etc/", script)
        if metadata is None:
            metadata = (
                f"{identity}:{self.config.stat().st_mode & 0o777:o}"
                if self.config.exists() else "absent"
            )
        return subprocess.run(
            ["sh", "-s", "--", mode, expected, metadata],
            input=script,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )

    def _hash(self) -> str:
        return hashlib.sha256(self.config.read_bytes()).hexdigest()

    def test_read_only_inspection_creates_no_files_and_does_not_source_os_release(self) -> None:
        marker = self.sandbox / "executed"
        (self.sandbox / "os-release").write_text(
            f'ID=ubuntu\nVERSION_ID="24.04"\nEVIL=$(touch {marker})\n'
        )
        before = {path.name: path.read_bytes() for path in self.sandbox.iterdir()}
        result = self._run("inspect")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("linux_id=ubuntu", result.stdout)
        self.assertEqual(
            {path.name: path.read_bytes() for path in self.sandbox.iterdir()}, before
        )
        self.assertFalse(marker.exists())

    def test_merge_preserves_unrelated_settings_and_original_permissions(self) -> None:
        self.config.write_text(
            "# retained\n[automount]\noptions=metadata\n[boot]\ncommand=echo hello\n"
            "systemd=false\n[user]\ndefault=operator\n"
        )
        self.config.chmod(0o640)
        result = self._run("apply", self._hash())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.config.read_text(),
            "# retained\n[automount]\noptions=metadata\n[boot]\ncommand=echo hello\n"
            "systemd=true\n[user]\ndefault=operator\n",
        )
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o640)
        self.assertFalse((self.sandbox / ".tsw-wsl-conf.lock").exists())

    def test_duplicate_boot_key_and_stale_configuration_are_preserved(self) -> None:
        original = "[boot]\nsystemd=false\nsystemd=true\n"
        self.config.write_text(original)
        self.config.chmod(0o644)
        self.assertNotEqual(self._run("apply", self._hash()).returncode, 0)
        self.assertEqual(self.config.read_text(), original)
        self.config.write_text("[automount]\noptions=metadata\n")
        self.assertNotEqual(self._run("apply", "stale").returncode, 0)
        self.assertEqual(self.config.read_text(), "[automount]\noptions=metadata\n")

    def test_symlink_config_and_preexisting_lock_cannot_damage_targets(self) -> None:
        target = self.sandbox / "unrelated"
        target.write_text("preserve me")
        self.config.symlink_to(target)
        self.assertNotEqual(self._run("apply", self._hash()).returncode, 0)
        self.assertEqual(target.read_text(), "preserve me")
        self.config.unlink()
        self.config.write_text("[boot]\nsystemd=false\n")
        self.config.chmod(0o644)
        (self.sandbox / ".tsw-wsl-conf.lock").symlink_to(target)
        self.assertNotEqual(self._run("apply", self._hash()).returncode, 0)
        self.assertEqual(target.read_text(), "preserve me")
        self.assertEqual(self.config.read_text(), "[boot]\nsystemd=false\n")

    def test_absent_config_creation_and_mixed_case_key_merge(self) -> None:
        created = self._run("apply", "absent")
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertEqual(self.config.read_text(), "[boot]\nsystemd=true\n")
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o644)
        self.config.write_text("[boot]\nSystemd=false\n[automount]\nenabled=true\n")
        merged = self._run("apply", self._hash())
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(
            self.config.read_text(), "[boot]\nsystemd=true\n[automount]\nenabled=true\n"
        )

    def test_approved_metadata_drift_blocks_even_when_bytes_match(self) -> None:
        self.config.write_text("[boot]\nsystemd=false\n")
        self.config.chmod(0o644)
        identity = f"{os.getuid()}:{os.getgid()}"
        old_hash = self._hash()
        self.config.chmod(0o600)
        result = self._run("apply", old_hash, f"{identity}:644")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config.read_text(), "[boot]\nsystemd=false\n")
        self.assertFalse((self.sandbox / ".tsw-wsl-conf.lock").exists())

    def test_non_ubuntu_identity_blocks_before_configuration_changes(self) -> None:
        (self.sandbox / "os-release").write_text('ID=debian\nVERSION_ID="24.04"\n')
        self.assertNotEqual(self._run("inspect").returncode, 0)
        self.assertFalse(self.config.exists())


if __name__ == "__main__":
    unittest.main()

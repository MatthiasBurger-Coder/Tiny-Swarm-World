import hashlib
import os
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe


class TestHostPreflightProbe(unittest.TestCase):
    def test_secret_available_uses_environment_without_reading_values(self):
        probe = HostPreflightProbe(Path.cwd())

        with patch.dict(os.environ, {"TSW_TEST_SECRET": "secret-value"}):
            self.assertTrue(probe.secret_available("TSW_TEST_SECRET"))

        self.assertFalse(probe.secret_available("TSW_TEST_SECRET"))

    def test_port_available_reports_occupied_loopback_port(self):
        probe = HostPreflightProbe(Path.cwd())
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            occupied_port = listener.getsockname()[1]

            self.assertFalse(probe.port_available(occupied_port))

        self.assertTrue(probe.port_available(occupied_port))

    def test_path_ignored_by_git_uses_check_ignore(self):
        probe = HostPreflightProbe(Path.cwd())
        completed = subprocess.CompletedProcess(
            args=["git", "check-ignore"],
            returncode=0,
        )

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.subprocess.run",
            return_value=completed,
        ) as run:
            self.assertTrue(probe.path_ignored_by_git(".env"))

        run.assert_called_once_with(
            ["git", "check-ignore", "-q", "--", ".env"],
            cwd=Path.cwd(),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_forbidden_tracked_secret_fingerprints_scan_git_tracked_files(self):
        token = "synthetic-test-token"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_file = root / "src" / "example.py"
            source_file.parent.mkdir()
            source_file.write_text(f"TOKEN = '{token}'\n", encoding="utf-8")
            probe = HostPreflightProbe(root)
            completed = subprocess.CompletedProcess(
                args=["git", "ls-files"],
                returncode=0,
                stdout="src/example.py\n",
            )

            with patch(
                "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.subprocess.run",
                return_value=completed,
            ):
                found = probe.forbidden_tracked_secret_fingerprints(
                    {
                        "example-default-token": hashlib.sha256(
                            token.encode("utf-8")
                        ).hexdigest()
                    }
                )

        self.assertEqual(("example-default-token",), tuple(found))

    def test_tracked_file_scan_ignores_paths_outside_repository_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outside_file = root.parent / "outside.py"
            outside_file.write_text("TOKEN = 'outside-token'\n", encoding="utf-8")
            probe = HostPreflightProbe(root)
            completed = subprocess.CompletedProcess(
                args=["git", "ls-files"],
                returncode=0,
                stdout="../outside.py\n",
            )

            with patch(
                "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.subprocess.run",
                return_value=completed,
            ):
                found = probe.forbidden_tracked_secret_fingerprints(
                    {
                        "outside-token": hashlib.sha256(
                            b"outside-token"
                        ).hexdigest()
                    }
                )

            outside_file.unlink()

        self.assertEqual((), tuple(found))

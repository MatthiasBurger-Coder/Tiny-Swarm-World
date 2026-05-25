import hashlib
import io
import os
import socket
import subprocess
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tiny_swarm_world.infrastructure.adapters.preflight import (
    HostPreflightProbe,
    ensure_common_executable_paths,
)


class TestHostPreflightProbe(unittest.TestCase):
    def test_executable_available_uses_existing_path_entries(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            executable = Path(temporary_directory) / "tool"
            executable.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
            executable.chmod(0o755)
            probe = HostPreflightProbe(
                Path.cwd(),
                executable_fallback_directories=(),
            )

            with patch.dict(os.environ, {"PATH": temporary_directory}):
                self.assertTrue(probe.executable_available("tool"))

    def test_executable_available_uses_wsl_snap_fallback_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fallback_directory = Path(temporary_directory) / "snap" / "bin"
            fallback_directory.mkdir(parents=True)
            executable = fallback_directory / "multipass"
            executable.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
            executable.chmod(0o755)
            probe = HostPreflightProbe(
                Path.cwd(),
                executable_fallback_directories=(fallback_directory,),
            )

            with patch.dict(os.environ, {"PATH": ""}):
                self.assertTrue(probe.executable_available("multipass"))

    def test_ensure_common_executable_paths_adds_existing_fallback_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fallback_directory = Path(temporary_directory) / "snap" / "bin"
            fallback_directory.mkdir(parents=True)

            with patch.dict(os.environ, {"PATH": "/usr/bin"}):
                ensure_common_executable_paths((fallback_directory,))

                self.assertEqual(
                    os.pathsep.join(("/usr/bin", str(fallback_directory))),
                    os.environ["PATH"],
                )

    def test_ensure_common_executable_paths_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fallback_directory = Path(temporary_directory) / "snap" / "bin"
            fallback_directory.mkdir(parents=True)

            with patch.dict(os.environ, {"PATH": str(fallback_directory)}):
                ensure_common_executable_paths((fallback_directory,))

                self.assertEqual(str(fallback_directory), os.environ["PATH"])

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

    def test_port_available_fails_closed_when_bind_is_not_permitted(self):
        probe = HostPreflightProbe(Path.cwd())
        bind_socket = MagicMock()
        bind_socket.__enter__.return_value = bind_socket
        bind_socket.bind.side_effect = PermissionError()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.socket.socket",
            return_value=bind_socket,
        ):
            self.assertFalse(probe.port_available(80))

    def test_port_matches_expected_service_recognizes_portainer(self):
        probe = HostPreflightProbe(Path.cwd())
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = {"Server": "Portainer"}
        response.read.return_value = b'{"Version":"2.25.1"}'

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            return_value=response,
        ):
            self.assertTrue(probe.port_matches_expected_service(9000, "Portainer"))

    def test_port_matches_expected_service_rejects_unknown_http_service(self):
        probe = HostPreflightProbe(Path.cwd())
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = {"Server": "Example"}
        response.read.return_value = b"hello"

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            return_value=response,
        ):
            self.assertFalse(probe.port_matches_expected_service(9000, "Portainer"))

    def test_port_matches_expected_service_rejects_empty_nginx_404_for_service_access(self):
        probe = HostPreflightProbe(Path.cwd())
        error = urllib.error.HTTPError(
            url="http://127.0.0.1:80/",
            code=404,
            msg="Not Found",
            hdrs={
                "Server": "nginx/1.31.1",
                "Access-Control-Allow-Origin": "*",
            },
            fp=io.BytesIO(b""),
        )

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            side_effect=error,
        ):
            self.assertFalse(
                probe.port_matches_expected_service(80, "Service Access dashboard")
            )

    def test_port_matches_expected_service_recognizes_legacy_swagger_api_cors_404(self):
        probe = HostPreflightProbe(Path.cwd())
        error = urllib.error.HTTPError(
            url="http://127.0.0.1:8084/",
            code=404,
            msg="Not Found",
            hdrs={"Access-Control-Allow-Origin": "*"},
            fp=io.BytesIO(b""),
        )

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            side_effect=error,
        ):
            self.assertTrue(probe.port_matches_expected_service(8084, "Swagger API"))

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

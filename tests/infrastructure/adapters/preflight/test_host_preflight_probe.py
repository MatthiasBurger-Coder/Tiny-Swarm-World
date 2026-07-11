import hashlib
import io
import json
import os
import socket
import ssl
import subprocess
import tempfile
import urllib.error
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests.support.sonar_safe_literals import sample_text

from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    SetupPath,
)
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
            executable = fallback_directory / "incus"
            executable.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
            executable.chmod(0o755)
            probe = HostPreflightProbe(
                Path.cwd(),
                executable_fallback_directories=(fallback_directory,),
            )

            with patch.dict(os.environ, {"PATH": ""}):
                self.assertTrue(probe.executable_available("incus"))

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

    def test_host_environment_report_classifies_verified_native_linux(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(os_root, "proc", "version", text="Linux version 6.8\n")
            _write_os_signal(
                os_root,
                "proc",
                "sys",
                "kernel",
                "osrelease",
                text="6.8.0-generic\n",
            )
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.NATIVE_LINUX, report.environment)
        self.assertEqual(SetupPath.NATIVE_LINUX, report.setup_path)
        self.assertTrue(report.allows_live_setup)
        self.assertFalse(report.static_validation_only)
        self.assertEqual("native_linux", report.evidence["classification"])
        self.assertEqual("present", report.evidence["kernel_signal"])

    def test_host_environment_report_classifies_container_marker_as_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(os_root, "proc", "version", text="Linux version 6.8\n")
            (os_root / ".dockerenv").write_text("", encoding="utf-8")
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.SANDBOX_UNVERIFIED, report.environment)
        self.assertEqual(SetupPath.SANDBOX_UNVERIFIED, report.setup_path)
        self.assertFalse(report.allows_live_setup)
        self.assertTrue(report.static_validation_only)
        self.assertEqual("container_marker", report.evidence["sandbox_signal"])

    def test_host_environment_report_classifies_cgroup_container_as_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(os_root, "proc", "version", text="Linux version 6.8\n")
            _write_os_signal(
                os_root,
                "proc",
                "self",
                "cgroup",
                text="0::/docker/synthetic\n",
            )
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.SANDBOX_UNVERIFIED, report.environment)
        self.assertEqual(SetupPath.SANDBOX_UNVERIFIED, report.setup_path)
        self.assertEqual("container_marker", report.evidence["sandbox_signal"])

    def test_host_environment_report_classifies_ci_environment_as_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(os_root, "proc", "version", text="Linux version 6.8\n")
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {"CI": "true"}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.SANDBOX_UNVERIFIED, report.environment)
        self.assertEqual(SetupPath.SANDBOX_UNVERIFIED, report.setup_path)
        self.assertEqual("ci_marker", report.evidence["sandbox_signal"])

    def test_host_environment_report_keeps_container_wsl2_as_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(
                os_root,
                "proc",
                "sys",
                "kernel",
                "osrelease",
                text="5.15.90.1-microsoft-standard-WSL2\n",
            )
            (os_root / ".dockerenv").write_text("", encoding="utf-8")
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.SANDBOX_UNVERIFIED, report.environment)
        self.assertEqual(SetupPath.SANDBOX_UNVERIFIED, report.setup_path)
        self.assertEqual("container_marker", report.evidence["sandbox_signal"])

    def test_host_environment_report_classifies_missing_kernel_signals_as_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            probe = HostPreflightProbe(Path.cwd(), os_root=Path(temporary_directory))

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.SANDBOX_UNVERIFIED, report.environment)
        self.assertEqual(SetupPath.SANDBOX_UNVERIFIED, report.setup_path)
        self.assertEqual("kernel_signal_missing", report.evidence["sandbox_signal"])

    def test_host_environment_report_requires_independent_wsl_signal_for_wsl2(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(
                os_root,
                "proc",
                "sys",
                "kernel",
                "osrelease",
                text="5.15.90.1-microsoft-standard-WSL2\n",
            )
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, report.environment)
        self.assertNotEqual(HostEnvironmentKind.WSL2, report.environment)
        self.assertEqual(SetupPath.UNSUPPORTED, report.setup_path)
        self.assertEqual("unknown", report.evidence["wsl_generation"])
        self.assertEqual("absent", report.evidence["wsl_independent_signal"])

    def test_host_environment_report_classifies_verified_wsl2(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(
                os_root,
                "proc",
                "sys",
                "kernel",
                "osrelease",
                text="5.15.90.1-microsoft-standard-WSL2\n",
            )
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.WSL2, report.environment)
        self.assertEqual(SetupPath.WSL2, report.setup_path)
        self.assertTrue(report.allows_live_setup)
        self.assertFalse(report.static_validation_only)
        self.assertEqual("wsl2", report.evidence["classification"])
        self.assertEqual("2", report.evidence["wsl_generation"])
        self.assertEqual("present", report.evidence["wsl_independent_signal"])

    def test_host_environment_report_classifies_wsl1_as_unsupported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(
                os_root,
                "proc",
                "version",
                text="Linux version 4.4.0-19041-Microsoft\n",
            )
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {"WSL_INTEROP": "present"}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.WSL1_UNSUPPORTED, report.environment)
        self.assertEqual(SetupPath.UNSUPPORTED, report.setup_path)
        self.assertFalse(report.allows_live_setup)
        self.assertEqual("wsl1_unsupported", report.evidence["classification"])
        self.assertEqual("1", report.evidence["wsl_generation"])

    def test_host_environment_report_blocks_ambiguous_wsl_signal(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(os_root, "proc", "version", text="Linux version 6.8\n")
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, report.environment)
        self.assertEqual(SetupPath.UNSUPPORTED, report.setup_path)
        self.assertFalse(report.allows_live_setup)
        self.assertEqual("wsl_unknown", report.evidence["classification"])
        self.assertEqual("unknown", report.evidence["wsl_generation"])

    def test_host_environment_report_uses_wsl_interop_marker_as_independent_signal(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            os_root = Path(temporary_directory)
            _write_os_signal(
                os_root,
                "proc",
                "sys",
                "kernel",
                "osrelease",
                text="5.15.90.1-microsoft-standard-WSL2\n",
            )
            _write_os_signal(
                os_root,
                "proc",
                "sys",
                "fs",
                "binfmt_misc",
                "WSLInterop",
                text="enabled\n",
            )
            probe = HostPreflightProbe(Path.cwd(), os_root=os_root)

            with (
                patch(
                    "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
                    return_value="Linux",
                ),
                patch.dict(os.environ, {}, clear=True),
            ):
                report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.WSL2, report.environment)
        self.assertEqual(SetupPath.WSL2, report.setup_path)
        self.assertEqual("present", report.evidence["wsl_independent_signal"])

    def test_host_environment_report_fails_closed_for_non_linux_platform(self):
        probe = HostPreflightProbe(Path.cwd())

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.platform.system",
            return_value="Darwin",
        ):
            report = probe.host_environment_report()

        self.assertEqual(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, report.environment)
        self.assertEqual(SetupPath.UNSUPPORTED, report.setup_path)
        self.assertFalse(report.allows_live_setup)
        self.assertFalse(report.static_validation_only)
        self.assertEqual("unknown_unsupported", report.evidence["classification"])
        self.assertEqual("darwin", report.evidence["kernel_family"])

    def test_windows_wsl_bridge_status_reports_missing_state_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            probe = HostPreflightProbe(Path(temporary_directory))

            status = probe.windows_wsl_bridge_status((80, 10000))

        self.assertFalse(status.prepared)
        self.assertEqual("state_missing", status.reason)
        self.assertEqual((80, 10000), status.missing_ports)
        self.assertEqual("tools/windows/.tws-wsl-bridge.state.json", status.state_path)

    def test_windows_wsl_bridge_status_accepts_current_ip_and_all_expected_ports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _write_bridge_state(root, wsl_ip="172.20.0.2", ports=(80, 10000))
            probe = HostPreflightProbe(root)

            with patch(
                "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.current_wsl_ipv4",
                return_value="172.20.0.2",
            ):
                status = probe.windows_wsl_bridge_status((80, 10000))

        self.assertTrue(status.prepared)
        self.assertEqual("prepared", status.reason)
        self.assertEqual((80, 10000), status.mapped_ports)
        self.assertEqual((), status.missing_ports)

    def test_windows_wsl_bridge_status_detects_changed_wsl_ip(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _write_bridge_state(root, wsl_ip="172.20.0.2", ports=(80,))
            probe = HostPreflightProbe(root)

            with patch(
                "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.current_wsl_ipv4",
                return_value="172.21.0.9",
            ):
                status = probe.windows_wsl_bridge_status((80,))

        self.assertFalse(status.prepared)
        self.assertEqual("wsl_ip_changed", status.reason)
        self.assertEqual("172.20.0.2", status.state_wsl_ip)
        self.assertEqual("172.21.0.9", status.current_wsl_ip)

    def test_windows_wsl_bridge_status_detects_missing_expected_ports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _write_bridge_state(root, wsl_ip="172.20.0.2", ports=(80,))
            probe = HostPreflightProbe(root)

            with patch(
                "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.current_wsl_ipv4",
                return_value="172.20.0.2",
            ):
                status = probe.windows_wsl_bridge_status((80, 10000))

        self.assertFalse(status.prepared)
        self.assertEqual("missing_ports", status.reason)
        self.assertEqual((10000,), status.missing_ports)

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

    def test_port_available_fails_closed_when_unprivileged_bind_is_not_permitted(self):
        probe = HostPreflightProbe(Path.cwd())
        bind_socket = MagicMock()
        bind_socket.__enter__.return_value = bind_socket
        bind_socket.bind.side_effect = PermissionError()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.socket.socket",
            return_value=bind_socket,
        ):
            self.assertFalse(probe.port_available(8080))

    def test_privileged_port_available_when_bind_denied_and_no_listener_exists(self):
        probe = HostPreflightProbe(Path.cwd())
        bind_socket = MagicMock()
        bind_socket.__enter__.return_value = bind_socket
        bind_socket.bind.side_effect = PermissionError()
        connect_socket = MagicMock()
        connect_socket.__enter__.return_value = connect_socket
        connect_socket.connect_ex.return_value = 111

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.socket.socket",
            side_effect=(bind_socket, connect_socket),
        ):
            self.assertTrue(probe.port_available(80))

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

    def test_port_matches_expected_service_recognizes_infisical_https(self):
        probe = HostPreflightProbe(Path.cwd())
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = {
            "Server": "nginx/1.31.1",
            "Content-Security-Policy": "default-src 'none'",
        }
        response.read.return_value = b""

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            self.assertTrue(probe.port_matches_expected_service(443, "Infisical HTTPS"))

        request = urlopen.call_args.args[0]
        self.assertEqual("https://127.0.0.1:443/", request.full_url)
        tls_context = urlopen.call_args.kwargs["context"]
        self.assertEqual(ssl.PROTOCOL_TLS_CLIENT, tls_context.protocol)
        self.assertEqual(ssl.TLSVersion.TLSv1_2, tls_context.minimum_version)
        self.assertEqual(ssl.CERT_REQUIRED, tls_context.verify_mode)
        self.assertTrue(tls_context.check_hostname)

    def test_port_matches_expected_service_recognizes_traefik_http_ingress(self):
        probe = HostPreflightProbe(Path.cwd())
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 404
        response.headers = {"Server": "Traefik"}
        response.read.return_value = b"404 page not found"

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            return_value=response,
        ):
            self.assertTrue(
                probe.port_matches_expected_service(80, "Traefik HTTP ingress")
            )

    def test_port_matches_expected_service_recognizes_traefik_https_ingress(self):
        probe = HostPreflightProbe(Path.cwd())
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 404
        response.headers = {"Server": "Traefik"}
        response.read.return_value = b"404 page not found"

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            self.assertTrue(
                probe.port_matches_expected_service(443, "Traefik HTTPS ingress")
            )

        request = urlopen.call_args.args[0]
        self.assertEqual("https://127.0.0.1:443/", request.full_url)
        tls_context = urlopen.call_args.kwargs["context"]
        self.assertEqual(ssl.PROTOCOL_TLS_CLIENT, tls_context.protocol)
        self.assertEqual(ssl.TLSVersion.TLSv1_2, tls_context.minimum_version)
        self.assertEqual(ssl.CERT_REQUIRED, tls_context.verify_mode)
        self.assertTrue(tls_context.check_hostname)

    def test_port_matches_expected_service_recognizes_pulsar_admin_api(self):
        probe = HostPreflightProbe(Path.cwd())
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = {"Content-Type": "application/json"}
        response.read.return_value = b'["standalone"]'

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            self.assertTrue(probe.port_matches_expected_service(8087, "Pulsar Admin API"))

        request = urlopen.call_args.args[0]
        self.assertEqual("http://127.0.0.1:8087/admin/v2/clusters", request.full_url)

    def test_port_matches_expected_service_recognizes_pulsar_broker_tcp(self):
        probe = HostPreflightProbe(Path.cwd())

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.socket.create_connection",
        ) as create_connection:
            create_connection.return_value.__enter__.return_value = create_connection.return_value

            self.assertTrue(probe.port_matches_expected_service(6650, "Pulsar broker protocol"))

    def test_port_matches_expected_service_recognizes_pulsar_manager_ui(self):
        probe = HostPreflightProbe(Path.cwd())
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = {"Content-Type": "text/html"}
        response.read.return_value = b"<html><title>Pulsar Manager</title></html>"

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            self.assertTrue(probe.port_matches_expected_service(9527, "Pulsar Manager UI"))

        request = urlopen.call_args.args[0]
        self.assertEqual("http://127.0.0.1:9527/", request.full_url)

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
        self.addCleanup(error.close)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            side_effect=error,
        ):
            self.assertFalse(
                probe.port_matches_expected_service(80, "Service Access dashboard")
            )

    def test_port_matches_expected_service_recognizes_service_access_https(self):
        probe = HostPreflightProbe(Path.cwd())
        http_error = OSError("plain http unavailable")
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = {"Server": "nginx/1.31.2"}
        response.read.return_value = b"<html>Infisical</html>"

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe.urllib.request.urlopen",
            side_effect=(http_error, response),
        ) as urlopen:
            self.assertTrue(probe.port_matches_expected_service(443, "Service Access"))

        self.assertEqual("http://127.0.0.1:443/", urlopen.call_args_list[0].args[0].full_url)
        self.assertEqual("https://127.0.0.1:443/", urlopen.call_args_list[1].args[0].full_url)
        tls_context = urlopen.call_args_list[1].kwargs["context"]
        self.assertEqual(ssl.PROTOCOL_TLS_CLIENT, tls_context.protocol)
        self.assertEqual(ssl.TLSVersion.TLSv1_2, tls_context.minimum_version)
        self.assertEqual(ssl.CERT_REQUIRED, tls_context.verify_mode)
        self.assertTrue(tls_context.check_hostname)

    def test_port_matches_expected_service_recognizes_legacy_swagger_api_cors_404(self):
        probe = HostPreflightProbe(Path.cwd())
        error = urllib.error.HTTPError(
            url="http://127.0.0.1:8084/",
            code=404,
            msg="Not Found",
            hdrs={"Access-Control-Allow-Origin": "*"},
            fp=io.BytesIO(b""),
        )
        self.addCleanup(error.close)

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
        marker_value = sample_text("synthetic-test-", "to", "ken")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_file = root / "src" / "example.py"
            source_file.parent.mkdir()
            source_file.write_text(f"TOKEN = '{marker_value}'\n", encoding="utf-8")
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
                            marker_value.encode("utf-8")
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


def _write_os_signal(root: Path, *parts: str, text: str) -> None:
    target = root.joinpath(*parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _write_bridge_state(root: Path, *, wsl_ip: str, ports: tuple[int, ...]) -> None:
    target = root / "tools" / "windows" / ".tws-wsl-bridge.state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "contractVersion": 2,
        "agentMode": "scheduled-discovery",
        "agentStatus": "ready",
        "generatedAt": datetime.now(UTC).isoformat(),
        "action": "install",
        "wslIp": wsl_ip,
        "listenAddress": "0.0.0.0",
        "mappings": [
            {"name": f"port-{port}", "listenPort": port, "connectPort": port}
            for port in ports
        ],
    }
    target.write_text(json.dumps(state), encoding="utf-8")

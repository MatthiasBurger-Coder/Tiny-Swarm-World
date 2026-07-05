import json
import stat
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world import installer


class TestInstaller(unittest.TestCase):
    def test_parse_args_defaults_to_service_access_and_secret_generation(self):
        options = installer.parse_args(())

        self.assertEqual("service-access", options.service_profile)
        self.assertTrue(options.generate_secrets)
        self.assertEqual("generated", options.secrets_mode)
        self.assertFalse(options.confirm_reset)
        self.assertFalse(options.non_interactive_live_approval)
        self.assertFalse(options.headless)

    def test_parse_args_supports_headless_and_noninteractive_approval(self):
        options = installer.parse_args(
            (
                "--service-profile",
                "default",
                "--no-generate-secrets",
                "--secrets-mode",
                "fixed",
                "--confirm-reset",
                "--non-interactive-live-approval",
                "--headless",
            )
        )

        self.assertEqual("default", options.service_profile)
        self.assertFalse(options.generate_secrets)
        self.assertEqual("fixed", options.secrets_mode)
        self.assertTrue(options.confirm_reset)
        self.assertTrue(options.non_interactive_live_approval)
        self.assertTrue(options.headless)

    def test_detect_host_runtime_prefers_wsl_environment(self):
        runtime = installer.detect_host_runtime({"WSL_DISTRO_NAME": "Ubuntu"})

        self.assertEqual("wsl2", runtime.name)
        self.assertEqual("wsl_environment", runtime.detection_source)

    def test_detect_host_runtime_uses_kernel_signal(self):
        def fake_read_text(path: Path) -> str:
            if path.as_posix() == "/proc/sys/kernel/osrelease":
                return "6.1.0-microsoft-standard-WSL2"
            return ""

        with patch.object(installer, "_read_text", side_effect=fake_read_text):
            runtime = installer.detect_host_runtime({})

        self.assertEqual("wsl2", runtime.name)
        self.assertEqual("kernel_signal", runtime.detection_source)

    def test_ensure_python_environment_keeps_wsl_python_when_imports_available(self):
        with tempfile.TemporaryDirectory() as tempdir:
            paths = installer.InstallerPaths(
                secret_env_file=Path(tempdir) / "local.env",
                fixed_secret_env_file=Path(tempdir) / "fixed.env",
                infisical_secret_env_file=Path(tempdir) / "infisical.env",
                generated_secret_env_file=Path(tempdir) / "generated.env",
                native_linux_venv=Path(tempdir) / "install-venv",
            )

            with patch.object(installer, "_python_imports_available", return_value=True):
                python_bin = installer.ensure_python_environment(
                    installer.HostRuntime("wsl2", "test"),
                    paths,
                    {},
                )

        self.assertEqual("python3", python_bin)

    def test_ensure_python_environment_bootstraps_wsl_when_imports_are_missing(self):
        with tempfile.TemporaryDirectory() as tempdir:
            paths = installer.InstallerPaths(
                secret_env_file=Path(tempdir) / "local.env",
                fixed_secret_env_file=Path(tempdir) / "fixed.env",
                infisical_secret_env_file=Path(tempdir) / "infisical.env",
                generated_secret_env_file=Path(tempdir) / "generated.env",
                native_linux_venv=Path(tempdir) / "install-venv",
            )
            venv_python = paths.native_linux_venv / "bin" / "python"

            def fake_imports_available(python_bin: str, env: object) -> bool:
                return python_bin == venv_python.as_posix()

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if command[:3] == ["python3", "-m", "venv"]:
                    venv_python.parent.mkdir(parents=True)
                    venv_python.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
                    return subprocess.CompletedProcess(command, 0)
                if command[:3] == [venv_python.as_posix(), "-m", "pip"]:
                    return subprocess.CompletedProcess(command, 0)
                return subprocess.CompletedProcess(command, 99)

            with (
                patch.object(installer, "_python_imports_available", side_effect=fake_imports_available),
                patch.object(installer.subprocess, "run", side_effect=fake_run),
            ):
                python_bin = installer.ensure_python_environment(
                    installer.HostRuntime("wsl2", "test"),
                    paths,
                    {},
                )

        self.assertEqual(venv_python.as_posix(), python_bin)

    def test_load_export_file_parses_shell_quoted_values(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "live.env"
            path.write_text(
                "\n".join(
                    (
                        "# local secrets",
                        "export TSW_ONE='quoted value'",
                        "TSW_TWO=plain",
                        "not an assignment",
                    )
                ),
                encoding="utf-8",
            )

            values = installer._load_export_file(path)

        self.assertEqual(
            {
                "TSW_ONE": "quoted value",
                "TSW_TWO": "plain",
            },
            values,
        )

    def test_load_export_file_rejects_invalid_shell_quoting_without_value_leak(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "live.env"
            path.write_text(
                "export TSW_INFISICAL_LOGIN_EMAIL='admin@tiny-swarm-world.local\n",
                encoding="utf-8",
            )

            with self.assertRaises(installer.InstallerError) as raised:
                installer._load_export_file(path)

        self.assertIn("invalid shell quoting", str(raised.exception))
        self.assertNotIn("admin@tiny-swarm-world.local", str(raised.exception))

    def test_normalized_email_value_removes_accidental_literal_quote(self):
        self.assertEqual(
            "admin@tiny-swarm-world.local",
            installer._normalized_email_value("'admin@tiny-swarm-world.local"),
        )

    def test_normalize_export_file_collapses_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "live.env"
            path.write_text(
                "\n".join(
                    (
                        "# local operator values",
                        "export TSW_EXAMPLE='first-secret'",
                        "export TSW_OTHER='other-secret'",
                        "export TSW_EXAMPLE='second-secret'",
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            installer._normalize_export_file_if_duplicate_keys(path)

            content = path.read_text(encoding="utf-8")
            values = installer._load_export_file(path)
            mode = stat.S_IMODE(path.stat().st_mode)

        self.assertEqual(
            {
                "TSW_EXAMPLE": "second-secret",
                "TSW_OTHER": "other-secret",
            },
            values,
        )
        self.assertEqual(0o600, mode)
        self.assertEqual(1, content.count("TSW_EXAMPLE="))
        self.assertIn("Normalized by install.sh", content)

    def test_required_installer_secret_entries_come_from_manifest(self):
        entries = installer._required_installer_secret_entries(
            Path("infra/config/secrets/infisical-secrets.yaml")
        )
        keys = {entry.key for entry in entries}

        self.assertIn("TSW_PORTAINER_ADMIN_PASSWORD", keys)
        self.assertIn("TSW_INFISICAL_REDIS_PASSWORD", keys)
        self.assertNotIn("TSW_TRAEFIK_TLS_CERT_SECRET_NAME", keys)
        self.assertTrue(
            all(entry.source in installer.INSTALLER_REQUIRED_SOURCES for entry in entries)
        )

    def test_required_installer_secret_entries_can_include_external_required_keys(self):
        entries = installer._required_installer_secret_entries(
            Path("infra/config/secrets/infisical-secrets.yaml"),
            sources=None,
        )
        keys = {entry.key for entry in entries}

        self.assertIn("TSW_TRAEFIK_TLS_CERT_SECRET_NAME", keys)
        self.assertIn("TSW_TRAEFIK_TLS_KEY_SECRET_NAME", keys)

    def test_fixed_installer_secret_values_rejects_missing_key(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fixed_file = Path(tempdir) / "fixed.env"
            fixed_file.write_text("export TSW_PRESENT_PASSWORD='fixed'\n", encoding="utf-8")
            entries = (
                installer.InstallerSecretEntry("TSW_PRESENT_PASSWORD", "generated_local_secret", True),
                installer.InstallerSecretEntry("TSW_MISSING_PASSWORD", "generated_local_secret", True),
            )

            with self.assertRaisesRegex(installer.InstallerError, "TSW_MISSING_PASSWORD"):
                installer._fixed_installer_secret_values(fixed_file, entries)

    def test_confirm_reset_reports_missing_noninteractive_input(self):
        options = installer.InstallerOptions(
            service_profile="service-access",
            generate_secrets=False,
            secrets_mode="generated",
            confirm_reset=False,
            non_interactive_live_approval=False,
            headless=False,
        )

        with patch("builtins.input", side_effect=EOFError):
            with self.assertRaisesRegex(installer.InstallerError, "was not provided"):
                installer._confirm_reset(options)

    def test_windows_wsl_bridge_guard_passes_for_native_linux_without_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            guard = installer._windows_wsl_bridge_guard(
                installer.HostRuntime("native_linux", "test"),
                {},
                Path(tempdir),
            )

        self.assertTrue(guard.passed)
        self.assertEqual("not_wsl2", guard.reason)

    def test_windows_wsl_bridge_guard_blocks_wsl_without_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_ports_registry(root, (80, 10000))

            guard = installer._windows_wsl_bridge_guard(
                installer.HostRuntime("wsl2", "test"),
                {},
                root,
            )

        self.assertFalse(guard.passed)
        self.assertEqual("state_missing", guard.reason)
        self.assertEqual((80, 10000), guard.missing_ports)

    def test_windows_wsl_bridge_guard_accepts_current_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_ports_registry(root, (80, 10000))
            _write_windows_bridge_state(root, "172.20.0.2", (80, 10000))

            with patch(
                "tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state.current_wsl_ipv4",
                return_value="172.20.0.2",
            ):
                guard = installer._windows_wsl_bridge_guard(
                    installer.HostRuntime("wsl2", "test"),
                    {},
                    root,
                )

        self.assertTrue(guard.passed)
        self.assertEqual("prepared", guard.reason)

    def test_windows_wsl_bridge_guard_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as tempdir:
            guard = installer._windows_wsl_bridge_guard(
                installer.HostRuntime("wsl2", "test"),
                {"TSW_WINDOWS_EXPOSURE": "disabled"},
                Path(tempdir),
            )

        self.assertTrue(guard.passed)
        self.assertEqual("windows_exposure_disabled", guard.reason)

    def test_suggested_checks_for_phase_returns_phase_specific_commands(self):
        self.assertEqual(
            (
                "incus exec swarm-manager -- docker node ls",
                "incus exec swarm-manager -- docker service ls",
            ),
            installer._suggested_checks_for_phase("setup platform"),
        )
        self.assertEqual(
            (
                "./tsw doctor network",
                "./tsw network repair --linux-forwarding --apply",
                "powershell.exe -ExecutionPolicy Bypass -File .\\tools\\windows\\doctor-portproxy.ps1",
            ),
            installer._suggested_checks_for_phase(
                "setup platform",
                log_text="first_failure_reason: apt_repository_unreachable",
            ),
        )
        self.assertEqual(
            ("incus list", "docker context ls"),
            installer._suggested_checks_for_phase("reset platform"),
        )
        self.assertEqual((), installer._suggested_checks_for_phase("preflight"))

    def test_fallback_install_event_renderer_covers_status_branches(self):
        install_started = installer._FallbackInstallEvent(
            event_type="INSTALL_STARTED",
            status="STARTED",
            step="Install",
            message="starting",
        )
        step_started = installer._FallbackInstallEvent(
            event_type="STEP_STARTED",
            status="STARTED",
            step="Preflight",
            target="host",
            message="checking",
            sequence=1,
            total=2,
        )
        succeeded = installer._FallbackInstallEvent(
            event_type="STEP_SUCCEEDED",
            status="SUCCEEDED",
            step="Preflight",
            message="done",
        )
        unknown = installer._FallbackInstallEvent(
            event_type="STEP_SKIPPED",
            status="SKIPPED",
            step="Preflight",
            target="host",
        )

        self.assertEqual(
            ("Tiny Swarm World Installer", "  RUNNING starting"),
            installer._render_fallback_install_event(install_started),
        )
        self.assertEqual(
            ("[1/2] Preflight", "  RUNNING checking"),
            installer._render_fallback_install_event(step_started),
        )
        self.assertEqual(("  OK      done",), installer._render_fallback_install_event(succeeded))
        self.assertEqual(("  SKIPPED host",), installer._render_fallback_install_event(unknown))

    def test_reset_failure_guidance_explains_privileged_lxc_block(self):
        log_text = "\n".join(
            (
                "classification: managed_nodes_reset_blocked",
                "first_failure_mismatch_reasons: unsafe_instance_config",
                "first_failure_unsafe_instance_settings: security.privileged",
            )
        )

        lines = installer._reset_failure_guidance_lines(log_text)

        rendered = "\n".join(lines)
        self.assertIn("security.privileged", rendered)
        self.assertIn("incus profile get docker-swarm security.privileged", rendered)
        self.assertIn("disposable Tiny Swarm World nodes", rendered)

    def test_reset_failure_guidance_stays_silent_for_other_reset_blocks(self):
        lines = installer._reset_failure_guidance_lines(
            "\n".join(
                (
                    "classification: managed_nodes_reset_blocked",
                    "first_failure_mismatch_reasons: unsafe_instance_devices",
                )
            )
        )

        self.assertEqual((), lines)

    def test_setup_failure_guidance_explains_apt_repository_reachability(self):
        lines = installer._setup_failure_guidance_lines(
            "first_failure_reason: apt_repository_unreachable"
        )

        rendered = "\n".join(lines)
        self.assertIn("APT repositories", rendered)
        self.assertIn("./tsw doctor network", rendered)
        self.assertIn("./tsw network repair --linux-forwarding --apply", rendered)
        self.assertIn("does not change iptables", rendered)

    def test_setup_failure_guidance_stays_silent_for_other_setup_blocks(self):
        self.assertEqual((), installer._setup_failure_guidance_lines("failed_to_apply"))


def _write_ports_registry(root: Path, ports: tuple[int, ...]) -> None:
    registry = root / "infra" / "config" / "ports.yaml"
    registry.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "ports:",
    ]
    for index, port in enumerate(ports):
        lines.extend(
            (
                f"  - id: port-{index}",
                f"    service_id: service-{index}",
                f"    internal_port: {port}",
                f"    external_port: {port}",
                "    exposure: diagnostic",
                "    protocol: tcp",
            )
        )
    registry.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_windows_bridge_state(root: Path, wsl_ip: str, ports: tuple[int, ...]) -> None:
    state_path = root / "tools" / "windows" / ".tws-wsl-bridge.state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "wslIp": wsl_ip,
        "mappings": [
            {
                "name": f"port-{port}",
                "listenPort": port,
                "connectPort": port,
            }
            for port in ports
        ],
    }
    state_path.write_text(json.dumps(state), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

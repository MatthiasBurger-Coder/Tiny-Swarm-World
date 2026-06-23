import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world import installer


class TestInstaller(unittest.TestCase):
    def test_parse_args_defaults_to_service_access_and_secret_generation(self):
        options = installer.parse_args(())

        self.assertEqual("service-access", options.service_profile)
        self.assertTrue(options.generate_secrets)
        self.assertFalse(options.confirm_reset)
        self.assertFalse(options.non_interactive_live_approval)
        self.assertFalse(options.headless)

    def test_parse_args_supports_headless_and_noninteractive_approval(self):
        options = installer.parse_args(
            (
                "--service-profile",
                "default",
                "--no-generate-secrets",
                "--confirm-reset",
                "--non-interactive-live-approval",
                "--headless",
            )
        )

        self.assertEqual("default", options.service_profile)
        self.assertFalse(options.generate_secrets)
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

    def test_confirm_reset_reports_missing_noninteractive_input(self):
        options = installer.InstallerOptions(
            service_profile="service-access",
            generate_secrets=False,
            confirm_reset=False,
            non_interactive_live_approval=False,
            headless=False,
        )

        with patch("builtins.input", side_effect=EOFError):
            with self.assertRaisesRegex(installer.InstallerError, "was not provided"):
                installer._confirm_reset(options)

    def test_suggested_checks_for_phase_returns_phase_specific_commands(self):
        self.assertEqual(
            (
                "lxc exec swarm-manager -- docker node ls",
                "lxc exec swarm-manager -- docker service ls",
            ),
            installer._suggested_checks_for_phase("setup platform"),
        )
        self.assertEqual(
            ("lxc list", "docker context ls"),
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


if __name__ == "__main__":
    unittest.main()

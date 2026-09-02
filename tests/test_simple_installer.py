import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world import installer
from tiny_swarm_world.domain.configuration.configuration_contract import validate_traefik_htpasswd
from tiny_swarm_world.domain.configuration.internal_test_credentials import (
    INTERNAL_TEST_PASSWORD,
    internal_test_credential,
)
from tiny_swarm_world.simple_installer import (
    _load_explicit_bootstrap_override,
    main,
    _prepare_bootstrap_environment,
    _print_operator_credentials,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class TestSimpleInstallerSecretBootstrap(unittest.TestCase):
    def test_resolves_catalog_defaults_without_creating_recovery_state(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            state_dir = Path(temporary_dir) / "state"
            base_env = {
                "HOME": temporary_dir,
            }

            first = _prepare_bootstrap_environment(base_env, REPOSITORY_ROOT)
            second = _prepare_bootstrap_environment(base_env, REPOSITORY_ROOT)

            secret_file = state_dir / "bootstrap-secrets.env"
            self.assertFalse(secret_file.exists())
            self.assertEqual(
                first["TSW_PORTAINER_ADMIN_PASSWORD"],
                INTERNAL_TEST_PASSWORD,
            )
            self.assertEqual(
                first["TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"],
                internal_test_credential("TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"),
            )
            self.assertEqual(first, second)
            self.assertEqual(first["TSW_SECRETS_MODE"], "internal-test")

    def test_resolves_catalog_traefik_htpasswd_without_random_generation(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            with patch(
                "tiny_swarm_world.simple_installer.legacy._generated_secret_values",
                side_effect=AssertionError("catalog path must not generate secrets"),
            ):
                env = _prepare_bootstrap_environment(
                    {"HOME": temporary_dir},
                    REPOSITORY_ROOT,
                )

            value = env["TSW_TRAEFIK_GUI_USERS_HTPASSWD"]
            validate_traefik_htpasswd(value)
            self.assertEqual(
                value,
                internal_test_credential("TSW_TRAEFIK_GUI_USERS_HTPASSWD"),
            )

    def test_preserves_explicit_environment_override(self):
        env = _prepare_bootstrap_environment(
            {
                "TSW_PORTAINER_ADMIN_PASSWORD": "operator-portainer-password",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": "operator-infisical-password",
            },
            REPOSITORY_ROOT,
        )

        self.assertEqual(env["TSW_PORTAINER_ADMIN_PASSWORD"], "operator-portainer-password")
        self.assertEqual(
            env["TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"],
            "operator-infisical-password",
        )
        self.assertEqual(
            env["TSW_JENKINS_ADMIN_PASSWORD"],
            INTERNAL_TEST_PASSWORD,
        )

    def test_populates_every_required_manifest_key_from_catalog(self):
        env = _prepare_bootstrap_environment({}, REPOSITORY_ROOT)
        entries = installer._required_installer_secret_entries(
            REPOSITORY_ROOT / installer.DEFAULT_SECRET_MANIFEST_PATH,
            sources=installer.INSTALLER_REQUIRED_SOURCES,
        )

        for entry in entries:
            with self.subTest(key=entry.key):
                self.assertEqual(env[entry.key], internal_test_credential(entry.key))

    def test_main_passes_internal_test_options_to_legacy_execution(self):
        with (
            tempfile.TemporaryDirectory() as temporary_dir,
            patch.dict(os.environ, {"HOME": temporary_dir}, clear=True),
            patch("tiny_swarm_world.simple_installer.Path.cwd", return_value=REPOSITORY_ROOT),
            patch("tiny_swarm_world.simple_installer.legacy.run", return_value=0) as run,
            patch("tiny_swarm_world.simple_installer._print_operator_credentials"),
        ):
            result = main(("--headless",))

        self.assertEqual(result, 0)
        options = run.call_args.args[0]
        self.assertEqual(options.secrets_mode, "internal-test")
        self.assertFalse(options.generate_secrets)
        self.assertEqual(run.call_args.kwargs["env"]["TSW_SECRETS_MODE"], "internal-test")

    def test_main_returns_execution_failure_without_printing_credentials(self):
        with (
            tempfile.TemporaryDirectory() as temporary_dir,
            patch.dict(os.environ, {"HOME": temporary_dir}, clear=True),
            patch("tiny_swarm_world.simple_installer.Path.cwd", return_value=REPOSITORY_ROOT),
            patch("tiny_swarm_world.simple_installer.legacy.run", return_value=2),
            patch("tiny_swarm_world.simple_installer._print_operator_credentials") as print_credentials,
        ):
            result = main(("--headless",))

        self.assertEqual(result, 2)
        print_credentials.assert_not_called()

    def test_main_reports_installer_error_without_exposing_values(self):
        stderr = io.StringIO()
        with (
            tempfile.TemporaryDirectory() as temporary_dir,
            patch.dict(os.environ, {"HOME": temporary_dir}, clear=True),
            patch("tiny_swarm_world.simple_installer.Path.cwd", return_value=REPOSITORY_ROOT),
            patch(
                "tiny_swarm_world.simple_installer.legacy.run",
                side_effect=installer.InstallerError("setup failed for a redacted reason"),
            ),
            redirect_stdout(io.StringIO()),
            redirect_stderr(stderr),
        ):
            result = main(("--headless",))

        self.assertEqual(result, 1)
        self.assertIn("setup failed for a redacted reason", stderr.getvalue())

    def test_relative_explicit_override_paths_resolve_from_cwd(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            override_file = root / "override.env"
            override_file.write_text(
                "export TSW_PORTAINER_ADMIN_PASSWORD='relative-file-password'\n",
                encoding="utf-8",
            )
            state_file = root / "state" / "bootstrap-secrets.env"
            state_file.parent.mkdir()
            state_file.write_text(
                "export TSW_PORTAINER_ADMIN_PASSWORD='relative-state-password'\n",
                encoding="utf-8",
            )

            file_values = _load_explicit_bootstrap_override(
                {"TSW_BOOTSTRAP_SECRET_ENV_FILE": "override.env"},
                root,
            )
            state_values = _load_explicit_bootstrap_override(
                {"TSW_BOOTSTRAP_STATE_DIR": "state"},
                root,
            )

        self.assertEqual(file_values["TSW_PORTAINER_ADMIN_PASSWORD"], "relative-file-password")
        self.assertEqual(state_values["TSW_PORTAINER_ADMIN_PASSWORD"], "relative-state-password")

    def test_loads_only_explicit_bootstrap_override_file(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            override_file = Path(temporary_dir) / "bootstrap.env"
            override_file.write_text(
                "export TSW_PORTAINER_ADMIN_PASSWORD='file-portainer-password'\n",
                encoding="utf-8",
            )

            env = _prepare_bootstrap_environment(
                {"TSW_BOOTSTRAP_SECRET_ENV_FILE": override_file.as_posix()},
                REPOSITORY_ROOT,
            )

        self.assertEqual(env["TSW_PORTAINER_ADMIN_PASSWORD"], "file-portainer-password")

    def test_missing_explicit_bootstrap_override_fails_before_resolution(self):
        with self.assertRaisesRegex(RuntimeError, "(?i)explicit bootstrap credential override"):
            _prepare_bootstrap_environment(
                {"TSW_BOOTSTRAP_SECRET_ENV_FILE": "/missing/bootstrap.env"},
                REPOSITORY_ROOT,
            )

    def test_completion_output_exposes_only_operator_credentials(self):
        env = {
            "TSW_PORTAINER_ADMIN_PASSWORD": "portainer-visible",
            "TSW_INFISICAL_LOGIN_EMAIL": "admin@example.invalid",
            "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": "infisical-visible",
            "TSW_INFISICAL_ENCRYPTION_KEY": "must-stay-hidden",
            "TSW_POSTGRES_PASSWORD": "also-hidden",
        }
        output = io.StringIO()

        with redirect_stdout(output):
            _print_operator_credentials(env)

        rendered = output.getvalue()
        self.assertIn("portainer-visible", rendered)
        self.assertIn("infisical-visible", rendered)
        self.assertNotIn("must-stay-hidden", rendered)
        self.assertNotIn("also-hidden", rendered)
        self.assertIn("All other generated secrets are internal", rendered)

    def test_normal_cli_no_longer_exposes_secret_modes(self):
        install_script = (REPOSITORY_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("tiny_swarm_world.simple_installer", install_script)
        simple_source = (
            REPOSITORY_ROOT / "src/tiny_swarm_world/simple_installer.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"--secrets-mode"', simple_source)
        self.assertNotIn('"--no-generate-secrets"', simple_source)
        self.assertNotIn("_generated_secret_values", simple_source)


if __name__ == "__main__":
    unittest.main()

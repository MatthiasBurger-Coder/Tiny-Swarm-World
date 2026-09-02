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
from tiny_swarm_world.domain.configuration.credential_resolution import CredentialSource
from tiny_swarm_world.application.services.credential_resolution import (
    CREDENTIAL_SOURCE_MAP_ENVIRONMENT,
    decode_source_metadata,
)
from tiny_swarm_world.simple_installer import (
    SimpleInstallerError,
    _load_explicit_bootstrap_override,
    main,
    _prepare_bootstrap_environment,
    _print_operator_credentials,
    _validate_secure_override_path,
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
            self.assertNotIn("TSW_SECRETS_MODE", first)
            sources = decode_source_metadata(first[CREDENTIAL_SOURCE_MAP_ENVIRONMENT])
            self.assertEqual(sources["TSW_PORTAINER_ADMIN_PASSWORD"], CredentialSource.DEFAULT)

    def test_resolves_catalog_traefik_htpasswd_without_random_generation(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
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
        sources = decode_source_metadata(env[CREDENTIAL_SOURCE_MAP_ENVIRONMENT])
        self.assertEqual(sources["TSW_PORTAINER_ADMIN_PASSWORD"], CredentialSource.OPERATOR)
        self.assertEqual(sources["TSW_JENKINS_ADMIN_PASSWORD"], CredentialSource.DEFAULT)

    def test_process_environment_overrides_operator_install_file(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            operator_file = Path(temporary_dir) / "operator.env"
            operator_file.write_text(
                "export TSW_PORTAINER_ADMIN_PASSWORD='file-portainer-password'\n"
                "export TSW_JENKINS_ADMIN_PASSWORD='file-jenkins-password'\n",
                encoding="utf-8",
            )
            operator_file.chmod(0o600)
            env = _prepare_bootstrap_environment(
                {
                    "TSW_INSTALL_ENV_FILE": operator_file.as_posix(),
                    "TSW_PORTAINER_ADMIN_PASSWORD": "process-portainer-password",
                },
                REPOSITORY_ROOT,
            )

        self.assertEqual(env["TSW_PORTAINER_ADMIN_PASSWORD"], "process-portainer-password")
        self.assertEqual(env["TSW_JENKINS_ADMIN_PASSWORD"], "file-jenkins-password")
        sources = decode_source_metadata(env[CREDENTIAL_SOURCE_MAP_ENVIRONMENT])
        self.assertEqual(sources["TSW_PORTAINER_ADMIN_PASSWORD"], CredentialSource.OPERATOR)
        self.assertEqual(sources["TSW_JENKINS_ADMIN_PASSWORD"], CredentialSource.OPERATOR)

    def test_rejects_unprotected_operator_install_file_before_reading(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            operator_file = Path(temporary_dir) / "operator.env"
            operator_file.write_text(
                "export TSW_PORTAINER_ADMIN_PASSWORD='file-portainer-password'\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SimpleInstallerError, "0600"):
                _prepare_bootstrap_environment(
                    {"TSW_INSTALL_ENV_FILE": operator_file.as_posix()},
                    REPOSITORY_ROOT,
                )

    def test_rejects_invalid_operator_file_syntax(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            operator_file = Path(temporary_dir) / "operator.env"
            operator_file.write_text("export TSW_PASSWORD=$(unsafe)\n", encoding="utf-8")
            operator_file.chmod(0o600)

            with self.assertRaisesRegex(SimpleInstallerError, "invalid"):
                _prepare_bootstrap_environment(
                    {"TSW_INSTALL_ENV_FILE": operator_file.as_posix()},
                    REPOSITORY_ROOT,
                )

    def test_rejects_invalid_explicit_bootstrap_file_syntax(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            override_file = Path(temporary_dir) / "bootstrap.env"
            override_file.write_text("export TSW_PASSWORD=$(unsafe)\n", encoding="utf-8")
            override_file.chmod(0o600)

            with self.assertRaisesRegex(SimpleInstallerError, "invalid"):
                _load_explicit_bootstrap_override(
                    {"TSW_BOOTSTRAP_SECRET_ENV_FILE": override_file.as_posix()},
                    REPOSITORY_ROOT,
                )

    def test_rejects_symlinked_bootstrap_override(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            target = root / "target.env"
            target.write_text("export TSW_PORTAINER_ADMIN_PASSWORD='value'\n", encoding="utf-8")
            target.chmod(0o600)
            link = root / "link.env"
            link.symlink_to(target)

            with self.assertRaisesRegex(SimpleInstallerError, "symbolic links"):
                _validate_secure_override_path(link)

    def test_rejects_windows_mounted_override_path(self):
        with self.assertRaisesRegex(SimpleInstallerError, "WSL-native"):
            _validate_secure_override_path(Path("/mnt/d/credential-override.env"))

    def test_rejects_override_when_metadata_cannot_be_verified(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            override_file = Path(temporary_dir) / "override.env"
            override_file.write_text("export TSW_PASSWORD='value'\n", encoding="utf-8")
            override_file.chmod(0o600)

            with (
                patch.object(Path, "resolve", return_value=override_file),
                patch.object(Path, "is_symlink", return_value=False),
                patch.object(Path, "stat", side_effect=OSError("stat failed")),
            ):
                with self.assertRaisesRegex(SimpleInstallerError, "metadata"):
                    _validate_secure_override_path(override_file)

    def test_populates_every_required_manifest_key_from_catalog(self):
        env = _prepare_bootstrap_environment({}, REPOSITORY_ROOT)
        entries = installer._required_installer_secret_entries(
            REPOSITORY_ROOT / installer.DEFAULT_SECRET_MANIFEST_PATH,
        )

        for entry in entries:
            with self.subTest(key=entry.key):
                self.assertEqual(env[entry.key], internal_test_credential(entry.key))

    def test_main_passes_single_credential_contract_to_legacy_execution(self):
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
        self.assertEqual(options.service_profile, "service-access")
        self.assertNotIn("TSW_SECRETS_MODE", run.call_args.kwargs["env"])

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
            override_file.chmod(0o600)
            state_file = root / "state" / "bootstrap-secrets.env"
            state_file.parent.mkdir()
            state_file.parent.chmod(0o700)
            state_file.write_text(
                "export TSW_PORTAINER_ADMIN_PASSWORD='relative-state-password'\n",
                encoding="utf-8",
            )
            state_file.chmod(0o600)

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
            override_file.chmod(0o600)

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

    def test_conflicting_explicit_bootstrap_override_paths_fail(self):
        with self.assertRaisesRegex(RuntimeError, "mutually exclusive"):
            _prepare_bootstrap_environment(
                {
                    "TSW_BOOTSTRAP_SECRET_ENV_FILE": "/tmp/bootstrap.env",
                    "TSW_BOOTSTRAP_STATE_DIR": "/tmp/bootstrap-state",
                },
                REPOSITORY_ROOT,
            )

    def test_completion_output_exposes_targets_without_printing_credential_values(self):
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
        self.assertIn("http://localhost:10001", rendered)
        self.assertIn("admin@example.invalid", rendered)
        self.assertIn("INTERNAL/TEST ONLY", rendered)
        self.assertIn("catalog default or protected operator override", rendered)
        self.assertIn("internal-test-credential-catalog.md", rendered)
        self.assertNotIn("portainer-visible", rendered)
        self.assertNotIn("infisical-visible", rendered)
        self.assertNotIn("must-stay-hidden", rendered)
        self.assertNotIn("also-hidden", rendered)
        self.assertIn("All other catalog-managed secrets are internal", rendered)

    def test_normal_cli_no_longer_exposes_secret_modes(self):
        install_script = (REPOSITORY_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("tiny_swarm_world.simple_installer", install_script)
        self.assertNotIn("tiny_swarm_world.installer", install_script)
        simple_source = (
            REPOSITORY_ROOT / "src/tiny_swarm_world/simple_installer.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"--secrets-mode"', simple_source)
        self.assertNotIn('"--no-generate-secrets"', simple_source)
        self.assertNotIn("_generated_secret_values", simple_source)


if __name__ == "__main__":
    unittest.main()

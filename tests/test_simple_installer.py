import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tiny_swarm_world.domain.configuration.configuration_contract import validate_traefik_htpasswd
from tiny_swarm_world.simple_installer import (
    _prepare_bootstrap_environment,
    _print_operator_credentials,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class TestSimpleInstallerSecretBootstrap(unittest.TestCase):
    def test_generates_once_and_reuses_one_canonical_secret_store(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            state_dir = Path(temporary_dir) / "state"
            base_env = {
                "TSW_BOOTSTRAP_STATE_DIR": state_dir.as_posix(),
                "HOME": temporary_dir,
            }

            first = _prepare_bootstrap_environment(base_env, REPOSITORY_ROOT)
            second = _prepare_bootstrap_environment(base_env, REPOSITORY_ROOT)

            secret_file = state_dir / "bootstrap-secrets.env"
            self.assertTrue(secret_file.is_file())
            self.assertEqual(secret_file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                first["TSW_PORTAINER_ADMIN_PASSWORD"],
                second["TSW_PORTAINER_ADMIN_PASSWORD"],
            )
            self.assertEqual(
                first["TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"],
                second["TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"],
            )
            self.assertEqual(first["TSW_INSTALL_ENV_FILE"], secret_file.as_posix())
            self.assertEqual(first["TSW_GENERATED_SECRET_ENV_FILE"], secret_file.as_posix())
            self.assertEqual(first["TSW_FIXED_SECRET_ENV_FILE"], secret_file.as_posix())
            self.assertNotEqual(
                first["TSW_INFISICAL_SECRET_ENV_FILE"],
                (REPOSITORY_ROOT / ".tiny-swarm/secrets/bootstrap.local.env").as_posix(),
            )

    def test_generates_internal_traefik_htpasswd_without_operator_input(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            env = _prepare_bootstrap_environment(
                {
                    "TSW_BOOTSTRAP_STATE_DIR": (Path(temporary_dir) / "state").as_posix(),
                    "HOME": temporary_dir,
                },
                REPOSITORY_ROOT,
            )

            value = env["TSW_TRAEFIK_GUI_USERS_HTPASSWD"]
            validate_traefik_htpasswd(value)
            self.assertTrue(value.startswith("admin:{SHA}"))

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


if __name__ == "__main__":
    unittest.main()

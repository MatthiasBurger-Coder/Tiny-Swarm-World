import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = REPOSITORY_ROOT / "install.sh"


class TestInstallScript(unittest.TestCase):
    def test_install_runs_reset_before_setup_and_records_evidence(self):
        with _install_script_fixture() as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                [
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world platform reset "
                        "--live --confirm RESET_TINY_SWARM_PLATFORM "
                        "--service-profile service-access"
                    ),
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world setup run "
                        "--live --service-profile service-access"
                    ),
                ],
                fixture.recorded_commands(),
            )
            evidence_dir = fixture.single_evidence_dir()
            self.assertEqual("0", (evidence_dir / "reset-run.exit").read_text().strip())
            self.assertEqual("0", (evidence_dir / "setup-run.exit").read_text().strip())
            self.assertTrue((evidence_dir / "reset-run.log").is_file())
            self.assertTrue((evidence_dir / "setup-run.log").is_file())
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("fresh_install_reset=required", context)
            self.assertIn("host_runtime_type=native_linux", context)
            self.assertIn("host_runtime_detection_source=test_override", context)
            self.assertIn(
                ".tiny-swarm-world/evidence/installation-tests/native_linux/",
                context,
            )
            self.assertIn("live_execution_mode=interactive", context)
            self.assertIn("live_approval_source=operator_prompt", context)
            self.assertIn("terminal_recording_mode=terminal_recorder", context)
            self.assertIn("reset_confirmation_present=yes", context)
            self.assertIn("reset_confirmation_source=interactive_prompt", context)
            self.assertIn("reset_exit=0", context)
            self.assertIn("setup_exit=0", context)

    def test_install_aborts_setup_when_reset_fails(self):
        with _install_script_fixture(reset_exit=17) as fixture:
            result = fixture.run()

            self.assertEqual(17, result.returncode)
            self.assertEqual(
                [
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world platform reset "
                        "--live --confirm RESET_TINY_SWARM_PLATFORM "
                        "--service-profile service-access"
                    ),
                ],
                fixture.recorded_commands(),
            )
            evidence_dir = fixture.single_evidence_dir()
            self.assertEqual("17", (evidence_dir / "reset-run.exit").read_text().strip())
            self.assertFalse((evidence_dir / "setup-run.exit").exists())
            self.assertTrue((evidence_dir / "reset-run.log").is_file())
            self.assertFalse((evidence_dir / "setup-run.log").exists())
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("reset_exit=17", context)
            self.assertIn("setup_skipped_due_to_reset_failure=yes", context)
            self.assertIn("Setup will not start", result.stderr)

    def test_install_records_setup_failure_after_successful_reset(self):
        with _install_script_fixture(setup_exit=23) as fixture:
            result = fixture.run()

            self.assertEqual(23, result.returncode)
            self.assertEqual(2, len(fixture.recorded_commands()))
            evidence_dir = fixture.single_evidence_dir()
            self.assertEqual("0", (evidence_dir / "reset-run.exit").read_text().strip())
            self.assertEqual("23", (evidence_dir / "setup-run.exit").read_text().strip())
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("reset_exit=0", context)
            self.assertIn("setup_exit=23", context)
            self.assertNotIn("Installation completed successfully.", result.stdout)

    def test_install_forwards_selected_service_profile_to_reset_and_setup(self):
        with _install_script_fixture(extra_args=("--service-profile", "default")) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                [
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world platform reset "
                        "--live --confirm RESET_TINY_SWARM_PLATFORM "
                        "--service-profile default"
                    ),
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world setup run "
                        "--live --service-profile default"
                    ),
                ],
                fixture.recorded_commands(),
            )

    def test_install_refuses_missing_reset_confirmation_before_script_execution(self):
        with _install_script_fixture(reset_confirmation="wrong") as fixture:
            result = fixture.run()

            self.assertEqual(1, result.returncode)
            self.assertEqual([], fixture.recorded_commands())
            self.assertIn("confirmation did not match", result.stderr)

    def test_install_confirm_reset_flag_skips_interactive_reset_phrase(self):
        with _install_script_fixture(
            extra_args=("--confirm-reset",),
            reset_confirmation="",
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(2, len(fixture.recorded_commands()))
            self.assertIn(
                "Fresh-install reset confirmed by explicit --confirm-reset flag.",
                result.stdout,
            )
            evidence_dir = fixture.single_evidence_dir()
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("reset_confirmation_present=yes", context)
            self.assertIn("reset_confirmation_source=explicit_flag", context)

    def test_install_requires_infisical_encryption_key_value(self):
        secret_environment = _required_secret_environment()
        secret_environment.pop("TSW_INFISICAL_ENCRYPTION_KEY")
        with _install_script_fixture(secret_environment=secret_environment) as fixture:
            result = fixture.run()

            self.assertEqual(1, result.returncode)
            self.assertEqual([], fixture.recorded_commands())
            self.assertIn("TSW_INFISICAL_ENCRYPTION_KEY", result.stderr)

    def test_install_generates_infisical_platform_secrets(self):
        secret_environment = _required_secret_environment()
        secret_environment.pop("TSW_INFISICAL_LOGIN_EMAIL")
        secret_environment.pop("TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD")
        secret_environment.pop("TSW_INFISICAL_ENCRYPTION_KEY")
        secret_environment.pop("TSW_INFISICAL_AUTH_SECRET")
        secret_environment.pop("TSW_INFISICAL_POSTGRES_PASSWORD")
        with _install_script_fixture(
            secret_environment=secret_environment,
            generate_secrets=True,
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            secret_file = fixture.root / ".tiny-swarm-world" / "local" / "live-installation.env"
            secret_content = secret_file.read_text()
            self.assertIn("TSW_INFISICAL_LOGIN_EMAIL=", secret_content)
            self.assertIn("TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD=", secret_content)
            self.assertIn("TSW_INFISICAL_ENCRYPTION_KEY=", secret_content)
            self.assertIn("TSW_INFISICAL_AUTH_SECRET=", secret_content)
            self.assertIn("TSW_INFISICAL_POSTGRES_PASSWORD=", secret_content)
            infisical_secret_content = (
                fixture.root / ".tiny-swarm" / "secrets" / "bootstrap.local.env"
            ).read_text()
            self.assertIn("TSW_DASHBOARD_URL=http://localhost:10000", infisical_secret_content)
            self.assertIn("TSW_INFISICAL_URL=http://localhost:17080", infisical_secret_content)
            self.assertIn("TSW_JENKINS_URL=http://localhost:11080", infisical_secret_content)
            self.assertIn("TSW_NEXUS_URL=http://localhost:13081", infisical_secret_content)
            self.assertIn("TSW_PORTAINER_URL=http://localhost:10001", infisical_secret_content)
            self.assertIn("TSW_PULSAR_PUBLIC_ADMIN_URL=http://localhost:14080", infisical_secret_content)
            self.assertIn("TSW_PULSAR_MANAGER_URL=http://localhost:14081", infisical_secret_content)
            self.assertIn("TSW_SONARQUBE_URL=http://localhost:12000", infisical_secret_content)
            self.assertIn("TSW_SWAGGER_URL=http://localhost:16081", infisical_secret_content)
            self.assertIn("TSW_INFISICAL_LOGIN_EMAIL=admin@tiny-swarm-world.local", infisical_secret_content)
            self.assertIn("TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD=", infisical_secret_content)
            self.assertNotIn("export INITIAL_BOOTSTRAP_ADMIN_EMAIL=", infisical_secret_content)
            self.assertNotIn("export INITIAL_BOOTSTRAP_ADMIN_PASSWORD=", infisical_secret_content)
            self.assertNotIn("export ENCRYPTION_KEY=", infisical_secret_content)

    def test_install_regenerates_sonarqube_password_without_special_character(self):
        secret_environment = _required_secret_environment()
        secret_environment["TSW_SONARQUBE_ADMIN_PASSWORD"] = "sonarqube-password"
        with _install_script_fixture(
            secret_environment=secret_environment,
            generate_secrets=True,
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            secret_content = (
                fixture.root / ".tiny-swarm-world" / "local" / "live-installation.env"
            ).read_text()
            generated_content = (
                fixture.root / ".tiny-swarm" / "secrets" / "generated.local.env"
            ).read_text()
            self.assertIn("Regenerated by install.sh for SonarQube password policy", secret_content)
            self.assertIn("TSW_SONARQUBE_ADMIN_PASSWORD=", secret_content)
            self.assertIn("TSW_SONARQUBE_ADMIN_PASSWORD=", generated_content)

    def test_install_refuses_invalid_sonarqube_password_without_secret_generation(self):
        secret_environment = _required_secret_environment()
        secret_environment["TSW_SONARQUBE_ADMIN_PASSWORD"] = "sonarqube-password"
        with _install_script_fixture(secret_environment=secret_environment) as fixture:
            result = fixture.run()

            self.assertEqual(1, result.returncode)
            self.assertEqual([], fixture.recorded_commands())
            self.assertIn("TSW_SONARQUBE_ADMIN_PASSWORD must be", result.stderr)

    def test_install_writes_default_traefik_tls_secret_names(self):
        with _install_script_fixture() as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            secret_file = fixture.root / ".tiny-swarm-world" / "local" / "live-installation.env"
            secret_content = secret_file.read_text()
            self.assertIn("TSW_TRAEFIK_TLS_CERT_SECRET_NAME=tsw_traefik_tls_cert", secret_content)
            self.assertIn("TSW_TRAEFIK_TLS_KEY_SECRET_NAME=tsw_traefik_tls_key", secret_content)

    def test_interactive_install_does_not_pipe_live_consent_into_cli_prompt(self):
        with _install_script_fixture() as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(["", ""], fixture.recorded_live_confirmations())

    def test_noninteractive_live_approval_flag_passes_explicit_cli_approval(self):
        with _install_script_fixture(
            extra_args=("--non-interactive-live-approval",),
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                [
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world platform reset "
                        "--live --approve-live --confirm RESET_TINY_SWARM_PLATFORM "
                        "--service-profile service-access"
                    ),
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world setup run "
                        "--live --approve-live --service-profile service-access"
                    ),
                ],
                fixture.recorded_commands(),
            )
            evidence_dir = fixture.single_evidence_dir()
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("live_execution_mode=non_interactive", context)
            self.assertIn("live_approval_source=explicit_automation_flag", context)
            self.assertEqual(["", ""], fixture.recorded_live_confirmations())

    def test_headless_install_runs_governed_commands_without_terminal_recorder(self):
        with _install_script_fixture(
            extra_args=("--headless", "--non-interactive-live-approval"),
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                [
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world platform reset "
                        "--live --approve-live --confirm RESET_TINY_SWARM_PLATFORM "
                        "--service-profile service-access"
                    ),
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world setup run "
                        "--live --approve-live --service-profile service-access"
                    ),
                ],
                fixture.recorded_commands(),
            )
            evidence_dir = fixture.single_evidence_dir()
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("terminal_recording_mode=headless", context)
            self.assertIn("live_execution_mode=non_interactive", context)
            self.assertEqual("0", (evidence_dir / "reset-run.exit").read_text().strip())
            self.assertEqual("0", (evidence_dir / "setup-run.exit").read_text().strip())
            self.assertIn("fake headless command", (evidence_dir / "reset-run.log").read_text())
            self.assertIn("fake headless command", (evidence_dir / "setup-run.log").read_text())
            self.assertFalse(fixture.recorded_live_confirmations())

    def test_headless_install_preserves_reset_failure_exit_code_and_skips_setup(self):
        with _install_script_fixture(
            reset_exit=17,
            extra_args=("--headless", "--non-interactive-live-approval"),
        ) as fixture:
            result = fixture.run()

            self.assertEqual(17, result.returncode)
            self.assertEqual(1, len(fixture.recorded_commands()))
            evidence_dir = fixture.single_evidence_dir()
            self.assertEqual("17", (evidence_dir / "reset-run.exit").read_text().strip())
            self.assertFalse((evidence_dir / "setup-run.exit").exists())
            self.assertFalse(fixture.recorded_live_confirmations())

    def test_headless_install_can_be_enabled_by_environment(self):
        with _install_script_fixture(
            extra_args=("--non-interactive-live-approval",),
            extra_environment={"TSW_INSTALL_HEADLESS": "1"},
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            evidence_dir = fixture.single_evidence_dir()
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("terminal_recording_mode=headless", context)
            self.assertIn("fake headless command", (evidence_dir / "reset-run.log").read_text())
            self.assertIn("fake headless command", (evidence_dir / "setup-run.log").read_text())
            self.assertFalse(fixture.recorded_live_confirmations())

    def test_headless_install_can_run_with_fixed_secret_file(self):
        fixed_secrets = _required_fixed_secret_environment()
        fixed_value = fixed_secrets["TSW_NEXUS_ADMIN_PASSWORD"]
        with _install_script_fixture(
            extra_args=(
                "--secrets-mode",
                "fixed",
                "--headless",
                "--confirm-reset",
                "--non-interactive-live-approval",
            ),
            fixed_secret_environment=fixed_secrets,
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                [
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world platform reset "
                        "--live --approve-live --confirm RESET_TINY_SWARM_PLATFORM "
                        "--service-profile service-access"
                    ),
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world setup run "
                        "--live --approve-live --service-profile service-access"
                    ),
                ],
                fixture.recorded_commands(),
            )
            context = (fixture.single_evidence_dir() / "context.txt").read_text()
            self.assertIn("secrets_mode=fixed", context)
            self.assertIn("TSW_NEXUS_ADMIN_PASSWORD", context)
            self.assertNotIn(fixed_value, context)

    def test_install_disables_infisical_item_seed_by_default(self):
        with _install_script_fixture() as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(["0", "0"], fixture.recorded_seed_flags())

    def test_native_linux_bootstraps_missing_python_dependencies_into_local_venv(self):
        with _install_script_fixture(
            skip_native_dependency_bootstrap=False,
            extra_environment={"TSW_INSTALL_TEST_FORCE_MISSING_IMPORTS": "1"},
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(
                (fixture.root / ".tiny-swarm-world" / "install-venv" / "bin" / "python").is_file()
            )
            venv_python = (fixture.root / ".tiny-swarm-world" / "install-venv" / "bin" / "python").as_posix()
            self.assertEqual(
                [
                    (
                        f"PYTHONPATH=src {venv_python} -m tiny_swarm_world platform reset "
                        "--live --confirm RESET_TINY_SWARM_PLATFORM --service-profile service-access"
                    ),
                    (
                        f"PYTHONPATH=src {venv_python} -m tiny_swarm_world setup run "
                        "--live --service-profile service-access"
                    ),
                ],
                fixture.recorded_commands(),
            )

    def test_wsl_path_keeps_python3_when_dependency_bootstrap_is_skipped(self):
        with _install_script_fixture(
            extra_environment={
                "TSW_INSTALL_TEST_HOST_RUNTIME": "wsl2",
                "TSW_WINDOWS_EXPOSURE": "disabled",
                "WSL_DISTRO_NAME": "Ubuntu",
            },
        ) as fixture:
            result = fixture.run()

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((fixture.root / ".tiny-swarm-world" / "install-venv").exists())
            self.assertIn("PYTHONPATH=src python3 -m tiny_swarm_world", fixture.recorded_commands()[0])
            evidence_dir = fixture.single_evidence_dir("wsl2")
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("host_runtime_type=wsl2", context)
            self.assertIn("host_runtime_detection_source=test_override", context)
            self.assertIn("windows_wsl_bridge_reason=windows_exposure_disabled", context)

    def test_native_linux_and_wsl2_use_distinct_evidence_directories(self):
        with _install_script_fixture() as native_fixture:
            native_result = native_fixture.run()

            self.assertEqual(0, native_result.returncode, native_result.stderr)
            native_evidence_dir = native_fixture.single_evidence_dir("native_linux")
            self.assertIn(
                ".tiny-swarm-world/evidence/installation-tests/native_linux/",
                native_evidence_dir.as_posix(),
            )

        with _install_script_fixture(
            extra_environment={
                "TSW_INSTALL_TEST_HOST_RUNTIME": "wsl2",
                "TSW_WINDOWS_EXPOSURE": "disabled",
                "WSL_DISTRO_NAME": "Ubuntu",
            },
        ) as wsl_fixture:
            wsl_result = wsl_fixture.run()

            self.assertEqual(0, wsl_result.returncode, wsl_result.stderr)
            wsl_evidence_dir = wsl_fixture.single_evidence_dir("wsl2")
            self.assertIn(
                ".tiny-swarm-world/evidence/installation-tests/wsl2/",
                wsl_evidence_dir.as_posix(),
            )

    def test_wsl_install_aborts_before_reset_when_windows_bridge_is_missing(self):
        with _install_script_fixture(
            extra_environment={
                "TSW_INSTALL_TEST_HOST_RUNTIME": "wsl2",
                "WSL_DISTRO_NAME": "Ubuntu",
            },
        ) as fixture:
            result = fixture.run()

            self.assertEqual(1, result.returncode)
            self.assertEqual([], fixture.recorded_commands())
            evidence_dir = fixture.single_evidence_dir("wsl2")
            context = (evidence_dir / "context.txt").read_text()
            self.assertIn("windows_wsl_bridge_passed=no", context)
            self.assertIn("windows_wsl_bridge_reason=state_missing", context)
            self.assertIn("reset_skipped_due_to_windows_wsl_bridge=yes", context)
            self.assertFalse((evidence_dir / "reset-run.exit").exists())
            self.assertFalse((evidence_dir / "setup-run.exit").exists())
            self.assertIn("Windows <-> WSL bridge is not prepared", result.stderr)


class _InstallScriptFixture:
    def __init__(
        self,
        reset_exit: int = 0,
        setup_exit: int = 0,
        extra_args: tuple[str, ...] = (),
        reset_confirmation: str = "RESET_TINY_SWARM_PLATFORM",
        secret_environment: dict[str, str] | None = None,
        fixed_secret_environment: dict[str, str] | None = None,
        generate_secrets: bool = False,
        skip_native_dependency_bootstrap: bool = True,
        extra_environment: dict[str, str] | None = None,
    ):
        self.reset_exit = reset_exit
        self.setup_exit = setup_exit
        self.extra_args = extra_args
        self.reset_confirmation = reset_confirmation
        self.secret_environment = secret_environment
        self.fixed_secret_environment = fixed_secret_environment
        self.generate_secrets = generate_secrets
        self.skip_native_dependency_bootstrap = skip_native_dependency_bootstrap
        self.extra_environment = extra_environment or {}
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name)
        self.fake_bin = self.root / "fake-bin"
        self.commands_file = self.root / "commands.txt"

    def __enter__(self):
        self._prepare()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._tempdir.cleanup()

    def run(self) -> subprocess.CompletedProcess[str]:
        env = {
            **{
                key: value
                for key, value in os.environ.items()
                if key
                not in (
                    *_install_secret_environment_names(),
                    *_wsl_environment_names(),
                )
            },
            **(self.secret_environment or _required_secret_environment()),
            "PATH": f"{self.fake_bin}:{os.environ['PATH']}",
            "TSW_FAKE_SCRIPT_COMMANDS": str(self.commands_file),
            "TSW_FAKE_RESET_EXIT": str(self.reset_exit),
            "TSW_FAKE_SETUP_EXIT": str(self.setup_exit),
            "TSW_INSTALL_ENV_FILE": ".tiny-swarm-world/local/live-installation.env",
            "TSW_INSTALL_SKIP_NATIVE_DEPENDENCY_BOOTSTRAP": (
                "1" if self.skip_native_dependency_bootstrap else "0"
            ),
            "TSW_INSTALL_SKIP_NATIVE_GROUP_SWITCH": "1",
            "TSW_INSTALL_TEST_MODE": "1",
            "TSW_INSTALL_TEST_HOST_RUNTIME": "native_linux",
            **self.extra_environment,
        }
        return subprocess.run(
            [
                "bash",
                str(self.root / "install.sh"),
                *(() if self.generate_secrets else ("--no-generate-secrets",)),
                *self.extra_args,
            ],
            cwd=self.root,
            env=env,
            input=f"{self.reset_confirmation}\n",
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )

    def recorded_commands(self) -> list[str]:
        if not self.commands_file.exists():
            return []
        return self.commands_file.read_text().splitlines()

    def recorded_live_confirmations(self) -> list[str]:
        confirmations_file = self.root / "live-confirmations.txt"
        if not confirmations_file.exists():
            return []
        return confirmations_file.read_text().splitlines()

    def recorded_seed_flags(self) -> list[str]:
        seed_file = self.root / "seed-flags.txt"
        if not seed_file.exists():
            return []
        return seed_file.read_text().splitlines()

    def single_evidence_dir(self, host_directory: str = "native_linux") -> Path:
        evidence_root = (
            self.root
            / ".tiny-swarm-world"
            / "evidence"
            / "installation-tests"
            / host_directory
        )
        evidence_dirs = tuple(evidence_root.iterdir())
        self_test = unittest.TestCase()
        self_test.assertEqual(1, len(evidence_dirs))
        return evidence_dirs[0]

    def _prepare(self) -> None:
        shutil.copy2(INSTALL_SCRIPT, self.root / "install.sh")
        (self.root / "src" / "tiny_swarm_world").mkdir(parents=True)
        (self.root / "src" / "tiny_swarm_world" / "__init__.py").write_text("")
        shutil.copy2(
            REPOSITORY_ROOT / "src" / "tiny_swarm_world" / "installer.py",
            self.root / "src" / "tiny_swarm_world" / "installer.py",
        )
        (self.root / "infra" / "config" / "secrets").mkdir(parents=True)
        shutil.copy2(
            REPOSITORY_ROOT / "infra" / "config" / "secrets" / "infisical-secrets.yaml",
            self.root / "infra" / "config" / "secrets" / "infisical-secrets.yaml",
        )
        self.fake_bin.mkdir()
        _write_executable(self.fake_bin / "python3", _fake_python3())
        _write_executable(self.fake_bin / "grep", _fake_grep())
        _write_executable(self.fake_bin / "script", _fake_script())
        if self.fixed_secret_environment is not None:
            fixed_file = self.root / ".tiny-swarm-world" / "local" / "fixed-secrets.env"
            _write_env_file(fixed_file, self.fixed_secret_environment)


def _install_script_fixture(
    reset_exit: int = 0,
    setup_exit: int = 0,
    extra_args: tuple[str, ...] = (),
    reset_confirmation: str = "RESET_TINY_SWARM_PLATFORM",
    secret_environment: dict[str, str] | None = None,
    fixed_secret_environment: dict[str, str] | None = None,
    generate_secrets: bool = False,
    skip_native_dependency_bootstrap: bool = True,
    extra_environment: dict[str, str] | None = None,
) -> _InstallScriptFixture:
    return _InstallScriptFixture(
        reset_exit=reset_exit,
        setup_exit=setup_exit,
        extra_args=extra_args,
        reset_confirmation=reset_confirmation,
        secret_environment=secret_environment,
        fixed_secret_environment=fixed_secret_environment,
        generate_secrets=generate_secrets,
        skip_native_dependency_bootstrap=skip_native_dependency_bootstrap,
        extra_environment=extra_environment,
    )


def _required_secret_environment() -> dict[str, str]:
    return {
        "TSW_PORTAINER_ADMIN_PASSWORD": "portainer-admin-password",
        "TSW_NEXUS_ADMIN_PASSWORD": "nexus-password",
        "TSW_JENKINS_ADMIN_PASSWORD": "jenkins-password",
        "TSW_SONARQUBE_ADMIN_PASSWORD": "sonarqube-password!",
        "TSW_POSTGRES_PASSWORD": "postgres-password",
        "TSW_SONARQUBE_POSTGRES_PASSWORD": "sonarqube-postgres-password",
        "TSW_PULSAR_TOKEN_SECRET_KEY": "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        "TSW_PULSAR_ADMIN_TOKEN": "header.payload.signature",
        "TSW_PULSAR_MANAGER_ADMIN_PASSWORD": "pulsar-manager-password",
        "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
        "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": "infisical-bootstrap-admin-password",
        "TSW_INFISICAL_ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef",
        "TSW_INFISICAL_AUTH_SECRET": "infisical-auth-secret",
        "TSW_INFISICAL_POSTGRES_PASSWORD": "infisical-postgres-password",
        "TSW_INFISICAL_REDIS_PASSWORD": "infisical-redis-password",
    }


def _required_fixed_secret_environment() -> dict[str, str]:
    return {
        **_required_secret_environment(),
        "TSW_TRAEFIK_TLS_CERT_SECRET_NAME": "tsw_traefik_tls_cert",
        "TSW_TRAEFIK_TLS_KEY_SECRET_NAME": "tsw_traefik_tls_key",
    }


def _install_secret_environment_names() -> tuple[str, ...]:
    return (
        *tuple(_required_secret_environment()),
        "TSW_TRAEFIK_TLS_CERT_SECRET_NAME",
        "TSW_TRAEFIK_TLS_KEY_SECRET_NAME",
    )


def _wsl_environment_names() -> tuple[str, ...]:
    return (
        "WSL_DISTRO_NAME",
        "WSL_INTEROP",
    )


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def _write_env_file(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"export {key}='{value}'\n" for key, value in values.items()),
        encoding="utf-8",
    )


def _fake_grep() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail
        if [[ "$*" == *microsoft* || "$*" == *wsl* ]]; then
          exit 1
        fi
        exec /usr/bin/grep "$@"
        """
    )


def _fake_python3() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail
        if [[ "${1:-}" == "-c" ]]; then
          exit "${TSW_FAKE_IMPORT_CHECK_EXIT:-1}"
        fi
        if [[ "${1:-}" == "-m" && "${2:-}" == "venv" ]]; then
          target="$3"
          mkdir -p "$target/bin"
          cat >"$target/bin/python" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "-c" ]]; then
  exit 0
fi
if [[ "${1:-}" == "-m" && "${2:-}" == "pip" ]]; then
  exit 0
fi
if [[ "${1:-}" == "-m" && "${2:-}" == "tiny_swarm_world" ]]; then
  printf 'PYTHONPATH=%s %s %s\\n' "${PYTHONPATH:-}" "$0" "$*" >>"$TSW_FAKE_SCRIPT_COMMANDS"
  printf 'fake headless command for %s\\n' "$*"
  case "$*" in
    *" platform reset "*)
      exit "$TSW_FAKE_RESET_EXIT"
      ;;
    *" setup run "*)
      exit "$TSW_FAKE_SETUP_EXIT"
      ;;
    *)
      exit 99
      ;;
  esac
fi
printf 'fake venv python should only handle import checks and pip\\n' >&2
exit 44
SH
          chmod 755 "$target/bin/python"
          exit 0
        fi
        if [[ "${1:-}" == "-m" && "${2:-}" == "tiny_swarm_world.installer" ]]; then
          exec /usr/bin/python3 "$@"
        fi
        if [[ "${1:-}" == "-m" && "${2:-}" == "tiny_swarm_world" ]]; then
          printf 'PYTHONPATH=%s python3 %s\\n' "${PYTHONPATH:-}" "$*" >>"$TSW_FAKE_SCRIPT_COMMANDS"
          printf 'fake headless command for %s\\n' "$*"
          case "$*" in
            *" platform reset "*)
              exit "$TSW_FAKE_RESET_EXIT"
              ;;
            *" setup run "*)
              exit "$TSW_FAKE_SETUP_EXIT"
              ;;
            *)
              exit 99
              ;;
          esac
        fi
        printf 'fake python3 should be invoked only through fake script or secret generation\\n' >&2
        exit 43
        """
    )


def _fake_script() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        command_line=""
        log_file=""
        while [[ $# -gt 0 ]]; do
          case "$1" in
            -q|-e)
              shift
              ;;
            -c)
              command_line="$2"
              shift 2
              ;;
            *)
              log_file="$1"
              shift
              ;;
          esac
        done

        confirmation=""
        IFS= read -r confirmation || true
        printf '%s\\n' "$command_line" >>"$TSW_FAKE_SCRIPT_COMMANDS"
        printf '%s\\n' "$confirmation" >>"$(dirname "$TSW_FAKE_SCRIPT_COMMANDS")/live-confirmations.txt"
        printf '%s\\n' "${TSW_SEED_INFISICAL_ITEMS:-}" >>"$(dirname "$TSW_FAKE_SCRIPT_COMMANDS")/seed-flags.txt"
        mkdir -p "$(dirname "$log_file")"
        printf 'fake script log for %s\\n' "$command_line" >"$log_file"

        case "$command_line" in
          *" platform reset "*)
            exit "$TSW_FAKE_RESET_EXIT"
            ;;
          *" setup run "*)
            exit "$TSW_FAKE_SETUP_EXIT"
            ;;
          *)
            exit 99
            ;;
        esac
        """
    )



if __name__ == "__main__":
    unittest.main()

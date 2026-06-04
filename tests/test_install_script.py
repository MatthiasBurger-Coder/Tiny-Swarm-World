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
                        "--service-profile 'service-access'"
                    ),
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world setup run "
                        "--live --service-profile 'service-access'"
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
            self.assertIn("reset_confirmation_present=yes", context)
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
                        "--service-profile 'service-access'"
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
                        "--service-profile 'default'"
                    ),
                    (
                        "PYTHONPATH=src python3 -m tiny_swarm_world setup run "
                        "--live --service-profile 'default'"
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


class _InstallScriptFixture:
    def __init__(
        self,
        reset_exit: int = 0,
        setup_exit: int = 0,
        extra_args: tuple[str, ...] = (),
        reset_confirmation: str = "RESET_TINY_SWARM_PLATFORM",
    ):
        self.reset_exit = reset_exit
        self.setup_exit = setup_exit
        self.extra_args = extra_args
        self.reset_confirmation = reset_confirmation
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
            **os.environ,
            **_required_secret_environment(),
            "PATH": f"{self.fake_bin}:{os.environ['PATH']}",
            "TSW_FAKE_SCRIPT_COMMANDS": str(self.commands_file),
            "TSW_FAKE_RESET_EXIT": str(self.reset_exit),
            "TSW_FAKE_SETUP_EXIT": str(self.setup_exit),
            "TSW_INSTALL_ENV_FILE": ".tiny-swarm-world/local/live-installation.env",
        }
        return subprocess.run(
            [
                "bash",
                str(self.root / "install.sh"),
                "--no-generate-secrets",
                *self.extra_args,
            ],
            cwd=self.root,
            env=env,
            input=f"{self.reset_confirmation}\n",
            text=True,
            capture_output=True,
            check=False,
        )

    def recorded_commands(self) -> list[str]:
        if not self.commands_file.exists():
            return []
        return self.commands_file.read_text().splitlines()

    def single_evidence_dir(self) -> Path:
        evidence_root = self.root / ".tiny-swarm-world" / "evidence" / "installation-tests" / "wsl2"
        evidence_dirs = tuple(evidence_root.iterdir())
        self_test = unittest.TestCase()
        self_test.assertEqual(1, len(evidence_dirs))
        return evidence_dirs[0]

    def _prepare(self) -> None:
        shutil.copy2(INSTALL_SCRIPT, self.root / "install.sh")
        (self.root / "src" / "tiny_swarm_world").mkdir(parents=True)
        self.fake_bin.mkdir()
        _write_executable(self.fake_bin / "python3", _fake_python3())
        _write_executable(self.fake_bin / "script", _fake_script())


def _install_script_fixture(
    reset_exit: int = 0,
    setup_exit: int = 0,
    extra_args: tuple[str, ...] = (),
    reset_confirmation: str = "RESET_TINY_SWARM_PLATFORM",
) -> _InstallScriptFixture:
    return _InstallScriptFixture(
        reset_exit=reset_exit,
        setup_exit=setup_exit,
        extra_args=extra_args,
        reset_confirmation=reset_confirmation,
    )


def _required_secret_environment() -> dict[str, str]:
    return {
        "TSW_PORTAINER_PASSWORD": "portainer-password",
        "TSW_NEXUS_ADMIN_PASSWORD": "nexus-password",
        "TSW_JENKINS_ADMIN_PASSWORD": "jenkins-password",
        "TSW_RABBITMQ_PASSWORD": "rabbitmq-password",
        "TSW_SONARQUBE_ADMIN_PASSWORD": "sonarqube-password",
        "TSW_POSTGRES_PASSWORD": "postgres-password",
        "TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "vaultwarden-token",
    }


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def _fake_python3() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        printf 'fake python3 should be invoked only through fake script\\n' >&2
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

        printf '%s\\n' "$command_line" >>"$TSW_FAKE_SCRIPT_COMMANDS"
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

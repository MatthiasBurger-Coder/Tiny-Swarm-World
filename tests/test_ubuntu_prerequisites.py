"""BOOT-W02 acceptance coverage; all host/package operations are simulated."""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from tests.test_prepare_linux import QUALIFIED
from tiny_swarm_world.application.services.native_preparation import NativePreparationService
from tiny_swarm_world.infrastructure.adapters.installation.prerequisites import (
    validate_assets, validate_user_paths,
)
from tiny_swarm_world.infrastructure.adapters.installation import process
from tiny_swarm_world.infrastructure.process import ProcessTimeoutError
from tiny_swarm_world.infrastructure.adapters.native_package_manager import AptHostPackageManager
from tiny_swarm_world.prepare_linux import main

ROOT = Path(__file__).resolve().parents[1]


class UbuntuPreparationAcceptanceTests(unittest.TestCase):
    def setUp(self):
        boundary = patch("tiny_swarm_world.prepare_linux.run_incus_preparation", return_value=0)
        self.incus_boundary = boundary.start()
        self.addCleanup(boundary.stop)

    def test_ac1_native_and_wsl_fresh_packages_then_python_with_separate_consent(self):
        for wsl in (False, True):
            facts = replace(QUALIFIED, is_wsl=wsl, wsl2=wsl, kernel_ready=False)
            packages = Mock(missing=Mock(side_effect=(("incus", "git"), ("incus", "git"), ())))
            service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages, prerequisites_only=True)
            with (
                patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
                patch("tiny_swarm_world.prepare_linux._validate_mutation_paths"),
                patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer") as evidence,
                patch("tiny_swarm_world.prepare_linux._prepare_python_dependencies", return_value=0) as python,
                patch("builtins.input", return_value="yes"),
                redirect_stdout(io.StringIO()),
            ):
                evidence.return_value.write.return_value = Path("/redacted/evidence")
                self.assertEqual(main(()), 0)
            packages.install.assert_called_once_with(("incus", "git"))
            python.assert_called_once_with(read_only=False)

    def test_ac2_wsl1_and_missing_systemd_block_before_inventory(self):
        for facts in (
            replace(QUALIFIED, is_wsl=True),
            replace(QUALIFIED, is_wsl=True, wsl2=True, systemd_ready=False),
        ):
            packages = Mock()
            service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages, prerequisites_only=True)
            self.assertFalse(service.plan().qualified)
            packages.missing.assert_not_called()

    def test_wsl_memory_floor_does_not_inherit_native_exception(self):
        facts = replace(QUALIFIED, is_wsl=True, wsl2=True, memory_bytes=15 * 1024**3)
        service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), Mock(missing=Mock(return_value=())), prerequisites_only=True)
        self.assertIn("16 GiB", " ".join(service.plan().failures))

    def test_ac4_failed_package_attempt_records_observed_partial_state_and_stops_python(self):
        facts = replace(QUALIFIED, kernel_ready=False)
        packages = Mock(missing=Mock(side_effect=(("git", "incus"), ("git", "incus"), ("incus",))))
        packages.install.side_effect = RuntimeError("sensitive APT output")
        service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages, prerequisites_only=True)
        output = io.StringIO()
        with (
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
            patch("tiny_swarm_world.prepare_linux._validate_mutation_paths"),
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer") as evidence,
            patch("tiny_swarm_world.prepare_linux._prepare_python_dependencies") as python,
            patch("builtins.input", return_value="yes"),
            redirect_stdout(output), redirect_stderr(output),
        ):
            evidence.return_value.write.return_value = Path("/redacted/evidence")
            self.assertEqual(main(()), 1)
        final = evidence.return_value.write.call_args.kwargs
        self.assertEqual(final["added"], ("git",))
        self.assertEqual(final["uncertain"], ("incus",))
        python.assert_not_called()
        self.assertNotIn("sensitive", output.getvalue())
        self.assertIn("./prepare_linux.sh --dry-run", output.getvalue())

    def test_ac3_read_only_never_validates_mutation_paths_writes_evidence_or_prompts(self):
        service = NativePreparationService(Mock(inspect=Mock(return_value=QUALIFIED)), Mock(missing=Mock(return_value=("incus",))), prerequisites_only=True)
        for option in ("--dry-run", "--preflight"):
            with (
                patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
                patch("tiny_swarm_world.prepare_linux._validate_mutation_paths") as paths,
                patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer") as evidence,
                patch("tiny_swarm_world.prepare_linux._prepare_python_dependencies", return_value=0) as python,
                patch("builtins.input") as prompt,
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main((option,)), 2)
            paths.assert_not_called()
            evidence.assert_not_called()
            prompt.assert_not_called()
            python.assert_called_once_with(read_only=True)

    def test_apt_connectivity_lock_and_timeout_are_bounded_and_stop_install(self):
        runner = Mock()
        runner.run_text.side_effect = ProcessTimeoutError()
        with self.assertRaisesRegex(RuntimeError, "could not finish"):
            AptHostPackageManager(runner).install(("incus",))
        self.assertEqual(runner.run_text.call_count, 1)
        command = runner.run_text.call_args.args[0]
        self.assertIn("DPkg::Lock::Timeout=30", command)
        self.assertIn("APT::Update::Error-Mode=any", command)
        self.assertEqual(runner.run_text.call_args.kwargs["timeout"], 900)

    def test_pip_failure_is_safe_and_actionable(self):
        with patch.object(process, "run_process", side_effect=subprocess.CalledProcessError(1, "pip", stderr="secret")):
            with self.assertRaisesRegex(RuntimeError, "./prepare_linux.sh --dry-run") as error:
                process._run_installer_subprocess(("python3", "-m", "pip"), env={}, check=True)
        self.assertNotIn("secret", str(error.exception))


class UserRuntimeSafetyTests(unittest.TestCase):
    def test_release_lock_validated_without_writes_and_rejects_unhashed_input(self):
        validate_assets(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/tiny_swarm_world").mkdir(parents=True)
            (root / "src/tiny_swarm_world/prepare_linux.py").touch()
            (root / "pyproject.toml").touch()
            (root / "requirements.build.lock").write_text((ROOT / "requirements.build.lock").read_text())
            (root / "requirements.lock").write_text("requests==2.34.2\n")
            with self.assertRaisesRegex(RuntimeError, "SHA256"):
                validate_assets(root)
            self.assertFalse((root / "venv").exists())

    def test_preserves_unknown_and_symlinked_venv_and_rejects_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            venv = root / "venv"
            venv.mkdir()
            sentinel = venv / "foreign"
            sentinel.write_text("preserve")
            with self.assertRaisesRegex(RuntimeError, "not a recognized"):
                validate_user_paths(root, venv, is_wsl=False)
            self.assertEqual(sentinel.read_text(), "preserve")
            link = root / "linked"
            link.symlink_to(venv)
            with self.assertRaisesRegex(RuntimeError, "symlinks"):
                validate_user_paths(root, link, is_wsl=False)
            with patch("os.geteuid", return_value=0):
                with self.assertRaisesRegex(RuntimeError, "ordinary user"):
                    validate_user_paths(root, root / "new", is_wsl=False)
            self.assertFalse((root / "new").exists())

    def test_symlinked_venv_metadata_preserves_external_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            venv = root / "venv"
            venv.mkdir()
            target = root / "preserve"
            target.write_text("original")
            (venv / "pyvenv.cfg").symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, "not a recognized"):
                validate_user_paths(root, venv, is_wsl=False)
            self.assertEqual(target.read_text(), "original")

    def test_wsl_windows_mount_is_rejected_before_creating_environment(self):
        with self.assertRaisesRegex(RuntimeError, "Linux-native"):
            validate_user_paths(Path("/mnt/c/project"), Path("/mnt/c/project/venv"), is_wsl=True)


class MissingInterpreterShellTests(unittest.TestCase):
    def setUp(self):
        boundary = patch("tiny_swarm_world.prepare_linux.run_incus_preparation", return_value=0)
        self.incus_boundary = boundary.start()
        self.addCleanup(boundary.stop)

    def run_boundary(self, args=(), *, python_ready=False, apt_fails=False, release="24.04", kernel="6.8.0-linux", evidence_failure="", consent="yes\nyes\n"):
        # Fake extracted release and fake executables: no real package commands.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/tiny_swarm_world").mkdir(parents=True)
            (root / "src/tiny_swarm_world/prepare_linux.py").touch()
            (root / "requirements.lock").write_text((ROOT / "requirements.lock").read_text())
            (root / "requirements.build.lock").write_text((ROOT / "requirements.build.lock").read_text())
            (root / "pyproject.toml").touch()
            release_file = root / "os-release"
            release_file.write_text(f'ID=ubuntu\nVERSION_ID="{release}"\n')
            (root / "systemd").mkdir()
            helper = (ROOT / "tools/ubuntu_python_prerequisites.sh").read_text().replace("/etc/os-release", str(release_file)).replace("/run/systemd/system", str(root / "systemd"))
            (root / "helper.sh").write_text(helper)
            scripts = root / "bin"
            scripts.mkdir()
            for name, body in {
                "uname": f'case "$1" in -s) echo Linux;; -m) echo x86_64;; -r) echo {kernel};; esac',
                "python3": '[[ -f "$FAKE_ROOT/ready" ]]',
                "dpkg-query": '[[ -f "$FAKE_ROOT/ready" ]] && printf "install ok installed"',
                "sudo": 'exit 99',
                "timeout": 'if [[ "$2" == dpkg-query || "$2" == find ]]; then shift; "$@"; exit $?; fi\nprintf "%s\\n" "$*" >> "$FAKE_ROOT/commands"\n' + ('exit 1' if apt_fails else '[[ "$*" == *apt-cache* ]] && echo "  Candidate: 3.12.1"\n[[ "$*" == *install* ]] && touch "$FAKE_ROOT/ready"\nexit 0'),
            }.items():
                path = scripts / name
                path.write_text("#!/usr/bin/env bash\n" + body + "\n")
                path.chmod(0o755)
            if evidence_failure:
                evidence_file = root / "forced-evidence"
                if evidence_failure == "before":
                    evidence_file.symlink_to("/dev/full")
                else:
                    evidence_file.touch(mode=0o600)
                    python_stub = scripts / "python3"
                    python_stub.write_text('#!/usr/bin/env bash\n[[ -f "$FAKE_ROOT/ready" ]] || exit 1\nrm "$FAKE_ROOT/forced-evidence"; ln -s /dev/full "$FAKE_ROOT/forced-evidence"\n')
                (scripts / "mktemp").write_text('#!/usr/bin/env bash\nprintf "%s/forced-evidence\\n" "$FAKE_ROOT"\n')
                (scripts / "mktemp").chmod(0o755)
            if python_ready:
                (root / "ready").touch()
            env = {**os.environ, "PATH": str(scripts) + ":" + os.environ["PATH"], "FAKE_ROOT": str(root), "XDG_STATE_HOME": str(root / "state")}
            before = {p.relative_to(root) for p in root.rglob("*")}
            result = subprocess.run(
                ["bash", "-c", 'source ./helper.sh; tsw_minimum_capacity() { return 0; }; tsw_python_prerequisites "$@"', "fixture", *args],
                cwd=root, env=env, input=consent, capture_output=True, text=True, timeout=10,
            )
            after = {p.relative_to(root) for p in root.rglob("*")}
            commands = (root / "commands").read_text() if (root / "commands").exists() else ""
            return result, commands, after - before

    def test_ac1_absent_interpreter_bootstraps_and_hands_off_without_manual_pip(self):
        result, commands, _ = self.run_boundary()
        wsl, _, _ = self.run_boundary(kernel="6.6-microsoft-standard-WSL2")
        self.assertEqual(wsl.returncode, 0, wsl.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("apt-get", commands)
        self.assertIn("python3=3.12.1 python3-venv=3.12.1", commands)
        self.assertNotIn("pip", commands)
        self.assertIn("DPkg::Lock::Timeout=30", commands)

    def test_ac2_satisfied_python_skips_apt_and_unsupported_release_blocks(self):
        ready, commands, changed = self.run_boundary(python_ready=True)
        self.assertEqual(ready.returncode, 0)
        self.assertEqual((commands, changed), ("", set()))
        blocked, commands, changed = self.run_boundary(release="22.04")
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual((commands, changed), ("", set()))

    def test_ac3_help_and_read_only_work_without_python_or_any_writes(self):
        for option, expected in (("--help", 10), ("--dry-run", 2), ("--preflight", 2)):
            result, commands, changed = self.run_boundary((option,))
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertEqual((commands, changed), ("", set()))

    def test_ac4_package_failure_and_declined_consent_stop_handoff(self):
        failed, commands, _ = self.run_boundary(apt_fails=True)
        self.assertEqual(failed.returncode, 4)
        self.assertNotIn("install --yes", commands)
        self.assertIn("Observed python3", failed.stderr)
        self.assertIn("./prepare_linux.sh --dry-run", failed.stderr)
        cancelled, commands, changed = self.run_boundary(consent="no\n")
        self.assertEqual(cancelled.returncode, 2)
        self.assertEqual((commands, changed), ("", set()))

    def test_wsl1_blocks_before_mutation(self):
        result, commands, changed = self.run_boundary(kernel="4.4-microsoft")
        self.assertEqual(result.returncode, 2)
        self.assertEqual((commands, changed), ("", set()))

    def test_evidence_failure_stops_before_apt_or_handoff(self):
        before, commands, _ = self.run_boundary(evidence_failure="before")
        self.assertEqual(before.returncode, 2, before.stderr)
        self.assertEqual(commands, "")
        after, commands, _ = self.run_boundary(evidence_failure="after")
        self.assertEqual(after.returncode, 4, after.stderr)
        self.assertIn("install --yes", commands)
        self.assertIn("evidence write failed", after.stderr)

    def test_unknown_arguments_do_not_bootstrap(self):
        result, commands, changed = self.run_boundary(("--unknown",))
        self.assertEqual(result.returncode, 2)
        self.assertEqual((commands, changed), ("", set()))

    def test_entrypoint_help_is_dependency_light(self):
        result = subprocess.run(["bash", str(ROOT / "prepare_linux.sh"), "--help"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Services are not verified", result.stdout)


if __name__ == "__main__":
    unittest.main()

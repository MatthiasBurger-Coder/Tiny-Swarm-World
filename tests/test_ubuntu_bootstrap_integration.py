"""Joined BOOT-W02 owners with mocked process I/O, never real APT or pip."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from tests.test_prepare_linux import QUALIFIED
from tiny_swarm_world.application.services.native_preparation import NativePreparationService
from tiny_swarm_world.application.ports.installation import HostRuntime, InstallerError
from tiny_swarm_world.infrastructure.adapters.installation import process
from tiny_swarm_world.infrastructure.adapters.native_package_manager import AptHostPackageManager
from tiny_swarm_world.prepare_linux import main, _prepare_python_dependencies

ROOT = Path(__file__).resolve().parents[1]


class UbuntuJoinedBootstrapTests(unittest.TestCase):
    def test_ac1_real_package_and_locked_runtime_owners_fresh_then_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/tiny_swarm_world").mkdir(parents=True)
            (root / "src/tiny_swarm_world/prepare_linux.py").touch()
            for name in ("requirements.lock", "requirements.build.lock", "pyproject.toml"):
                shutil.copyfile(ROOT / name, root / name)
            installed: set[str] = set()
            package_commands = []
            python_commands = []
            runtime_ready = False

            def package_run(command, **kwargs):
                package_commands.append(command)
                if command[0] == "dpkg-query":
                    return subprocess.CompletedProcess(command, 0 if command[-1] in installed else 1,
                                                       "install ok installed" if command[-1] in installed else "", "")
                if command[0] == "apt-cache":
                    return subprocess.CompletedProcess(command, 0, "  Candidate: 1.2.3\n", "")
                if "install" in command:
                    installed.update(item.split("=", 1)[0] for item in command[command.index("--") + 1:])
                return subprocess.CompletedProcess(command, 0, "", "")

            def python_run(command, **kwargs):
                nonlocal runtime_ready
                python_commands.append(command)
                if command[1:3] == ["-m", "venv"]:
                    target = Path(command[3])
                    (target / "bin").mkdir(parents=True)
                    (target / "bin/python").touch()
                    (target / "pyvenv.cfg").write_text("home = /usr/bin\n")
                if "--no-build-isolation" in command:
                    runtime_ready = True
                return subprocess.CompletedProcess(command, 0)

            runner = Mock(run_text=Mock(side_effect=package_run))
            manager = AptHostPackageManager(runner, candidate_consent=lambda candidates: True,
                                            target_snapshot=lambda: ("ubuntu", "24.04"))
            service = NativePreparationService(Mock(inspect=Mock(return_value=QUALIFIED)), manager, prerequisites_only=True)
            previous = Path.cwd()
            os.chdir(root)
            try:
                with (
                    patch.dict(os.environ, {"TSW_NATIVE_LINUX_VENV": str(root / "venv"), "XDG_STATE_HOME": str(root / "state")}),
                    patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
                    patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer") as evidence,
                    patch("tiny_swarm_world.infrastructure.composition_installation.detect_host_runtime", return_value=HostRuntime("native_linux", "fixture")),
                    patch("tiny_swarm_world.infrastructure.composition_installation._python_imports_available", side_effect=lambda *args: runtime_ready),
                    patch.object(process, "_python_imports_available", side_effect=lambda *args: runtime_ready),
                    patch.object(process, "_run_installer_subprocess", side_effect=python_run),
                    patch("builtins.input", return_value="yes"),
                    redirect_stdout(io.StringIO()),
                ):
                    evidence.return_value.write.return_value = root / "redacted-evidence"
                    self.assertEqual(main(()), 0)
                    initial_package_mutations = sum("apt-get" in command for command in package_commands)
                    initial_python_commands = len(python_commands)
                    self.assertEqual(main(()), 0)
                    self.assertEqual(sum("apt-get" in command for command in package_commands), initial_package_mutations)
                    self.assertEqual(len(python_commands), initial_python_commands)
            finally:
                os.chdir(previous)
            self.assertEqual(len(python_commands), 3)
            self.assertIn("--require-hashes", python_commands[1])
            self.assertIn("requirements.build.lock", python_commands[1])
            self.assertIn("--no-deps", python_commands[2])
            self.assertIn("--no-build-isolation", python_commands[2])
            self.assertTrue((root / "venv/pyvenv.cfg").is_file())
            self.assertTrue(all(item.endswith("=1.2.3") for command in package_commands if "install" in command
                                for item in command[command.index("--") + 1:]))

    def test_ac4_probe_timeout_is_actionable_and_does_not_prompt_or_bootstrap(self):
        with (
            patch("tiny_swarm_world.infrastructure.composition_installation._python_imports_available", side_effect=InstallerError("timed out")),
            patch("tiny_swarm_world.infrastructure.composition_installation.ensure_python_environment") as bootstrap,
            patch("builtins.input") as prompt,
            redirect_stderr(io.StringIO()) as output,
        ):
            self.assertEqual(_prepare_python_dependencies(read_only=True), 2)
        bootstrap.assert_not_called()
        prompt.assert_not_called()
        self.assertIn("./prepare_linux.sh --dry-run", output.getvalue())

    def test_candidate_decline_or_drift_stops_package_install_after_refresh(self):
        for decline, target_drift, candidate_drift in ((True, False, False), (False, True, False), (False, False, True)):
            commands = []
            candidate_calls = 0

            def run(command, **kwargs):
                nonlocal candidate_calls
                commands.append(command)
                if command[0] == "apt-cache":
                    candidate_calls += 1
                    version = "2" if candidate_drift and candidate_calls > 1 else "1"
                    return subprocess.CompletedProcess(command, 0, f" Candidate: {version}\n", "")
                if command[0] == "dpkg-query":
                    return subprocess.CompletedProcess(command, 1, "", "")
                return subprocess.CompletedProcess(command, 0, "", "")

            manager = AptHostPackageManager(Mock(run_text=Mock(side_effect=run)),
                                            candidate_consent=lambda _: not decline,
                                            target_snapshot=Mock(side_effect=("target-a", "target-b" if target_drift else "target-a")))
            with self.assertRaises(RuntimeError):
                manager.install(("incus",))
            self.assertTrue(any("update" in command for command in commands))
            self.assertFalse(any("install" in command for command in commands))

    def test_composed_candidate_snapshot_requalifies_capacity_and_assets(self):
        from dataclasses import replace
        from tiny_swarm_world.infrastructure.composition_native_preparation import _prerequisite_snapshot
        inspector = Mock(inspect=Mock(return_value=QUALIFIED))
        with patch("tiny_swarm_world.infrastructure.composition_native_preparation.validate_preparation_paths", return_value=("lock-a",)) as paths:
            initial = _prerequisite_snapshot(inspector, ROOT, "service-access")
            inspector.inspect.return_value = replace(QUALIFIED, memory_bytes=1)
            with self.assertRaisesRegex(RuntimeError, "prerequisites changed"):
                _prerequisite_snapshot(inspector, ROOT, "service-access")
            inspector.inspect.return_value = QUALIFIED
            paths.return_value = ("lock-b",)
            self.assertNotEqual(initial, _prerequisite_snapshot(inspector, ROOT, "service-access"))

    def test_python_consent_fingerprint_drift_stops_bootstrap(self):
        with (
            patch("tiny_swarm_world.infrastructure.composition_installation._python_imports_available", return_value=False),
            patch("tiny_swarm_world.prepare_linux._validate_mutation_paths", side_effect=(("a",), ("b",))),
            patch("tiny_swarm_world.infrastructure.composition_installation.detect_host_runtime", return_value=HostRuntime("native_linux", "fixture")),
            patch("tiny_swarm_world.infrastructure.composition_installation.ensure_python_environment") as bootstrap,
            patch("tiny_swarm_world.prepare_linux.record_python_preparation") as evidence,
            patch("builtins.input", return_value="yes"),
            redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(_prepare_python_dependencies(read_only=False), 1)
        bootstrap.assert_not_called()
        self.assertEqual(evidence.call_args.args, ("failed",))

    def test_changed_supported_release_needs_new_consent(self):
        from dataclasses import replace
        service = NativePreparationService(Mock(inspect=Mock(side_effect=(QUALIFIED, replace(QUALIFIED, version_id="26.04")))),
                                           Mock(missing=Mock(return_value=("incus",))), prerequisites_only=True)
        with self.assertRaisesRegex(ValueError, "target"):
            service.apply(service.plan())


if __name__ == "__main__":
    unittest.main()

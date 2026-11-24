from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from contextlib import chdir
from pathlib import Path
from sys import executable
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
BOOTSTRAP = Path("modules/tsw_native_linux/boostrap")


def _run_committed_install_preview() -> int:
    """Run real installer admission with fixture host and preflight inputs."""
    from unittest.mock import Mock

    from tiny_swarm_world.application.ports.installation import HostRuntime
    from tiny_swarm_world.infrastructure.adapters.guided_setup_state import GuidedSetupState
    from tiny_swarm_world.infrastructure.adapters.installation import bootstrap
    from tiny_swarm_world.infrastructure.adapters.installation.configuration import ConfigurationPreparationAdapter
    from tiny_swarm_world.infrastructure.adapters.installation.guided_observation import guided_observation
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
    from tiny_swarm_world.infrastructure.composition_installation import build_installation_service

    calls = Path(os.environ["CALLS"])
    runtime = HostRuntime("native_linux", "test")
    load_journal = JsonProfileLifecycleJournal.load

    def inventory(options, env, cwd, _runtime):
        record = GuidedSetupState(Path(os.environ["XDG_STATE_HOME"]), options.service_profile).prior()
        with calls.open("a", encoding="utf-8") as trace:
            trace.write(f"inventory {record['stage']}/{record['status']}\n")
        nonce = options.guided_plan_nonce
        listener = {"category": "PORT", "check_id": "PORT-10001", "message": "Portainer listener owned",
                    "evidence": {"port": "10001", "source": "installation_owned_proxy"}}
        return guided_observation(nonce, env, cwd, json.dumps({"checks": [listener]})) if nonce else None

    def read_journal(journal):
        checkpoint = load_journal(journal)
        with calls.open("a", encoding="utf-8") as trace:
            trace.write(f"observe installation_committed={checkpoint.installation_committed}\n")
        return checkpoint

    def build_service():
        service = build_installation_service()
        service.host = Mock(detect=Mock(return_value=runtime))
        return service

    with (
        patch.object(bootstrap.host, "detect_host_runtime", return_value=runtime),
        patch.object(bootstrap, "_ensure_native_python"),
        patch.object(bootstrap, "_prepare_bootstrap_environment", side_effect=lambda env, _: dict(env)),
        patch.object(bootstrap, "build_installation_service", side_effect=build_service),
        patch.object(ConfigurationPreparationAdapter, "validate_read_only", side_effect=inventory),
        patch.object(JsonProfileLifecycleJournal, "load", read_journal),
    ):
        return bootstrap.main()


class SetupLinuxTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="tsw setup fixture ")
        self.addCleanup(directory.cleanup)
        self.checkout = Path(directory.name).resolve()
        self.calls = self.checkout / "calls"
        (self.checkout / BOOTSTRAP).mkdir(parents=True)
        (self.checkout / "bin").mkdir()
        core = Path("modules/tsw_core")
        adapters = core / "src/infrastructure/adapters"
        for path in (
            Path("setup_linux.sh"), BOOTSTRAP / "setup_linux.sh",
            core / "__init__.py", core / "src/__init__.py",
            adapters / "guided_setup.py", adapters / "guided_setup_state.py",
            adapters / "bootstrap_state.py",
            core / "src/infrastructure/process/runner.py",
            core / "src/infrastructure/process/streaming.py",
        ):
            (self.checkout / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, self.checkout / path)
        self.state = self.checkout / "state"
        self.record = self.state / "tiny-swarm-world/guided-setup/setup.state.json"
        self.env = {
            "PATH": f"{self.checkout / 'bin'}:{os.defpath}",
            "CALLS": str(self.calls),
            "XDG_STATE_HOME": str(self.state),
        }
        (self.checkout / "bin/python3").symlink_to(executable)
        self._stub("bin/dpkg", """
[[ "$1" == --audit ]] || exit 99
if [[ "${MOCK_DPKG_PARTIAL:-0}" == 1 ]]; then printf 'Unconfigured packages\n'; fi
""")
        self._stub("bin/uname", """
case "$1" in
  -s) printf '%s\\n' "${MOCK_SYSTEM:-Linux}" ;;
  -m) printf '%s\\n' "${MOCK_ARCH:-x86_64}" ;;
  -r) printf '%s\\n' "${MOCK_KERNEL:-linux}" ;;
  *) exit 1 ;;
esac
""")
        self._stub("bin/git", """
case "$*" in
  'rev-parse --show-toplevel') printf '%s\\n' "$PWD" ;;
  'rev-parse --verify HEAD')
    if [[ "${MOCK_DRIFT:-0}" == 1 ]] && grep -q "^install --dry-run" "$CALLS" 2>/dev/null; then
      printf 'changed-revision\\n'
    else
      printf 'initial-revision\\n'
    fi ;;
  'ls-files -z --cached --others --exclude-standard -- '*)
    printf 'setup_linux.sh\\0install.sh\\0' ;;
  *) exit 1 ;;
esac
""")
        self._stub(BOOTSTRAP / "prepare_linux.sh", """
[[ "$TSW_REPOSITORY_ROOT" == "$PWD" && "$TSW_INFRA_ROOT" == "$PWD/modules/tsw_core/infra" ]] || exit 99
printf 'prepare %s\\n' "$*" >> "$CALLS"
case "$1" in
  --preflight|--dry-run) exit "${MOCK_PREPARE_PLAN_EXIT:-0}" ;;
esac
if [[ "${MOCK_PREPARE_CONSENT:-0}" == 1 ]]; then
  IFS= read -r answer && [[ "$answer" == yes ]] || exit 2
fi
exit "${MOCK_PREPARE_EXIT:-0}"
""")
        self._stub("install.sh", """
[[ "$TSW_REPOSITORY_ROOT" == "$PWD" && "$TSW_INFRA_ROOT" == "$PWD/modules/tsw_core/infra" ]] || exit 99
printf 'install %s\\n' "$*" >> "$CALLS"
case "$1" in
  --preflight|--dry-run)
    if [[ "$*" == *--guided-plan* ]]; then
      [[ -n "${TSW_GUIDED_PLAN_NONCE:-}" && -z "${TSW_GUIDED_PLAN_EXPECTED:-}" ]] || exit 99
      if [[ "$*" == *--guided-resume* && "${MOCK_SCOPED:-0}" == 0 ]]; then exit 65; fi
      printf 'Guided plan fingerprint: %064d\\n' 0
    fi
    exit "${MOCK_PLAN_EXIT:-0}" ;;
  --selection-plan) exit "${MOCK_SELECTION_EXIT:-0}" ;;
  --guided-status) exit 0 ;;
  *)
    [[ "$*" == *--guided-report* && "$*" != *--confirm-reset* &&
       "$TSW_GUIDED_PLAN_EXPECTED" == "$(printf %064d 0)" ]] || exit 99
    if [[ "${MOCK_PLAN_CHANGED:-0}" == 1 ]]; then exit 65; fi
    if [[ "${MOCK_WAIT_FOR_SIGNAL:-0}" == 1 ]]; then
      exec python3 -c 'from pathlib import Path; import signal, sys; Path(sys.argv[1]).touch(); signal.pause()' "$CALLS.ready"
    fi
    exit "${MOCK_INSTALL_EXIT:-0}" ;;
esac
""")

    def _stub(self, relative: str | Path, body: str) -> None:
        path = self.checkout / relative
        if path.is_symlink():
            path.unlink()
        path.write_text("#!/usr/bin/env bash\nset -eu\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def _command(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.checkout / "setup_linux.sh"), *args], cwd="/",
            env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=10,
        )

    def _guided(self, answers: bytes, *args: str) -> subprocess.CompletedProcess[bytes]:
        master, terminal = os.openpty()
        try:
            os.write(master, answers)
            return subprocess.run(
                [str(self.checkout / "setup_linux.sh"), *args], cwd="/", env=self.env,
                stdin=terminal, stdout=terminal, stderr=subprocess.PIPE, timeout=10,
            )
        finally:
            os.close(terminal)
            os.close(master)

    def _observed(self) -> list[str]:
        return self.calls.read_text(encoding="utf-8").splitlines() if self.calls.exists() else []

    def _require_ordinary_user(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("The setup entrypoint requires an ordinary user.")

    def test_help_and_invalid_arguments_do_not_inspect_host(self) -> None:
        for name in ("git", "uname", "python3"):
            self._stub(f"bin/{name}", 'printf "unexpected probe\\n" >> "$CALLS"\nexit 1\n')
        help_result = self._command("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--dry-run", help_result.stdout)
        for arguments in (
            ("--help", "--confirm-reset"), ("--preflight", "--dry-run"),
            ("--dry-run", "--resume"), ("--resume", "--resume"),
            ("--profile",), ("--profile", "classic"), ("--profile", "custom"),
            ("--services", "jenkins"), ("--profile", "minimal", "--services", "jenkins"),
            ("--non-interactive-live-approval",), ("--install-dir", "/other"),
        ):
            with self.subTest(arguments=arguments):
                self.assertEqual(self._command(*arguments).returncode, 2)
        self.assertEqual(self._observed(), [])

    def test_unsupported_host_stops_before_either_child(self) -> None:
        for name, value in (
            ("MOCK_SYSTEM", "Darwin"), ("MOCK_ARCH", "aarch64"),
            ("MOCK_KERNEL", "microsoft-standard-WSL2"), ("WSL_INTEROP", "present"),
        ):
            with self.subTest(name=name):
                self.env[name] = value
                result = self._command("--dry-run")
                self.assertEqual(result.returncode, 2)
                self.assertIn("Native Ubuntu", result.stderr)
                del self.env[name]
        self.assertEqual(self._observed(), [])

    def test_read_only_modes_forward_only_read_only_arguments(self) -> None:
        self._require_ordinary_user()
        for mode, outcome in (("--preflight", "READY"), ("--dry-run", "PLAN_READY")):
            with self.subTest(mode=mode):
                result = self._command(mode, "--profile", "default")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(outcome, result.stdout)
                self.assertEqual(self._observed(), [
                    f"prepare {mode} --service-profile default",
                    f"install {mode} --service-profile default",
                ])
                self.calls.unlink()
                self.assertFalse(self.state.exists())

    def test_selective_dry_run_delegates_without_host_preparation(self) -> None:
        self._require_ordinary_user()
        result = self._command("--dry-run", "--profile", "minimal")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SELECTION_PLAN_READY", result.stdout)
        self.assertEqual(self._observed(), ["install --selection-plan minimal"])
        self.calls.unlink()

        self.env["MOCK_SELECTION_EXIT"] = "2"
        result = self._command("--dry-run", "--profile", "custom", "--services", "unknown")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("SELECTION_PLAN_READY", result.stdout)
        self.assertEqual(self._observed(), ["install --selection-plan custom --services=unknown"])

    def test_apply_requires_terminal_and_one_checkout(self) -> None:
        self._require_ordinary_user()
        result = self._command()
        self.assertEqual(result.returncode, 2)
        self.assertIn("interactive terminal", result.stderr)
        self.env["TSW_INFRA_ROOT"] = "/other-checkout/infra"
        result = self._command("--preflight")
        self.assertEqual(result.returncode, 2)
        self.assertIn("infrastructure paths", result.stderr)
        self.assertEqual(self._observed(), [])

    def test_repeat_observes_ready_preparation_and_requests_fresh_consent(self) -> None:
        self._require_ordinary_user()
        inventory = "prepare --dry-run --service-profile service-access"
        preview = "install --dry-run --service-profile service-access --guided-plan"
        install = "install --service-profile service-access --guided-report --guided-plan"
        report = "install --guided-status --service-profile service-access"

        declined = self._guided(b"no\n")
        self.assertEqual(declined.returncode, 2, declined.stderr)
        self.assertEqual(self._observed(), [inventory, preview])
        self.assertFalse(self.record.exists())
        self.calls.unlink()

        for _ in range(2):
            result = self._guided(b"yes\n")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._observed(), [inventory, preview, inventory, install, report] * 2)
        self.assertEqual(json.loads(self.record.read_text())["record"]["status"], "succeeded")
        self.assertEqual(self.record.stat().st_mode & 0o777, 0o600)

    def test_mutating_prepare_failures_report_uncertain_effects(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_PREPARE_PLAN_EXIT"] = "2"
        for child, expected in ((1, 1), (2, 1), (3, 3), (4, 1), (124, 124), (130, 130), (143, 130)):
            with self.subTest(child=child):
                self.env["MOCK_PREPARE_EXIT"] = str(child)
                result = self._guided(b"yes\n")
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertIn(f"prepare: (child exit {child})".encode(), result.stderr)
                self.assertIn(b"--resume", result.stderr)
                self.assertEqual(self._observed(), [
                    "prepare --dry-run --service-profile service-access",
                    "prepare --service-profile service-access",
                ])
                record = json.loads(self.record.read_text())["record"]
                self.assertEqual(record["uncertain"], ["prepare"])
                self.assertEqual(record["exit_code"], child)
                self.record.unlink()
                self.calls.unlink()

    def test_read_only_restart_with_no_checkpoint_recommends_fresh_setup(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_PREPARE_PLAN_EXIT"] = "3"
        result = self._command("--preflight")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("Next: ./setup_linux.sh --profile service-access\n", result.stderr)
        self.assertFalse(self.state.exists())

    def test_login_restart_reobserves_and_skips_completed_preparation(self) -> None:
        self._require_ordinary_user()
        self.env.update(MOCK_PREPARE_PLAN_EXIT="2", MOCK_PREPARE_EXIT="3", MOCK_PREPARE_CONSENT="1")
        stopped = self._guided(b"yes\n")
        self.assertEqual(stopped.returncode, 3, stopped.stderr)
        self.assertIn(b"RESTART_REQUIRED", stopped.stderr)
        self.env["MOCK_PREPARE_PLAN_EXIT"] = "0"
        self.calls.unlink()

        declined = self._guided(b"no\n", "--resume")
        self.assertEqual(declined.returncode, 2, declined.stderr)
        self.assertIn(b"Previous prepare stage recorded restart_required", declined.stderr)
        self.calls.unlink()
        resumed = self._guided(b"yes\n", "--resume")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertTrue(all(call.startswith("prepare --dry-run") for call in self._observed() if call.startswith("prepare ")))
        self.assertIn("install --service-profile service-access --guided-report --guided-plan", self._observed())

    def test_interrupted_install_requires_explicit_resume_and_reinventory(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_INSTALL_EXIT"] = "130"
        stopped = self._guided(b"yes\n")
        self.assertEqual(stopped.returncode, 130, stopped.stderr)
        self.assertIn(b"Partial or uncertain effects", stopped.stderr)
        self.calls.unlink()
        blocked = self._guided(b"yes\n")
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertEqual(self._observed(), [])
        self.env.update(MOCK_PREPARE_PLAN_EXIT="2", MOCK_INSTALL_EXIT="0")
        drifted = self._guided(b"yes\n", "--resume")
        self.assertEqual(drifted.returncode, 2, drifted.stderr)
        self.assertEqual(self._observed(), ["prepare --dry-run --service-profile service-access"])
        self.calls.unlink()

        self.env["MOCK_PREPARE_PLAN_EXIT"] = "0"
        legacy = self._guided(b"yes\n", "--resume")
        self.assertEqual(legacy.returncode, 2, legacy.stderr)
        self.assertNotIn(b"Type yes", legacy.stderr)
        self.calls.unlink()

        self.env["MOCK_SCOPED"] = "1"
        resumed = self._guided(b"yes\n", "--resume")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self._observed()[-2:], [
            "install --service-profile service-access --guided-report --guided-plan --guided-resume",
            "install --guided-status --service-profile service-access",
        ])

    def test_tsw_494_reg_01_resume_after_committed_install_interruption(self) -> None:
        self._require_ordinary_user()

        from modules.tsw_core.tests.domain.lifecycle.test_models import manifest_fixture
        from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import intent_fixture
        from tiny_swarm_world.domain.lifecycle.models import InstallationManifest, migrate_manifest_v1
        from tiny_swarm_world.domain.lifecycle.profile_lifecycle import (
            ProfileLifecycleCheckpoint,
            installation_manifest_sha256,
        )
        from tiny_swarm_world.infrastructure.adapters.guided_setup_state import GuidedSetupState
        from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
        from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
        from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
        from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal

        self.env.update(REGRESSION_SOURCE=str(ROOT), REGRESSION_PYTHON=executable)
        self._stub("install.sh", """
case "${1:-}" in
  --dry-run|--preflight)
    export PYTHONPATH="$REGRESSION_SOURCE"
    exec "$REGRESSION_PYTHON" -B -c 'from modules.tsw_native_linux.tests.test_setup_linux import _run_committed_install_preview; raise SystemExit(_run_committed_install_preview())' "$@" ;;
  --guided-status) printf 'observe service access\\n' >> "$CALLS" ;;
  *)
    printf 'unexpected installer apply or reset\n' >> "$CALLS"
    exit 99 ;;
esac
""")
        intent = intent_fixture()
        catalog = NativeComponentCatalog(ROOT).load()
        manifest = InstallationManifest.model_validate(migrate_manifest_v1(manifest_fixture()).model_copy(update={
            "installation_id": intent.profile.installation_id,
            "installation_profile": intent.profile.profile,
            "service_preset": "service-access",
            "checkpoint_reference": "profile-" + intent.profile.operation_id,
            "components": tuple(component for service in catalog.services
                                if service.service_id in intent.profile.resolved_services
                                for component in service.components),
        }).model_dump())
        catalog.validate_manifest(manifest)
        journal = JsonProfileLifecycleJournal(self.checkout)
        manifests = JsonManifestRepository(journal.path.with_name("manifest.json"))
        committed = ProfileLifecycleCheckpoint(
            intent=intent, stage="completed", previous_stage="completed",
            instance_uuid="11111111-1111-1111-1111-111111111111",
            observation_sha256="a" * 64, installation_committed=True,
            installation_manifest_sha256=installation_manifest_sha256(manifest),
        )
        with JsonInstallationOperationLock(self.checkout).exclusive("profile-lifecycle") as lease:
            with journal.exclusive(lease):
                manifests.save(manifest, expected_token=None)
                journal.save(committed, expected=None, lease=lease)
        self.assertEqual(journal.load(), committed)

        with patch.dict(os.environ, self.env, clear=True), chdir(self.checkout):
            state = GuidedSetupState(self.state, "service-access")
            try:
                state.acquire()
                state.checkpoint("install", "started")
                initial = state.prior()
            finally:
                state.close()
        assert initial is not None
        self.assertEqual((initial["stage"], initial["status"]), ("install", "started"))
        original = self.record.read_bytes()

        # A fully committed installation has no outstanding mutation to approve.
        resumed = self._guided(b"no\n", "--profile", "service-access", "--verbose", "--resume")
        observed = self._observed()
        self.assertEqual(observed, [
            "prepare --dry-run --service-profile service-access",
            "inventory install/started",
            "observe installation_committed=True",
            "observe service access",
        ], resumed.stderr.decode())
        self.assertNotIn(b"Type yes", resumed.stderr)
        self.assertEqual(journal.load(), committed)
        self.assertEqual(manifests.load().manifest, manifest)
        self.assertEqual(
            resumed.returncode, 0,
            f"{resumed.stderr.decode()}"
            f"Wrapper checkpoint unchanged: {self.record.read_bytes() == original}",
        )
        with patch.dict(os.environ, self.env, clear=True), chdir(self.checkout):
            completed = GuidedSetupState(self.state, "service-access").prior()
        assert completed is not None
        self.assertEqual((completed["stage"], completed["status"], completed["exit_code"]), ("install", "succeeded", 0))

    def test_wrapper_signal_interrupts_child_and_retains_install_intent(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_WAIT_FOR_SIGNAL"] = "1"
        master, terminal = os.openpty()
        child = None
        try:
            os.write(master, b"yes\n")
            child = subprocess.Popen(
                [str(self.checkout / "setup_linux.sh")], cwd="/", env=self.env,
                stdin=terminal, stdout=terminal, stderr=subprocess.PIPE,
            )
            ready = self.calls.with_suffix(".ready")
            deadline = time.monotonic() + 5
            while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists(), "installer did not reach the signal boundary")
            child.send_signal(signal.SIGTERM)
            _, diagnostics = child.communicate(timeout=10)
            self.assertEqual(child.returncode, 130, diagnostics)
            prior = json.loads(self.record.read_text())["record"]
            self.assertEqual((prior["stage"], prior["status"], prior["uncertain"]),
                             ("install", "interrupted", ["install"]))
        finally:
            if child is not None and child.poll() is None:
                child.send_signal(signal.SIGTERM)
                try:
                    child.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate(timeout=5)
            os.close(terminal)
            os.close(master)

    def test_pending_package_configuration_blocks_resume_before_mutation(self) -> None:
        self._require_ordinary_user()
        self.env.update(MOCK_PREPARE_PLAN_EXIT="2", MOCK_PREPARE_EXIT="4")
        self.assertEqual(self._guided(b"yes\n").returncode, 1)
        self.calls.unlink()
        self.env["MOCK_DPKG_PARTIAL"] = "1"
        result = self._guided(b"yes\n", "--resume")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"dpkg --audit", result.stderr)
        self.assertEqual(self._observed(), [])

    def test_preview_failure_and_changed_revision_stop_apply(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_PLAN_EXIT"] = "17"
        result = self._guided(b"yes\n")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"plan: (child exit 17)", result.stderr)
        self.assertNotIn(b"Type yes", result.stderr)
        self.assertEqual(len(self._observed()), 2)
        self.calls.unlink()
        self.env.update(MOCK_PLAN_EXIT="0", MOCK_DRIFT="1")
        result = self._guided(b"yes\n")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"Checkout or target changed", result.stderr)
        self.assertFalse(self.record.exists())
        self.assertEqual(len(self._observed()), 3)

    def test_plan_binding_refusal_retains_preparation_and_allows_new_consent(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_PLAN_CHANGED"] = "1"
        blocked = self._guided(b"yes\n")
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        saved = json.loads(self.record.read_text())["record"]
        self.assertEqual((saved["stage"], saved["status"], saved["uncertain"]),
                         ("prepare", "succeeded", []))

        self.env["MOCK_PLAN_CHANGED"] = "0"
        declined = self._guided(b"no\n")
        self.assertEqual(declined.returncode, 2, declined.stderr)
        self.assertEqual(json.loads(self.record.read_text())["record"], saved)

    def test_read_only_preserves_partial_state_and_rejects_stale_or_corrupt_records(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_INSTALL_EXIT"] = "17"
        stopped = self._guided(b"yes\n")
        self.assertEqual(stopped.returncode, 1, stopped.stderr)
        self.assertIn(b"install: (child exit 17)", stopped.stderr)
        previous = self.record.read_bytes()
        self.assertEqual(self._command("--dry-run").returncode, 0)
        self.assertEqual(self.record.read_bytes(), previous)
        self.calls.unlink()

        stale = self._command("--dry-run", "--profile", "default")
        self.assertEqual(stale.returncode, 2, stale.stderr)
        self.assertEqual(self.record.read_bytes(), previous)
        invalid = json.loads(previous)
        invalid["record"]["status"] = "succeeded"
        self.record.write_text(json.dumps(invalid))
        inconsistent = self._guided(b"yes\n", "--resume")
        self.assertEqual(inconsistent.returncode, 2, inconsistent.stderr)
        self.assertEqual(json.loads(self.record.read_text()), invalid)
        self.record.write_text("{}")
        corrupt = self._guided(b"yes\n", "--resume")
        self.assertEqual(corrupt.returncode, 2, corrupt.stderr)
        self.assertEqual(self.record.read_text(), "{}")
        self.assertEqual(self._observed(), [])

    def test_missing_python_blocks_apply_with_retained_python_checkpoint(self) -> None:
        self._require_ordinary_user()
        self._stub("bin/python3", "exit 1\n")
        checkpoint = self.state / "tiny-swarm-world/bootstrap/incus.state.json"
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_text("foreign checkpoint")
        result = self._guided(b"yes\n")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"Restore Python before validating", result.stderr)
        self.assertEqual(checkpoint.read_text(), "foreign checkpoint")
        self.assertEqual(self._observed(), [])

    def test_resume_without_checkpoint_keeps_mutating_children_blocked(self) -> None:
        self._require_ordinary_user()
        result = self._guided(b"yes\n", "--resume")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"No setup recovery record", result.stderr)
        self.assertEqual(self._observed(), [])

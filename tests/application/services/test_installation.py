"""Lifecycle policy tests use ports only, with no host or filesystem adapters."""

from contextlib import contextmanager
from pathlib import Path
import unittest
from unittest.mock import Mock

from tiny_swarm_world.application.ports.installation import (
    InstallerOptions,
    InstallerPaths,
    HostRuntime,
    InstallerError,
    _GitProbeResult,
    _EvidenceProbeSnapshot,
    WindowsWslBridgeGuardResult,
)
from tiny_swarm_world.application.services.installation import InstallationService


class TestInstallationService(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.active_snapshot = False
        self.host = Mock()
        self.configuration = Mock()
        self.credentials = Mock()
        self.process = Mock()
        self.evidence = Mock()
        self.presentation = Mock()
        self.reporter = Mock()
        self.service = InstallationService(
            self.host,
            self.configuration,
            self.credentials,
            self.process,
            self.evidence,
            self.presentation,
        )
        self.options = InstallerOptions("service-access", True, True, True, False)
        self.environment = {"TSW_NODE_PROVIDER": "lxc_native"}
        self.cwd = Path("/repository")
        self.host.require_repository.side_effect = lambda *_: self.calls.append(
            "repository"
        )
        self.host.detect.side_effect = lambda *_: self.record(
            "detect", HostRuntime("native_linux", "test")
        )
        self.host.authorize.side_effect = lambda *_, **__: self.calls.append(
            "authorize"
        )
        self.configuration.paths.return_value = InstallerPaths(
            Path("/operator.env"), Path("/venv")
        )
        self.process.ensure_python.side_effect = lambda *_: self.record(
            "bootstrap", "python"
        )
        self.process.current_python.return_value = "prepared-python"
        self.credentials.prepare.side_effect = lambda *args: self.record(
            "credentials", (dict(args[1]), ())
        )
        self.evidence.git_probe.return_value = _GitProbeResult(
            False, False, "outside_worktree"
        )
        self.evidence.run_id.return_value = "run-1"
        self.evidence.directory.return_value = Path("/evidence")
        self.evidence.probes.return_value = _EvidenceProbeSnapshot(
            "main", "hash", "Linux", "kernel", "kernel"
        )
        self.evidence.path.side_effect = lambda directory, name: directory / name
        self.evidence.timestamp.return_value = "finished"
        self.presentation.approval.return_value = (
            "approved",
            "explicit_flag",
            " --approve-live",
        )
        self.process.recorder_available.return_value = True
        self.host.bridge.side_effect = lambda *_: self.record(
            "bridge", WindowsWslBridgeGuardResult(True, "not_wsl2", Path("/bridge"))
        )
        self.process.command.side_effect = lambda python, phase, *_: phase
        self.process.phase.side_effect = self.phase
        self.configuration.snapshot.side_effect = self.snapshot

    def record(self, name, result):
        self.calls.append(name)
        return result

    @contextmanager
    def snapshot(self, options, env, cwd, runtime):
        self.calls.append("snapshot-open")
        self.active_snapshot = True
        try:
            yield {**env, "SNAPSHOT": "active"}
        finally:
            self.active_snapshot = False
            self.calls.append("snapshot-close")

    def phase(self, name, command, path, options, env, cwd, reporter, **kwargs):
        self.assertTrue(self.active_snapshot)
        self.assertEqual(env["SNAPSHOT"], "active")
        self.assertEqual(cwd, self.cwd)
        self.calls.append(command)
        return 0

    def run_install(self, **changes):
        options = InstallerOptions(**{**self.options.__dict__, **changes})
        return self.service.run(
            options, env=self.environment, cwd=self.cwd, reporter=self.reporter
        )

    def test_fresh_install_authorizes_before_bootstrap_and_bridges_before_reset(self):
        self.assertEqual(self.run_install(), 0)
        self.assertEqual(
            self.calls,
            [
                "repository",
                "detect",
                "authorize",
                "bootstrap",
                "snapshot-open",
                "credentials",
                "bridge",
                "reset",
                "setup",
                "snapshot-close",
            ],
        )
        self.assertEqual(
            [call.kwargs for call in self.process.phase.call_args_list],
            [{"sequence": 1, "total": 2}, {"sequence": 2, "total": 2}],
        )
        self.evidence.write.assert_any_call(Path("/evidence/reset-run.exit"), "0\n")
        self.evidence.write.assert_any_call(Path("/evidence/setup-run.exit"), "0\n")

    def test_native_reconciliation_never_bootstraps_or_resets(self):
        self.assertEqual(
            self.run_install(native_reconcile=True, confirm_reset=False), 0
        )
        self.process.ensure_python.assert_not_called()
        self.assertNotIn("reset", self.calls)
        self.assertEqual(
            self.process.phase.call_args.kwargs, {"sequence": 1, "total": 1}
        )
        self.host.validate_native.assert_called_once()
        self.configuration.validate_read_only.assert_called_once()
        self.evidence.append.assert_any_call(
            Path("/evidence"), {"reset_skipped_for_native_reconcile": "yes"}
        )

    def test_native_read_only_has_no_mutating_ports_or_snapshot(self):
        for mode in ("preflight_only", "dry_run"):
            with self.subTest(mode=mode):
                self.setUp()
                self.assertEqual(
                    self.run_install(
                        native_reconcile=True, confirm_reset=False, **{mode: True}
                    ),
                    0,
                )
                self.host.authorize.assert_not_called()
                self.process.ensure_python.assert_not_called()
                self.configuration.snapshot.assert_not_called()
                self.credentials.prepare.assert_not_called()
                self.evidence.directory.assert_not_called()
                self.evidence.write_context.assert_not_called()
                self.process.phase.assert_not_called()

    def test_non_native_read_only_is_rejected_before_authorization(self):
        with self.assertRaisesRegex(InstallerError, "require native Linux"):
            self.run_install(preflight_only=True)
        self.host.authorize.assert_not_called()
        self.configuration.snapshot.assert_not_called()

    def test_native_mode_rejects_wsl_before_inventory(self):
        self.host.detect.return_value = HostRuntime("wsl2", "test")
        self.host.detect.side_effect = None
        with self.assertRaisesRegex(InstallerError, "native Linux host"):
            self.run_install(native_reconcile=True)
        self.host.validate_native.assert_not_called()

    def test_bridge_failure_prevents_both_child_phases_and_records_skip(self):
        self.host.bridge.side_effect = None
        self.host.bridge.return_value = WindowsWslBridgeGuardResult(
            False, "stale", Path("/bridge")
        )
        self.assertEqual(self.run_install(), 1)
        self.process.phase.assert_not_called()
        self.evidence.append.assert_any_call(
            Path("/evidence"),
            {
                "reset_skipped_due_to_windows_wsl_bridge": "yes",
                "setup_skipped_due_to_windows_wsl_bridge": "yes",
                "finished_utc": "finished",
            },
        )
        self.assertFalse(self.active_snapshot)

    def test_reset_failure_preserves_child_exit_and_never_starts_setup(self):
        for code in (17, 124, 130):
            with self.subTest(code=code):
                self.setUp()
                self.process.phase.side_effect = lambda *_, **__: code
                self.assertEqual(self.run_install(), code)
                self.process.phase.assert_called_once()
                self.evidence.append.assert_any_call(
                    Path("/evidence"),
                    {
                        "setup_skipped_due_to_reset_failure": "yes",
                        "finished_utc": "finished",
                    },
                )
                self.assertFalse(self.active_snapshot)

    def test_setup_failure_records_child_exit_and_completion(self):
        self.process.phase.side_effect = (0, 23)
        self.assertEqual(self.run_install(), 23)
        self.evidence.write.assert_any_call(Path("/evidence/setup-run.exit"), "23\n")
        self.presentation.completion.assert_called_once_with(
            23, Path("/evidence"), failed=True
        )
        self.presentation.setup_guidance.assert_called_once_with(
            Path("/evidence/setup-run.log")
        )

    def test_snapshot_closes_on_credential_failure_before_evidence(self):
        self.credentials.prepare.side_effect = InstallerError("invalid credentials")
        with self.assertRaisesRegex(InstallerError, "invalid credentials"):
            self.run_install()
        self.assertFalse(self.active_snapshot)
        self.assertEqual(self.calls[-1], "snapshot-close")
        self.evidence.directory.assert_not_called()
        self.process.phase.assert_not_called()

    def test_filesystem_rejection_stops_dependency_bootstrap(self):
        self.host.authorize.side_effect = InstallerError("filesystem blocked")
        with self.assertRaisesRegex(InstallerError, "filesystem blocked"):
            self.run_install()
        self.process.ensure_python.assert_not_called()
        self.configuration.snapshot.assert_not_called()

    def test_missing_terminal_recorder_stops_before_bridge_and_reset(self):
        self.process.recorder_available.return_value = False
        with self.assertRaisesRegex(InstallerError, "terminal recording"):
            self.run_install(headless=False)
        self.host.bridge.assert_not_called()
        self.process.phase.assert_not_called()
        self.assertFalse(self.active_snapshot)

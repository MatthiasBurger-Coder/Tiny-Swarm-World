"""Exercise guided setup decisions with simulated preparation and installer children."""

from __future__ import annotations

import io
import signal
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, call, patch

from tiny_swarm_world.infrastructure.adapters import guided_setup
from tiny_swarm_world.infrastructure.process import streaming


PLAN_DIGEST = "a" * 64
PLAN = (0, f"Observed plan\n{guided_setup.PLAN_PREFIX}{PLAN_DIGEST}")
COMMITTED = (0, f"{guided_setup.GUIDED_COMMITTED_PREFIX}{PLAN_DIGEST}")
READY = (0, "")
PARTIAL = {"stage": "install", "status": "interrupted"}


class GuidedSetupDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = Mock(
            root=Path("/fixture/guided-setup"),
            **{"acquire.return_value": 99, "prior.return_value": None,
               "has_preparation_record.return_value": False, "unchanged_target.return_value": True},
        )
        self.children = Mock()
        self.package_audit = Mock(return_value=subprocess.CompletedProcess([], 0, b"", b""))
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def invoke(self, mode, children=(), *, answer="yes\n", interactive=True, profile="service-access"):
        self.children.side_effect = children
        terminal = Mock(**{"isatty.return_value": interactive, "readline.return_value": answer})
        with (
            patch.object(guided_setup, "GuidedSetupState", return_value=self.state),
            patch.object(guided_setup, "run_foreground_process", self.children),
            patch.object(guided_setup, "run_process", self.package_audit),
            patch.object(guided_setup.os, "geteuid", return_value=1000),
            patch.object(guided_setup.signal, "signal"),
            patch.object(guided_setup.sys, "stdin", terminal),
            patch.object(self.stdout, "isatty", return_value=interactive),
            redirect_stdout(self.stdout),
            redirect_stderr(self.stderr),
        ):
            return guided_setup.main(mode, profile, verbose=True)

    def test_read_only_inventory_reports_previous_install_and_never_acquires_lease(self):
        self.state.prior.return_value = PARTIAL
        self.assertEqual(self.invoke("--dry-run", (READY, READY), interactive=False), 0)
        self.state.acquire.assert_not_called()
        self.state.checkpoint.assert_not_called()
        self.package_audit.assert_not_called()
        self.assertIn("Previous install stage", self.stderr.getvalue())
        self.assertIn("PLAN_READY", self.stdout.getvalue())
        self.assertEqual([child.args[0][0] for child in self.children.call_args_list],
                         [guided_setup.PREPARE, guided_setup.INSTALL])
        self.assertTrue(all(child.kwargs["timeout_seconds"] == 240 for child in self.children.call_args_list))

    def test_invalid_mode_and_noninteractive_apply_stop_before_inventory(self):
        self.assertEqual(self.invoke("--unsupported"), 2)
        self.assertEqual(self.invoke("apply", interactive=False), 2)
        self.children.assert_not_called()
        self.state.prior.assert_not_called()

    def test_read_only_child_failures_never_write_state(self):
        for children in (((1, ""),), (READY, (1, "")), (READY, (guided_setup.GUIDED_PLAN_REFUSED, ""))):
            with self.subTest(children=children):
                self.assertEqual(self.invoke("--preflight", children), 2)
        self.state.checkpoint.assert_not_called()
        self.state.acquire.assert_not_called()
        self.assertIn("Review the installer admission message", self.stderr.getvalue())

    def test_read_only_restart_recommends_resume_only_with_retained_state(self):
        self.assertEqual(self.invoke("--preflight", ((3, ""),)), 3)
        self.assertTrue(self.stderr.getvalue().endswith("./setup_linux.sh --profile service-access --verbose\n"))
        self.state.has_preparation_record.return_value = True
        self.assertEqual(self.invoke("--preflight", ((3, ""),)), 3)
        self.assertTrue(self.stderr.getvalue().endswith("--resume\n"))
        self.state.acquire.assert_not_called()

    def test_success_uses_consent_bound_plan_and_records_both_stages(self):
        self.assertEqual(self.invoke("apply", ((2, ""), READY, PLAN, READY, READY, READY)), 0)
        self.assertEqual(self.state.checkpoint.call_args_list, [
            call("prepare", "started"), call("prepare", "succeeded", 0),
            call("install", "started"), call("install", "succeeded", 0),
        ])
        self.package_audit.assert_called_once()
        self.assertIn("Observed plan", self.stdout.getvalue())
        self.assertNotIn(PLAN_DIGEST, self.stdout.getvalue())
        install, report = self.children.call_args_list[-2:]
        self.assertIn("--guided-report", install.args[0])
        self.assertEqual(install.kwargs["lease"], (99,))
        self.assertIsNone(install.kwargs["timeout_seconds"])
        self.assertEqual(install.kwargs["env"][guided_setup.EXPECTED_ENV], PLAN_DIGEST)
        self.assertEqual(report.args[0], (guided_setup.INSTALL, "--guided-status", "--service-profile", "service-access"))
        self.assertEqual(report.kwargs["timeout_seconds"], 240)

    def test_work_stops_when_consent_is_denied_or_inventory_changes(self):
        self.assertEqual(self.invoke("apply", (READY, PLAN), answer="no\n"), 2)
        self.assertEqual(self.invoke("apply", (READY, PLAN, (1, ""))), 2)
        self.state.unchanged_target.return_value = False
        self.assertEqual(self.invoke("apply", (READY, PLAN, READY)), 2)
        self.assertEqual(self.invoke("apply", ((2, ""),)), 2)
        self.state.checkpoint.assert_not_called()

    def test_malformed_or_unexpected_markers_stop_before_install(self):
        for preview in ((0, "no plan"), (0, f"{guided_setup.PLAN_PREFIX}short"), COMMITTED):
            with self.subTest(preview=preview):
                self.assertEqual(self.invoke("apply", (READY, preview)), 2)
        self.assertIn("Invalid committed installation observation", self.stderr.getvalue())
        self.state.checkpoint.assert_not_called()

    def test_resume_requires_retained_state_and_an_explicit_recovery_mode(self):
        self.assertEqual(self.invoke("--resume"), 2)
        self.state.acquire.assert_not_called()
        self.state.prior.return_value = PARTIAL
        self.assertEqual(self.invoke("apply"), 2)
        self.children.assert_not_called()
        self.assertIn("Explicit recovery is required", self.stderr.getvalue())
        self.assertEqual(self.invoke("--resume", ((2, ""),)), 2)
        self.state.checkpoint.assert_not_called()

    def test_confirmed_installer_completion_is_recorded_without_reapplying(self):
        self.state.prior.return_value = PARTIAL
        self.assertEqual(self.invoke("--resume", (READY, COMMITTED, READY), answer="no\n"), 0)
        self.assertEqual(self.children.call_count, 3)
        self.assertIn("--guided-resume", self.children.call_args_list[1].args[0])
        self.assertIn("--guided-status", self.children.call_args.args[0])
        self.state.checkpoint.assert_called_once_with("install", "succeeded", 0)
        self.assertNotIn("Type yes", self.stderr.getvalue())

    def test_unavailable_report_preserves_completed_installation(self):
        self.assertEqual(self.invoke("apply", (READY, PLAN, READY, READY, (124, ""))), 124)
        self.state.checkpoint.assert_called_with("install", "succeeded", 0)
        self.assertIn("INSTALLATION_COMPLETE", self.stdout.getvalue())
        self.assertIn("Service access report incomplete", self.stderr.getvalue())

    def test_stale_installer_completion_does_not_replace_existing_checkpoint(self):
        self.state.prior.side_effect = [PARTIAL, PARTIAL, {"stage": "install", "status": "started"}]
        self.assertEqual(self.invoke("--resume", (READY, COMMITTED)), 2)
        self.state.checkpoint.assert_not_called()

    def test_rejected_plan_binding_restores_prior_or_confirmed_preparation(self):
        result = (guided_setup.GUIDED_PLAN_REFUSED, "")
        self.assertEqual(self.invoke("apply", (READY, PLAN, READY, result)), 2)
        self.assertEqual(self.state.checkpoint.call_args_list,
                         [call("install", "started"), call("prepare", "succeeded", 0)])
        self.state.prior.return_value = PARTIAL
        self.assertEqual(self.invoke("--resume", (READY, PLAN, READY, result)), 2)
        self.state.restore.assert_called_once_with(PARTIAL)

    def test_child_outcomes_retain_uncertain_checkpoints(self):
        for code, expected, status in ((3, 3, "restart_required"), (143, 130, "interrupted"),
                                       (124, 124, "partial"), (1, 1, "partial")):
            with self.subTest(code=code):
                self.assertEqual(self.invoke("apply", ((2, ""), (code, ""))), expected)
                self.state.checkpoint.assert_called_with("prepare", status, code)
        self.state.checkpoint.side_effect = (None, OSError("checkpoint unavailable"))
        self.assertEqual(self.invoke("apply", (READY, PLAN, READY, (1, ""))), 1)
        self.assertIn("saved intent still requires review", self.stderr.getvalue())

    def test_package_review_and_unexpected_errors_fail_closed(self):
        self.state.prior.return_value = PARTIAL
        self.package_audit.return_value = subprocess.CompletedProcess([], 0, b"pending", b"")
        self.assertEqual(self.invoke("--resume"), 2)
        self.children.assert_not_called()
        self.assertIn("dpkg --audit", self.stderr.getvalue())

        self.state.prior.return_value = None
        self.assertEqual(self.invoke("apply", (READY, PLAN, READY, OSError("child unavailable"))), 1)
        self.assertIn("PARTIAL at install", self.stderr.getvalue())
        self.assertEqual(self.invoke("--preflight", (KeyboardInterrupt(),)), 130)
        self.state.close.assert_called()


class ForegroundCleanupTests(unittest.TestCase):
    def test_capture_normalizes_signal_exit_and_releases_stream(self):
        child = Mock(returncode=-signal.SIGTERM, **{"communicate.return_value": ("report", None)})
        with patch.object(streaming.subprocess, "Popen", return_value=child) as start:
            result = streaming.run_foreground_process(("fixture",), timeout_seconds=3, capture=True, lease=(99,))
        self.assertEqual(result, (143, "report"))
        self.assertEqual(start.call_args.kwargs["pass_fds"], (99,))
        child.stdout.close.assert_called_once()

    def test_interrupt_grace_timeout_signals_and_reaps_child(self):
        timeout = subprocess.TimeoutExpired("fixture", 1)
        child = Mock(**{"communicate.side_effect": (KeyboardInterrupt(), timeout, timeout)})
        with patch.object(streaming.subprocess, "Popen", return_value=child):
            result = streaming.run_foreground_process(("fixture",), timeout_seconds=None, capture=False, lease=())
        self.assertEqual(result, (130, ""))
        child.send_signal.assert_called_once_with(signal.SIGINT)
        child.kill.assert_called_once()
        child.wait.assert_called_once_with(timeout=5)

    def test_foreground_timeout_and_requested_termination_remain_distinct(self):
        for event, expected in ((subprocess.TimeoutExpired("fixture", 1), 124),
                                (streaming.ForegroundTerminationRequested(), 130)):
            with self.subTest(event=type(event)):
                child = Mock(stdout=None, **{"communicate.side_effect": (event, ("", None))})
                with patch.object(streaming.subprocess, "Popen", return_value=child):
                    result = streaming.run_foreground_process(("fixture",), timeout_seconds=1, capture=False, lease=())
                self.assertEqual(result, (expected, ""))
                child.send_signal.assert_called_once_with(signal.SIGINT)

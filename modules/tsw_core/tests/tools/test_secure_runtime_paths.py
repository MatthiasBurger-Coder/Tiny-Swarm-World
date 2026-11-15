from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from modules.tsw_core.tests.e2e.classic import run_classic_acceptance
from modules.tsw_native_linux.tools.live.secure_runtime_paths import (
    NATIVE_LINUX,
    classify_path,
    ensure_secure_directory,
)


class TestSecureRuntimePaths(unittest.TestCase):
    def test_classic_e2e_command_exposes_source_package_to_python(self) -> None:
        self.assertEqual(
            ("env", "PYTHONPATH=.", "TSW_RUN_POST_INSTALL_BROWSER_LIVE=1"),
            run_classic_acceptance.CLASSIC_E2E_COMMAND[:3],
        )
        self.assertEqual(
            "modules.tsw_core.tests.e2e.classic.test_post_install_browser_live.PostInstallBrowserLiveTest",
            run_classic_acceptance.CLASSIC_E2E_COMMAND[-1],
        )


    def test_native_host_classifies_without_reading_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.env"
            self.assertEqual(NATIVE_LINUX, classify_path(path, host="native_linux"))

    def test_existing_non_private_evidence_directory_is_not_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "evidence"
            evidence.mkdir(mode=0o755)
            evidence.chmod(0o755)

            with self.assertRaises(RuntimeError):
                ensure_secure_directory(evidence)

            self.assertEqual(0o755, evidence.stat().st_mode & 0o777)

    def test_new_evidence_directory_is_created_owner_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "nested" / "evidence"

            assessment = ensure_secure_directory(evidence)

            self.assertTrue(assessment.allowed)
            self.assertEqual(0o700, evidence.stat().st_mode & 0o777)

    def test_new_evidence_ancestors_are_private_with_group_writable_umask(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "state" / "installation" / "evidence"
            previous_umask = os.umask(0o002)
            try:
                assessment = ensure_secure_directory(evidence)
            finally:
                os.umask(previous_umask)

            self.assertTrue(assessment.allowed)
            for path in (evidence, evidence.parent, evidence.parent.parent):
                self.assertEqual(0o700, path.stat().st_mode & 0o777)

    def test_e2e_summary_does_not_propagate_secret_like_output(self) -> None:
        secret = "previously-exposed-value"
        summary = run_classic_acceptance._summarize(
            "classic_e2e",
            f"FAILED: {secret}\n",
            "",
        )

        self.assertNotIn(secret, repr(summary))
        self.assertEqual("failed", summary["result"])

    def test_skipped_e2e_is_not_a_success(self) -> None:
        result = run_classic_acceptance.CommandResult(
            operation="classic_e2e",
            started_at="now",
            finished_at="now",
            duration_seconds=0.1,
            exit_code=0,
            summary=run_classic_acceptance._summarize(
                "classic_e2e",
                "Ran 1 test in 0.1s\nOK (skipped=1)\n",
                "",
            ),
        )

        self.assertFalse(run_classic_acceptance._operation_succeeded(result))
        self.assertFalse(run_classic_acceptance._valid_rotation_reference("raw secret"))
        self.assertTrue(run_classic_acceptance._valid_rotation_reference("ticket-271-20260829"))

    def test_disposable_test_profile_does_not_require_rotation_reference(self) -> None:
        self.assertTrue(run_classic_acceptance._rotation_reference_valid_for_profile(True, None))
        self.assertFalse(run_classic_acceptance._rotation_reference_valid_for_profile(False, None))
        self.assertEqual(
            "not_applicable_test_only",
            run_classic_acceptance._rotation_evidence_status(True, "ignored-reference"),
        )
        self.assertEqual(
            "recorded",
            run_classic_acceptance._rotation_evidence_status(False, "ticket-271-20260829"),
        )

    def test_structured_summary_accepts_runner_status_lines_before_json(self) -> None:
        payload = run_classic_acceptance._find_structured_payload(
            "setup phase started\n{\n  \"status\": \"completed\"\n}\n",
            "",
        )

        self.assertEqual({"status": "completed"}, payload)

    def test_structured_summary_keeps_diagnostics_redacted_and_bounded(self) -> None:
        summary = run_classic_acceptance._summarize(
            "setup",
            "{\"status\": \"failed\", \"message\": \"password=secret-value\", "
            "\"phase_results\": [{\"name\": \"setup\", \"status\": \"failed\"}]}\n",
            "",
        )

        self.assertEqual("failed", summary["result"])
        self.assertEqual("password=<redacted>", summary["message"])
        self.assertEqual(
            {"count": 1, "failed": [{"name": "setup"}]},
            summary["phase_results"],
        )


if __name__ == "__main__":
    unittest.main()

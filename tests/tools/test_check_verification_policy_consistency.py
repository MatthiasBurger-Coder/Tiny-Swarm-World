from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from tools.check_verification_policy_consistency import check_repository


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPOSITORY_ROOT / "documentation/process/verification-state-policy.md"


class VerificationPolicyConsistencyTests(unittest.TestCase):
    def test_real_repository_is_consistent(self) -> None:
        self.assertEqual(check_repository(REPOSITORY_ROOT), ())

    def test_unconditional_selenium_wording_is_rejected(self) -> None:
        with self._repository_fixture("Selenium E2E evidence exists for this workflow.") as root:
            findings = check_repository(root)

        self.assertTrue(any("unconditional verification wording" in finding.message for finding in findings))

    def test_explicitly_negative_wording_is_allowed(self) -> None:
        with self._repository_fixture(
            "The workflow must not claim that Selenium E2E evidence exists."
        ) as root:
            self.assertEqual(check_repository(root), ())

    def test_unknown_state_is_rejected(self) -> None:
        with self._repository_fixture("The result is LIVE_UNKNOWN.") as root:
            findings = check_repository(root)

        self.assertTrue(any("unknown verification state" in finding.message for finding in findings))

    def test_unavailable_success_is_rejected(self) -> None:
        with self._repository_fixture("The unavailable SonarQube result is green.") as root:
            findings = check_repository(root)

        self.assertTrue(any("described as success" in finding.message for finding in findings))

    def test_install_command_requires_consent_context(self) -> None:
        command = (
            "./install.sh --headless --confirm-reset --non-interactive-live-approval"
        )
        with self._repository_fixture(command) as root:
            findings = check_repository(root)

        self.assertTrue(any("consent context" in finding.message for finding in findings))

    def _repository_fixture(self, governance_line: str):
        temporary_directory = tempfile.TemporaryDirectory()
        root = Path(temporary_directory.name)
        policy_target = root / "documentation/process/verification-state-policy.md"
        policy_target.parent.mkdir(parents=True)
        shutil.copyfile(POLICY_PATH, policy_target)
        governance_target = root / "documentation/process/governance.md"
        governance_target.write_text(governance_line + "\n", encoding="utf-8")
        return _TemporaryRepository(temporary_directory, root)


class _TemporaryRepository:
    def __init__(self, temporary_directory: tempfile.TemporaryDirectory, root: Path):
        self._temporary_directory = temporary_directory
        self.root = root

    def __enter__(self) -> Path:
        return self.root

    def __exit__(self, *_: object) -> None:
        self._temporary_directory.cleanup()


if __name__ == "__main__":
    unittest.main()

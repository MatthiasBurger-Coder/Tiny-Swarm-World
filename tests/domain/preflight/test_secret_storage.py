from __future__ import annotations

import unittest

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.preflight.secret_storage import (
    SecretStorageInspection,
    assess_secret_storage,
)
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind


class TestSecretStoragePolicy(unittest.TestCase):
    def test_windows_mounted_secret_is_blocked_even_with_private_mode_bits(self) -> None:
        inspection = _inspection(ProjectFilesystemKind.WINDOWS_MOUNTED)

        assessment = assess_secret_storage(
            HostEnvironmentKind.WSL2,
            inspection,
            expected_uid=1000,
            expected_gid=1000,
            require_existing_file=True,
        )

        self.assertFalse(assessment.allowed)
        self.assertIn("storage_filesystem_not_linux_native", assessment.reasons)
        self.assertNotIn("/mnt/c/Users/private", repr(assessment))

    def test_wsl_native_secret_requires_owner_and_exact_modes(self) -> None:
        inspection = _inspection(ProjectFilesystemKind.WSL_LINUX)

        assessment = assess_secret_storage(
            HostEnvironmentKind.WSL2,
            inspection,
            expected_uid=1000,
            expected_gid=1000,
            require_existing_file=True,
        )

        self.assertTrue(assessment.allowed)
        self.assertEqual("allowed", assessment.decision.value)
        self.assertEqual("verified", inspection.to_safe_dict(expected_uid=1000, expected_gid=1000)["file_mode_private"])

    def test_wrong_owner_or_mode_fails_closed(self) -> None:
        inspection = _inspection(
            ProjectFilesystemKind.WSL_LINUX,
            owner_uid=1001,
            mode=0o644,
        )

        assessment = assess_secret_storage(
            HostEnvironmentKind.WSL2,
            inspection,
            expected_uid=1000,
            expected_gid=1000,
            require_existing_file=True,
        )

        self.assertFalse(assessment.allowed)
        self.assertIn("secret_file_owner_mismatch", assessment.reasons)
        self.assertIn("secret_file_mode_not_0600", assessment.reasons)


def _inspection(
    filesystem_kind: ProjectFilesystemKind,
    *,
    owner_uid: int = 1000,
    mode: int = 0o600,
) -> SecretStorageInspection:
    return SecretStorageInspection(
        resolved_path="/mnt/c/Users/private/live-installation.env",
        filesystem_kind=filesystem_kind,
        filesystem_type="9p" if filesystem_kind is ProjectFilesystemKind.WINDOWS_MOUNTED else "ext4",
        exists=True,
        is_regular_file=True,
        owner_uid=owner_uid,
        group_gid=1000,
        mode=mode,
        parent_exists=True,
        parent_owner_uid=1000,
        parent_group_gid=1000,
        parent_mode=0o700,
        classification_source="test_fixture",
    )


if __name__ == "__main__":
    unittest.main()

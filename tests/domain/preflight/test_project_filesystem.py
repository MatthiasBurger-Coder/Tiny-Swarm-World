import unittest

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    LINUX_HOME_RECOMMENDATION,
    ProjectFilesystemDecision,
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
    assess_project_filesystem,
)


class TestProjectFilesystemPolicy(unittest.TestCase):
    def test_wsl_windows_mount_blocks_by_default(self):
        assessment = assess_project_filesystem(
            HostEnvironmentKind.WSL2,
            _inspection(ProjectFilesystemKind.WINDOWS_MOUNTED, "/mnt/d/project"),
            allow_wsl_windows_filesystem=False,
        )

        self.assertEqual(ProjectFilesystemDecision.BLOCKED, assessment.decision)
        self.assertTrue(assessment.blocked)
        self.assertFalse(assessment.override_applied)
        self.assertIn(LINUX_HOME_RECOMMENDATION, assessment.remediation)

    def test_wsl_windows_mount_requires_explicit_typed_override(self):
        assessment = assess_project_filesystem(
            HostEnvironmentKind.WSL2,
            _inspection(ProjectFilesystemKind.WINDOWS_MOUNTED, "/mnt/e/project"),
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual(
            ProjectFilesystemDecision.ALLOWED_BY_OVERRIDE,
            assessment.decision,
        )
        self.assertTrue(assessment.allowed)
        self.assertTrue(assessment.override_requested)
        self.assertTrue(assessment.override_applied)

    def test_wsl_native_filesystem_is_allowed_without_applying_override(self):
        assessment = assess_project_filesystem(
            HostEnvironmentKind.WSL2,
            _inspection(ProjectFilesystemKind.WSL_LINUX, "/home/user/project"),
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual(ProjectFilesystemDecision.ALLOWED, assessment.decision)
        self.assertTrue(assessment.override_requested)
        self.assertFalse(assessment.override_applied)

    def test_unknown_wsl_filesystem_fails_closed_even_with_override(self):
        assessment = assess_project_filesystem(
            HostEnvironmentKind.WSL2,
            _inspection(ProjectFilesystemKind.UNKNOWN, "/work/project"),
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual(ProjectFilesystemDecision.BLOCKED, assessment.decision)
        self.assertFalse(assessment.override_applied)

    def test_native_linux_is_allowed_without_windows_override_semantics(self):
        assessment = assess_project_filesystem(
            HostEnvironmentKind.NATIVE_LINUX,
            _inspection(ProjectFilesystemKind.NATIVE_LINUX, "/srv/project"),
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual(ProjectFilesystemDecision.ALLOWED, assessment.decision)
        self.assertFalse(assessment.override_applied)

    def test_unsupported_host_cannot_be_released_by_filesystem_override(self):
        assessment = assess_project_filesystem(
            HostEnvironmentKind.WSL1_UNSUPPORTED,
            _inspection(ProjectFilesystemKind.WINDOWS_MOUNTED, "/mnt/c/project"),
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual(ProjectFilesystemDecision.BLOCKED, assessment.decision)
        self.assertFalse(assessment.override_applied)

    def test_safe_serialization_and_repr_never_expose_resolved_path(self):
        path = "/mnt/c/Users/private/project"
        inspection = _inspection(ProjectFilesystemKind.WINDOWS_MOUNTED, path)
        assessment = assess_project_filesystem(
            HostEnvironmentKind.WSL2,
            inspection,
            allow_wsl_windows_filesystem=True,
        )

        self.assertNotIn(path, repr(inspection))
        self.assertNotIn(path, repr(assessment))
        self.assertNotIn(path, str(assessment.to_safe_dict()))
        self.assertNotIn("project_path", assessment.to_safe_dict())
        self.assertEqual(
            "allowed_by_override",
            assessment.to_safe_dict()["decision"],
        )


def _inspection(
    kind: ProjectFilesystemKind,
    path: str,
) -> ProjectFilesystemInspection:
    return ProjectFilesystemInspection(
        kind=kind,
        resolved_project_path=path,
        filesystem_type="9p" if kind is ProjectFilesystemKind.WINDOWS_MOUNTED else "ext4",
        classification_source="test_fixture",
    )

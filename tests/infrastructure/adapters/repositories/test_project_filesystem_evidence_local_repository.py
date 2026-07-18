import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.application.ports.host.port_project_filesystem_inspector import (
    PortProjectFilesystemInspector,
)
from tiny_swarm_world.application.ports.repositories.port_project_filesystem_evidence_repository import (
    ProjectFilesystemEvidenceError,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemAssessment,
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
    assess_project_filesystem,
)
from tiny_swarm_world.infrastructure.adapters.repositories import (
    project_filesystem_evidence_local_repository as repository_module,
)
from tiny_swarm_world.infrastructure.adapters.repositories.project_filesystem_evidence_local_repository import (
    ProjectFilesystemEvidenceLocalRepository,
)


class TestProjectFilesystemEvidenceLocalRepository(unittest.TestCase):
    def test_writes_exact_allowlist_atomically_with_private_modes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "state" / "decision.json"
            inspector = _TargetInspector(ProjectFilesystemKind.WSL_LINUX)
            repository = ProjectFilesystemEvidenceLocalRepository(
                path=path,
                target_inspector=inspector,
            )

            repository.write(_override_assessment())

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "decision",
                    "filesystem_classification",
                    "override_applied",
                    "override_requested",
                    "project_path",
                    "schema_version",
                },
                set(payload),
            )
            self.assertEqual(1, payload["schema_version"])
            self.assertEqual("allowed_by_override", payload["decision"])
            self.assertEqual("/mnt/d/project", payload["project_path"])
            self.assertEqual(0o700, stat.S_IMODE(path.parent.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
            self.assertEqual(
                [(path.parent.as_posix(), HostEnvironmentKind.WSL2)],
                inspector.calls,
            )
            self.assertEqual([], list(path.parent.glob(".*.tmp")))

    def test_windows_mounted_or_unknown_evidence_target_blocks_override(self):
        for kind in (
            ProjectFilesystemKind.WINDOWS_MOUNTED,
            ProjectFilesystemKind.UNKNOWN,
        ):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary_directory:
                path = Path(temporary_directory) / "state" / "decision.json"
                repository = ProjectFilesystemEvidenceLocalRepository(
                    path=path,
                    target_inspector=_TargetInspector(kind),
                )

                with self.assertRaises(ProjectFilesystemEvidenceError):
                    repository.write(_override_assessment())

                self.assertFalse(path.exists())

    def test_failed_atomic_replace_preserves_previous_complete_document(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "state" / "decision.json"
            path.parent.mkdir()
            path.write_text("previous-complete-evidence\n", encoding="utf-8")
            repository = ProjectFilesystemEvidenceLocalRepository(
                path=path,
                target_inspector=_TargetInspector(ProjectFilesystemKind.WSL_LINUX),
            )

            with patch.object(repository_module.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(ProjectFilesystemEvidenceError):
                    repository.write(_override_assessment())

            self.assertEqual("previous-complete-evidence\n", path.read_text(encoding="utf-8"))
            self.assertEqual([], list(path.parent.glob(".*.tmp")))

    def test_permission_verification_failure_is_blocking(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "state" / "decision.json"
            repository = ProjectFilesystemEvidenceLocalRepository(
                path=path,
                target_inspector=_TargetInspector(ProjectFilesystemKind.WSL_LINUX),
            )

            with patch.object(
                repository_module,
                "_set_private_mode",
                side_effect=ProjectFilesystemEvidenceError("mode mismatch"),
            ):
                with self.assertRaises(ProjectFilesystemEvidenceError):
                    repository.write(_override_assessment())

    def test_from_environment_uses_xdg_state_home_not_repository_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            xdg_root = Path(temporary_directory) / "xdg-state"

            repository = ProjectFilesystemEvidenceLocalRepository.from_environment(
                {"XDG_STATE_HOME": xdg_root.as_posix()},
                target_inspector=_TargetInspector(ProjectFilesystemKind.WSL_LINUX),
            )

            self.assertEqual(
                xdg_root
                / "tiny-swarm-world"
                / "installation"
                / "project-filesystem-decision.json",
                repository.path,
            )

    def test_relative_xdg_state_home_blocks_only_an_override_evidence_write(self):
        repository = ProjectFilesystemEvidenceLocalRepository.from_environment(
            {"XDG_STATE_HOME": "relative/state"},
            target_inspector=_TargetInspector(ProjectFilesystemKind.WSL_LINUX),
        )

        with self.assertRaisesRegex(
            ProjectFilesystemEvidenceError,
            "XDG_STATE_HOME must be an absolute Linux path",
        ):
            repository.write(_override_assessment())


class _TargetInspector(PortProjectFilesystemInspector):
    def __init__(self, kind: ProjectFilesystemKind) -> None:
        self.kind = kind
        self.calls: list[tuple[str, HostEnvironmentKind]] = []

    def inspect(
        self,
        repository_root: str,
        host_environment: HostEnvironmentKind,
    ) -> ProjectFilesystemInspection:
        self.calls.append((repository_root, host_environment))
        return ProjectFilesystemInspection(
            kind=self.kind,
            resolved_project_path=repository_root,
            filesystem_type="ext4",
            classification_source="fake",
        )


def _override_assessment() -> ProjectFilesystemAssessment:
    return assess_project_filesystem(
        HostEnvironmentKind.WSL2,
        ProjectFilesystemInspection(
            kind=ProjectFilesystemKind.WINDOWS_MOUNTED,
            resolved_project_path="/mnt/d/project",
            filesystem_type="9p",
            classification_source="fake",
        ),
        allow_wsl_windows_filesystem=True,
    )

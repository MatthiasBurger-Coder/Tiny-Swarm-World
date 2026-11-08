import unittest

from tiny_swarm_world.application.ports.host.port_project_filesystem_inspector import (
    PortProjectFilesystemInspector,
)
from tiny_swarm_world.application.ports.repositories.port_project_filesystem_evidence_repository import (
    PortProjectFilesystemEvidenceRepository,
    ProjectFilesystemEvidenceError,
)
from tiny_swarm_world.application.services.platform.host.authorize_project_filesystem import (
    AuthorizeProjectFilesystem,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemAssessment,
    ProjectFilesystemDecision,
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
)


class TestAuthorizeProjectFilesystem(unittest.TestCase):
    def test_records_only_an_applied_windows_filesystem_override(self):
        repository = _EvidenceRepository()
        service = AuthorizeProjectFilesystem(
            _Inspector(ProjectFilesystemKind.WINDOWS_MOUNTED),
            repository,
        )

        assessment = service.run(
            HostEnvironmentKind.WSL2,
            "/mnt/d/project",
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual(ProjectFilesystemDecision.ALLOWED_BY_OVERRIDE, assessment.decision)
        self.assertEqual(repository.writes, [assessment])

    def test_normal_allowed_decision_does_not_write_override_evidence(self):
        repository = _EvidenceRepository()

        assessment = AuthorizeProjectFilesystem(
            _Inspector(ProjectFilesystemKind.WSL_LINUX),
            repository,
        ).run(
            HostEnvironmentKind.WSL2,
            "/home/user/project",
            allow_wsl_windows_filesystem=False,
        )

        self.assertEqual(ProjectFilesystemDecision.ALLOWED, assessment.decision)
        self.assertEqual(repository.writes, [])

    def test_evidence_failure_turns_applied_override_into_blocked(self):
        repository = _EvidenceRepository(
            error=ProjectFilesystemEvidenceError("protected evidence unavailable")
        )

        assessment = AuthorizeProjectFilesystem(
            _Inspector(ProjectFilesystemKind.WINDOWS_MOUNTED),
            repository,
        ).run(
            HostEnvironmentKind.WSL2,
            "/mnt/d/project",
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual(ProjectFilesystemDecision.BLOCKED, assessment.decision)
        self.assertFalse(assessment.override_applied)
        self.assertEqual(
            assessment.to_safe_dict()["evidence_status"],
            "protected_evidence_unavailable",
        )
        self.assertNotIn("/mnt/d/project", str(assessment.to_safe_dict()))


class _Inspector(PortProjectFilesystemInspector):
    def __init__(self, kind: ProjectFilesystemKind) -> None:
        self.kind = kind

    def inspect(
        self,
        repository_root: str,
        host_environment: HostEnvironmentKind,
    ) -> ProjectFilesystemInspection:
        return ProjectFilesystemInspection(
            kind=self.kind,
            resolved_project_path=repository_root,
            filesystem_type="9p" if self.kind is ProjectFilesystemKind.WINDOWS_MOUNTED else "ext4",
            classification_source="fake",
        )


class _EvidenceRepository(PortProjectFilesystemEvidenceRepository):
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.writes: list[ProjectFilesystemAssessment] = []

    def write(self, assessment: ProjectFilesystemAssessment) -> None:
        if self.error is not None:
            raise self.error
        self.writes.append(assessment)

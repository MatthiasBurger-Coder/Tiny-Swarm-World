import unittest

from tiny_swarm_world.application.ports.host.port_project_filesystem_inspector import (
    PortProjectFilesystemInspector,
)
from tiny_swarm_world.application.services.platform.host.evaluate_project_filesystem import (
    EvaluateProjectFilesystem,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemDecision,
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
)


class TestEvaluateProjectFilesystem(unittest.TestCase):
    def test_delegates_inspection_and_applies_pure_policy(self):
        inspector = _Inspector(ProjectFilesystemKind.WINDOWS_MOUNTED)
        service = EvaluateProjectFilesystem(inspector)

        assessment = service.run(
            HostEnvironmentKind.WSL2,
            "/mnt/d/project",
            allow_wsl_windows_filesystem=False,
        )

        self.assertEqual(
            [("/mnt/d/project", HostEnvironmentKind.WSL2)],
            inspector.calls,
        )
        self.assertEqual(ProjectFilesystemDecision.BLOCKED, assessment.decision)

    def test_does_not_inspect_filesystem_for_unsupported_host(self):
        inspector = _Inspector(ProjectFilesystemKind.WINDOWS_MOUNTED)

        assessment = EvaluateProjectFilesystem(inspector).run(
            HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
            "/mnt/d/project",
            allow_wsl_windows_filesystem=True,
        )

        self.assertEqual([], inspector.calls)
        self.assertEqual(ProjectFilesystemDecision.BLOCKED, assessment.decision)
        self.assertFalse(assessment.override_applied)


class _Inspector(PortProjectFilesystemInspector):
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
            filesystem_type="9p",
            classification_source="fake",
        )

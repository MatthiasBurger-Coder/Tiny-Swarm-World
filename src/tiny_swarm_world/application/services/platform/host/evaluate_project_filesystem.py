from __future__ import annotations

from tiny_swarm_world.application.ports.host.port_project_filesystem_inspector import (
    PortProjectFilesystemInspector,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemAssessment,
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
    assess_project_filesystem,
)


class EvaluateProjectFilesystem:
    def __init__(self, inspector: PortProjectFilesystemInspector) -> None:
        self.inspector = inspector

    def run(
        self,
        host_environment: HostEnvironmentKind,
        project_path: str,
        *,
        allow_wsl_windows_filesystem: bool,
    ) -> ProjectFilesystemAssessment:
        if host_environment not in {
            HostEnvironmentKind.NATIVE_LINUX,
            HostEnvironmentKind.WSL2,
        }:
            inspection = ProjectFilesystemInspection(
                kind=ProjectFilesystemKind.UNKNOWN,
                resolved_project_path=project_path,
                classification_source="host_unsupported",
            )
        else:
            inspection = self.inspector.inspect(project_path, host_environment)
        return assess_project_filesystem(
            host_environment,
            inspection,
            allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
        )

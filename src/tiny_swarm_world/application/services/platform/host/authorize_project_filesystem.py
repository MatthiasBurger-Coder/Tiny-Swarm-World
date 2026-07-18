from __future__ import annotations

from tiny_swarm_world.application.ports.host.port_project_filesystem_inspector import (
    PortProjectFilesystemInspector,
)
from tiny_swarm_world.application.ports.repositories.port_project_filesystem_evidence_repository import (
    PortProjectFilesystemEvidenceRepository,
    ProjectFilesystemEvidenceError,
)
from tiny_swarm_world.application.services.platform.host.evaluate_project_filesystem import (
    EvaluateProjectFilesystem,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemAssessment,
    ProjectFilesystemDecision,
)


class AuthorizeProjectFilesystem:
    def __init__(
        self,
        inspector: PortProjectFilesystemInspector,
        evidence_repository: PortProjectFilesystemEvidenceRepository,
    ) -> None:
        self.evaluator = EvaluateProjectFilesystem(inspector)
        self.evidence_repository = evidence_repository

    def run(
        self,
        host_environment: HostEnvironmentKind,
        project_path: str,
        *,
        allow_wsl_windows_filesystem: bool,
    ) -> ProjectFilesystemAssessment:
        assessment = self.evaluator.run(
            host_environment,
            project_path,
            allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
        )
        if assessment.decision is not ProjectFilesystemDecision.ALLOWED_BY_OVERRIDE:
            return assessment
        recorded = assessment.mark_evidence_recorded()
        try:
            self.evidence_repository.write(recorded)
        except ProjectFilesystemEvidenceError:
            return assessment.block_for_evidence_failure()
        return recorded

from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemAssessment


class ProjectFilesystemEvidenceError(OperationError, RuntimeError):
    """Protected filesystem-decision evidence could not be stored safely."""

    def __init__(self, message: str):
        super().__init__(OperationFailure.for_cause("evidence.write", "filesystem_evidence", "filesystem_error"))
        self.args = (message,)


class PortProjectFilesystemEvidenceRepository(ABC):
    @abstractmethod
    def write(self, assessment: ProjectFilesystemAssessment) -> None:
        """Atomically store the allowlisted applied-override decision."""

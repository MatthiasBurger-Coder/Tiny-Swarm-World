from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemAssessment


class ProjectFilesystemEvidenceError(RuntimeError):
    """Protected filesystem-decision evidence could not be stored safely."""


class PortProjectFilesystemEvidenceRepository(ABC):
    @abstractmethod
    def write(self, assessment: ProjectFilesystemAssessment) -> None:
        """Atomically store the allowlisted applied-override decision."""

from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemInspection


class PortProjectFilesystemInspector(ABC):
    @abstractmethod
    def inspect(
        self,
        repository_root: str,
        host_environment: HostEnvironmentKind,
    ) -> ProjectFilesystemInspection:
        """Return normalized project-filesystem facts without executing commands."""

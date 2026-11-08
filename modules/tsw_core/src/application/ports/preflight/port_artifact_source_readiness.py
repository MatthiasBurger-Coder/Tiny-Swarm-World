from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.preflight.artifact_sources import ArtifactSourceReadiness


class PortArtifactSourceReadiness(ABC):
    @abstractmethod
    def check(self) -> ArtifactSourceReadiness:
        """Check configured package and container sources without mutation."""

        raise NotImplementedError

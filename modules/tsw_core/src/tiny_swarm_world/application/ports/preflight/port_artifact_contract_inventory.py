from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from tiny_swarm_world.domain.artifacts import ArtifactImageInventory


class PortArtifactContractInventory(ABC):
    """Application boundary for static image contracts and approved build inputs."""

    @abstractmethod
    def get_image_inventory(self) -> ArtifactImageInventory:
        """Return the effective inventory for the selected service profile."""

    @abstractmethod
    def get_build_context_path(self, build_context: str) -> Path:
        """Resolve an approved local build context for static inspection."""

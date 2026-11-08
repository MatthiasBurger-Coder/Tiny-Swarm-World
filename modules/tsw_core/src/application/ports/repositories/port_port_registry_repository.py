from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.network import PortRegistry


class PortPortRegistryRepository(ABC):
    @abstractmethod
    def load(self) -> PortRegistry:
        """Load the desired port registry from committed product configuration."""
        pass

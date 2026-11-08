from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.inventory import ObservedInventory


class PortObservedInventoryRepository(ABC):
    @abstractmethod
    def load(self) -> ObservedInventory:
        """Load the latest ignored local observed inventory snapshot."""

    @abstractmethod
    def save(self, inventory: ObservedInventory) -> None:
        """Persist an ignored local observed inventory snapshot."""

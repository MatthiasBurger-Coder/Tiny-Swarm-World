from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.inventory import DesiredInventory


class PortDesiredInventoryRepository(ABC):
    @abstractmethod
    def load(self) -> DesiredInventory:
        """Load desired inventory from committed product configuration."""

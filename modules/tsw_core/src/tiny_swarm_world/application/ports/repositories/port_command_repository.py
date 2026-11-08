from abc import ABC, abstractmethod
from typing import Dict

from tiny_swarm_world.domain.command.command_entity import CommandEntity


class PortCommandRepository(ABC):
    """Interface for command repositories."""

    @abstractmethod
    def get_all_commands(self) -> Dict[int, CommandEntity]:
        """Returns all configured commands."""
        pass

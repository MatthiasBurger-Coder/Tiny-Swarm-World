
from abc import ABC, abstractmethod

from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition


class PortComposeFileRepository(ABC):
    @abstractmethod
    def get_compose_of(self, stack_name: str) -> StackDefinition:
        """Returns the compose content for the requested stack."""
        pass

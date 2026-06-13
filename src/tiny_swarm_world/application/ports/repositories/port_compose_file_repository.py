
from abc import ABC, abstractmethod

from tiny_swarm_world.domain.deployment.stack_definition import (
    ComposeServiceDefinition,
    StackDefinition,
)


class PortComposeFileRepository(ABC):
    @abstractmethod
    def get_compose_of(self, stack_name: str) -> StackDefinition:
        """Returns the compose content for the requested stack."""
        pass

    @abstractmethod
    def get_services_of(self, stack_name: str) -> tuple[ComposeServiceDefinition, ...]:
        """Returns service names and published ports from the requested stack."""
        pass

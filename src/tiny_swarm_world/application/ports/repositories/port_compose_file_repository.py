
from abc import ABC, abstractmethod
from pathlib import Path

from tiny_swarm_world.application.ports.preflight import PortArtifactContractInventory
from tiny_swarm_world.domain.artifacts import ArtifactImageInventory
from tiny_swarm_world.domain.deployment.stack_definition import (
    ComposeServiceDefinition,
    StackDefinition,
)


class PortComposeFileRepository(PortArtifactContractInventory, ABC):
    @abstractmethod
    def get_compose_of(self, stack_name: str) -> StackDefinition:
        """Returns the compose content for the requested stack."""
        pass

    @abstractmethod
    def get_services_of(self, stack_name: str) -> tuple[ComposeServiceDefinition, ...]:
        """Returns service names and published ports from the requested stack."""
        pass

    @abstractmethod
    def get_image_inventory(self) -> ArtifactImageInventory:
        """Return the effective image inventory for the selected service profile."""
        pass

    @abstractmethod
    def get_build_context_path(self, build_context: str) -> Path:
        """Resolve one approved build context without inspecting or mutating it."""
        pass

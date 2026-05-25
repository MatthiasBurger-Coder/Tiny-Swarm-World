from abc import ABC, abstractmethod
from collections.abc import Mapping

from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition


class PortPortainerClient(ABC):
    @abstractmethod
    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        pass

    @abstractmethod
    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        pass

    @abstractmethod
    def create_stack(
        self,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    def update_stack(
        self,
        stack_id: int,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        pass

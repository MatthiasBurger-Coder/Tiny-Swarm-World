from abc import ABC, abstractmethod

from domain.deployment.stack_definition import StackDefinition


class PortPortainerClient(ABC):
    @abstractmethod
    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        pass

    @abstractmethod
    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        pass

    @abstractmethod
    def create_stack(self, stack_definition: StackDefinition, endpoint_id: int) -> None:
        pass

    @abstractmethod
    def update_stack(self, stack_id: int, stack_definition: StackDefinition, endpoint_id: int) -> None:
        pass

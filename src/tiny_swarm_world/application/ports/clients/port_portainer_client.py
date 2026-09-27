from tiny_swarm_world.application.ports.operation_result import OperationError

from abc import ABC, abstractmethod
from collections.abc import Mapping

from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition


class PortPortainerClient(ABC):
    @abstractmethod
    def ensure_local_endpoint(self, endpoint_name: str) -> int:
        pass

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


class PortainerClientError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

    def __init__(self, failure, *, status_code: int | None = None, detail: str = ""):
        super().__init__(failure)
        if detail not in {"", "Portainer did not report a Swarm cluster ID.", "Portainer authentication succeeded without returning a JWT.", "Selected Portainer endpoint was not found."}:
            raise ValueError("Client error detail must be a declared safe message.")
        if status_code is not None and type(status_code) is not int:
            raise TypeError("HTTP status must be numeric.")
        self.status_code = status_code
        self.args = (f"{self.args[0]} {detail}" + (f" HTTP {status_code}." if status_code is not None else ""),)

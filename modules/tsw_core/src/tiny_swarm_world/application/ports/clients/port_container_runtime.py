from tiny_swarm_world.application.ports.operation_result import OperationError

from abc import ABC, abstractmethod


class PortContainerRuntime(ABC):
    @abstractmethod
    def find_container_names(self, name_filter: str) -> list[str]:
        pass

    @abstractmethod
    def file_exists(self, container_name: str, file_path: str) -> bool:
        pass

    @abstractmethod
    def read_file(self, container_name: str, file_path: str) -> str:
        pass


class ContainerRuntimeError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

    def __init__(self, failure, *, exit_code: int | None = None):
        super().__init__(failure)
        if exit_code is not None and type(exit_code) is not int:
            raise TypeError("Process exit code must be numeric.")
        detail = "LXC Docker runtime operation timed out." if failure.cause == "process_timeout" else "LXC Docker runtime operation failed."
        if exit_code is not None:
            detail += f" Process failed with exit code {exit_code}."
        self.args = (f"{detail} {self.args[0]}",)

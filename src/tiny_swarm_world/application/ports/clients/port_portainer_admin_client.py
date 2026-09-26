from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure
from abc import ABC, abstractmethod


class PortainerAdminInitializationRejected(OperationError, RuntimeError):
    """Raised when admin initialization is rejected and requested credentials fail."""

    def __init__(self, message: str | None = None, *, status_code: int | None = None):
        super().__init__(OperationFailure.for_cause("service.bootstrap", "portainer", "request_failed"))
        if status_code is not None and type(status_code) is not int:
            raise TypeError("HTTP status must be numeric.")
        self.status_code = status_code
        if status_code is not None:
            self.args = (f"{self.args[0]} HTTP {status_code}.",)


class PortPortainerAdminClient(ABC):
    @abstractmethod
    def can_authenticate(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def initialize_admin_user(self, username: str, password: str) -> None:
        pass

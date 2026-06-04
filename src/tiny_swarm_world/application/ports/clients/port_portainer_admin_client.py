from abc import ABC, abstractmethod


class PortainerAdminInitializationRejected(RuntimeError):
    """Raised when admin initialization is rejected and requested credentials fail."""

    def __init__(self, message: str | None = None, *, status_code: int | None = None):
        super().__init__(message or "Portainer rejected admin initialization.")
        self.status_code = status_code


class PortPortainerAdminClient(ABC):
    @abstractmethod
    def can_authenticate(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def initialize_admin_user(self, username: str, password: str) -> None:
        pass

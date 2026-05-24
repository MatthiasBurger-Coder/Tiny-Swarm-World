from abc import ABC, abstractmethod


class PortPortainerAdminClient(ABC):
    @abstractmethod
    def can_authenticate(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def initialize_admin_user(self, username: str, password: str) -> None:
        pass

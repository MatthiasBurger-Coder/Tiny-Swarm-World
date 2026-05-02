from abc import ABC, abstractmethod

from tiny_swarm_world.domain.nexus.nexus_user import NexusUser


class PortNexusClient(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def can_authenticate(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def get_user(self, username: str, password: str, target_user_id: str) -> NexusUser:
        pass

    @abstractmethod
    def update_user(self, username: str, password: str, user: NexusUser) -> None:
        pass

    @abstractmethod
    def change_password(self, username: str, password: str, target_user_id: str, new_password: str) -> None:
        pass

    @abstractmethod
    def set_anonymous_access(self, username: str, password: str, enabled: bool) -> None:
        pass

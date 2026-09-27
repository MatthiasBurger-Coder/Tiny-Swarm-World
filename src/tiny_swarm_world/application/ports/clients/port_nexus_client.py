from tiny_swarm_world.application.ports.operation_result import OperationError

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

    @abstractmethod
    def repository_exists(self, username: str, password: str, repository_name: str) -> bool:
        pass

    @abstractmethod
    def create_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        pass

    @abstractmethod
    def update_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        pass

    @abstractmethod
    def create_docker_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
        remote_url: str,
    ) -> None:
        pass

    @abstractmethod
    def create_maven_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        remote_url: str,
    ) -> None:
        pass


class NexusClientError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

    def __init__(self, failure, *, status_code: int | None = None):
        super().__init__(failure)
        if status_code is not None and type(status_code) is not int:
            raise TypeError("HTTP status must be numeric.")
        self.status_code = status_code
        if status_code is not None:
            self.args = (f"{self.args[0]} HTTP {status_code}.",)

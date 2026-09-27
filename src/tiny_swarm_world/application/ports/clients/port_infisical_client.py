from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError

from abc import ABC, abstractmethod


class PortInfisicalClient(ABC):
    @abstractmethod
    def can_authenticate(self, email: str, password: str) -> bool:
        pass

    @abstractmethod
    def secret_item_exists(self, email: str, password: str, item_name: str) -> bool:
        pass

    @abstractmethod
    def create_secret_item(
        self,
        email: str,
        password: str,
        item_name: str,
        username: str,
        secret_value: str,
    ) -> None:
        pass


class InfisicalClientError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

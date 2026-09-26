from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError

from abc import ABC, abstractmethod


class PortSonarqubeClient(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def can_authenticate(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        pass


class SonarqubeClientError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

    def __str__(self):
        return "SonarQube request failed with redacted output. " + super().__str__()

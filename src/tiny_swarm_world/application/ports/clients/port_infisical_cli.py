from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class InfisicalCliResult:
    return_code: int
    stdout: str = ""
    stderr: str = ""
    failure: OperationFailure | None = None


class PortInfisicalCli(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def run_bootstrap(self, args: tuple[str, ...]) -> InfisicalCliResult:
        pass

    @abstractmethod
    def ensure_project_environment(self, project: str, environment: str) -> None:
        pass

    @abstractmethod
    def secret_exists(self, key: str, *, project: str, environment: str) -> bool:
        pass

    @abstractmethod
    def get_secret(self, key: str, *, project: str, environment: str) -> str | None:
        """Return one managed value without logging or exposing it in evidence."""
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str, *, project: str, environment: str) -> None:
        pass


class InfisicalCliError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

    def __str__(self):
        return "Infisical request failed with redacted output. " + super().__str__()

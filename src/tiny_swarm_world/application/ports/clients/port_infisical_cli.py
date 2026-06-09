from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class InfisicalCliResult:
    return_code: int
    stdout: str = ""
    stderr: str = ""


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
    def set_secret(self, key: str, value: str, *, project: str, environment: str) -> None:
        pass

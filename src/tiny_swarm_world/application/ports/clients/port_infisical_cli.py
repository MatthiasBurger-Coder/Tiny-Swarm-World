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

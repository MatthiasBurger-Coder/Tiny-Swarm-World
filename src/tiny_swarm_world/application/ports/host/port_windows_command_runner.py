from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol


class PortPath(Protocol):
    """Minimal path value required by the Windows command boundary."""

    def __fspath__(self) -> str:
        ...


@dataclass(frozen=True)
class WindowsCommandResult:
    return_code: int | None
    timed_out: bool = False
    interrupted: bool = False
    stdout: str = field(default="", repr=False)
    stderr: str = field(default="", repr=False)


class PortWindowsCommandRunner(ABC):
    @abstractmethod
    def run(
        self,
        action: str,
        *,
        script_path: PortPath,
        config_path: PortPath,
        port_registry_path: PortPath,
        timeout_seconds: float,
    ) -> WindowsCommandResult:
        """Run one bounded Windows bridge action through the infrastructure boundary."""

        raise NotImplementedError

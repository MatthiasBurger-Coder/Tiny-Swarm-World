from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


WSL_INTEROP_MARKER = ("proc", "sys", "fs", "binfmt_misc", "WSLInterop")


@dataclass(frozen=True)
class WslHostSignals:
    distribution: str
    windows_interop_available: bool


class WslHostSignalReader:
    """Read WSL-specific environment and interop facts without mutation."""

    def __init__(
        self,
        *,
        os_root: Path = Path("/"),
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.os_root = os_root
        self.environment = os.environ if environment is None else environment

    def read(self) -> WslHostSignals:
        return WslHostSignals(
            distribution=self.environment.get("WSL_DISTRO_NAME", ""),
            windows_interop_available=bool(
                self.environment.get("WSL_INTEROP")
            )
            or self._interop_marker_enabled(),
        )

    def _interop_marker_enabled(self) -> bool:
        path = self.os_root.joinpath(*WSL_INTEROP_MARKER)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return False
        return "enabled" in text.casefold()

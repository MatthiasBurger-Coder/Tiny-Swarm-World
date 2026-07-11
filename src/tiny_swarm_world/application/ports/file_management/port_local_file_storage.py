from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextFileSnapshot:
    path: Path
    text: str


class PortLocalFileStorage(ABC):
    """Application boundary for local configuration and evidence files."""

    @abstractmethod
    def load_yaml(self, path: Path) -> object:
        """Load one YAML document without exposing the parser to application code."""

    @abstractmethod
    def read_text(self, path: Path) -> str | None:
        """Return UTF-8 text, or ``None`` when the file does not exist."""

    @abstractmethod
    def scan_text_files(
        self,
        root: Path,
        *,
        suffixes: frozenset[str],
        skip_parts: frozenset[str],
    ) -> tuple[TextFileSnapshot, ...]:
        """Return readable candidate files below ``root`` in deterministic order."""

    @abstractmethod
    def write_text(self, path: Path, text: str, *, private: bool = False) -> None:
        """Write UTF-8 text atomically enough for local installer state."""

    @abstractmethod
    def ensure_directory(self, path: Path, *, private: bool = False) -> None:
        """Ensure a local directory exists with optional owner-only permissions."""

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Return whether the local path exists."""

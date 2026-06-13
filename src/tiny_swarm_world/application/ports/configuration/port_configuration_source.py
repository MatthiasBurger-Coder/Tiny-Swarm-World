from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping


class ConfigurationSourceLoadError(ValueError):
    def __init__(self, message: str, *, safe_detail: str | None = None) -> None:
        super().__init__(message)
        self.safe_detail = safe_detail


class PortConfigurationSource(ABC):
    @abstractmethod
    def load(self) -> Mapping[str, str]:
        pass

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping


class PortConfigurationSource(ABC):
    @abstractmethod
    def load(self) -> Mapping[str, str]:
        pass

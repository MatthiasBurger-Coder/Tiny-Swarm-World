from abc import ABC, abstractmethod
from typing import Any

class ExtractionStrategy(ABC):
    """Abstract base for extraction strategies."""

    @abstractmethod
    def extract(self, result) -> Any:
        """Extract specific information from a command result."""
        pass

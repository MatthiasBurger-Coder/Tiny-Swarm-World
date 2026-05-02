from abc import ABC, abstractmethod
from typing import Any

class ExtractionStrategy(ABC):
    """Abstrakte Basis für verschiedene Extraktionsstrategien."""

    @abstractmethod
    def extract(self, result) -> Any:
        """Extrahiert eine bestimmte Information aus dem Resultat."""
        pass

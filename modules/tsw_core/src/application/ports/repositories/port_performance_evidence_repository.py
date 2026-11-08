from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from tiny_swarm_world.domain.performance import PerformanceMeasurement


class PortPerformanceEvidenceRepository(ABC):
    @abstractmethod
    def write(self, measurement: PerformanceMeasurement) -> tuple[Path, Path]:
        """Write deterministic structured and human-readable evidence."""

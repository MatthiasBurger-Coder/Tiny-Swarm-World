from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.preflight.host_environment import HostEnvironmentReport


class PortHostEnvironmentDetector(ABC):
    @abstractmethod
    def detect(self) -> HostEnvironmentReport:
        """Return a typed, read-only host classification."""

        raise NotImplementedError

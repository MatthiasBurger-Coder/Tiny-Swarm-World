from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.ingress import DesiredHttpsIngress


class PortEffectiveAccessModelRepository(ABC):
    @abstractmethod
    def get_effective_access_model(self) -> DesiredHttpsIngress:
        """Return the effective routed-service access model."""

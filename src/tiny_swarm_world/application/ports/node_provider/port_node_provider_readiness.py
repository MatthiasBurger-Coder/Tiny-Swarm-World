from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    ProviderReadiness,
)


class PortNodeProviderReadiness(ABC):
    @abstractmethod
    async def provider_readiness(
        self,
        provider: NodeProviderKind,
        preferred_backend: ManagedLxcBackend | None = None,
    ) -> ProviderReadiness:
        pass

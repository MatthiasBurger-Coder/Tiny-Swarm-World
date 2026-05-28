from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.inventory import VerificationResult
from tiny_swarm_world.domain.node_provider import NodeSpec, ProviderSelection


class PortNodeLifecycle(ABC):
    @abstractmethod
    async def ensure_node(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
    ) -> VerificationResult:
        pass

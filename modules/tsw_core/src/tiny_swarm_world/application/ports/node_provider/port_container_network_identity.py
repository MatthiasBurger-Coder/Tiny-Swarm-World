from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.node_provider import NodeSpec


class PortContainerNetworkIdentity(ABC):
    @abstractmethod
    async def manager_advertise_address(self, node: NodeSpec) -> str:
        pass

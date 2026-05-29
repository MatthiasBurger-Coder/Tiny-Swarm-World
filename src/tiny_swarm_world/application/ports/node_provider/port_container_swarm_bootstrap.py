from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.node_provider import (
    NodeSpec,
    SwarmManagerBootstrapOutcome,
    SwarmWorkerJoinCredential,
    SwarmWorkerJoinOutcome,
)


class PortContainerSwarmBootstrap(ABC):
    @abstractmethod
    async def inspect_manager(self, node: NodeSpec) -> SwarmManagerBootstrapOutcome:
        pass

    @abstractmethod
    async def initialize_manager(
        self,
        node: NodeSpec,
        advertise_address: str,
    ) -> SwarmManagerBootstrapOutcome:
        pass

    @abstractmethod
    async def worker_join_credential(self, node: NodeSpec) -> SwarmWorkerJoinCredential:
        pass

    @abstractmethod
    async def inspect_worker(self, node: NodeSpec) -> SwarmWorkerJoinOutcome:
        pass

    @abstractmethod
    async def join_worker(
        self,
        node: NodeSpec,
        manager_address: str,
        credential: SwarmWorkerJoinCredential,
    ) -> SwarmWorkerJoinOutcome:
        pass

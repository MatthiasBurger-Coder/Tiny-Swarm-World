from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    NodeSpec,
)


class PortContainerDockerRuntime(ABC):
    @abstractmethod
    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        pass

    @abstractmethod
    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        pass

    @abstractmethod
    async def verify_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        pass

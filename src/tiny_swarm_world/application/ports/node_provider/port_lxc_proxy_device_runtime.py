from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import NodeSpec


class LxcProxyDeviceState(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    DRIFTED = "drifted"
    UNKNOWN = "unknown"


class PortLxcProxyDeviceRuntime(ABC):
    @abstractmethod
    async def inspect_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        pass

    @abstractmethod
    async def create_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        pass

    @abstractmethod
    async def update_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        pass

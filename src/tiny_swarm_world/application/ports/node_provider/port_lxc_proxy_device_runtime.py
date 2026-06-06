from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import NodeSpec


class LxcProxyDeviceState(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    DRIFTED = "drifted"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LxcProxyDriftRepairOutcome:
    expected_profile_device_count: int
    stale_direct_device_count: int = 0
    removed_count: int = 0
    refused_count: int = 0
    lookup_failure_count: int = 0
    remove_failure_count: int = 0
    mutation_allowed: bool = True
    removed_devices: tuple[str, ...] = ()
    refused_devices: tuple[str, ...] = ()
    failed_devices: tuple[str, ...] = ()

    @property
    def blocked_count(self) -> int:
        return self.refused_count + self.lookup_failure_count


class PortLxcProxyDeviceRuntime(ABC):
    @abstractmethod
    async def inspect_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        pass

    @abstractmethod
    async def create_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        pass

    @abstractmethod
    async def update_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        pass

    @abstractmethod
    async def repair_stale_proxy_devices(
        self,
        profile_name: str,
        gateway_node: NodeSpec,
        plans: tuple[LxcProxyDevicePlan, ...],
    ) -> LxcProxyDriftRepairOutcome:
        pass

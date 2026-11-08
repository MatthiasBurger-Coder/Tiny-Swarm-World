from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tiny_swarm_world.application.ports.network.port_network_probe import CommandObservation


@dataclass(frozen=True)
class NetworkRepairMutationResult:
    target: str
    applied: bool
    success: bool
    message: str
    details: tuple[str, ...] = ()
    commands: tuple[CommandObservation, ...] = ()


class PortNetworkRepair(Protocol):
    async def apply_wsl2_nat_runtime(self) -> NetworkRepairMutationResult:
        ...

    async def apply_incus_repair(self) -> NetworkRepairMutationResult:
        ...

    async def apply_linux_forwarding(self, bridge: str, node_name: str) -> NetworkRepairMutationResult:
        ...

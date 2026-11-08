from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CommandObservation:
    command: str
    return_code: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.return_code == 0 and not self.timed_out

    @property
    def combined_output(self) -> str:
        return "\n".join(part for part in (self.stdout, self.stderr) if part)


@dataclass(frozen=True)
class RuntimeObservation:
    runtime: str
    networking_mode: str
    wsl_ipv4: str
    host_ipv4: str
    commands: tuple[CommandObservation, ...] = ()
    remediation: tuple[str, ...] = ()

    @property
    def is_wsl2(self) -> bool:
        return self.runtime == "wsl2"

    @property
    def supported_host(self) -> bool:
        return self.runtime in {"native-linux", "wsl2"}


@dataclass(frozen=True)
class WslHostObservation:
    ip_addr: CommandObservation
    ip_route: CommandObservation
    resolv_conf: CommandObservation
    ping_egress: CommandObservation
    dns_lookup: CommandObservation
    http_probe: CommandObservation


@dataclass(frozen=True)
class IncusObservation:
    version: CommandObservation
    network_list: CommandObservation
    network_show: CommandObservation
    network_info: CommandObservation
    bridge_addr: CommandObservation
    journal: CommandObservation
    dnsmasq_log: CommandObservation
    gateway_ipv4: str = ""


@dataclass(frozen=True)
class LxcNodeObservation:
    node_name: str
    incus_list: CommandObservation
    ip_addr: CommandObservation
    ip_route: CommandObservation
    resolv_conf: CommandObservation
    ping_gateway: CommandObservation
    ping_egress: CommandObservation
    dns_lookup: CommandObservation
    http_probe: CommandObservation


@dataclass(frozen=True)
class ForwardingObservation:
    ip_forward: CommandObservation
    iptables_forward: CommandObservation
    iptables_nat: CommandObservation
    nft_rules: CommandObservation


@dataclass(frozen=True)
class ServicePortObservation:
    listeners: CommandObservation


class PortNetworkProbe(Protocol):
    async def runtime(self) -> RuntimeObservation:
        ...

    async def wsl_host(self) -> WslHostObservation:
        ...

    async def incus(self) -> IncusObservation:
        ...

    async def lxc_node(self, node_name: str, gateway_ipv4: str) -> LxcNodeObservation:
        ...

    async def forwarding(self) -> ForwardingObservation:
        ...

    async def service_ports(self) -> ServicePortObservation:
        ...

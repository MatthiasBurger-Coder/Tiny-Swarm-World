from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


_SAFE_NETWORK_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_IP_LITERAL_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?\b")
_HOST_PATH_PATTERN = re.compile(r"^(?:/|[A-Za-z]:\\)")


class ContainerNetworkPurpose(str, Enum):
    CONTROL = "control"
    SERVICE = "service"
    PUBLISHED_PORTS = "published_ports"


@dataclass(frozen=True)
class ContainerNetworkPlan:
    name: str
    purpose: ContainerNetworkPurpose
    provider_managed: bool = True
    host_network: bool = False
    host_addresses: tuple[str, ...] = ()
    host_gateways: tuple[str, ...] = ()
    host_bridge: str | None = None
    firewall_mutation: bool = False
    published_host_ports: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not _SAFE_NETWORK_NAME_PATTERN.fullmatch(self.name):
            raise ValueError("container network name contains invalid characters")
        if _IP_LITERAL_PATTERN.fullmatch(self.name):
            raise ValueError("container network name must not be an address")
        object.__setattr__(self, "purpose", _network_purpose(self.purpose))
        object.__setattr__(self, "host_addresses", tuple(self.host_addresses))
        object.__setattr__(self, "host_gateways", tuple(self.host_gateways))
        object.__setattr__(self, "published_host_ports", tuple(self.published_host_ports))
        for port in self.published_host_ports:
            if port < 1 or port > 65535:
                raise ValueError("published host ports must be valid TCP/UDP ports")

    @classmethod
    def provider_managed_control(cls, name: str = "control") -> ContainerNetworkPlan:
        return cls(name=name, purpose=ContainerNetworkPurpose.CONTROL)

    @property
    def safe_for_static_config(self) -> bool:
        return not self.validation_errors()

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.provider_managed:
            errors.append("network_not_provider_managed")
        if self.host_network:
            errors.append("host_network_forbidden")
        if self.host_addresses or self.host_gateways:
            errors.append("host_address_forbidden")
        if self.host_bridge is not None:
            errors.append("host_bridge_forbidden")
        if self.firewall_mutation:
            errors.append("firewall_mutation_forbidden")
        if self.published_host_ports:
            errors.append("host_port_publication_requires_approval")
        for value in (*self.host_addresses, *self.host_gateways, self.host_bridge or ""):
            if _IP_LITERAL_PATTERN.search(value) or _HOST_PATH_PATTERN.search(value):
                errors.append("host_specific_value_forbidden")
                break
        return tuple(errors)


def _network_purpose(value: ContainerNetworkPurpose | str) -> ContainerNetworkPurpose:
    return value if isinstance(value, ContainerNetworkPurpose) else ContainerNetworkPurpose(str(value))

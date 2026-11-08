from __future__ import annotations

import re
from dataclasses import dataclass


_LXC_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_LXC_GATEWAY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SUPPORTED_LISTEN_ADDRESSES = frozenset(("127.0.0.1", "0.0.0.0"))
_SUPPORTED_CONNECT_ADDRESS = "127.0.0.1"


@dataclass(frozen=True)
class LxcProxyDevicePlan:
    service: str
    listen_port: int
    target_port: int
    listen_address: str = "127.0.0.1"
    target_address: str = _SUPPORTED_CONNECT_ADDRESS
    gateway_node: str = "swarm-manager"
    device_name: str = ""

    def __post_init__(self) -> None:
        service = self.service.strip()
        listen_address = self.listen_address.strip()
        target_address = self.target_address.strip()
        gateway_node = self.gateway_node.strip()
        device_name = self.device_name.strip() or f"tsw-proxy-{self.listen_port}"

        if not service:
            raise ValueError("LXC proxy service cannot be empty.")
        _validate_port(self.listen_port, "listen_port")
        _validate_port(self.target_port, "target_port")
        if listen_address not in _SUPPORTED_LISTEN_ADDRESSES:
            raise ValueError("LXC proxy listen address must be 127.0.0.1 or 0.0.0.0.")
        if target_address != _SUPPORTED_CONNECT_ADDRESS:
            raise ValueError("LXC proxy target address must be 127.0.0.1.")
        if not _LXC_GATEWAY_PATTERN.fullmatch(gateway_node):
            raise ValueError("LXC proxy gateway node name is invalid.")
        if not _LXC_NAME_PATTERN.fullmatch(device_name):
            raise ValueError("LXC proxy device name is invalid.")

        object.__setattr__(self, "service", service)
        object.__setattr__(self, "listen_address", listen_address)
        object.__setattr__(self, "target_address", target_address)
        object.__setattr__(self, "gateway_node", gateway_node)
        object.__setattr__(self, "device_name", device_name)

    @property
    def listen_endpoint(self) -> str:
        return f"tcp:{self.listen_address}:{self.listen_port}"

    @property
    def target_endpoint(self) -> str:
        return f"tcp:{self.target_address}:{self.target_port}"

    def to_dict(self) -> dict[str, object]:
        return {
            "service": self.service,
            "gateway_node": self.gateway_node,
            "device_name": self.device_name,
            "listen_address": self.listen_address,
            "listen_port": self.listen_port,
            "target_address": self.target_address,
            "target_port": self.target_port,
        }


def _validate_port(value: int, field_name: str) -> None:
    if not isinstance(value, int) or value < 1 or value > 65535:
        raise ValueError(f"{field_name} must be a TCP port between 1 and 65535")

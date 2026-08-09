"""Safety checks for observed LXC instance configuration and devices."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping


ALLOW_PRIVILEGED_SWARM_INGRESS_ENVIRONMENT = "TSW_LXC_ALLOW_PRIVILEGED_SWARM_INGRESS"
SECURITY_PRIVILEGED_KEY = "security.privileged"
SECURITY_PRIVILEGED_VALUE = "true"
MANAGED_MARKER = "user.tiny_swarm_world.managed"
NODE_MARKER = "user.tiny_swarm_world.node"
IMAGE_ALIAS_MARKER = "user.tiny_swarm_world.image_alias"
_PROJECT_PROXY_DEVICE_NAME_PATTERN = re.compile(r"^tsw-proxy-(?P<port>[1-9]\d{0,4})$")


def has_unsafe_instance_config(config: Mapping[str, str]) -> bool:
    return bool(unsafe_instance_config_keys(config))


def unsafe_instance_config_keys(config: Mapping[str, str]) -> tuple[str, ...]:
    keys: list[str] = []
    privileged_enabled = (
        config.get(SECURITY_PRIVILEGED_KEY, "").casefold() == SECURITY_PRIVILEGED_VALUE
    )
    if privileged_enabled and not allow_privileged_swarm_ingress():
        keys.append(SECURITY_PRIVILEGED_KEY)
    if any(key.startswith("raw.") for key in config):
        keys.append("raw.*")
    return tuple(keys)


def has_unsafe_instance_devices(
    devices: Mapping[str, Mapping[str, str]],
    *,
    allow_project_proxy_devices: bool = False,
) -> bool:
    return any(
        unsafe_instance_device(
            name,
            device,
            allow_project_proxy_devices=allow_project_proxy_devices,
        )
        for name, device in devices.items()
    )


def unsafe_instance_device(
    name: str,
    device: Mapping[str, str],
    *,
    allow_project_proxy_devices: bool,
) -> bool:
    device_type = device.get("type", "").casefold()
    if device_type == "disk":
        return "source" in device
    if device_type == "nic":
        return unsafe_network_device(device)
    if allow_project_proxy_devices and safe_project_proxy_device(name, device):
        return False
    return bool(device_type)


def safe_project_proxy_device(name: str, device: Mapping[str, str]) -> bool:
    name_match = _PROJECT_PROXY_DEVICE_NAME_PATTERN.fullmatch(name)
    if name_match is None:
        return False
    return (
        device.get("type", "").casefold() == "proxy"
        and set(device) <= {"type", "listen", "connect"}
        and safe_proxy_endpoint_pair(
            device.get("listen", ""),
            device.get("connect", ""),
            expected_port=int(name_match.group("port")),
        )
    )


def safe_proxy_endpoint_pair(listen: str, connect: str, *, expected_port: int) -> bool:
    listen_endpoint = parse_tcp_proxy_endpoint(listen)
    connect_endpoint = parse_tcp_proxy_endpoint(connect)
    if listen_endpoint is None or connect_endpoint is None:
        return False
    listen_host, listen_port = listen_endpoint
    connect_host, connect_port = connect_endpoint
    return (
        listen_host in {"0.0.0.0", "127.0.0.1"}
        and connect_host == "127.0.0.1"
        and listen_port == connect_port
        and listen_port == expected_port
        and 1 <= listen_port <= 65535
    )


def parse_tcp_proxy_endpoint(value: str) -> tuple[str, int] | None:
    prefix, separator, port_text = value.rpartition(":")
    if not separator or not port_text.isdigit():
        return None
    scheme, scheme_separator, host = prefix.partition(":")
    if scheme != "tcp" or scheme_separator != ":":
        return None
    return host, int(port_text)


def unsafe_network_device(device: Mapping[str, str]) -> bool:
    return (
        "parent" in device
        or "network" not in device
        or device.get("nictype", "").casefold() in {"macvlan", "physical", "sriov"}
    )


def allow_privileged_swarm_ingress() -> bool:
    return os.getenv(ALLOW_PRIVILEGED_SWARM_INGRESS_ENVIRONMENT, "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }

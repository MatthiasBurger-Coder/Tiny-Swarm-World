from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlparse


class ForwardingStrategy(str, Enum):
    NATIVE_LINUX_DIRECT = "native_linux_direct"
    WSL2_SOCAT = "wsl2_socat"
    WSL2_NETSH_DOCUMENTED = "wsl2_netsh_documented"
    WSL2_IPTABLES_OPTIONAL = "wsl2_iptables_optional"
    UNSUPPORTED = "unsupported"


SERVICE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
RANGE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]*$")


class PortExposureClass(str, Enum):
    PUBLIC_INGRESS = "public_ingress"
    DIRECT = "direct"
    DIAGNOSTIC = "diagnostic"
    COMPATIBILITY = "compatibility"
    INTERNAL = "internal"


@dataclass(frozen=True)
class PortRange:
    range_id: str
    start: int
    end: int
    description: str = ""

    def __post_init__(self) -> None:
        _validate_identifier(self.range_id, "range_id", RANGE_IDENTIFIER_PATTERN)
        _validate_port(self.start, "start")
        _validate_port(self.end, "end")
        if self.start > self.end:
            raise ValueError("port range start must be less than or equal to end")
        object.__setattr__(self, "description", self.description.strip())

    def contains(self, port: int) -> bool:
        _validate_port(port, "port")
        return self.start <= port <= self.end

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.range_id,
            "start": self.start,
            "end": self.end,
            "description": self.description,
        }


@dataclass(frozen=True)
class ServicePortMapping:
    service_id: str
    port_id: str
    internal_port: int
    external_port: int | None
    exposure: PortExposureClass
    range_id: str | None = None
    protocol: str = "tcp"
    route_host: str | None = None
    required_for_preflight: bool = True
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.service_id, "service_id", SERVICE_IDENTIFIER_PATTERN)
        _validate_identifier(self.port_id, "port_id", SERVICE_IDENTIFIER_PATTERN)
        _validate_port(self.internal_port, "internal_port")
        if self.external_port is not None:
            _validate_port(self.external_port, "external_port")
        if self.range_id is not None:
            _validate_identifier(self.range_id, "range_id", RANGE_IDENTIFIER_PATTERN)
        exposure = PortExposureClass(self.exposure)
        _validate_public_ingress_ownership(
            self.service_id,
            self.external_port,
            exposure,
        )
        normalized_protocol = self.protocol.strip().lower()
        if normalized_protocol not in {"tcp", "udp"}:
            raise ValueError("protocol must be tcp or udp")
        route_host = _validate_route_host(self.route_host)
        object.__setattr__(self, "protocol", normalized_protocol)
        object.__setattr__(self, "route_host", route_host)
        object.__setattr__(self, "exposure", exposure)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(_safe_metadata(self.metadata or {})),
        )

    @property
    def externally_visible(self) -> bool:
        return self.external_port is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "service_id": self.service_id,
            "port_id": self.port_id,
            "internal_port": self.internal_port,
            "external_port": self.external_port,
            "exposure": self.exposure.value,
            "range_id": self.range_id,
            "protocol": self.protocol,
            "route_host": self.route_host,
            "required_for_preflight": self.required_for_preflight,
            "metadata": dict(self.metadata or {}),
        }


@dataclass(frozen=True)
class PortRegistry:
    ranges: tuple[PortRange, ...]
    mappings: tuple[ServicePortMapping, ...]
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        ranges = tuple(self.ranges)
        mappings = tuple(self.mappings)
        _reject_duplicate_range_ids(ranges)
        _reject_overlapping_ranges(ranges)
        _validate_mapping_ranges(ranges, mappings)
        _reject_duplicate_external_ports(mappings)
        object.__setattr__(self, "ranges", ranges)
        object.__setattr__(self, "mappings", mappings)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(_safe_metadata(self.metadata or {})),
        )

    @property
    def external_ports(self) -> tuple[int, ...]:
        return tuple(
            mapping.external_port
            for mapping in self.mappings
            if mapping.external_port is not None
        )

    @property
    def preflight_ports(self) -> tuple[ServicePortMapping, ...]:
        return tuple(
            mapping
            for mapping in self.mappings
            if mapping.external_port is not None and mapping.required_for_preflight
        )

    def mapping_for_port_id(self, port_id: str) -> ServicePortMapping:
        _validate_identifier(port_id, "port_id", SERVICE_IDENTIFIER_PATTERN)
        for mapping in self.mappings:
            if mapping.port_id == port_id:
                return mapping
        raise KeyError(port_id)

    def to_dict(self) -> dict[str, object]:
        return {
            "metadata": dict(self.metadata or {}),
            "ranges": [port_range.to_dict() for port_range in self.ranges],
            "ports": [mapping.to_dict() for mapping in self.mappings],
        }


@dataclass(frozen=True)
class PortForwardingPlan:
    strategy: ForwardingStrategy
    service: str
    listen_port: int
    target_port: int
    remediation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.service.strip():
            raise ValueError("service cannot be empty")
        _validate_port(self.listen_port, "listen_port")
        _validate_port(self.target_port, "target_port")
        object.__setattr__(self, "service", self.service.strip())
        object.__setattr__(self, "remediation", tuple(self.remediation))

    @property
    def requires_operator_action(self) -> bool:
        return self.strategy in {
            ForwardingStrategy.WSL2_SOCAT,
            ForwardingStrategy.WSL2_NETSH_DOCUMENTED,
            ForwardingStrategy.WSL2_IPTABLES_OPTIONAL,
        }

    @property
    def supported_without_operator_action(self) -> bool:
        return self.strategy == ForwardingStrategy.NATIVE_LINUX_DIRECT

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy.value,
            "service": self.service,
            "listen_port": self.listen_port,
            "target_port": self.target_port,
            "requires_operator_action": self.requires_operator_action,
            "supported_without_operator_action": self.supported_without_operator_action,
            "remediation": list(self.remediation),
        }


def _validate_port(value: int, field_name: str) -> None:
    if not isinstance(value, int) or value < 1 or value > 65535:
        raise ValueError(f"{field_name} must be a TCP port between 1 and 65535")


def _validate_identifier(value: str, field_name: str, pattern: re.Pattern[str]) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError(f"{field_name} contains invalid characters")


def _validate_route_host(value: str | None) -> str | None:
    if value is None:
        return None
    route_host = value.strip().lower()
    if not route_host:
        return None
    if "://" in route_host or "@" in route_host or "/" in route_host:
        raise ValueError("route_host must be a host name, not a URL")
    try:
        ipaddress.ip_address(route_host)
    except ValueError:
        return route_host
    raise ValueError("route_host must not be a host-specific IP address")


def _validate_public_ingress_ownership(
    service_id: str,
    external_port: int | None,
    exposure: PortExposureClass,
) -> None:
    if exposure is not PortExposureClass.PUBLIC_INGRESS:
        return
    if service_id != "traefik" or external_port not in {80, 443}:
        raise ValueError("public ingress ports must be Traefik-owned 80 or 443")


def _safe_metadata(metadata: Mapping[str, str]) -> dict[str, str]:
    safe_metadata: dict[str, str] = {}
    for key, value in metadata.items():
        normalized_key = str(key).strip().lower()
        normalized_value = str(value).strip()
        if not normalized_key:
            raise ValueError("metadata keys cannot be empty")
        if _is_sensitive_metadata_key(normalized_key):
            raise ValueError("port registry metadata must not contain secrets")
        if _is_host_specific_value(normalized_value):
            raise ValueError("port registry metadata must not contain host-specific values")
        if _is_credential_url(normalized_value):
            raise ValueError("port registry metadata must not contain credential URLs")
        safe_metadata[normalized_key] = normalized_value
    return safe_metadata


def _is_sensitive_metadata_key(key: str) -> bool:
    return any(
        forbidden in key
        for forbidden in (
            "address",
            "host_ip",
            "listen_address",
            "password",
            "secret",
            "token",
            "url",
            "vm_ip",
        )
    )


def _is_host_specific_value(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def _is_credential_url(value: str) -> bool:
    if "://" not in value:
        return False
    parsed = urlparse(value)
    return bool(parsed.username or parsed.password)


def _reject_duplicate_range_ids(ranges: tuple[PortRange, ...]) -> None:
    seen: set[str] = set()
    for port_range in ranges:
        if port_range.range_id in seen:
            raise ValueError("port registry contains duplicate range IDs")
        seen.add(port_range.range_id)


def _reject_overlapping_ranges(ranges: tuple[PortRange, ...]) -> None:
    ordered_ranges = sorted(ranges, key=lambda port_range: port_range.start)
    previous: PortRange | None = None
    for port_range in ordered_ranges:
        if previous is not None and port_range.start <= previous.end:
            raise ValueError("port registry ranges must not overlap")
        previous = port_range


def _validate_mapping_ranges(
    ranges: tuple[PortRange, ...],
    mappings: tuple[ServicePortMapping, ...],
) -> None:
    ranges_by_id = {port_range.range_id: port_range for port_range in ranges}
    for mapping in mappings:
        if mapping.range_id is None:
            continue
        port_range = ranges_by_id.get(mapping.range_id)
        if port_range is None:
            raise ValueError("service port mapping references an unknown range")
        if mapping.external_port is None:
            raise ValueError("range_id requires an external_port")
        if not port_range.contains(mapping.external_port):
            raise ValueError("external_port must belong to the declared range")


def _reject_duplicate_external_ports(
    mappings: tuple[ServicePortMapping, ...],
) -> None:
    seen: dict[tuple[int, str], ServicePortMapping] = {}
    for mapping in mappings:
        if mapping.external_port is None:
            continue
        key = (mapping.external_port, mapping.protocol)
        if key in seen:
            raise ValueError("port registry contains duplicate external ports")
        seen[key] = mapping

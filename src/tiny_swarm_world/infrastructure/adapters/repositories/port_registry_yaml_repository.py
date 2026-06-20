from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.repositories.port_port_registry_repository import (
    PortPortRegistryRepository,
)
from tiny_swarm_world.domain.network import (
    PortExposureClass,
    PortRange,
    PortRegistry,
    ServicePortMapping,
)
from tiny_swarm_world.infrastructure.project_paths import config_root


DEFAULT_PORT_REGISTRY_PATH = Path("ports.yaml")


class PortRegistryYamlRepository(PortPortRegistryRepository):
    def __init__(self, path: Path | None = None):
        self.path = path or (config_root() / DEFAULT_PORT_REGISTRY_PATH)
        self.yaml = YAML(typ="safe")

    def load(self) -> PortRegistry:
        if not self.path.exists():
            return PortRegistry(ranges=(), mappings=())

        data = self.yaml.load(self.path.read_text(encoding="utf-8"))
        if data is None:
            return PortRegistry(ranges=(), mappings=())
        if not isinstance(data, Mapping):
            raise ValueError("port registry YAML root must be a mapping")

        return PortRegistry(
            ranges=_ranges_from(data.get("ranges", ())),
            mappings=_mappings_from(data.get("ports", ())),
            metadata=_metadata_from(data.get("metadata", {})),
        )


def _ranges_from(value: object) -> tuple[PortRange, ...]:
    if not isinstance(value, list):
        raise ValueError("port registry ranges must be a list")
    return tuple(_range_from(item) for item in value)


def _range_from(value: object) -> PortRange:
    if not isinstance(value, Mapping):
        raise ValueError("port registry range entries must be mappings")
    return PortRange(
        range_id=_string(value, "id"),
        start=_integer(value, "start"),
        end=_integer(value, "end"),
        description=str(value.get("description", "")),
    )


def _mappings_from(value: object) -> tuple[ServicePortMapping, ...]:
    if not isinstance(value, list):
        raise ValueError("port registry ports must be a list")
    return tuple(_mapping_from(item) for item in value)


def _mapping_from(value: object) -> ServicePortMapping:
    if not isinstance(value, Mapping):
        raise ValueError("port registry port entries must be mappings")
    return ServicePortMapping(
        service_id=_string(value, "service_id"),
        port_id=_string(value, "id"),
        internal_port=_integer(value, "internal_port"),
        external_port=_optional_integer(value, "external_port"),
        exposure=PortExposureClass(_string(value, "exposure")),
        range_id=_optional_string(value, "range_id"),
        protocol=str(value.get("protocol", "tcp")),
        route_host=_optional_string(value, "route_host"),
        required_for_preflight=bool(value.get("required_for_preflight", True)),
        metadata=_metadata_from(value.get("metadata", {})),
    )


def _metadata_from(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("port registry metadata must be a mapping")
    return {str(key): str(item) for key, item in value.items()}


def _string(value: Mapping[Any, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"port registry field '{key}' must be a string")
    return item


def _optional_string(value: Mapping[Any, Any], key: str) -> str | None:
    item = value.get(key)
    if item is None:
        return None
    if not isinstance(item, str):
        raise ValueError(f"port registry field '{key}' must be a string")
    return item


def _integer(value: Mapping[Any, Any], key: str) -> int:
    item = value.get(key)
    if not isinstance(item, int):
        raise ValueError(f"port registry field '{key}' must be an integer")
    return item


def _optional_integer(value: Mapping[Any, Any], key: str) -> int | None:
    item = value.get(key)
    if item is None:
        return None
    if not isinstance(item, int):
        raise ValueError(f"port registry field '{key}' must be an integer")
    return item

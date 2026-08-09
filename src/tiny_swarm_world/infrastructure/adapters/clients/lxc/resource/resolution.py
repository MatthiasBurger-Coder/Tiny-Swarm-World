"""Provider resource validation and backend-specific resolution helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfig,
    NodeProviderNodeConfig,
    ProviderBackendResourceResolution,
    ProviderResourceResolution,
)


RESOURCE_KEYS = frozenset(("cpu", "memory", "disk"))
CPU_PATTERN = re.compile(r"^[1-9]\d*$")
SIZE_PATTERN = re.compile(r"^[1-9]\d*[KMGT]i?B?$")


def resources_supported(resources: Mapping[str, str]) -> bool:
    if set(resources) - RESOURCE_KEYS:
        return False
    cpu = resources.get("cpu")
    memory = resources.get("memory")
    disk = resources.get("disk")
    return (
        (cpu is None or CPU_PATTERN.fullmatch(cpu) is not None)
        and (memory is None or SIZE_PATTERN.fullmatch(memory) is not None)
        and (disk is None or SIZE_PATTERN.fullmatch(disk) is not None)
    )


def uses_provider_resource_resolution(config: NodeProviderConfig) -> bool:
    return "provider_resource_resolution" in config.verification_metadata.checks


def resource_cpu(value: str | None) -> int:
    if not value or CPU_PATTERN.fullmatch(value.strip()) is None:
        return 0
    return int(value)


def resource_memory_bytes(value: str | None) -> int:
    if not value:
        return 0
    match = re.fullmatch(r"(\d+)([KMGT])i?B?", value.strip(), re.IGNORECASE)
    if match is None:
        return 0
    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    return int(match.group(1)) * multipliers[match.group(2).upper()]


def selected_provider_resource_resolution(
    config: NodeProviderConfig,
    backend: ManagedLxcBackend,
) -> ProviderBackendResourceResolution | None:
    if config.provider_resource_resolution is None:
        return None
    return config.provider_resource_resolution.for_backend(backend)


def resolved_network(
    node_config: NodeProviderNodeConfig,
    provider_resource_resolution: ProviderBackendResourceResolution,
) -> str:
    return provider_resource_resolution.network_mappings[node_config.networks[0]]


def resource_resolution_evidence(
    node_config: NodeProviderNodeConfig,
    provider_resource_resolution: ProviderResourceResolution | None,
    *,
    backend: ManagedLxcBackend,
    available_networks: tuple[str, ...] = (),
    available_storage_pools: tuple[str, ...] = (),
) -> dict[str, str]:
    backend_resolution = (
        provider_resource_resolution.for_backend(backend)
        if provider_resource_resolution is not None
        else None
    )
    resolved = (
        resolved_network(node_config, backend_resolution)
        if backend_resolution is not None
        and node_config.networks
        and node_config.networks[0] in backend_resolution.network_mappings
        else ""
    )
    return {
        "expected_profile": node_config.profile,
        "available_profiles": "",
        "backend": backend.value,
        "logical_network": ",".join(node_config.networks),
        "resolved_network": resolved,
        "available_networks": ",".join(available_networks),
        "expected_storage_pool": (
            backend_resolution.storage_pool if backend_resolution is not None else ""
        ),
        "available_storage_pools": ",".join(available_storage_pools),
        "remediation_hint": resource_resolution_remediation_hint(
            node_config,
            provider_resource_resolution,
            backend=backend,
            available_networks=available_networks,
            available_storage_pools=available_storage_pools,
        ),
    }


def resource_resolution_remediation_hint(
    node_config: NodeProviderNodeConfig,
    provider_resource_resolution: ProviderResourceResolution | None,
    *,
    backend: ManagedLxcBackend,
    available_networks: tuple[str, ...],
    available_storage_pools: tuple[str, ...],
) -> str:
    if provider_resource_resolution is None:
        return "Configure provider resource resolution for the LXC-native node inventory."
    backend_resolution = provider_resource_resolution.for_backend(backend)
    if backend_resolution is None:
        return "Configure provider resource resolution for the selected backend."
    if not node_config.networks:
        return "Configure at least one logical network for the LXC-native node."
    if node_config.networks[0] not in backend_resolution.network_mappings:
        return "Add an explicit logical-to-backend network mapping for the inventory network."
    resolved = resolved_network(node_config, backend_resolution)
    if resolved not in available_networks:
        return "Create or configure the resolved backend network before platform mutation."
    if backend_resolution.storage_pool not in available_storage_pools:
        return "Create or configure the expected backend storage pool before platform mutation."
    return "Provider resource resolution is satisfied."

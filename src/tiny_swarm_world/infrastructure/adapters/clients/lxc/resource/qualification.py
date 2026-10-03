"""Read-only qualification of LXC host capacity and backend resources."""

from __future__ import annotations

import json
from collections.abc import Mapping

from tiny_swarm_world.domain.inventory import VerificationResult
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeSpec,
    ProviderSelection,
)
from tiny_swarm_world.domain.preflight.resources import (
    HostResources,
    PlannedContainerLimit,
    validate_planned_container_limits,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.args import (
    network_list_args,
    storage_pool_list_args,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.diagnostics import (
    command_failed,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import (
    LxcNodeCommandResult,
    LxcNodeCommandRunner,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.node.results import blocked
from tiny_swarm_world.infrastructure.adapters.clients.lxc.resource.resolution import (
    resource_cpu,
    resource_memory_bytes,
    resource_resolution_evidence,
    resolved_network as _resolved_network,
    selected_provider_resource_resolution,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfig,
    NodeProviderNodeConfig,
)


class LxcResourceQualification:
    """Qualify capacity and configured network/storage without lifecycle mutation."""

    def __init__(self, runner: LxcNodeCommandRunner):
        self.runner = runner

    def host_capacity_block(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        config: NodeProviderConfig,
        inspector: object | None = None,
    ) -> VerificationResult | None:
        inspect = getattr(inspector, "inspect", None)
        if not callable(inspect):
            return None
        resources = inspect()
        if not isinstance(resources, HostResources):
            return None
        planned = tuple(
            PlannedContainerLimit(
                item.spec.name,
                resource_cpu(item.resources.get("cpu")),
                resource_memory_bytes(item.resources.get("memory")),
            )
            for item in config.nodes
        )
        if validate_planned_container_limits(resources, planned):
            return None
        return blocked(
            node,
            selection,
            "host_capacity_exceeded",
            extra_evidence={
                "cpu_threads": str(resources.cpu_threads),
                "effective_memory_bytes": str(resources.effective_memory_bytes),
                "planned_cpu_threads": str(sum(item.cpu_threads for item in planned)),
                "planned_memory_bytes": str(sum(item.memory_bytes for item in planned)),
                "mutation": "not_started",
            },
        )

    async def verify_provider_resources(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
    ) -> VerificationResult | None:
        if "provider_resource_resolution" not in config.verification_metadata.checks:
            return None
        resource_resolution = config.provider_resource_resolution
        backend_resource_resolution = selected_provider_resource_resolution(
            config, backend
        )
        logical_networks = node_config.networks
        if (
            resource_resolution is None
            or backend_resource_resolution is None
            or not logical_networks
        ):
            return blocked(
                node,
                selection,
                "inventory_mapping_missing",
                backend=backend,
                extra_evidence=resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                ),
            )
        unresolved_networks = tuple(
            network
            for network in logical_networks
            if network not in backend_resource_resolution.network_mappings
        )
        if unresolved_networks:
            return blocked(
                node,
                selection,
                "inventory_mapping_missing",
                backend=backend,
                extra_evidence=resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                ),
            )

        resolved_network = _resolved_network(node_config, backend_resource_resolution)
        available_networks = await self._available_network_names(backend, config)
        if resolved_network not in available_networks:
            return blocked(
                node,
                selection,
                "network_missing",
                backend=backend,
                extra_evidence=resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                    available_networks=available_networks,
                ),
            )

        available_storage_pools = await self._available_storage_pool_names(
            backend, config
        )
        if backend_resource_resolution.storage_pool not in available_storage_pools:
            return blocked(
                node,
                selection,
                "storage_pool_missing",
                backend=backend,
                extra_evidence=resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                    available_networks=available_networks,
                    available_storage_pools=available_storage_pools,
                ),
            )
        return None

    async def _available_network_names(
        self,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
    ) -> tuple[str, ...]:
        result = await self.runner.run(
            network_list_args(backend),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        return _name_list_from_json(result)

    async def _available_storage_pool_names(
        self,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
    ) -> tuple[str, ...]:
        result = await self.runner.run(
            storage_pool_list_args(backend),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        return _name_list_from_json(result)


def _name_list_from_json(result: LxcNodeCommandResult) -> tuple[str, ...]:
    if command_failed(result):
        return ()
    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return ()
    if not isinstance(payload, list):
        return ()
    names = (
        name
        for item in payload
        if isinstance(item, Mapping)
        for name in (_mapping_name(item),)
        if name is not None
    )
    return tuple(sorted(names))


def _mapping_name(item: Mapping[object, object]) -> str | None:
    name = item.get("name")
    return name if isinstance(name, str) else None

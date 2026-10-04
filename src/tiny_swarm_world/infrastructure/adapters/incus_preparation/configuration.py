"""Resolve existing provider names and profile policy without a second catalog."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeProviderKind
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.policy import required_profile_settings
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfigYamlRepository, NodeProviderProfileRequirement,
)


@dataclass(frozen=True)
class IncusRequirements:
    storage: str
    networks: tuple[str, ...]
    profiles: tuple[NodeProviderProfileRequirement, ...]
    profile_networks: tuple[tuple[str, str], ...]


def load_requirements(path: Path) -> IncusRequirements:
    config = NodeProviderConfigYamlRepository(path=path).load()
    if config.default_provider != NodeProviderKind.LXC_NATIVE or config.preferred_backend != ManagedLxcBackend.INCUS:
        raise IncusPreparationFailure("Use the declared Incus provider; review provider_config.yaml.")
    resolution = config.provider_resource_resolution
    resources = resolution.for_backend(ManagedLxcBackend.INCUS) if resolution else None
    if resources is None:
        raise IncusPreparationFailure("Incus resource resolution is missing; review provider_config.yaml.")
    bindings: dict[str, str] = {}
    declared = {name for node in config.nodes for name in node.expected_profiles}
    for node in config.nodes:
        if len(node.networks) != 1:
            raise IncusPreparationFailure("Preparation requires one resolved network per node; review provider_config.yaml.")
        network = resources.network_mappings[node.networks[0]]
        if node.profile in bindings and bindings[node.profile] != network:
            raise IncusPreparationFailure("A shared profile has conflicting networks; review provider_config.yaml.")
        bindings[node.profile] = network
    profiles = tuple(profile for profile in config.profiles if profile.name in declared)
    for profile in profiles:
        settings = required_profile_settings(profile)
        if profile.privileged_default or settings.get("security.privileged") == "true":
            raise IncusPreparationFailure("Privileged bootstrap profiles are forbidden; remove the privileged override.")
        if profile.host_network or profile.host_mounts or profile.capability_additions:
            raise IncusPreparationFailure("Host-access bootstrap profiles are forbidden; review provider_config.yaml.")
    return IncusRequirements(resources.storage_pool,
                             tuple(sorted(set(resources.network_mappings.values()))),
                             profiles, tuple(sorted(bindings.items())))

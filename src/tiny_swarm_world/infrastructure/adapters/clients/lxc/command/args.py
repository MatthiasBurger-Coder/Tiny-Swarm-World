"""Deterministic provider command construction for LXC node lifecycle."""

from __future__ import annotations

from collections.abc import Mapping

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.backend_cli import backend_cli
from tiny_swarm_world.infrastructure.adapters.clients.lxc.node.safety import (
    IMAGE_ALIAS_MARKER,
    MANAGED_MARKER,
    NODE_MARKER,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderNodeConfig,
    ProviderBackendResourceResolution,
)


def profile_show_args(backend: ManagedLxcBackend, profile_name: str) -> tuple[str, ...]:
    return (backend_cli(backend), "profile", "show", profile_name)


def profile_list_args(backend: ManagedLxcBackend) -> tuple[str, ...]:
    return (backend_cli(backend), "profile", "list", "--format", "json")


def network_list_args(backend: ManagedLxcBackend) -> tuple[str, ...]:
    return (backend_cli(backend), "network", "list", "--format", "json")


def storage_pool_list_args(backend: ManagedLxcBackend) -> tuple[str, ...]:
    return (backend_cli(backend), "storage", "list", "--format", "json")


def profile_create_args(backend: ManagedLxcBackend, profile_name: str) -> tuple[str, ...]:
    return (backend_cli(backend), "profile", "create", profile_name)


def profile_set_args(
    backend: ManagedLxcBackend,
    profile_name: str,
    key: str,
    value: str,
) -> tuple[str, ...]:
    return (backend_cli(backend), "profile", "set", profile_name, key, value)


def list_args(backend: ManagedLxcBackend, node_name: str) -> tuple[str, ...]:
    return (backend_cli(backend), "list", node_name, "--format", "json")


def start_args(backend: ManagedLxcBackend, node_name: str) -> tuple[str, ...]:
    return (backend_cli(backend), "start", node_name)


def image_info_args(backend: ManagedLxcBackend, image_ref: str) -> tuple[str, ...]:
    return (backend_cli(backend), "image", "info", image_ref)


def delete_args(backend: ManagedLxcBackend, node_name: str) -> tuple[str, ...]:
    return (backend_cli(backend), "delete", node_name, "--force")


def launch_args(
    backend: ManagedLxcBackend,
    node_config: NodeProviderNodeConfig,
    image_references: Mapping[str, str],
    *,
    provider_resource_resolution: ProviderBackendResourceResolution | None = None,
) -> tuple[str, ...]:
    args: list[str] = [
        backend_cli(backend),
        "launch",
        image_ref(node_config.image_alias, image_references, backend),
        node_config.spec.name,
    ]
    if provider_resource_resolution is not None:
        args.extend(("--network", provider_resource_resolution.network_mappings[node_config.networks[0]]))
        args.extend(("--storage", provider_resource_resolution.storage_pool))
    for profile_name in node_config.expected_profiles:
        args.extend(("--profile", profile_name))
    args.extend(
        (
            "-c",
            f"{MANAGED_MARKER}=true",
            "-c",
            f"{NODE_MARKER}={node_config.spec.name}",
            "-c",
            f"{IMAGE_ALIAS_MARKER}={node_config.image_alias}",
        )
    )
    for key, flag in (("cpu", "-c"), ("memory", "-c")):
        value = node_config.resources.get(key)
        if value is not None:
            args.extend((flag, f"limits.{key}={value}"))
    disk = node_config.resources.get("disk")
    if disk is not None:
        args.extend(("-d", f"root,size={disk}"))
    return tuple(args)


def image_ref(
    image_alias: str,
    image_references: Mapping[str, str],
    backend: ManagedLxcBackend | None = None,
) -> str:
    if backend is not None:
        backend_key = f"{backend.value}:{image_alias}"
        if backend_key in image_references:
            return image_references[backend_key]
    return image_references.get(image_alias, image_alias)

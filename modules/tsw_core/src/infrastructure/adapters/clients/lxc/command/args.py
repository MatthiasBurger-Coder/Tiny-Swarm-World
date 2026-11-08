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

DEFAULT_INCUS_PROJECT = "default"


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


def list_args(
    backend: ManagedLxcBackend,
    node_name: str,
    *,
    project: str | None = None,
) -> tuple[str, ...]:
    args = [backend_cli(backend), "list"]
    if project is not None:
        args.extend(("--project", project))
    args.extend((node_name, "--format", "json"))
    return tuple(args)


def start_args(backend: ManagedLxcBackend, node_name: str) -> tuple[str, ...]:
    return (backend_cli(backend), "start", node_name)


def image_info_args(backend: ManagedLxcBackend, image_ref: str) -> tuple[str, ...]:
    return (backend_cli(backend), "image", "info", image_ref)


def delete_args(
    backend: ManagedLxcBackend,
    node_name: str,
    *,
    project: str | None = None,
) -> tuple[str, ...]:
    args = [backend_cli(backend), "delete"]
    if project is not None:
        args.extend(("--project", project))
    args.extend((node_name, "--force"))
    return tuple(args)


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


def scoped_node_config(intent, node):
    """Exact creation config for a checkpoint-bound manager or selected worker."""
    return {**intent.markers(), MANAGED_MARKER: 'true', NODE_MARKER: node.node_name,
            IMAGE_ALIAS_MARKER: node.image_fingerprint, 'limits.cpu': str(node.cpu),
            'limits.memory': node.memory, 'boot.autostart': 'false'}


def scoped_init_args(intent, node_name: str) -> tuple[str, ...]:
    """Stopped creation only, with an explicit fixed project and immutable image."""
    from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, WorkerCreateIntent

    checked = ManagerCreateIntent.model_validate_json(intent.model_dump_json())
    node: ManagerCreateIntent | WorkerCreateIntent
    if checked.node_name == node_name:
        node = checked
        profiles = checked.attachments()
    else:
        worker = next((item for item in checked.workers if item.node_name == node_name), None)
        if worker is None:
            raise ValueError('Node is outside the bound scoped topology.')
        node = worker
        profiles = worker.base_profiles
    args = ['--project', 'default', 'init', node.image_fingerprint, node.node_name]
    for profile in profiles:
        args.extend(('--profile', profile))
    args.extend(('--network', node.network, '--storage', node.storage_pool, '-d', 'root,size=' + node.disk))
    for key, value in scoped_node_config(checked, node).items():
        args.extend(('-c', key + '=' + value))
    return tuple(args)

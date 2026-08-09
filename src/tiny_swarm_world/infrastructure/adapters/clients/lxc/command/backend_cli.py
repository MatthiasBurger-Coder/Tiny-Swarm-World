"""Authoritative managed-LXC backend to CLI mapping."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend


BACKEND_CLI: Final[Mapping[ManagedLxcBackend, str]] = MappingProxyType(
    {
        ManagedLxcBackend.INCUS: "incus",
        ManagedLxcBackend.LXD: "lxc",
    }
)


def backend_cli(backend: ManagedLxcBackend) -> str:
    """Return the executable name for a managed LXC backend."""

    try:
        return BACKEND_CLI[backend]
    except KeyError as exc:
        raise ValueError(f"Unsupported managed LXC backend: {backend!r}") from exc

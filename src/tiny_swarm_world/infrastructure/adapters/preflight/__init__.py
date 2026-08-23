"""Preflight adapters with lazy exports for dependency-light bootstrap checks."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "HostPreflightProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe",
        "HostPreflightProbe",
    ),
    "ensure_common_executable_paths": (
        "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe",
        "ensure_common_executable_paths",
    ),
    "LxcProviderPreflightProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.lxc_provider_preflight",
        "LxcProviderPreflightProbe",
    ),
    "HttpArtifactSourceReadiness": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_source_readiness",
        "HttpArtifactSourceReadiness",
    ),
    "ARTIFACT_READINESS_TARGETS": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "ARTIFACT_READINESS_TARGETS",
    ),
    "BoundedArtifactReadinessAdapter": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "BoundedArtifactReadinessAdapter",
    ),
    "DockerManagerReadinessProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "DockerManagerReadinessProbe",
    ),
    "HttpEndpointReadinessProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "HttpEndpointReadinessProbe",
    ),
    "LocalDirectoryReadinessProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "LocalDirectoryReadinessProbe",
    ),
    "ManagedLxcDirectoryReadinessProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "ManagedLxcDirectoryReadinessProbe",
    ),
    "ManagedLxcDockerManagerReadinessProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "ManagedLxcDockerManagerReadinessProbe",
    ),
    "UnavailableArtifactReadinessProbe": (
        "tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness",
        "UnavailableArtifactReadinessProbe",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value

from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.domain.preflight.setup_manifest import (
    SetupManifest,
    SetupProfile,
    default_setup_manifest,
)


GIB = 1024**3


@dataclass(frozen=True)
class RequiredDependency:
    name: str


@dataclass(frozen=True)
class RequiredPort:
    port: int
    service: str


@dataclass(frozen=True)
class RequiredSecret:
    name: str
    service: str


@dataclass(frozen=True)
class ForbiddenSecretFingerprint:
    identifier: str
    sha256_digest: str


@dataclass(frozen=True)
class ResourceThresholds:
    minimum_cpu_count: int
    minimum_memory_bytes: int
    minimum_disk_free_bytes: int
    disk_path: str


@dataclass(frozen=True)
class PreflightConfiguration:
    setup_profile: SetupProfile
    setup_manifest: SetupManifest
    required_dependencies: tuple[RequiredDependency, ...]
    required_ports: tuple[RequiredPort, ...]
    required_secrets: tuple[RequiredSecret, ...]
    forbidden_secret_fingerprints: tuple[ForbiddenSecretFingerprint, ...]
    required_ignored_paths: tuple[str, ...]
    resources: ResourceThresholds
    minimum_python_version: tuple[int, int]


def default_preflight_configuration(
    setup_profile: SetupProfile = SetupProfile.FULL,
) -> PreflightConfiguration:
    setup_manifest = default_setup_manifest(setup_profile)
    return PreflightConfiguration(
        setup_profile=setup_profile,
        setup_manifest=setup_manifest,
        required_dependencies=(
            RequiredDependency("python3"),
            RequiredDependency("multipass"),
            RequiredDependency("docker"),
        ),
        required_ports=tuple(
            RequiredPort(port.port, port.service)
            for port in setup_manifest.required_ports
        ),
        required_secrets=tuple(
            RequiredSecret(secret.name, secret.service)
            for secret in setup_manifest.required_secrets
        ),
        forbidden_secret_fingerprints=(
            ForbiddenSecretFingerprint(
                "portainer-default-password",
                "7ba9293f74fb0b610b7cce1494530ba975d15348ffec0b478b143fbe198bd917",
            ),
            ForbiddenSecretFingerprint(
                "legacy-nexus-admin-password",
                "72fc9fee800d9f881eb0d85d8d7287a6230ed81bdf9b03634f9454b83ae603d7",
            ),
            ForbiddenSecretFingerprint(
                "portainer-token-echo",
                "d15db825d357c5a749f208ffc6de615140f53fb98f3f8aeedf0f82d0ca7bceda",
            ),
        ),
        required_ignored_paths=(
            ".tiny-swarm-world/",
            ".env",
            ".env.local",
        ),
        resources=ResourceThresholds(
            minimum_cpu_count=4,
            minimum_memory_bytes=16 * GIB,
            minimum_disk_free_bytes=60 * GIB,
            disk_path=".",
        ),
        minimum_python_version=(3, 12),
    )

from __future__ import annotations

from dataclasses import dataclass


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
    required_dependencies: tuple[RequiredDependency, ...]
    required_ports: tuple[RequiredPort, ...]
    required_secrets: tuple[RequiredSecret, ...]
    forbidden_secret_fingerprints: tuple[ForbiddenSecretFingerprint, ...]
    required_ignored_paths: tuple[str, ...]
    resources: ResourceThresholds
    minimum_python_version: tuple[int, int]


def default_preflight_configuration() -> PreflightConfiguration:
    return PreflightConfiguration(
        required_dependencies=(
            RequiredDependency("python3"),
            RequiredDependency("multipass"),
            RequiredDependency("docker"),
        ),
        required_ports=(
            RequiredPort(9000, "Portainer"),
            RequiredPort(8081, "Nexus"),
            RequiredPort(8080, "Jenkins"),
            RequiredPort(5000, "Nexus Docker registry"),
            RequiredPort(5672, "RabbitMQ AMQP"),
            RequiredPort(15672, "RabbitMQ management"),
            RequiredPort(9001, "SonarQube"),
            RequiredPort(80, "Swagger/NGINX"),
        ),
        required_secrets=(
            RequiredSecret("TSW_PORTAINER_PASSWORD", "Portainer"),
            RequiredSecret("TSW_NEXUS_ADMIN_PASSWORD", "Nexus"),
            RequiredSecret("TSW_JENKINS_ADMIN_PASSWORD", "Jenkins"),
            RequiredSecret("TSW_RABBITMQ_PASSWORD", "RabbitMQ"),
            RequiredSecret("TSW_SONARQUBE_ADMIN_PASSWORD", "SonarQube"),
            RequiredSecret("TSW_POSTGRES_PASSWORD", "SonarQube PostgreSQL"),
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

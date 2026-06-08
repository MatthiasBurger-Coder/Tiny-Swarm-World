from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from tiny_swarm_world.domain.deployment import ServiceStackProfile


class SetupProfile(str, Enum):
    FULL = "full"
    RESOURCE_GATED = "resource-gated"


@dataclass(frozen=True)
class SetupPortRequirement:
    port: int
    service: str
    host_preflight_required: bool = True


@dataclass(frozen=True)
class SetupSecretRequirement:
    name: str
    service: str
    value_kind: str = "secret_value"


@dataclass(frozen=True)
class SetupServiceRequirement:
    name: str
    ports: tuple[SetupPortRequirement, ...] = ()
    secrets: tuple[SetupSecretRequirement, ...] = ()
    required_for_full: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "ports": [
                {
                    "host_preflight_required": port.host_preflight_required,
                    "port": port.port,
                    "service": port.service,
                }
                for port in self.ports
            ],
            "secrets": [
                {
                    "name": secret.name,
                    "service": secret.service,
                    "value_kind": secret.value_kind,
                }
                for secret in self.secrets
            ],
            "required_for_full": self.required_for_full,
        }


@dataclass(frozen=True)
class SetupManifest:
    profile: SetupProfile
    services: tuple[SetupServiceRequirement, ...]
    evidence_root: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.evidence_root.startswith("/") or ".." in self.evidence_root.split("/"):
            raise ValueError("setup evidence root must be a repository-local relative path")
        if not self.evidence_root.startswith(".tiny-swarm-world/"):
            raise ValueError("setup evidence root must stay under ignored local state")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def required_ports(self) -> tuple[SetupPortRequirement, ...]:
        return tuple(port for service in self.services for port in service.ports)

    @property
    def required_secrets(self) -> tuple[SetupSecretRequirement, ...]:
        return tuple(secret for service in self.services for secret in service.secrets)

    @property
    def service_names(self) -> tuple[str, ...]:
        return tuple(service.name for service in self.services)

    def summary(self) -> dict[str, object]:
        return {
            "profile": self.profile.value,
            "services": list(self.service_names),
            "evidence_root": self.evidence_root,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            **self.summary(),
            "metadata": dict(self.metadata),
            "services": [service.to_dict() for service in self.services],
        }


def default_setup_manifest(
    profile: SetupProfile = SetupProfile.FULL,
    service_profile: ServiceStackProfile | str = ServiceStackProfile.DEFAULT,
) -> SetupManifest:
    selected_service_profile = ServiceStackProfile(service_profile)
    services = [
        SetupServiceRequirement(
            name="Portainer",
            ports=(SetupPortRequirement(9000, "Portainer"),),
            secrets=(SetupSecretRequirement("TSW_PORTAINER_PASSWORD", "Portainer"),),
        ),
        SetupServiceRequirement(
            name="Nexus",
            ports=(
                SetupPortRequirement(8081, "Nexus"),
                SetupPortRequirement(5000, "Nexus Docker registry"),
            ),
            secrets=(SetupSecretRequirement("TSW_NEXUS_ADMIN_PASSWORD", "Nexus"),),
        ),
        SetupServiceRequirement(
            name="Jenkins",
            ports=(SetupPortRequirement(8080, "Jenkins"),),
            secrets=(SetupSecretRequirement("TSW_JENKINS_ADMIN_PASSWORD", "Jenkins"),),
        ),
        SetupServiceRequirement(
            name="RabbitMQ",
            ports=(
                SetupPortRequirement(5672, "RabbitMQ AMQP"),
                SetupPortRequirement(15672, "RabbitMQ management"),
            ),
            secrets=(SetupSecretRequirement("TSW_RABBITMQ_PASSWORD", "RabbitMQ"),),
        ),
        SetupServiceRequirement(
            name="SonarQube",
            ports=(SetupPortRequirement(9001, "SonarQube"),),
            secrets=(
                SetupSecretRequirement("TSW_SONARQUBE_ADMIN_PASSWORD", "SonarQube"),
                SetupSecretRequirement("TSW_POSTGRES_PASSWORD", "SonarQube PostgreSQL"),
            ),
        ),
        SetupServiceRequirement(
            name="Swagger/NGINX",
            ports=(SetupPortRequirement(8084, "Swagger/NGINX"),),
        ),
    ]
    if selected_service_profile is ServiceStackProfile.SERVICE_ACCESS:
        services.append(
            SetupServiceRequirement(
                name="Service Access",
                ports=(
                    SetupPortRequirement(80, "Service Access dashboard"),
                ),
            )
        )
        services.append(
            SetupServiceRequirement(
                name="Infisical",
                ports=(
                    SetupPortRequirement(8086, "Infisical"),
                    SetupPortRequirement(443, "Infisical HTTPS"),
                ),
                secrets=(
                    SetupSecretRequirement("TSW_INFISICAL_LOGIN_EMAIL", "Infisical admin login"),
                    SetupSecretRequirement("TSW_INFISICAL_PASSWORD", "Infisical admin login"),
                    SetupSecretRequirement("TSW_INFISICAL_ENCRYPTION_KEY", "Infisical"),
                    SetupSecretRequirement("TSW_INFISICAL_AUTH_SECRET", "Infisical"),
                    SetupSecretRequirement("TSW_INFISICAL_POSTGRES_PASSWORD", "Infisical PostgreSQL"),
                ),
            )
        )
    return SetupManifest(
        profile=profile,
        evidence_root=".tiny-swarm-world/evidence/live-installation",
        metadata={
            "live_smoke": "separate-operator-action",
            "service_profile": selected_service_profile.value,
        },
        services=tuple(services),
    )

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


def compatibility_port(port: int, service: str) -> SetupPortRequirement:
    return SetupPortRequirement(
        port,
        service,
        host_preflight_required=False,
    )


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
    centralized_ingress = selected_service_profile is ServiceStackProfile.SERVICE_ACCESS
    services = [
        SetupServiceRequirement(
            name="Portainer",
            ports=(
                (compatibility_port(10001, "Portainer"),)
                if centralized_ingress
                else (SetupPortRequirement(10001, "Portainer"),)
            ),
            secrets=(SetupSecretRequirement("TSW_PORTAINER_ADMIN_PASSWORD", "Portainer"),),
        ),
        SetupServiceRequirement(
            name="Nexus",
            ports=(
                (
                    compatibility_port(13081, "Nexus"),
                    compatibility_port(13500, "Nexus Docker registry"),
                    compatibility_port(13501, "Nexus Docker proxy registry"),
                )
                if centralized_ingress
                else (
                    SetupPortRequirement(13081, "Nexus"),
                    SetupPortRequirement(13500, "Nexus Docker registry"),
                    SetupPortRequirement(13501, "Nexus Docker proxy registry"),
                )
            ),
            secrets=(SetupSecretRequirement("TSW_NEXUS_ADMIN_PASSWORD", "Nexus"),),
        ),
        SetupServiceRequirement(
            name="Jenkins",
            ports=(
                (
                    compatibility_port(11080, "Jenkins"),
                    compatibility_port(11050, "Jenkins inbound agent"),
                )
                if centralized_ingress
                else (
                    SetupPortRequirement(11080, "Jenkins"),
                    SetupPortRequirement(11050, "Jenkins inbound agent"),
                )
            ),
            secrets=(SetupSecretRequirement("TSW_JENKINS_ADMIN_PASSWORD", "Jenkins"),),
        ),
        SetupServiceRequirement(
            name="Pulsar",
            ports=(
                (
                    compatibility_port(14001, "Pulsar broker protocol"),
                    compatibility_port(14080, "Pulsar Admin API"),
                    compatibility_port(14081, "Pulsar Manager UI"),
                    compatibility_port(7750, "Pulsar Manager backend"),
                )
                if centralized_ingress
                else (
                    SetupPortRequirement(14001, "Pulsar broker protocol"),
                    SetupPortRequirement(14080, "Pulsar Admin API"),
                    SetupPortRequirement(14081, "Pulsar Manager UI"),
                    SetupPortRequirement(7750, "Pulsar Manager backend"),
                )
            ),
            secrets=(
                SetupSecretRequirement("TSW_PULSAR_TOKEN_SECRET_KEY", "Pulsar token signing key"),
                SetupSecretRequirement("TSW_PULSAR_ADMIN_TOKEN", "Pulsar Admin API token"),
                SetupSecretRequirement("TSW_PULSAR_MANAGER_ADMIN_PASSWORD", "Pulsar Manager UI"),
            ),
        ),
        SetupServiceRequirement(
            name="SonarQube",
            ports=(
                (compatibility_port(12000, "SonarQube"),)
                if centralized_ingress
                else (SetupPortRequirement(12000, "SonarQube"),)
            ),
            secrets=(
                SetupSecretRequirement("TSW_SONARQUBE_ADMIN_PASSWORD", "SonarQube"),
                SetupSecretRequirement("TSW_POSTGRES_PASSWORD", "SonarQube PostgreSQL"),
            ),
        ),
        SetupServiceRequirement(
            name="Swagger/NGINX",
            ports=(
                (
                    compatibility_port(16080, "Swagger UI"),
                    compatibility_port(16081, "Swagger/NGINX"),
                )
                if centralized_ingress
                else (
                    SetupPortRequirement(16080, "Swagger UI"),
                    SetupPortRequirement(16081, "Swagger/NGINX"),
                )
            ),
        ),
    ]
    if selected_service_profile is ServiceStackProfile.SERVICE_ACCESS:
        services.append(
            SetupServiceRequirement(
                name="Traefik Ingress",
                ports=(
                    SetupPortRequirement(10080, "Traefik HTTP ingress"),
                    SetupPortRequirement(10443, "Traefik HTTPS ingress"),
                ),
            )
        )
        services.append(
            SetupServiceRequirement(
                name="Service Access",
                ports=(compatibility_port(10000, "Service Access"),),
            )
        )
        services.append(
            SetupServiceRequirement(
                name="Infisical",
                ports=(
                    compatibility_port(8086, "Infisical legacy route"),
                    compatibility_port(17080, "Infisical"),
                ),
                secrets=(
                    SetupSecretRequirement("TSW_INFISICAL_LOGIN_EMAIL", "Infisical admin login"),
                    SetupSecretRequirement("TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD", "Infisical admin login"),
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

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


SERVICE_IDENTIFIER_PATTERN = r"^[a-z0-9][a-z0-9_.-]*$"
STACK_NAME_PATTERN = re.compile(SERVICE_IDENTIFIER_PATTERN)
SERVICE_NAME_PATTERN = re.compile(SERVICE_IDENTIFIER_PATTERN)
ENDPOINT_NAME_PATTERN = re.compile(SERVICE_IDENTIFIER_PATTERN)


class ServiceStackProfile(str, Enum):
    DEFAULT = "default"
    SERVICE_ACCESS = "service-access"


@dataclass(frozen=True)
class ServiceEndpoint:
    name: str
    url: str
    localhost_forwarding_required: bool = True
    readiness_claimed: bool = False

    def __post_init__(self) -> None:
        if not ENDPOINT_NAME_PATTERN.fullmatch(self.name):
            raise ValueError("service endpoint name contains invalid characters")
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname != "localhost":
            raise ValueError("service endpoint URL must use localhost over http or https")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("service endpoint URL must not carry credentials or query data")
        try:
            parsed.port
        except ValueError as exc:
            raise ValueError("service endpoint URL contains an invalid port") from exc
        if self.readiness_claimed:
            raise ValueError("service endpoint configuration must not claim readiness")

    def to_dict(self) -> dict[str, object]:
        return {
            "localhost_forwarding_required": self.localhost_forwarding_required,
            "name": self.name,
            "readiness_claimed": self.readiness_claimed,
            "url": self.url,
        }


@dataclass(frozen=True)
class ServiceStackContract:
    stack_name: str
    required_services: tuple[str, ...]
    phase_id: str | None = None
    port_ids: tuple[str, ...] = ()
    endpoints: tuple[ServiceEndpoint, ...] = ()

    def __post_init__(self) -> None:
        if not STACK_NAME_PATTERN.fullmatch(self.stack_name):
            raise ValueError("service stack name contains invalid characters")
        if self.phase_id is not None and not STACK_NAME_PATTERN.fullmatch(self.phase_id):
            raise ValueError("service stack phase id contains invalid characters")
        if not self.required_services:
            raise ValueError("service stack contract requires at least one service")
        invalid_services = [
            service_name
            for service_name in self.required_services
            if not SERVICE_NAME_PATTERN.fullmatch(service_name)
        ]
        if invalid_services:
            raise ValueError("service stack contract contains invalid service names")
        invalid_port_ids = [
            port_id
            for port_id in self.port_ids
            if not SERVICE_NAME_PATTERN.fullmatch(port_id)
        ]
        if invalid_port_ids:
            raise ValueError("service stack contract contains invalid port ids")
        object.__setattr__(self, "required_services", tuple(self.required_services))
        object.__setattr__(self, "port_ids", tuple(self.port_ids))
        object.__setattr__(self, "endpoints", tuple(self.endpoints))

    @property
    def verification_target_id(self) -> str:
        return self.service_readiness_target_id

    @property
    def stack_target_id(self) -> str:
        return f"deployment:{self.stack_name}-stack"

    @property
    def service_readiness_target_id(self) -> str:
        return f"deployment:{self.stack_name}-service-readiness"

    def to_dict(self) -> dict[str, object]:
        return {
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
            "phase_id": self.phase_id,
            "port_ids": list(self.port_ids),
            "required_services": list(self.required_services),
            "service_readiness_target_id": self.service_readiness_target_id,
            "stack_target_id": self.stack_target_id,
            "stack_name": self.stack_name,
        }


DEFAULT_SERVICE_STACK_CONTRACTS = (
    ServiceStackContract(
        "portainer",
        ("portainer", "agent"),
        phase_id="platform",
        port_ids=("portainer-http",),
        endpoints=(ServiceEndpoint("portainer", "http://localhost:9000"),),
    ),
    ServiceStackContract(
        "traefik",
        ("traefik",),
        phase_id="network-routing",
        port_ids=("traefik-http", "traefik-https"),
        endpoints=(ServiceEndpoint("traefik", "https://localhost"),),
    ),
    ServiceStackContract(
        "nexus",
        ("nexus",),
        phase_id="artifacts",
        port_ids=("nexus-http", "nexus-docker-http", "nexus-docker-https"),
        endpoints=(
            ServiceEndpoint("nexus", "http://localhost:8081"),
            ServiceEndpoint("nexus-docker-registry", "http://localhost:5000"),
        ),
    ),
    ServiceStackContract(
        "jenkins",
        ("jenkins",),
        phase_id="cicd",
        port_ids=("jenkins-http", "jenkins-agent"),
        endpoints=(ServiceEndpoint("jenkins", "http://localhost:8080"),),
    ),
    ServiceStackContract(
        "pulsar",
        ("pulsar", "pulsar-manager"),
        phase_id="messaging",
        port_ids=("pulsar-broker", "pulsar-admin-api"),
        endpoints=(
            ServiceEndpoint("pulsar-admin-api", "http://localhost:8087"),
            ServiceEndpoint("pulsar-manager", "http://localhost:9527"),
            ServiceEndpoint("pulsar-manager-backend", "http://localhost:7750"),
        ),
    ),
    ServiceStackContract(
        "sonarqube",
        ("sonarqube", "sonar_db"),
        phase_id="quality",
        port_ids=("sonarqube-http",),
        endpoints=(ServiceEndpoint("sonarqube", "http://localhost:9001"),),
    ),
    ServiceStackContract(
        "swagger",
        ("swagger-editor", "swagger-ui", "swagger-api", "swagger-nginx"),
        phase_id="docs",
        port_ids=("swagger-ui", "openapi-aggregator"),
        endpoints=(ServiceEndpoint("swagger", "http://localhost:8084"),),
    ),
)

SERVICE_ACCESS_STACK_CONTRACT = ServiceStackContract(
    "service-access",
    ("service-access-dashboard", "service-access-nginx"),
    phase_id="control",
    port_ids=("service-access-http",),
    endpoints=(
        ServiceEndpoint("service-access", "http://localhost:10000"),
    ),
)

INFISICAL_STACK_CONTRACT = ServiceStackContract(
    "infisical",
    ("infisical", "infisical-db", "infisical-redis"),
    phase_id="secrets",
    port_ids=("infisical-http",),
    endpoints=(ServiceEndpoint("infisical", "http://localhost:8086"),),
)


def service_stack_contracts_for_profile(
    service_profile: ServiceStackProfile | str = ServiceStackProfile.DEFAULT,
) -> tuple[ServiceStackContract, ...]:
    profile = ServiceStackProfile(service_profile)
    if profile is ServiceStackProfile.SERVICE_ACCESS:
        return (*DEFAULT_SERVICE_STACK_CONTRACTS, INFISICAL_STACK_CONTRACT, SERVICE_ACCESS_STACK_CONTRACT)
    return DEFAULT_SERVICE_STACK_CONTRACTS


def portainer_managed_service_stack_contracts_for_profile(
    service_profile: ServiceStackProfile | str = ServiceStackProfile.DEFAULT,
) -> tuple[ServiceStackContract, ...]:
    return tuple(
        contract
        for contract in service_stack_contracts_for_profile(service_profile)
        if contract.stack_name != "portainer"
    )


DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS = portainer_managed_service_stack_contracts_for_profile()

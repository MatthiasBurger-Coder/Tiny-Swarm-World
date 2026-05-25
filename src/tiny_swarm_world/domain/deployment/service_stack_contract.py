from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


STACK_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
SERVICE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class ServiceStackProfile(str, Enum):
    DEFAULT = "default"
    SERVICE_ACCESS = "service-access"


@dataclass(frozen=True)
class ServiceStackContract:
    stack_name: str
    required_services: tuple[str, ...]

    def __post_init__(self) -> None:
        if not STACK_NAME_PATTERN.fullmatch(self.stack_name):
            raise ValueError("service stack name contains invalid characters")
        if not self.required_services:
            raise ValueError("service stack contract requires at least one service")
        invalid_services = [
            service_name
            for service_name in self.required_services
            if not SERVICE_NAME_PATTERN.fullmatch(service_name)
        ]
        if invalid_services:
            raise ValueError("service stack contract contains invalid service names")
        object.__setattr__(self, "required_services", tuple(self.required_services))

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
            "required_services": list(self.required_services),
            "service_readiness_target_id": self.service_readiness_target_id,
            "stack_target_id": self.stack_target_id,
            "stack_name": self.stack_name,
        }


DEFAULT_SERVICE_STACK_CONTRACTS = (
    ServiceStackContract("portainer", ("portainer", "agent")),
    ServiceStackContract("nexus", ("nexus",)),
    ServiceStackContract("jenkins", ("jenkins",)),
    ServiceStackContract("rabbitmq", ("rabbitmq",)),
    ServiceStackContract("sonarqube", ("sonarqube", "sonar_db")),
    ServiceStackContract("swagger", ("swagger-editor", "swagger-ui", "swagger-api", "swagger-nginx")),
)

SERVICE_ACCESS_STACK_CONTRACT = ServiceStackContract(
    "service-access",
    ("service-access-dashboard", "vaultwarden", "service-access-nginx"),
)


def service_stack_contracts_for_profile(
    service_profile: ServiceStackProfile | str = ServiceStackProfile.DEFAULT,
) -> tuple[ServiceStackContract, ...]:
    profile = ServiceStackProfile(service_profile)
    if profile is ServiceStackProfile.SERVICE_ACCESS:
        return (*DEFAULT_SERVICE_STACK_CONTRACTS, SERVICE_ACCESS_STACK_CONTRACT)
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

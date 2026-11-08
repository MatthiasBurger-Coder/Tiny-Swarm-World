"""Build the guided setup preview from the declared compose inventory."""

from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.preflight import (
    default_installation_plan,
    default_preflight_configuration,
)


@dataclass(frozen=True)
class SetupPlanService:
    name: str
    stack_name: str
    compose_service_names: tuple[str, ...]
    published_ports: tuple[int, ...]


@dataclass(frozen=True)
class SetupInstallationPlan:
    service_profile: ServiceStackProfile
    phase_names: tuple[str, ...]
    services: tuple[SetupPlanService, ...]


_STACK_NAMES = {
    "Jenkins": "jenkins",
    "Infisical": "infisical",
    "Nexus": "nexus",
    "Portainer": "portainer",
    "Pulsar": "pulsar",
    "Service Access": "service-access",
    "SonarQube": "sonarqube",
    "Swagger/NGINX": "swagger",
    "Traefik Ingress": "traefik",
}


def build_setup_installation_plan(
    service_profile: ServiceStackProfile | str,
    compose_repository: PortComposeFileRepository,
) -> SetupInstallationPlan:
    selected_profile = ServiceStackProfile(service_profile)
    manifest = default_preflight_configuration(service_profile=selected_profile).setup_manifest
    services = []
    for service in manifest.services:
        stack_name = _STACK_NAMES.get(service.name, "infra")
        try:
            compose_services = compose_repository.get_services_of(stack_name)
        except FileNotFoundError:
            compose_services = ()
        services.append(
            SetupPlanService(
                name=service.name,
                stack_name=stack_name,
                compose_service_names=tuple(item.name for item in compose_services),
                published_ports=tuple(
                    dict.fromkeys(
                        port
                        for item in compose_services
                        for port in item.published_ports
                    )
                ),
            )
        )
    return SetupInstallationPlan(
        selected_profile,
        default_installation_plan().ordered_workflow_phase_names(),
        tuple(services),
    )

from __future__ import annotations

from collections.abc import Mapping

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    PortDeploymentGateway,
)
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.application.services.deployment.ensure_service_stack import EnsureServiceStack
from tiny_swarm_world.domain.deployment import (
    DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS,
    ServiceStackProfile,
    portainer_managed_service_stack_contracts_for_profile,
)

DEFAULT_PORTAINER_ENDPOINT_NAME = "local"


def build_default_service_stack_steps(
    compose_repository: PortComposeFileRepository,
    deployment_gateway: PortDeploymentGateway,
) -> tuple[EnsureServiceStack, ...]:
    return build_service_stack_steps(
        compose_repository=compose_repository,
        deployment_gateway=deployment_gateway,
    )


def build_service_stack_steps(
    compose_repository: PortComposeFileRepository,
    deployment_gateway: PortDeploymentGateway,
    *,
    service_profile: ServiceStackProfile | str = ServiceStackProfile.DEFAULT,
    excluded_stack_names: tuple[str, ...] = (),
    stack_environments: Mapping[str, Mapping[str, str]] | None = None,
) -> tuple[EnsureServiceStack, ...]:
    excluded = set(excluded_stack_names)
    environments = stack_environments or {}
    contracts = (
        DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS
        if ServiceStackProfile(service_profile) is ServiceStackProfile.DEFAULT
        else portainer_managed_service_stack_contracts_for_profile(service_profile)
    )
    return tuple(
        EnsureServiceStack(
            compose_repository=compose_repository,
            deployment_gateway=deployment_gateway,
            service_stack=service_stack,
            stack_environment=environments.get(service_stack.stack_name),
        )
        for service_stack in contracts
        if service_stack.stack_name not in excluded
    )

from __future__ import annotations

from tiny_swarm_world.application.ports.clients.port_portainer_client import PortPortainerClient
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.application.services.deployment.ensure_service_stack import EnsureServiceStack
from tiny_swarm_world.domain.deployment import DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS


def build_default_service_stack_steps(
    compose_repository: PortComposeFileRepository,
    portainer_client: PortPortainerClient,
    endpoint_name: str,
) -> tuple[EnsureServiceStack, ...]:
    return tuple(
        EnsureServiceStack(
            compose_repository=compose_repository,
            portainer_client=portainer_client,
            service_stack=service_stack,
            endpoint_name=endpoint_name,
        )
        for service_stack in DEFAULT_PORTAINER_MANAGED_SERVICE_STACK_CONTRACTS
    )

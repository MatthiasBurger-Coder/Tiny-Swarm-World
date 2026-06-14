import asyncio
import logging

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
    PortDeploymentGateway,
)
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)


class EnsurePortainerStack:
    deployment_target_id = "deployment:portainer-stack"

    def __init__(
        self,
        compose_repository: PortComposeFileRepository,
        deployment_gateway: PortDeploymentGateway,
        stack_name: str,
    ):
        self.compose_repository = compose_repository
        self.deployment_gateway = deployment_gateway
        self.stack_name = stack_name
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> None:
        await asyncio.sleep(0)
        stack_definition = self.compose_repository.get_compose_of(self.stack_name)
        self.logger.info("Applying deployment stack '%s'.", stack_definition.name)
        self.deployment_gateway.apply_stack(
            DeploymentStackRequest(
                target_stack=self.stack_name,
                stack_definition=stack_definition,
            )
        )

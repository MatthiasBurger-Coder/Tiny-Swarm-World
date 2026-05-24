import logging

from tiny_swarm_world.application.ports.clients.port_portainer_client import PortPortainerClient
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)


class EnsurePortainerStack:
    deployment_target_id = "deployment:portainer-stack"

    def __init__(
        self,
        compose_repository: PortComposeFileRepository,
        portainer_client: PortPortainerClient,
        stack_name: str,
        endpoint_name: str,
    ):
        self.compose_repository = compose_repository
        self.portainer_client = portainer_client
        self.stack_name = stack_name
        self.endpoint_name = endpoint_name
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> None:
        stack_definition = self.compose_repository.get_compose_of(self.stack_name)
        endpoint_id = self.portainer_client.get_endpoint_id_by_name(self.endpoint_name)
        stack_id = self.portainer_client.find_stack_id_by_name(stack_definition.name)

        if stack_id is None:
            self.logger.info("Creating Portainer-managed stack '%s'.", stack_definition.name)
            self.portainer_client.create_stack(stack_definition, endpoint_id)
            return

        self.logger.info("Updating Portainer-managed stack '%s'.", stack_definition.name)
        self.portainer_client.update_stack(stack_id, stack_definition, endpoint_id)

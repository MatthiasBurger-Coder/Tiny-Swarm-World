import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow


class MultipassDockerInstall:
    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("Install docker on multipass")

        result = await self.command_workflow.run_async("command_multipass_docker_install_yaml.yaml")
        self.logger.info(f"Install docker on multipass: {result}")

        self.logger.info("Setting docker group on multipass")
        result = await self.command_workflow.run_async("command_multipass_docker_prepare_repository_yaml.yaml")
        self.logger.info(f"Setting docker group on multipass: {result}")

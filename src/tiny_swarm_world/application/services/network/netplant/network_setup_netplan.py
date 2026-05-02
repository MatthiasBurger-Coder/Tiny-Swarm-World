import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow


class NetworkSetupNetplan:
    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("initialisation of network")

        result = await self.command_workflow.run_async("command_netplant_setup_yaml.yaml")
        self.logger.info(f"initialisation of network : {result}")

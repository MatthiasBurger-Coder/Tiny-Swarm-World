import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow


class MultipassRestartVMs:
    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("Restart VMs")

        result = await self.command_workflow.run_async("command_multipass_restart_repository_yaml.yaml")
        self.logger.info(f"Restart VMs: {result}")

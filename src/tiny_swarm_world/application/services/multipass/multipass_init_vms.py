import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId


class MultipassInitVms:
    verification_target_id = "platform:init:multipass-vms"
    operator_block_reason = "command-backed verification is not configured"

    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("initialisation of multipass")

        result = await self.command_workflow.run_async(
            "command_multipass_init_repository_yaml.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info(f"initialisation of multipass: {result}")

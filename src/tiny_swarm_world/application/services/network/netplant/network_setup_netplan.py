import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId


class NetworkSetupNetplan:
    verification_target_id = "platform:init:network-setup-netplan"
    operator_block_reason = "post-apply verification is not implemented"

    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("initialisation of network")

        await self.command_workflow.run_async(
            "command_netplant_setup_yaml.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info("initialisation of network completed")

    def verify_pre_apply(self):
        from tiny_swarm_world.application.services.platform.command_verification import (
            verify_command_configs,
        )

        return verify_command_configs(
            self.command_workflow,
            target_id=self.verification_target_id,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            config_files=("command_netplant_setup_yaml.yaml",),
        )

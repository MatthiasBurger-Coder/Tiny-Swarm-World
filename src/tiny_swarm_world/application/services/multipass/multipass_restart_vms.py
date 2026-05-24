import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId


class MultipassRestartVMs:
    verification_target_id = "platform:init:multipass-restart-vms"
    operator_block_reason = "post-apply verification is not implemented"

    def __init__(
        self,
        command_workflow: PortCommandWorkflow,
        verify_max_attempts: int = 12,
        verify_wait_seconds: float = 10,
    ):
        self.command_workflow = command_workflow
        self.verify_max_attempts = verify_max_attempts
        self.verify_wait_seconds = verify_wait_seconds
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("Restart VMs")

        await self.command_workflow.run_async(
            "command_multipass_restart_repository_yaml.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info("Restart VMs completed")

    def verify_pre_apply(self):
        from tiny_swarm_world.application.services.platform.command_verification import (
            verify_command_configs,
        )

        return verify_command_configs(
            self.command_workflow,
            target_id=self.verification_target_id,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            config_files=("command_multipass_restart_repository_yaml.yaml",),
        )

    async def verify(self):
        from tiny_swarm_world.application.services.platform.command_verification import (
            verify_command_execution,
        )

        return await verify_command_execution(
            self.command_workflow,
            target_id=self.verification_target_id,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            config_file="command_multipass_instance_status_yaml.yaml",
            max_attempts=self.verify_max_attempts,
            wait_seconds=self.verify_wait_seconds,
        )

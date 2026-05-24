import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId


class MultipassDockerInstall:
    verification_target_id = "platform:init:multipass-docker-install"
    operator_block_reason = "post-apply verification is not implemented"

    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("Install docker on multipass")

        await self.command_workflow.run_async(
            "command_multipass_docker_install_yaml.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info("Install docker on multipass completed")

        self.logger.info("Setting docker group on multipass")
        await self.command_workflow.run_async(
            "command_multipass_docker_prepare_repository_yaml.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info("Setting docker group on multipass completed")

    def verify_pre_apply(self):
        from tiny_swarm_world.application.services.platform.command_verification import (
            verify_command_configs,
        )

        return verify_command_configs(
            self.command_workflow,
            target_id=self.verification_target_id,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            config_files=(
                "command_multipass_docker_install_yaml.yaml",
                "command_multipass_docker_prepare_repository_yaml.yaml",
            ),
        )

    async def verify(self):
        from tiny_swarm_world.application.services.platform.command_verification import (
            verify_command_execution,
        )

        return await verify_command_execution(
            self.command_workflow,
            target_id=self.verification_target_id,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            config_file="command_multipass_docker_verify_yaml.yaml",
        )

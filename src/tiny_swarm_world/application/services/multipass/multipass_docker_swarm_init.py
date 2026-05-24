import logging
from typing import Dict, Optional

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId


class MultipassDockerSwarmInit:
    verification_target_id = "platform:init:multipass-docker-swarm-init"
    operator_block_reason = "post-apply verification is not implemented"

    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):

        self.logger.info("Initializing Docker Swarm on Manager")
        await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_init.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info("Initializing Docker Swarm on Manager completed")

        self.logger.info("Getting join-token for the worker")
        await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_join_token.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info("Getting join-token for the worker completed with redacted output")

        self.logger.info("Getting Manager IP")
        result = await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_ip.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        ipaddress = list(result[0].values())[0].split()[0]
        self.parameter[ParameterType.SWARM_MANAGER_IP] = ipaddress
        self.parameter[ParameterType.SWARM_MANAGER_PORT] = "2377"
        self.logger.info("Getting Manager IP completed")

        self.logger.info("Getting join token")
        result = await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_join_token.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        token = result[0][1]
        self.logger.info("Getting join token completed with redacted output")

        self.logger.info("Join worker to Swarm")
        join_params = dict(self.parameter)
        join_params[ParameterType.SWARM_TOKEN] = token
        try:
            await self.command_workflow.run_sync(
                "command_multipass_docker_swarm_join_worker.yaml",
                join_params,
                workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            )
        finally:
            join_params.pop(ParameterType.SWARM_TOKEN, None)
            self.parameter.pop(ParameterType.SWARM_TOKEN, None)
        self.logger.info("Join worker to Swarm completed")

    def verify_pre_apply(self):
        from tiny_swarm_world.application.services.platform.command_verification import (
            verify_command_configs,
        )

        return verify_command_configs(
            self.command_workflow,
            target_id=self.verification_target_id,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            config_files=(
                "command_multipass_docker_swarm_manager_init.yaml",
                "command_multipass_docker_swarm_manager_join_token.yaml",
                "command_multipass_docker_swarm_manager_ip.yaml",
                "command_multipass_docker_swarm_join_worker.yaml",
            ),
        )

    def _setup_commands_init(self, config_file: str, parameter: Optional[Dict[ParameterType, str]]) -> Dict[
        str, Dict[int, ExecutableCommandEntity]]:
        """
        Sets up the initial multipass commands by reading from the YAML configuration.

        Args:
            config_file (str): The path to the YAML configuration file.

        Returns:
            Dict[str, Dict[int, ExecutableCommandEntity]]: The command list.
        """
        parameter = parameter or {}
        self.logger.info("getting command list from configured catalog")
        command_list = self.command_workflow.build_command_list(
            config_file,
            parameter,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        command_count = sum(len(commands) for commands in command_list.values())
        self.logger.info("command list built with %s configured entries", command_count)
        return command_list

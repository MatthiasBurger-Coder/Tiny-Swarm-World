import logging
from typing import Dict, Optional

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId


class MultipassDockerSwarmInit:
    def __init__(self, command_workflow: PortCommandWorkflow):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):

        self.logger.info("Initializing Docker Swarm on Manager")
        result = await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_init.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info(f"Initializing Docker Swarm on Manager: {result}")

        self.logger.info("Getting join-token for the worker")
        result = await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_join_token.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info(f"Getting join-token for the worker: {result}")

        self.logger.info("Getting Manager IP")
        result = await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_ip.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        ipaddress = list(result[0].values())[0].split()[0]
        self.parameter[ParameterType.SWARM_MANAGER_IP] = ipaddress
        self.parameter[ParameterType.SWARM_MANAGER_PORT] = "2377"
        self.logger.info(f"Getting Manager IP: {result}")

        self.logger.info("Getting join token")
        result = await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_manager_join_token.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        token = result[0][1]
        self.parameter[ParameterType.SWARM_TOKEN] = token
        self.logger.info(f"Getting join token: {token}")

        self.logger.info("Join worker to Swarm")
        result = await self.command_workflow.run_sync(
            "command_multipass_docker_swarm_join_worker.yaml",
            self.parameter,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info(f"Join worker to Swarm: {result}")

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
        self.logger.info(f"getting command list from {config_file}")
        command_list = self.command_workflow.build_command_list(
            config_file,
            parameter,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info(f"command builder: {command_list}")
        return command_list

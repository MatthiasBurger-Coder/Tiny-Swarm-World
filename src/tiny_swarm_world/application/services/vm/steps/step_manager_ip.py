import logging
from typing import Dict

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId
from tiny_swarm_world.domain.network.socat.docker_ip_list import DockerIpList


class StepManagerIp:
    def __init__(self, docker_ip_list: DockerIpList, command_workflow: PortCommandWorkflow):
        self.docker_ip_list = docker_ip_list
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):
        self.logger.info("Getting Manager IP")
        result = await self.command_workflow.run_async(
            "command_multipass_docker_swarm_manager_ip.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_RECONCILE.value,
        )
        ipaddress = next(iter(result[0].values())).split()[0]
        #ToDo listinig the correct vm ip use command vm_ip_list!!!
        self.docker_ip_list.external_ip = ipaddress
        self.logger.info("Manager IP result received")

import logging
import re
from typing import Dict

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.domain.network.ip_value import IpValue
from tiny_swarm_world.domain.network.socat.docker_ip_list import DockerIpList


class StepManagerGateway:
    def __init__(self, docker_ip_list: DockerIpList, command_workflow: PortCommandWorkflow):
        self.docker_ip_list = docker_ip_list
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):
        self.logger.info("Getting Manager Gateway")
        result = await self.command_workflow.run_async("command_vm_gateway_yaml.yaml")
        self.logger.info(f"Getting Manager Gateway: {result}")

        text = list(result[0].values())[0]

        match = re.search(r'default via ([\d.]+)', text)
        if match:
            ip_address = match.group(1)
            self.docker_ip_list.gateway = IpValue(ip_address=ip_address)
            self.logger.info(f"extracted ip address: {ip_address}")

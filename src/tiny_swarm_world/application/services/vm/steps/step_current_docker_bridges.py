import logging
from typing import Dict

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId
from tiny_swarm_world.domain.network.ip_value import IpValue
from tiny_swarm_world.domain.network.socat.docker_bridge_type import DockerBridgeType
from tiny_swarm_world.domain.network.socat.docker_ip_list import DockerIpList


class StepCurrentDockerBridges:
    def __init__(self, docker_ip_list: DockerIpList, command_workflow: PortCommandWorkflow):
        self.docker_ip_list = docker_ip_list
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):
        self.logger.info("Getting current docker bridges")
        result = await self.command_workflow.run_async(
            "command_vm_bridge_list.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_RECONCILE.value,
        )
        self.logger.info(f"Getting current docker bridges: {result}")
        bridge_list = result[0][1].split('\n')

        for bridge in bridge_list:

            self.parameter[ParameterType.DOCKER_BRIDGE] = bridge

            self.logger.info(f"docker bridge: {bridge}")
            result = await self.command_workflow.run_async(
                "command_vm_docker_bridge_list.yaml",
                self.parameter,
                workflow_id=CommandWorkflowId.PLATFORM_RECONCILE.value,
            )
            self.logger.info(f"docker bridge {bridge} ip: {result}")

            match bridge:
                case DockerBridgeType.BRIDGE.value:
                    self.docker_ip_list.docker_bridge_ip = IpValue(ip_address=result[0][1])
                case DockerBridgeType.DOCKER_GWBRIDGE.value:
                    self.docker_ip_list.docker_overlay_ip = IpValue(ip_address=result[0][1])

import logging
from typing import Dict, List

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository
from tiny_swarm_world.application.services.vm.steps.step_current_docker_bridges import StepCurrentDockerBridges
from tiny_swarm_world.application.services.vm.steps.step_manager_gateway import StepManagerGateway
from tiny_swarm_world.application.services.vm.steps.step_manager_ip import StepManagerIp
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.domain.multipass.vm_entity import VmEntity
from tiny_swarm_world.domain.network.socat.docker_ip_list import DockerIpList


class VmIpList:
    def __init__(self, command_workflow: PortCommandWorkflow, vm_repository: PortVmRepository):
        self.command_workflow = command_workflow
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parameter: Dict[ParameterType, str] = {}
        self.docker_ip_list = DockerIpList()
        self.step_current_docker_bridges = StepCurrentDockerBridges(self.docker_ip_list, command_workflow)
        self.step_manager_ip = StepManagerIp(self.docker_ip_list, command_workflow)
        self.step_manager_gateway = StepManagerGateway(self.docker_ip_list, command_workflow)
        self.vm_repository = vm_repository

    async def run(self):
        self.logger.info("starting vm ip list")

        await self.step_current_docker_bridges.run()
        await self.step_manager_ip.run()
        await self.step_manager_gateway.run()

        self.logger.info(f"docker ip list: {self.docker_ip_list}")
        vm_list: List[VmEntity] =self.vm_repository.get_all_vms()
        for vm in vm_list:
            vm.gateway = str(self.docker_ip_list.gateway)
            vm.external_ip = str(self.docker_ip_list.external_ip)
            vm.docker_bridge_ip = str(self.docker_ip_list.docker_bridge_ip)
            vm.docker_overlay_ip = str(self.docker_ip_list.docker_overlay_ip)
            self.logger.info(f"vm: {vm}, update with ip list: {self.docker_ip_list}")
            self.vm_repository.update_vm(vm)

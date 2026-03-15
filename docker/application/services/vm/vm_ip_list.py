from typing import Dict, List

from application.services.vm.steps.step_current_docker_bridges import StepCurrentDockerBridges
from application.services.vm.steps.step_manager_gateway import StepManagerGateway
from application.services.vm.steps.step_manager_ip import StepManagerIp
from domain.command.command_builder.vm_parameter.parameter_type import ParameterType
from domain.multipass.vm_entity import VmEntity
from domain.network.socat.docker_ip_list import DockerIpList
from infrastructure.adapters.command_runner.command_runner_factory import CommandRunnerFactory
from infrastructure.adapters.repositories.vm_repository_yaml import PortVmRepositoryYaml
from infrastructure.logging.logger_factory import LoggerFactory


class VmIpList:
    def __init__(self):
        self.command_runner_factory = CommandRunnerFactory()
        self.command_execute = None
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.parameter: Dict[ParameterType, str] = {}
        self.docker_ip_list = DockerIpList()
        self.step_current_docker_bridges = StepCurrentDockerBridges(self.docker_ip_list)
        self.step_manager_ip = StepManagerIp(self.docker_ip_list)
        self.step_manager_gateway = StepManagerGateway(self.docker_ip_list)
        self.vm_repository = PortVmRepositoryYaml()

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

from typing import Dict

from domain.command.command_builder.vm_parameter.command_builder import CommandBuilder
from domain.command.command_builder.vm_parameter.parameter_type import ParameterType
from domain.network.socat.docker_ip_list import DockerIpList
from infrastructure.adapters.command_runner.command_runner_factory import CommandRunnerFactory
from infrastructure.adapters.repositories.command_multipass_init_repository_yaml import PortCommandRepositoryYaml
from infrastructure.adapters.ui.command_async_runner_ui import AsyncCommandRunnerUI
from infrastructure.logging.logger_factory import LoggerFactory


class StepManagerIp:
    def __init__(self, docker_ip_list: DockerIpList):
        self.docker_ip_list = docker_ip_list
        self.command_runner_factory =  CommandRunnerFactory()
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):
        self.logger.info("Getting Manager IP")
        multipass_command_repository = PortCommandRepositoryYaml(filename="command_multipass_docker_swarm_manager_ip.yaml")
        command_builder: CommandBuilder = CommandBuilder(command_repository=multipass_command_repository)
        command_list = command_builder.get_command_list()
        runner_ui = AsyncCommandRunnerUI(command_list)
        result = await runner_ui.run()
        ipaddress = list(result[0].values())[0].split()[0]
        #ToDo listinig the correct vm ip use command vm_ip_list!!!
        self.docker_ip_list.external_ip = ipaddress
        self.logger.info(f"Getting Manager IP: {result}")
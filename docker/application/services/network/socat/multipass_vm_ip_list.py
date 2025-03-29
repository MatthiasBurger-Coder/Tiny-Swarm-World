from typing import Dict

from domain.command.command_builder.vm_parameter.command_builder import CommandBuilder
from domain.command.command_builder.vm_parameter.parameter_type import ParameterType
from domain.network.ip_value import IpValue
from domain.network.socat.docker_bridge_type import DockerBridgeType
from domain.network.socat.docker_ip_list import DockerIpList
from infrastructure.adapters.command_runner.command_runner_factory import CommandRunnerFactory
from infrastructure.adapters.repositories.command_multipass_init_repository_yaml import PortCommandRepositoryYaml
from infrastructure.adapters.ui.command_async_runner_ui import AsyncCommandRunnerUI
from infrastructure.logging.logger_factory import LoggerFactory


class MultipassVmIpList:
    def __init__(self, command_runner_factory=None):
        self.command_runner_factory = command_runner_factory or CommandRunnerFactory()
        self.ui = None
        self.command_execute = None
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):
        self.logger.info("Getting current docker bridges")
        multipass_command_repository = PortCommandRepositoryYaml(filename="command_socat_vm_bridge_list.yaml")
        command_builder: CommandBuilder = CommandBuilder(command_repository=multipass_command_repository)
        command_list = command_builder.get_command_list()
        runner_ui = AsyncCommandRunnerUI(command_list)
        result = await runner_ui.run()
        self.logger.info(f"Getting current docker bridges: {result}")

        bridge_list = result[0][1].split('\n')
        docker_ip_list = DockerIpList()
        for bridge in bridge_list:

            self.parameter[ParameterType.DOCKER_BRIDGE] = bridge

            self.logger.info(f"docker bridge: {bridge}")
            multipass_command_repository = PortCommandRepositoryYaml(filename="command_multipass_vm_ip_list.yaml")
            command_builder: CommandBuilder = CommandBuilder(command_repository=multipass_command_repository, parameter=self.parameter)
            command_list = command_builder.get_command_list()

            runner_ui = AsyncCommandRunnerUI(command_list)
            result = await runner_ui.run()
            self.logger.info(f"docker bridge {bridge} ip: {result}")

            match bridge:
                case DockerBridgeType.BRIDGE.value:
                    docker_ip_list.docker_bridge_ip = IpValue(ip_address=result[0][1])
                case DockerBridgeType.DOCKER_GWBRIDGE.value:
                    docker_ip_list.docker_overlay_ip = IpValue(ip_address=result[0][1])


        self.logger.info("Getting Manager IP")
        multipass_command_repository = PortCommandRepositoryYaml(filename="command_multipass_docker_swarm_manager_ip.yaml")
        command_builder: CommandBuilder = CommandBuilder(command_repository=multipass_command_repository)
        command_list = command_builder.get_command_list()
        runner_ui = AsyncCommandRunnerUI(command_list)
        result = await runner_ui.run()
        ipaddress = list(result[0].values())[0].split()[0]
        docker_ip_list.external_ip = ipaddress
        self.logger.info(f"Getting Manager IP: {result}")

        self.logger.info("Getting Manager Gateway")
        multipass_command_repository = PortCommandRepositoryYaml(filename="command_multipass_docker_swarm_manager_ip.yaml")
        command_builder: CommandBuilder = CommandBuilder(command_repository=multipass_command_repository)
        command_list = command_builder.get_command_list()
        runner_ui = AsyncCommandRunnerUI(command_list)
        result = await runner_ui.run()

        gateway_ip = self.ip_extractor_builder.build(result=result, ip_extractor_types=IpExtractorTypes.GATEWAY)
        self.logger.info(f"extracted gateway ip: {gateway_ip}")
        ip = self.ip_extractor_builder.build(result=result, ip_extractor_types=IpExtractorTypes.SWAM_MANAGER)
        self.logger.info(f"extracted ip: {ip}")

        self.logger.info(f"docker ip list: {docker_ip_list}")
from typing import Dict

from tiny_swarm_world.domain.command.command_builder.vm_parameter.command_builder import CommandBuilder
from tiny_swarm_world.domain.command.command_builder.vm_parameter.parameter_type import ParameterType
from tiny_swarm_world.domain.network.ip_value import IpValue
from tiny_swarm_world.domain.network.socat.docker_bridge_type import DockerBridgeType
from tiny_swarm_world.domain.network.socat.docker_ip_list import DockerIpList
from tiny_swarm_world.infrastructure.adapters.command_runner.command_runner_factory import CommandRunnerFactory
from tiny_swarm_world.infrastructure.adapters.repositories.command_multipass_init_repository_yaml import PortCommandRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui import AsyncCommandRunnerUI
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class StepCurrentDockerBridges:
    def __init__(self, docker_ip_list: DockerIpList):
        self.docker_ip_list = docker_ip_list
        self.command_runner_factory =  CommandRunnerFactory()
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.parameter: Dict[ParameterType, str] = {}

    async def run(self):
        self.logger.info("Getting current docker bridges")
        command_socat_vm_bridge_list = PortCommandRepositoryYaml(filename="command_vm_bridge_list.yaml")
        command_builder: CommandBuilder = CommandBuilder(command_repository=command_socat_vm_bridge_list)
        command_list = command_builder.get_command_list()
        runner_ui = AsyncCommandRunnerUI(command_list)
        result = await runner_ui.run()
        self.logger.info(f"Getting current docker bridges: {result}")
        bridge_list = result[0][1].split('\n')

        for bridge in bridge_list:

            self.parameter[ParameterType.DOCKER_BRIDGE] = bridge

            self.logger.info(f"docker bridge: {bridge}")
            multipass_command_repository = PortCommandRepositoryYaml(filename="command_vm_docker_bridge_list.yaml")
            command_builder: CommandBuilder = CommandBuilder(command_repository=multipass_command_repository,
                                                             parameter=self.parameter)
            command_list = command_builder.get_command_list()

            runner_ui = AsyncCommandRunnerUI(command_list)
            result = await runner_ui.run()
            self.logger.info(f"docker bridge {bridge} ip: {result}")

            match bridge:
                case DockerBridgeType.BRIDGE.value:
                    self.docker_ip_list.docker_bridge_ip = IpValue(ip_address=result[0][1])
                case DockerBridgeType.DOCKER_GWBRIDGE.value:
                    self.docker_ip_list.docker_overlay_ip = IpValue(ip_address=result[0][1])

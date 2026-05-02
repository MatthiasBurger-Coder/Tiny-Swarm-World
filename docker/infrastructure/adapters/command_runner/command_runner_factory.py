from application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory
from application.ports.commands.port_command_runner import PortCommandRunner
from domain.command.command_runner_type_enum import CommandRunnerType
from infrastructure.adapters.command_runner.ansible_runner import AnsiblePortCommandRunner
from infrastructure.adapters.command_runner.async_command_runner import AsyncPortCommandRunner
from infrastructure.adapters.command_runner.rest_api_runner import RestApiPortCommandRunner


class CommandRunnerFactory(PortCommandRunnerFactory):
    def get_runner(self, runner_type: CommandRunnerType) -> PortCommandRunner:
        if runner_type == CommandRunnerType.ASYNC:
            return AsyncPortCommandRunner()
        if runner_type == CommandRunnerType.REST:
            return RestApiPortCommandRunner()
        if runner_type == CommandRunnerType.ANSIBLE:
            return AnsiblePortCommandRunner()
        raise ValueError(f"Unsupported runner type: {runner_type}")

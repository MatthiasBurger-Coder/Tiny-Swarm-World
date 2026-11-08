from tiny_swarm_world.application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory
from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner
from tiny_swarm_world.domain.command.command_runner_type_enum import CommandRunnerType
from tiny_swarm_world.infrastructure.adapters.command_runner.async_command_runner import AsyncPortCommandRunner


class CommandRunnerFactory(PortCommandRunnerFactory):
    def get_runner(self, runner_type: CommandRunnerType) -> PortCommandRunner:
        if runner_type == CommandRunnerType.ASYNC:
            return AsyncPortCommandRunner()
        raise ValueError(
            f"Unsupported runner type for active Tiny Swarm World workflows: {runner_type.value}. "
            "Only the async shell command runner is selectable."
        )

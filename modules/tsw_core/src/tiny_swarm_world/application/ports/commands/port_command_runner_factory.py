from abc import ABC, abstractmethod

from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner
from tiny_swarm_world.domain.command.command_runner_type_enum import CommandRunnerType


class PortCommandRunnerFactory(ABC):
    @abstractmethod
    def get_runner(self, runner_type: CommandRunnerType) -> PortCommandRunner:
        pass

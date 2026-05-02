from abc import ABC, abstractmethod
from typing import Dict, Optional

from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.parameter_type import ParameterType
from tiny_swarm_world.domain.command.command_entity import CommandEntity
from tiny_swarm_world.application.services.commands.command_executer.excecuteable_commands import ExecutableCommandEntity
from tiny_swarm_world.domain.multipass.vm_type import VmType
from tiny_swarm_world.application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory


class CommandBuilderStrategy(ABC):
    """Abstract strategy class for processing VM types."""

    def __init__(self
                 , vm_type: VmType
                 , command_runner_factory: PortCommandRunnerFactory):
        self.command_runner_factory = command_runner_factory
        self.vm_type = vm_type

    @abstractmethod
    def categorize(self, command: CommandEntity, executable_commands: Dict[str, Dict[int, ExecutableCommandEntity]],parameter: Optional[Dict[ParameterType,str]]=None):
        """Inserts the command into the respective group based on its index."""
        pass

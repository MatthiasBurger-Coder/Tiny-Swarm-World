from typing import Dict, Optional

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.strategies.command_builder_strategy import CommandBuilderStrategy
from tiny_swarm_world.domain.command.command_entity import CommandEntity
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.multipass.vm_type import VmType


class InvalidCommandBuilderStrategy(CommandBuilderStrategy):
    def __init__(self, vm_type: VmType, command_runner_factory=None):
        super().__init__(vm_type=vm_type, command_runner_factory=command_runner_factory)

    def categorize(self, command: CommandEntity, executable_commands: Dict[str, Dict[int, ExecutableCommandEntity]], parameter: Optional[Dict[ParameterType, str]] = None):
        raise ValueError(f"Invalid vm found: {command.vm_type}")

from typing import Dict, Optional

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.strategies.command_builder_strategy import CommandBuilderStrategy
from tiny_swarm_world.domain.command.command_entity import CommandEntity
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.command.command_runner_type_enum import CommandRunnerType
from tiny_swarm_world.domain.command.vm_type import VmType


class NoneStrategy(CommandBuilderStrategy):

    def __init__(self, vm_type: VmType, command_runner_factory=None):
        super().__init__(vm_type=vm_type, command_runner_factory=command_runner_factory)

    def categorize(self, command: CommandEntity, executable_commands: Dict[str, Dict[int, ExecutableCommandEntity]], parameter: Optional[Dict[ParameterType, str]] = None):
        vm_instance_name = command.command_type.value
        executable_commands.setdefault(vm_instance_name, {})
        executable_commands[vm_instance_name][command.index] = ExecutableCommandEntity(
            command_id=command.id,
            safety_class=command.safety_class,
            verify=command.verify,
            evidence_policy=command.evidence_policy,
            vm_instance_name=vm_instance_name,
            description=command.description.format(vm_instance=vm_instance_name),
            command=command.command.format(vm_instance=vm_instance_name),
            runner=self.command_runner_factory.get_runner(CommandRunnerType.get_enum_from_value(command.runner)))

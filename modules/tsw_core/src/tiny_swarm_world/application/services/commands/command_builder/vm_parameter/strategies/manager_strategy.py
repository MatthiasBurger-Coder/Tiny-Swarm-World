import logging
from typing import Dict, Optional

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.strategies.command_builder_strategy import CommandBuilderStrategy
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.strategies.command_parameter_builder import CommandParameterBuilder
from tiny_swarm_world.domain.command.command_entity import CommandEntity
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.command.command_runner_type_enum import CommandRunnerType
from tiny_swarm_world.domain.command.vm_type import VmType
from tiny_swarm_world.application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository


class ManagerStrategy(CommandBuilderStrategy):

    def __init__(
        self,
        vm_type: VmType,
        command_runner_factory: PortCommandRunnerFactory,
        vm_repository: PortVmRepository,
    ):
        super().__init__(vm_type=vm_type, command_runner_factory=command_runner_factory)
        self.vm_repository = vm_repository
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("ManagerStrategy initialized")
        self.command_parameter_builder= CommandParameterBuilder()

    def categorize(self, command: CommandEntity, executable_commands: Dict[str, Dict[int, ExecutableCommandEntity]],parameter: Optional[Dict[ParameterType,str]]=None):
        active_parameter = dict(parameter or {})
        vm_instance_names = self.vm_repository.find_vm_instances_by_type(self.vm_type)

        if len(vm_instance_names) == 1:
            self.logger.info(f"Found vm instance: {vm_instance_names[0]}")
            vm_instance_name = vm_instance_names[0]
            active_parameter[ParameterType.VM_INSTANCE] = vm_instance_name
            executable_commands.setdefault(vm_instance_name, {})
            executable_commands[vm_instance_name][command.index] = ExecutableCommandEntity(
                command_id=command.id,
                safety_class=command.safety_class,
                verify=command.verify,
                evidence_policy=command.evidence_policy,
                vm_instance_name=vm_instance_name,
                description=command.description.format(vm_instance=vm_instance_name),
                command=self.command_parameter_builder.substitute_command(command.command,active_parameter),
                runner=self.command_runner_factory.get_runner(CommandRunnerType.get_enum_from_value(command.runner))
            )

from typing import Dict, Optional

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.strategies.manager_strategy import ManagerStrategy
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.strategies.none_strategy import NoneStrategy
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.strategies.worker_strategy import WorkerStrategy
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.command.vm_type import VmType
from tiny_swarm_world.application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory
from tiny_swarm_world.application.ports.repositories.port_command_repository import PortCommandRepository
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository


class CommandBuilder:
    executable_commands: Dict[str, Dict[int, ExecutableCommandEntity]]

    def __init__(
        self,
        command_repository: PortCommandRepository,
        command_runner_factory: PortCommandRunnerFactory,
        vm_repository: PortVmRepository,
        parameter: Optional[Dict[ParameterType, str]] = None,
        workflow_id: str = "",
    ):
        """
        :param command_repository: command repository for VM-scoped command templates.
        """
        self.vm_repository = vm_repository
        self.command_runner_factory = command_runner_factory
        self.command_repository = command_repository
        self.executable_commands = {}
        self.parameter = parameter or {}
        self.workflow_id = workflow_id

        self.STRATEGY_MAP = {
            VmType.MANAGER: ManagerStrategy(
                vm_type=VmType.MANAGER,
                command_runner_factory=self.command_runner_factory,
                vm_repository=self.vm_repository,
            ),
            VmType.WORKER: WorkerStrategy(
                vm_type=VmType.WORKER,
                command_runner_factory=self.command_runner_factory,
                vm_repository=self.vm_repository,
            ),
            VmType.NONE: NoneStrategy(vm_type=VmType.NONE, command_runner_factory=self.command_runner_factory),
        }

    def get_command_list(self) -> Dict[str, Dict[int, ExecutableCommandEntity]]:
        command_dict = self.command_repository.get_all_commands()

        for command in command_dict.values():
            command.ensure_allowed_for_workflow(self.workflow_id)
            for vm_type in command.vm_type:
                strategy = self.STRATEGY_MAP.get(vm_type)
                if strategy is None:
                    raise ValueError(f"Unsupported VM type: {vm_type}")
                strategy.categorize(command, self.executable_commands,self.parameter)
        return self.executable_commands

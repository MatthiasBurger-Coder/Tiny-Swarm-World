from typing import Any, Callable, Dict, Optional

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory
from tiny_swarm_world.application.ports.repositories.port_command_repository import PortCommandRepository
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.command_builder import CommandBuilder
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.infrastructure.adapters.command_runner.command_runner_factory import CommandRunnerFactory
from tiny_swarm_world.infrastructure.adapters.repositories.command_multipass_init_repository_yaml import (
    PortCommandRepositoryYaml,
)
from tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml import PortVmRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui import AsyncCommandRunnerUI
from tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui import SyncCommandRunnerUI


CommandRepositoryFactory = Callable[[str], PortCommandRepository]


class CommandWorkflow(PortCommandWorkflow):
    def __init__(
        self,
        command_runner_factory: PortCommandRunnerFactory | None = None,
        vm_repository: PortVmRepository | None = None,
        command_repository_factory: CommandRepositoryFactory | None = None,
    ):
        self.command_runner_factory = command_runner_factory or CommandRunnerFactory()
        self.vm_repository = vm_repository or PortVmRepositoryYaml()
        self.command_repository_factory = command_repository_factory or self._command_repository

    def build_command_list(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
    ) -> Dict[str, Dict[int, ExecutableCommandEntity]]:
        command_repository = self.command_repository_factory(config_file)
        command_builder = CommandBuilder(
            command_repository=command_repository,
            command_runner_factory=self.command_runner_factory,
            vm_repository=self.vm_repository,
            parameter=parameter,
            workflow_id=workflow_id,
        )
        return command_builder.get_command_list()

    async def run_async(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
    ) -> Any:
        return await AsyncCommandRunnerUI(
            self.build_command_list(config_file, parameter, workflow_id=workflow_id)
        ).run()

    async def run_sync(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
    ) -> Any:
        return await SyncCommandRunnerUI(
            self.build_command_list(config_file, parameter, workflow_id=workflow_id)
        ).run()

    @staticmethod
    def _command_repository(config_file: str) -> PortCommandRepository:
        return PortCommandRepositoryYaml(filename=config_file)

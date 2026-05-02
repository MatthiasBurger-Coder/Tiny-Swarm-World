from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.parameter_type import ParameterType
from tiny_swarm_world.application.services.commands.command_executer.excecuteable_commands import ExecutableCommandEntity


class PortCommandWorkflow(ABC):
    @abstractmethod
    def build_command_list(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
    ) -> Dict[str, Dict[int, ExecutableCommandEntity]]:
        pass

    @abstractmethod
    async def run_async(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
    ) -> Any:
        pass

    @abstractmethod
    async def run_sync(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
    ) -> Any:
        pass

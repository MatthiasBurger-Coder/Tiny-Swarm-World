from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.inventory import VerificationResult


class PortCommandWorkflow(ABC):
    @abstractmethod
    def build_command_list(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
    ) -> Dict[str, Dict[int, ExecutableCommandEntity]]:
        pass

    @abstractmethod
    async def run_async(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
    ) -> Any:
        pass

    @abstractmethod
    async def run_sync(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
    ) -> Any:
        pass

    @abstractmethod
    def verify_config_contract(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
        target_id: str,
    ) -> VerificationResult:
        pass

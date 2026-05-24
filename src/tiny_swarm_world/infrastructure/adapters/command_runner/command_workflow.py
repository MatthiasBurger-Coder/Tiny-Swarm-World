from typing import Any, Callable, Dict, Optional

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory
from tiny_swarm_world.application.ports.repositories.port_command_repository import PortCommandRepository
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.command_builder import CommandBuilder
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.command.command_entity import CommandCatalogValidationError
from tiny_swarm_world.domain.command.verification_probe import is_probe_allowed_for_workflow
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
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

    def verify_config_contract(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
        target_id: str,
    ) -> VerificationResult:
        try:
            command_list = self.build_command_list(
                config_file,
                parameter,
                workflow_id=workflow_id,
            )
        except (CommandCatalogValidationError, ValueError, TypeError):
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Command verification contract is invalid.",
                evidence={"phase": "pre_apply", "reason": "catalog_validation_failed"},
            )

        mutating_count = 0
        missing_count = 0
        manual_count = 0
        command_backed_count = 0
        unknown_probe_count = 0
        for commands in command_list.values():
            for command in commands.values():
                if not command.mutating:
                    continue
                mutating_count += 1
                if command.verify is None:
                    missing_count += 1
                elif command.verify.is_manual_only:
                    manual_count += 1
                elif command.verify.is_command_backed:
                    probe_id = command.verify.command or ""
                    if is_probe_allowed_for_workflow(probe_id, workflow_id):
                        command_backed_count += 1
                    else:
                        unknown_probe_count += 1
                else:
                    missing_count += 1

        if mutating_count == 0:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.VERIFIED,
                message="Command catalog contains read-only commands only.",
                evidence={"phase": "pre_apply", "mutating_count": "0"},
            )

        if unknown_probe_count:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Command-backed verification probe is not registered.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "verification_probe_not_registered",
                    "mutating_count": str(mutating_count),
                    "unknown_probe_count": str(unknown_probe_count),
                },
            )

        if missing_count or manual_count:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Command-backed verification is not configured.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "command_backed_verification_missing",
                    "mutating_count": str(mutating_count),
                    "manual_verify_count": str(manual_count),
                    "missing_verify_count": str(missing_count),
                },
            )

        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.VERIFIED,
            message="Command-backed verification contract is configured.",
            evidence={
                "phase": "pre_apply",
                "mutating_count": str(mutating_count),
                "command_backed_verify_count": str(command_backed_count),
            },
        )

    @staticmethod
    def _command_repository(config_file: str) -> PortCommandRepository:
        return PortCommandRepositoryYaml(filename=config_file)

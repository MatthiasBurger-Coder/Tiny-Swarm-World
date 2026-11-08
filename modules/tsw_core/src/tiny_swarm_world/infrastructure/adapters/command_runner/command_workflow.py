import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.commands.port_command_runner_factory import PortCommandRunnerFactory
from tiny_swarm_world.application.ports.repositories.port_command_repository import PortCommandRepository
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository
from tiny_swarm_world.application.ports.ui.port_ui import PortUI
from tiny_swarm_world.application.services.commands.command_builder.vm_parameter.command_builder import CommandBuilder
from tiny_swarm_world.application.services.commands.command_executer.command_executer import CommandExecuter
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.domain.command.vm_entity import VmEntity
from tiny_swarm_world.domain.command.vm_type import VmType
from tiny_swarm_world.domain.command.verification_probe import is_probe_allowed_for_workflow
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.infrastructure.adapters.command_runner.command_runner_factory import CommandRunnerFactory
from tiny_swarm_world.infrastructure.adapters.repositories.command_repository_yaml import (
    PortCommandRepositoryYaml,
)
from tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui import AsyncCommandRunnerUI
from tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui import SyncCommandRunnerUI
from tiny_swarm_world.infrastructure.adapters.ui.progress_trace_ui import TerminalMethodTrace
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.logging.progress_trace_logging import (
    CompositeMethodTrace,
    LoggingMethodTrace,
)


CommandRepositoryFactory = Callable[[str], PortCommandRepository]


@dataclass(frozen=True)
class _VerificationCounts:
    mutating: int = 0
    missing: int = 0
    manual: int = 0
    command_backed: int = 0
    unknown_probe: int = 0


class CommandWorkflow(PortCommandWorkflow):
    def __init__(
        self,
        command_runner_factory: PortCommandRunnerFactory | None = None,
        vm_repository: PortVmRepository | None = None,
        command_repository_factory: CommandRepositoryFactory | None = None,
    ):
        self.command_runner_factory = command_runner_factory or CommandRunnerFactory()
        self.vm_repository = vm_repository or _EmptyVmRepository()
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
        command_list = self.build_command_list(config_file, parameter, workflow_id=workflow_id)
        runner_ui = AsyncCommandRunnerUI(command_list)
        runner_ui.start()
        command_executor = _build_command_executor(runner_ui.ui)
        results: tuple[object, ...] = ()
        failures: list[BaseException] = []
        try:
            tasks = {
                vm: asyncio.create_task(command_executor.execute(command_list[vm]))
                for vm in runner_ui.instances
            }
            results = tuple(await asyncio.gather(*tasks.values(), return_exceptions=True))
            for vm, result in zip(runner_ui.instances, results):
                if isinstance(result, BaseException):
                    failures.append(result)
                    runner_ui.mark_instance_failed(vm, result)
                else:
                    runner_ui.mark_instance_completed(vm)
        finally:
            runner_ui.finish(failed=bool(failures))
            await runner_ui.wait_until_closed()

        if failures:
            raise failures[0]
        return results

    async def run_sync(
        self,
        config_file: str,
        parameter: Optional[Dict[ParameterType, str]] = None,
        *,
        workflow_id: str,
    ) -> Any:
        command_list = self.build_command_list(config_file, parameter, workflow_id=workflow_id)
        runner_ui = SyncCommandRunnerUI(command_list)
        runner_ui.start()
        command_executor = _build_command_executor(runner_ui.ui)
        failure: BaseException | None = None
        results = []
        try:
            for vm in runner_ui.instances:
                try:
                    result = await command_executor.execute(command_list[vm])
                except Exception as exc:
                    failure = exc
                    runner_ui.mark_instance_failed(vm, exc)
                    break
                else:
                    results.append(result)
                    runner_ui.mark_instance_completed(vm)
        finally:
            runner_ui.finish(failed=failure is not None)
            await runner_ui.wait_until_closed()

        if failure is not None:
            raise failure
        return results

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
        except (TypeError, ValueError):
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Command verification contract is invalid.",
                evidence={"phase": "pre_apply", "reason": "catalog_validation_failed"},
            )

        counts = _verification_counts(command_list, workflow_id)

        if counts.mutating == 0:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.VERIFIED,
                message="Command catalog contains read-only commands only.",
                evidence={"phase": "pre_apply", "mutating_count": "0"},
            )

        if counts.unknown_probe:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Command-backed verification probe is not registered.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "verification_probe_not_registered",
                    "mutating_count": str(counts.mutating),
                    "unknown_probe_count": str(counts.unknown_probe),
                },
            )

        if counts.missing or counts.manual:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Command-backed verification is not configured.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "command_backed_verification_missing",
                    "mutating_count": str(counts.mutating),
                    "manual_verify_count": str(counts.manual),
                    "missing_verify_count": str(counts.missing),
                },
            )

        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.VERIFIED,
            message="Command-backed verification contract is configured.",
            evidence={
                "phase": "pre_apply",
                "mutating_count": str(counts.mutating),
                "command_backed_verify_count": str(counts.command_backed),
            },
        )

    @staticmethod
    def _command_repository(config_file: str) -> PortCommandRepository:
        return PortCommandRepositoryYaml(filename=config_file)


def _verification_counts(
    command_list: Dict[str, Dict[int, ExecutableCommandEntity]],
    workflow_id: str,
) -> _VerificationCounts:
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
            classification = _verification_classification(command, workflow_id)
            if classification == "missing":
                missing_count += 1
            elif classification == "manual":
                manual_count += 1
            elif classification == "command_backed":
                command_backed_count += 1
            else:
                unknown_probe_count += 1
    return _VerificationCounts(
        mutating=mutating_count,
        missing=missing_count,
        manual=manual_count,
        command_backed=command_backed_count,
        unknown_probe=unknown_probe_count,
    )


def _verification_classification(
    command: ExecutableCommandEntity,
    workflow_id: str,
) -> str:
    if command.verify is None:
        return "missing"
    if command.verify.is_manual_only:
        return "manual"
    if not command.verify.is_command_backed:
        return "missing"
    probe_id = command.verify.command or ""
    if is_probe_allowed_for_workflow(probe_id, workflow_id):
        return "command_backed"
    return "unknown_probe"


def _build_command_executor(ui: PortUI) -> CommandExecuter:
    return CommandExecuter(
        ui=ui,
        method_trace=CompositeMethodTrace(
            (
                LoggingMethodTrace(LoggerFactory.get_logger("MethodTrace")),
                TerminalMethodTrace(ui),
            )
        ),
        trace_correlation_id="trace-command-execution",
    )


VM_REPOSITORY_NOT_CONFIGURED = "VM repository is not configured"


class _EmptyVmRepository(PortVmRepository):
    def get_all_vms(self) -> list[VmEntity]:
        return []

    def get_vm_by_name(self, name: str) -> VmEntity | None:
        return None

    def add_vm(self, vm: VmEntity) -> None:
        raise ValueError(VM_REPOSITORY_NOT_CONFIGURED)

    def remove_vm(self, name: str) -> None:
        raise ValueError(VM_REPOSITORY_NOT_CONFIGURED)

    def update_vm(self, vm: VmEntity) -> None:
        raise ValueError(VM_REPOSITORY_NOT_CONFIGURED)

    def find_all_vms(self) -> list[VmEntity]:
        return []

    def find_vm_instances_by_type(self, vm_type: VmType) -> list[str]:
        return []

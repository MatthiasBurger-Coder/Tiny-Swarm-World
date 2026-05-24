import unittest
from dataclasses import dataclass
from typing import Any

from tiny_swarm_world.application.ports.commands.executable_command import (
    ExecutableCommandEntity,
)
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.services.multipass.multipass_init_vms import MultipassInitVms
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


DESTRUCTIVE_CONFIG_FILES = {
    "command_multipass_clean_repository_yaml.yaml",
}
INIT_CONFIG_FILE = "command_multipass_init_repository_yaml.yaml"


class TestMultipassInitVms(unittest.IsolatedAsyncioTestCase):
    async def test_run_does_not_select_destructive_cleanup_yaml(self):
        command_workflow = _RecordingCommandWorkflow()

        await MultipassInitVms(command_workflow).run()

        requested_config_files = [call.config_file for call in command_workflow.async_calls]
        self.assertNotIn(
            "command_multipass_clean_repository_yaml.yaml",
            requested_config_files,
        )
        self.assertFalse(
            _destructive_or_reset_like_config_files(requested_config_files),
            requested_config_files,
        )

    async def test_run_executes_init_repository_once(self):
        command_workflow = _RecordingCommandWorkflow()

        await MultipassInitVms(command_workflow).run()

        requested_config_files = [call.config_file for call in command_workflow.async_calls]
        self.assertEqual(1, requested_config_files.count(INIT_CONFIG_FILE))
        self.assertEqual(
            [CommandWorkflowId.PLATFORM_INIT.value],
            [call.workflow_id for call in command_workflow.async_calls],
        )

    async def test_verify_pre_apply_checks_init_repository_contract(self):
        command_workflow = _RecordingCommandWorkflow()

        result = MultipassInitVms(command_workflow).verify_pre_apply()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(
            [INIT_CONFIG_FILE],
            [call.config_file for call in command_workflow.verify_calls],
        )
        self.assertEqual(
            [CommandWorkflowId.PLATFORM_INIT.value],
            [call.workflow_id for call in command_workflow.verify_calls],
        )

    async def test_post_apply_verify_is_not_a_metadata_only_success(self):
        command_workflow = _RecordingCommandWorkflow()
        service = MultipassInitVms(command_workflow)

        self.assertFalse(callable(getattr(service, "verify", None)))


def _destructive_or_reset_like_config_files(config_files: list[str]) -> list[str]:
    unsafe_terms = ("clean", "delete", "purge", "destroy", "reset")
    return [
        config_file
        for config_file in config_files
        if config_file in DESTRUCTIVE_CONFIG_FILES
        or any(term in config_file.lower() for term in unsafe_terms)
    ]


class _RecordingCommandWorkflow(PortCommandWorkflow):
    def __init__(self) -> None:
        self.async_calls: list[_WorkflowCall] = []
        self.sync_calls: list[_WorkflowCall] = []
        self.build_calls: list[_WorkflowCall] = []
        self.verify_calls: list[_WorkflowCall] = []

    def build_command_list(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
    ) -> dict[str, dict[int, ExecutableCommandEntity]]:
        self.build_calls.append(_WorkflowCall(config_file, parameter, workflow_id))
        return {}

    async def run_async(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
    ) -> Any:
        self.async_calls.append(_WorkflowCall(config_file, parameter, workflow_id))
        return f"ran {config_file}"

    async def run_sync(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
    ) -> Any:
        self.sync_calls.append(_WorkflowCall(config_file, parameter, workflow_id))
        return f"ran {config_file}"

    def verify_config_contract(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
        target_id: str,
    ) -> VerificationResult:
        self.verify_calls.append(_WorkflowCall(config_file, parameter, workflow_id))
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.VERIFIED,
            message="Command-backed verification contract is configured.",
            evidence={"phase": "pre_apply"},
        )


@dataclass(frozen=True)
class _WorkflowCall:
    config_file: str
    parameter: dict[ParameterType, str] | None
    workflow_id: str


if __name__ == "__main__":
    unittest.main()

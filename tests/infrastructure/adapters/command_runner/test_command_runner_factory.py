import asyncio
import unittest

from tiny_swarm_world.domain.command.command_entity import (
    CommandEffect,
    CommandEntity,
    CommandSafetyClass,
    CommandScope,
    CommandVerifySpec,
    CommandVerifyType,
    CommandWorkflowId,
    CommandExecutionMode,
)
from tiny_swarm_world.domain.command.command_runner_type_enum import CommandRunnerType
from tiny_swarm_world.domain.command.command_type_enum import CommandType
from tiny_swarm_world.domain.command.vm_type import VmType
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import (
    CommandWorkflow,
)
from tiny_swarm_world.infrastructure.adapters.command_runner.ansible_runner import (
    AnsiblePortCommandRunner,
)
from tiny_swarm_world.infrastructure.adapters.command_runner.async_command_runner import (
    AsyncPortCommandRunner,
)
from tiny_swarm_world.infrastructure.adapters.command_runner.command_runner_factory import (
    CommandRunnerFactory,
)
from tiny_swarm_world.infrastructure.adapters.command_runner.rest_api_runner import (
    RestApiPortCommandRunner,
)


class TestCommandRunnerFactory(unittest.TestCase):
    def test_factory_selects_only_async_runner_for_active_workflows(self):
        runner = CommandRunnerFactory().get_runner(CommandRunnerType.ASYNC)

        self.assertIsInstance(runner, AsyncPortCommandRunner)

    def test_factory_rejects_ansible_and_rest_runner_types(self):
        factory = CommandRunnerFactory()

        for runner_type in (CommandRunnerType.ANSIBLE, CommandRunnerType.REST):
            with self.subTest(runner_type=runner_type):
                with self.assertRaisesRegex(ValueError, "Only the async shell command runner"):
                    factory.get_runner(runner_type)

    def test_placeholder_runners_fail_closed_when_instantiated_directly(self):
        for runner in (AnsiblePortCommandRunner(), RestApiPortCommandRunner()):
            with self.subTest(runner=runner.__class__.__name__):
                with self.assertRaises(NotImplementedError):
                    asyncio.run(runner.run("echo unsafe"))
                self.assertEqual("Unsupported", runner.status["result"])

    def test_verify_config_contract_blocks_unsupported_runner_types(self):
        workflow = CommandWorkflow(command_repository_factory=lambda _: _FakeCommandRepository("rest"))

        result = workflow.verify_config_contract(
            "synthetic.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            target_id="commands:synthetic",
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("catalog_validation_failed", result.evidence["reason"])


class _FakeCommandRepository:
    def __init__(self, runner: str):
        self.runner = runner

    def get_all_commands(self):
        return {
            1: CommandEntity(
                id="synthetic.command",
                index=1,
                description="Synthetic command",
                intent="verify unsupported runner handling",
                execution_mode=CommandExecutionMode.SHELL,
                safety_class=CommandSafetyClass.SAFE_READ,
                scope=CommandScope.HOST,
                allowed_workflows=[CommandWorkflowId.PLATFORM_INIT.value],
                parameters=[],
                effects=[CommandEffect.READ.value],
                verify=CommandVerifySpec(
                    type=CommandVerifyType.NONE,
                    description="Read-only command.",
                ),
                command="echo ok",
                runner=self.runner,
                command_type=CommandType.HOSTOS,
                vm_type=[VmType.NONE],
            )
        }


if __name__ == "__main__":
    unittest.main()

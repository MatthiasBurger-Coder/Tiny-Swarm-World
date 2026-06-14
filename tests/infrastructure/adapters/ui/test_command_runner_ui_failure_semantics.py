import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from tests.support.async_helpers import async_checkpoint
from tests.support.sonar_safe_literals import ipv4_address

from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    STATUS_FAILED_TO_VERIFY,
    STATUS_ERROR,
    STATUS_SUCCESS,
    PortUI,
)
from tiny_swarm_world.application.services.commands.command_executer.command_executer import (
    CommandExecuter,
    CommandExecutionFailed,
)
from tiny_swarm_world.application.ports.commands.executable_command import (
    ExecutableCommandEntity,
)
from tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui import AsyncCommandRunnerUI
from tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui import SyncCommandRunnerUI
from tiny_swarm_world.infrastructure.adapters.exceptions.exception_command_execution import (
    CommandExecutionError,
)


class TestCommandRunnerUiFailureSemantics(unittest.IsolatedAsyncioTestCase):
    async def test_async_ui_marks_aggregate_error_and_raises_on_command_failure(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = AsyncCommandRunnerUI(
                _command_list(FailingRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await _assert_redacted_runner_ui_failure(runner_ui)

        self.assertIn(("swarm-manager", "failed", "execution", STATUS_ERROR), ui.updates)
        self.assertIn((AGGREGATE_INSTANCE, "finished", "execution", STATUS_ERROR), ui.updates)
        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])

    async def test_sync_ui_marks_aggregate_error_and_raises_on_command_failure(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = SyncCommandRunnerUI(
                _command_list(FailingRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await _assert_redacted_runner_ui_failure(runner_ui)

        self.assertIn(("swarm-manager", "failed", "execution", STATUS_ERROR), ui.updates)
        self.assertIn((AGGREGATE_INSTANCE, "finished", "execution", STATUS_ERROR), ui.updates)
        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])

    async def test_async_ui_redacts_arbitrary_runner_exception_text(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = AsyncCommandRunnerUI(
                _command_list(SensitiveRuntimeFailureRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await _assert_arbitrary_runner_ui_failure_redacted(runner_ui)

        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])

    async def test_sync_ui_redacts_arbitrary_runner_exception_text(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = SyncCommandRunnerUI(
                _command_list(SensitiveRuntimeFailureRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await _assert_arbitrary_runner_ui_failure_redacted(runner_ui)

        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])

    async def test_sync_ui_aggregate_failure_is_terminal_with_pending_later_instances(self):
        ui = RecordingUI(["swarm-manager", "swarm-worker"])

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = SyncCommandRunnerUI(
                {
                    "swarm-manager": _commands_for("swarm-manager", FailingRunner()),
                    "swarm-worker": _commands_for("swarm-worker", SuccessfulRunner()),
                },
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await _assert_redacted_runner_ui_failure(runner_ui)

        self.assertEqual("Pending", ui.status["swarm-worker"]["result"])
        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])
        self.assertTrue(ui.all_instances_terminal())

    async def test_async_ui_marks_aggregate_success_when_commands_succeed(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = AsyncCommandRunnerUI(
                _command_list(SuccessfulRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await runner_ui.run()

        self.assertIn(("swarm-manager", "completed", "execution", STATUS_SUCCESS), ui.updates)
        self.assertIn((AGGREGATE_INSTANCE, "finished", "execution", STATUS_SUCCESS), ui.updates)
        self.assertEqual(STATUS_SUCCESS, ui.aggregate_status["result"])

    async def test_sync_ui_marks_aggregate_success_when_commands_succeed(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = SyncCommandRunnerUI(
                _command_list(SuccessfulRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await runner_ui.run()

        self.assertIn(("swarm-manager", "completed", "execution", STATUS_SUCCESS), ui.updates)
        self.assertIn((AGGREGATE_INSTANCE, "finished", "execution", STATUS_SUCCESS), ui.updates)
        self.assertEqual(STATUS_SUCCESS, ui.aggregate_status["result"])

    async def test_async_ui_preserves_status_only_failure_as_aggregate_error(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = AsyncCommandRunnerUI(
                _command_list(StatusOnlyFailureRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await runner_ui.run()

        self.assertEqual(STATUS_FAILED_TO_VERIFY, ui.status["swarm-manager"]["result"])
        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])
        self.assertNotIn(("swarm-manager", "completed", "execution", STATUS_SUCCESS), ui.updates)

    async def test_sync_ui_preserves_status_only_failure_as_aggregate_error(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = SyncCommandRunnerUI(
                _command_list(StatusOnlyFailureRunner()),
                command_executor_factory=_command_executor_factory,
            )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            await runner_ui.run()

        self.assertEqual(STATUS_FAILED_TO_VERIFY, ui.status["swarm-manager"]["result"])
        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])
        self.assertNotIn(("swarm-manager", "completed", "execution", STATUS_SUCCESS), ui.updates)


def _command_list(runner: PortCommandRunner):
    return {
        "swarm-manager": _commands_for("swarm-manager", runner)
    }


def _command_executor_factory(ui: PortUI) -> CommandExecuter:
    return CommandExecuter(ui=ui)


def _commands_for(vm_instance_name: str, runner: PortCommandRunner):
    return {
        1: ExecutableCommandEntity(
            index=1,
            vm_instance_name=vm_instance_name,
            description="command",
            command="exit 1",
            runner=runner,
        )
    }


class FailingRunner(PortCommandRunner):
    async def run(self, command: str) -> str:
        await async_checkpoint()
        raise CommandExecutionError(
            command=command,
            return_code=2,
            stdout="raw vm output",
            stderr="cannot connect to the provider socket",
        )


class SuccessfulRunner(PortCommandRunner):
    async def run(self, command: str) -> str:
        await async_checkpoint()
        self.status["current_step"] = "Completed"
        self.status["result"] = STATUS_SUCCESS
        return "ok"


class StatusOnlyFailureRunner(PortCommandRunner):
    async def run(self, command: str) -> str:
        await async_checkpoint()
        self.status["current_step"] = "Verified"
        self.status["result"] = STATUS_FAILED_TO_VERIFY
        return "blocked"


class SensitiveRuntimeFailureRunner(PortCommandRunner):
    async def run(self, command: str) -> str:
        await async_checkpoint()
        raise RuntimeError(
            "raw runtime failure token stdout /home/operator 192.168.1.10"
        )


class RecordingUI(PortUI):
    def __init__(self, instances=None):
        super().__init__(instances or ["swarm-manager"], test_mode=True)
        self.updates = []
        self.ui_thread = None

    def start_in_thread(self):
        loop = asyncio.get_running_loop()
        self.ui_thread = loop.create_future()
        self.ui_thread.set_result(None)

    def update_status(self, instance, task, step, result=None):
        super().update_status(instance, task, step, result)
        self.updates.append(
            (
                instance,
                task,
                step,
                self._status_for_instance(instance)["result"],
            )
        )

    def start(self):
        # Test double; the UI event loop is driven directly by the test.
        pass


async def _assert_redacted_runner_ui_failure(runner_ui):
    with patch.object(runner_ui.command_execute.logger, "error") as command_error:
        with patch.object(runner_ui.logger, "error") as ui_error:
            with unittest.TestCase().assertRaises(CommandExecutionFailed) as context:
                await runner_ui.run()

    text = " ".join(
        str(call.args)
        for call in (*command_error.call_args_list, *ui_error.call_args_list)
    )
    text = f"{text} {context.exception}"
    unittest.TestCase().assertIn("return code 2", text)
    unittest.TestCase().assertNotIn("cannot connect to the provider socket", text)
    unittest.TestCase().assertNotIn("raw vm output", text)
    unittest.TestCase().assertNotIn("incus info", text)


async def _assert_arbitrary_runner_ui_failure_redacted(runner_ui):
    with patch.object(runner_ui.command_execute.logger, "error") as command_error:
        with patch.object(runner_ui.logger, "error") as ui_error:
            with unittest.TestCase().assertRaises(CommandExecutionFailed) as context:
                await runner_ui.run()

    text = " ".join(
        str(value)
        for value in (
            command_error.call_args_list,
            ui_error.call_args_list,
            context.exception,
            runner_ui.ui.updates,
        )
    )
    unittest.TestCase().assertIn("RuntimeError", text)
    unittest.TestCase().assertIn("Diagnostic payload redacted", text)
    unittest.TestCase().assertNotIn("token", text)
    unittest.TestCase().assertNotIn("stdout", text)
    unittest.TestCase().assertNotIn("/home/operator", text)
    unittest.TestCase().assertNotIn(ipv4_address(192, 168, 1, 10), text)
    unittest.TestCase().assertNotIn("raw runtime failure", text)
    unittest.TestCase().assertNotIn("exit 1", text)

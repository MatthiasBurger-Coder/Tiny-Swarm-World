import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner
from tiny_swarm_world.application.services.commands.command_executer.command_executer import (
    CommandExecutionFailed,
)
from tiny_swarm_world.application.ports.commands.executable_command import (
    ExecutableCommandEntity,
)
from tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui import AsyncCommandRunnerUI
from tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui import SyncCommandRunnerUI


class TestCommandRunnerUiFailureSemantics(unittest.IsolatedAsyncioTestCase):
    async def test_async_ui_marks_aggregate_error_and_raises_on_command_failure(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_async_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = AsyncCommandRunnerUI(_command_list(FailingRunner()))

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            with self.assertRaises(CommandExecutionFailed):
                await runner_ui.run()

        self.assertIn(("swarm-manager", "failed", "execution", "error"), ui.updates)
        self.assertIn(("all", "finished", "execution", "error"), ui.updates)

    async def test_sync_ui_marks_aggregate_error_and_raises_on_command_failure(self):
        ui = RecordingUI()

        with patch(
            "tiny_swarm_world.infrastructure.adapters.ui.command_sync_runner_ui.FactoryUI"
        ) as factory:
            factory.return_value.get_ui.return_value = ui
            runner_ui = SyncCommandRunnerUI(_command_list(FailingRunner()))

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            with self.assertRaises(CommandExecutionFailed):
                await runner_ui.run()

        self.assertIn(("swarm-manager", "failed", "execution", "error"), ui.updates)
        self.assertIn(("all", "finished", "execution", "error"), ui.updates)


def _command_list(runner: PortCommandRunner):
    return {
        "swarm-manager": {
            1: ExecutableCommandEntity(
                index=1,
                vm_instance_name="swarm-manager",
                description="failing command",
                command="exit 1",
                runner=runner,
            )
        }
    }


class FailingRunner(PortCommandRunner):
    async def run(self, command: str) -> str:
        raise RuntimeError("boom")


class RecordingUI:
    def __init__(self):
        self.updates = []
        self.ui_thread = None

    def start_in_thread(self):
        loop = asyncio.get_running_loop()
        self.ui_thread = loop.create_future()
        self.ui_thread.set_result(None)

    def update_status(self, instance, task, step, result=None):
        self.updates.append((instance, task, step, result))

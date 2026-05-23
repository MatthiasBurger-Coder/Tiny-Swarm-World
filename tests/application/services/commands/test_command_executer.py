import unittest
from unittest.mock import AsyncMock, patch

from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner
from tiny_swarm_world.application.services.commands.command_executer.command_executer import (
    CommandExecuter,
    CommandExecutionFailed,
)
from tiny_swarm_world.application.ports.commands.executable_command import (
    ExecutableCommandEntity,
)


class TestCommandExecuter(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_results_when_commands_succeed(self):
        ui = RecordingUI()
        executer = CommandExecuter(ui=ui)
        command = ExecutableCommandEntity(
            index=1,
            vm_instance_name="swarm-manager",
            description="successful command",
            command="echo ok",
            runner=SuccessfulRunner(),
        )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            result = await executer.execute({1: command})

        self.assertEqual({1: "ok"}, result)
        self.assertIn(
            ("swarm-manager", "successful command", "Completed", "Success"),
            ui.updates,
        )
        self.assertIn(
            ("swarm-manager", "closing", "Finishing", "Success"),
            ui.updates,
        )

    async def test_execute_raises_when_runner_fails(self):
        ui = RecordingUI()
        executer = CommandExecuter(ui=ui)
        command = ExecutableCommandEntity(
            index=1,
            vm_instance_name="swarm-manager",
            description="failing command",
            command="exit 1",
            runner=FailingRunner(),
        )

        with patch(
            "tiny_swarm_world.application.services.commands.command_executer.command_executer.asyncio.sleep",
            new=AsyncMock(),
        ):
            with self.assertRaises(CommandExecutionFailed):
                await executer.execute({1: command})

        self.assertIn(
            ("swarm-manager", "failing command", "Error", "Failed"),
            ui.updates,
        )
        self.assertNotIn(
            ("swarm-manager", "closing", "Finishing", "Success"),
            ui.updates,
        )

    async def test_execute_raises_when_command_is_incomplete(self):
        ui = RecordingUI()
        executer = CommandExecuter(ui=ui)
        command = ExecutableCommandEntity(
            index=1,
            vm_instance_name="swarm-manager",
            description="incomplete command",
            command=None,
            runner=SuccessfulRunner(),
        )

        with self.assertRaises(CommandExecutionFailed):
            await executer.execute({1: command})

        self.assertIn(
            ("swarm-manager", "incomplete command", "Error", "Failed"),
            ui.updates,
        )


class SuccessfulRunner(PortCommandRunner):
    async def run(self, command: str) -> str:
        self.status["current_step"] = "Completed"
        self.status["result"] = "Success"
        return "ok"


class FailingRunner(PortCommandRunner):
    async def run(self, command: str) -> str:
        raise RuntimeError("boom")


class RecordingUI:
    def __init__(self):
        self.updates = []

    def update_status(self, instance, task, step, result=None):
        self.updates.append((instance, task, step, result))

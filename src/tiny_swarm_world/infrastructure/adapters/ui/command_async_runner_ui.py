from typing import Dict

from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    STATUS_ERROR,
    STATUS_SUCCESS,
)
from tiny_swarm_world.infrastructure.adapters.ui.command_runner_ui import CommandRunnerUi
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.adapters.ui.factory_ui import FactoryUI


class AsyncCommandRunnerUI(CommandRunnerUi):
    """
    Handles the UI initialization and asynchronous execution of commands.
    """

    def __init__(
        self,
        command_list: Dict[str, Dict[int, ExecutableCommandEntity]],
    ):
        """
        Initializes the UI and command execution logic.

        :param command_list: Dictionary mapping instances to their respective command entities.
        """

        self.command_list = command_list
        self.instances = list(command_list.keys())
        self.ui = FactoryUI().get_ui(instances=self.instances, test_mode=False)
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.logger.info(f"CommandRunnerUI initialized {self.instances} instances")

    async def run(self):
        """
        Starts the UI session without owning command execution.
        """
        self.start()
        await self.wait_until_closed()

    def start(self) -> None:
        self.logger.info("start ui")
        self.ui.start_in_thread()

    def mark_instance_failed(self, vm: str, result: BaseException) -> None:
        self.logger.error(f"Execution failed for {vm}: {result}")
        self.ui.update_status(task="failed", step="execution", result=STATUS_ERROR, instance=vm)

    def mark_instance_completed(self, vm: str) -> None:
        self.logger.info(f"Execution successful for {vm}")
        self.ui.update_status(task="completed", step="execution", result=STATUS_SUCCESS, instance=vm)

    def finish(self, *, failed: bool) -> None:
        final_result = STATUS_ERROR if failed else STATUS_SUCCESS
        self.ui.update_status(
            task="finished",
            step="execution",
            result=final_result,
            instance=AGGREGATE_INSTANCE,
        )

    async def wait_until_closed(self) -> None:
        if self.ui.ui_thread is not None:
            self.logger.info("Waiting for UI thread to close...")
            await self.ui.ui_thread
        self.logger.info("Execution complete.")

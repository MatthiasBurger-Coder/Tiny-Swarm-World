import asyncio
from collections.abc import Sequence
from typing import Dict

from tiny_swarm_world.application.services.commands.command_executer.command_executer import CommandExecuter
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.infrastructure.adapters.ui.command_runner_ui import CommandRunnerUi
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.adapters.ui.factory_ui import FactoryUI

class AsyncCommandRunnerUI(CommandRunnerUi):
    """
    Handles the UI initialization and asynchronous execution of commands.
    """

    def __init__(self, command_list: Dict[str, Dict[int, ExecutableCommandEntity]]):
        """
        Initializes the UI and command execution logic.

        :param command_list: Dictionary mapping instances to their respective command entities.
        """

        self.command_list = command_list
        self.instances = list(command_list.keys())
        self.ui = FactoryUI().get_ui(instances=self.instances, test_mode=False)
        self.command_execute = CommandExecuter(ui=self.ui)
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.logger.info(f"CommandRunnerUI initialized {self.instances} instances")

    async def run(self):
        """
        Runs the UI and executes commands asynchronously.
        """
        # Start the UI in a separate thread
        self.logger.info("start ui")
        self.ui.start_in_thread()
        results: Sequence[object] = ()
        failures: list[BaseException] = []

        try:
            # Starte die parallele Ausführung der Befehle für jede VM
            tasks = {
                vm: asyncio.create_task(self.command_execute.execute(self.command_list[vm]))
                for vm in self.instances
            }

            # Warte darauf, dass alle VMs abgeschlossen sind und sammle Ergebnisse
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            # Fehlerhandling für einzelne VMs
            for vm, result in zip(self.instances, results):
                if isinstance(result, Exception):
                    failures.append(result)
                    self.logger.error(f"Execution failed for {vm}: {result}")
                    self.ui.update_status(task="failed", step="execution", result="error", instance=vm)
                else:
                    self.logger.info(f"Execution successful for {vm}")
                    self.ui.update_status(task="completed", step="execution", result="success", instance=vm)

        finally:
            # Aktualisiere die UI mit Abschlussstatus
            final_result = "error" if failures else "success"
            self.ui.update_status(task="finished", step="execution", result=final_result, instance="all")

            # Warte auf das Ende des UI-Threads
            self.logger.info("Waiting for UI thread to close...")
            await self.ui.ui_thread

            self.logger.info("Execution complete.")

        if failures:
            raise failures[0]

        return results

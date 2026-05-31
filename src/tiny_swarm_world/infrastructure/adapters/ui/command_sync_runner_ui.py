from typing import Dict

from tiny_swarm_world.application.services.commands.command_executer.command_executer import CommandExecuter
from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    STATUS_ERROR,
    STATUS_SUCCESS,
    PortUI,
)
from tiny_swarm_world.infrastructure.adapters.ui.command_runner_ui import CommandRunnerUi
from tiny_swarm_world.infrastructure.adapters.ui.progress_trace_ui import TerminalMethodTrace
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.logging.progress_trace_logging import (
    CompositeMethodTrace,
    LoggingMethodTrace,
)
from tiny_swarm_world.infrastructure.adapters.ui.factory_ui import FactoryUI

class SyncCommandRunnerUI(CommandRunnerUi):
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
        self.command_execute = CommandExecuter(
            ui=self.ui,
            method_trace=_build_command_method_trace(self.ui),
            trace_correlation_id="trace-command-execution",
        )
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.logger.info(f"CommandRunnerUI initialized {self.instances} instances")

    async def run(self):
        """
        Runs the UI and executes commands asynchronously.
        """
        # Start the UI in a separate thread
        self.logger.info("start ui")
        self.ui.start_in_thread()
        failure: BaseException | None = None
        results = []

        try:
            # Starte die parallele Ausführung der Befehle für jede VM
            for vm in self.instances:
                try:
                    result = await self.command_execute.execute(self.command_list[vm])
                except Exception as exc:
                    failure = exc
                    self.logger.error(f"Execution failed for {vm}: {exc}")
                    self.ui.update_status(task="failed", step="execution", result=STATUS_ERROR, instance=vm)
                    break
                else:
                    results.append(result)
                    self.logger.info(f"Execution successful for {vm}")
                    self.ui.update_status(task="completed", step="execution", result=STATUS_SUCCESS, instance=vm)

        finally:
            # Aktualisiere die UI mit Abschlussstatus
            final_result = STATUS_ERROR if failure else STATUS_SUCCESS
            self.ui.update_status(
                task="finished",
                step="execution",
                result=final_result,
                instance=AGGREGATE_INSTANCE,
            )

            # Warte auf das Ende des UI-Threads
            self.logger.info("Waiting for UI thread to close...")
            await self.ui.ui_thread

            self.logger.info("Execution complete.")

        if failure:
            raise failure

        return results


def _build_command_method_trace(ui: PortUI) -> CompositeMethodTrace:
    return CompositeMethodTrace(
        (
            LoggingMethodTrace(LoggerFactory.get_logger("MethodTrace")),
            TerminalMethodTrace(ui),
        )
    )

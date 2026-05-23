import logging
from typing import Dict

import asyncio

from tiny_swarm_world.application.ports.commands.executable_command import ExecutableCommandEntity
from tiny_swarm_world.application.ports.ui.port_ui import PortUI


class CommandExecuter:
    executable_commands: Dict[str, Dict[int, ExecutableCommandEntity]]

    def __init__(self, ui: PortUI):
        self.ui = ui
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, commands: dict[int, ExecutableCommandEntity]):
        self.logger.info("Command execution started with %d commands.", len(commands))
        current_vm = None
        run_result: dict[int, str] = {}
        for key, executable_command in commands.items():
            current_vm = executable_command.vm_instance_name
            self.logger.info("Executing command on VM '%s' with task: '%s'.", current_vm,
                             executable_command.description)
            try:
                self.logger.info("Before runner '%s'.", current_vm)
                if executable_command.runner is None or executable_command.command is None:
                    raise ValueError("Executable command is missing runner or command text")
                run_result[key] = await executable_command.runner.run(executable_command.command)
                self.logger.info("Command executed successfully on VM '%s'.", current_vm)

            except Exception as e:
                self.logger.error("Failed to execute command on VM '%s'. Error: %s", current_vm, str(e))
                self.ui.update_status(instance=current_vm, task=executable_command.description, step="Error",
                                      result="Failed")
                raise CommandExecutionFailed(
                    f"Failed to execute command {key} on VM '{current_vm}': {e}"
                ) from e

            self.logger.info("Updating status for VM '%s'.", current_vm)
            runner_status = executable_command.runner.status
            self.ui.update_status(instance=current_vm,
                                  task=executable_command.description,
                                  step=runner_status["current_step"],
                                  result=runner_status["result"])
            self.logger.info("Status updated for VM '%s': step='%s', result='%s'.", current_vm,
                             runner_status["current_step"], runner_status["result"])

            await asyncio.sleep(2)

        if current_vm is not None:
            self.ui.update_status(instance=current_vm, task="closing", step="Finishing", result="Success")
            await asyncio.sleep(2)
        self.logger.info("All commands executed. Final status updated.")
        return run_result


class CommandExecutionFailed(RuntimeError):
    """Raised when a command workflow step fails and execution must stop."""

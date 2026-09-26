import asyncio

from tiny_swarm_world.application.ports.commands.port_command_runner import CommandExecutionError
from tiny_swarm_world.application.ports.operation_result import OperationFailure
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner
from tiny_swarm_world.infrastructure.process.async_runner import run_async_process


class AsyncPortCommandRunner(PortCommandRunner):
    """Map shared process outcomes to the command application port."""

    def __init__(self):
        super().__init__()
        self.lock = asyncio.Lock()
        self.status = {"current_step": "Not started", "result": "Pending"}
        self.logger = LoggerFactory.get_logger(self.__class__)

    async def run(self, command: str, timeout: int = 900) -> str:
        async with self.lock:
            self.status.update(current_step="Executing command", result="Running...")
        try:
            result = await run_async_process(command, timeout=timeout, shell=True)
            if result.returncode != 0 or result.timed_out or result.failure_hint:
                raise CommandExecutionError(
                    command, -1 if result.timed_out or result.failure_hint else result.returncode,
                    result.stdout, result.stderr or "Process execution failed.",
                    failure=OperationFailure.for_cause(
                        "command.execute", "command_runner",
                        "process_timeout" if result.timed_out else (result.failure_hint or "process_exit_failed"),
                    ),
                )
        except asyncio.CancelledError:
            async with self.lock:
                self.status["result"] = "Error"
            raise
        except CommandExecutionError:
            async with self.lock:
                self.status["result"] = "Error"
            raise
        except Exception:
            async with self.lock:
                self.status["result"] = "Error"
            self.logger.error("Command execution failed; diagnostic payload redacted.")
            raise CommandExecutionError(
                command, -1, "", "Process execution failed.",
                failure=OperationFailure.for_cause(
                    "command.execute", "command_runner", "unexpected_failure",
                ),
            ) from None
        async with self.lock:
            self.status["result"] = "Success"
        self.logger.info("Command completed successfully")
        return result.stdout.strip()

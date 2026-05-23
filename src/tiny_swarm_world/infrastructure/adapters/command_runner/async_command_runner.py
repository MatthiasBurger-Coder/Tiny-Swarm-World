import asyncio
import inspect
from contextlib import suppress
from typing import Any, cast

from tiny_swarm_world.infrastructure.adapters.exceptions.exception_command_execution import CommandExecutionError
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner


class AsyncPortCommandRunner(PortCommandRunner):
    """
    A class for asynchronously running shell commands and handling their outputs and errors.
    """

    def __init__(self):
        super().__init__()
        # Use asyncio.Lock for asynchronous operations
        self.lock = asyncio.Lock()
        # Initialize status as a dictionary (if not already handled in the base class)
        self.status = {"current_step": "Not started", "result": "Pending"}  # Default status
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.logger.info("AsyncCommandRunner initialized")

    async def run(self, command: str, timeout: int = 120) -> str:
        self.logger.info("Starting subprocess")
        process = None
        communicate_task = None
        try:
            # Update status
            async with self.lock:
                self.status["current_step"] = "Executing command"
                self.status["result"] = "Running..."

            # Start subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.logger.info("Finishing subprocess")
            # Wait for subprocess to complete
            communicate_task = asyncio.create_task(process.communicate())
            stdout, stderr = await asyncio.wait_for(communicate_task, timeout=timeout)
            self.logger.info("Command produced stdout (%d bytes).", len(stdout))

            # Check process return code
            return_code = process.returncode if process.returncode is not None else -1
            if return_code != 0:
                error_message = stderr.decode('utf-8').strip()  # Read error from stderr
                self.logger.error(
                    "Command failed with return code %s; stderr redacted (%d bytes).",
                    return_code,
                    len(stderr),
                )
                async with self.lock:
                    self.status["result"] = "Error"
                raise CommandExecutionError(
                    command=command,
                    return_code=return_code,
                    stdout=stdout.decode('utf-8').strip(),
                    stderr=error_message
                )

            # Update status as successful
            async with self.lock:
                self.status["result"] = "Success"
            self.logger.info("Command completed successfully")

            return stdout.decode('utf-8').strip()

        except asyncio.TimeoutError:
            # Log timeout error
            async with self.lock:
                self.status["result"] = "Error"
            self.logger.error(f"Command timed out after {timeout} seconds")
            if communicate_task is not None:
                communicate_task.cancel()
                with suppress(asyncio.CancelledError):
                    await communicate_task
            if process is not None:
                kill_result = cast(Any, process).kill()
                if inspect.isawaitable(kill_result):
                    await kill_result
                await process.communicate()
            raise CommandExecutionError(
                command=command,
                return_code=-1,  # -1 = Special return code for timeout
                stdout="",
                stderr=f"Command timed out after {timeout} seconds."
            )

        except CommandExecutionError:
            raise

        except Exception as e:
            # Log unexpected errors
            self.logger.exception("An unexpected error occurred while executing the command")
            async with self.lock:
                self.status["result"] = "Error"
            raise CommandExecutionError(
                command=command,
                return_code=-1,  # -1 = Special return code for unexpected errors
                stdout="",
                stderr=f"An unexpected error occurred: {str(e)}"
            ) from e

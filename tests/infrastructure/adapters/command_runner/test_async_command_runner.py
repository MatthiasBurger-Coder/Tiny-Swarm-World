import subprocess
import unittest
from inspect import signature
from asyncio import TimeoutError, Lock
from unittest.mock import AsyncMock, MagicMock, patch

from tiny_swarm_world.infrastructure.adapters.command_runner.async_command_runner import AsyncPortCommandRunner
from tiny_swarm_world.infrastructure.adapters.exceptions.exception_command_execution import CommandExecutionError


class TestAsyncCommandRunner(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.command_runner = AsyncPortCommandRunner()

    def test_default_timeout_allows_infrastructure_bootstrap(self):
        self.assertEqual(900, signature(self.command_runner.run).parameters["timeout"].default)

    @patch('subprocess.run')
    def test_run_successful_command(self, mock_run):
        # Create a mock return value that mimics the `subprocess.run` result
        mock_run.return_value = MagicMock(
            stdout=b"Hello, World!\n",
            stderr=b"",
            returncode=0
        )

        # Example command for testing
        command = ["echo", "Hello, World!"]

        # Code under test
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.stdout, b"Hello, World!\n")


    @patch("asyncio.create_subprocess_shell")
    async def test_run_command_execution_error(self, mock_subprocess):
        command = "exit 1"
        stdout_output = b""
        stderr_output = b"Error occurred"

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (stdout_output, stderr_output)
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        with self.assertRaises(CommandExecutionError) as context:
            await self.command_runner.run(command)

        self.assertIn("return code 1", str(context.exception))
        self.assertNotIn(command, str(context.exception))
        self.assertNotIn("Error occurred", str(context.exception))
        self.assertEqual(context.exception.stdout, "")
        self.assertEqual("<redacted>", context.exception.stderr)

    @patch("asyncio.wait_for", side_effect=TimeoutError())
    @patch("asyncio.create_subprocess_shell")
    async def test_run_asyncio_timeout(self, mock_subprocess,mock_wait_for):
        command = "sleep 10"
        timeout = 1

        mock_process = AsyncMock()
        mock_process.pid = 1234
        mock_process.returncode = 0  # Simulate timeout during execution
        mock_process.wait = AsyncMock()
        mock_subprocess.return_value = mock_process

        with patch(
            "tiny_swarm_world.infrastructure.adapters.command_runner.async_command_runner.os.getpgid",
            return_value=1234,
        ):
            with patch(
                "tiny_swarm_world.infrastructure.adapters.command_runner.async_command_runner.os.killpg"
            ) as mock_killpg:
                with self.assertRaises(CommandExecutionError) as context:
                    await self.command_runner.run(command, timeout=timeout)

        self.assertIn("return code -1", str(context.exception))
        self.assertNotIn(command, str(context.exception))
        self.assertGreaterEqual(mock_wait_for.call_count, 1)
        self.assertGreaterEqual(mock_killpg.call_count, 1)
        self.assertTrue(mock_subprocess.call_args.kwargs["start_new_session"])

    @patch("asyncio.create_subprocess_shell")
    async def test_run_unexpected_error(self, mock_subprocess):
        command = "invalid command"

        mock_subprocess.side_effect = Exception("Unexpected error")

        with self.assertRaises(CommandExecutionError) as context:
            await self.command_runner.run(command)

        self.assertIn("return code -1", str(context.exception))
        self.assertNotIn("Unexpected error", str(context.exception))

    def test_lock_initialization(self):
        self.assertIsInstance(self.command_runner.lock, Lock)

    @patch("asyncio.create_subprocess_shell")
    async def test_run_does_not_log_raw_command(self, mock_subprocess):
        secret_command = "docker swarm join --token secret-token 10.0.0.1:2377"
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"ok", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        with patch.object(self.command_runner.logger, "info") as log_info:
            await self.command_runner.run(secret_command)

        self.assertTrue(mock_subprocess.call_args.kwargs["start_new_session"])
        logged_messages = [str(call.args[0]) for call in log_info.call_args_list if call.args]
        self.assertFalse(
            any(secret_command in message for message in logged_messages),
            logged_messages,
        )

    @patch("asyncio.create_subprocess_shell")
    async def test_run_does_not_log_raw_stdout_or_stderr(self, mock_subprocess):
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"secret stdout", b"secret stderr")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        with patch.object(self.command_runner.logger, "info") as log_info:
            with patch.object(self.command_runner.logger, "error") as log_error:
                with self.assertRaises(CommandExecutionError):
                    await self.command_runner.run("exit 1")

        logged_messages = [
            str(call.args[0])
            for call in (*log_info.call_args_list, *log_error.call_args_list)
            if call.args
        ]
        self.assertFalse(any("secret stdout" in message for message in logged_messages))
        self.assertFalse(any("secret stderr" in message for message in logged_messages))

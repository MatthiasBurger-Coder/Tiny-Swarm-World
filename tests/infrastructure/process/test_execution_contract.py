"""Outcome, secrecy and lifecycle contracts for the shared process boundary."""

import asyncio
import signal
import subprocess
import traceback
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from tiny_swarm_world.infrastructure.process.async_runner import (
    run_async_process, terminate_async_process,
)
from tiny_swarm_world.infrastructure.process.runner import (
    ProcessLaunchError, ProcessTimeoutError, SubprocessProcessRunner, run_process,
)
from tiny_swarm_world.infrastructure.process.streaming import run_bounded_process


class TestProcessDiagnostics(unittest.TestCase):
    def test_payload_is_usable_but_result_and_checked_failure_are_redacted(self):
        payload = "private-payload"
        completed = subprocess.CompletedProcess([payload], 7, payload, payload)
        with patch("subprocess.run", return_value=completed):
            result = run_process([payload])
        self.assertEqual(payload, result.stdout)
        self.assertNotIn(payload, repr(result))
        self.assertNotIn(payload, str(result))
        with self.assertRaises(subprocess.CalledProcessError) as raised:
            result.check_returncode()
        self.assertEqual(7, raised.exception.returncode)
        self.assertNotIn(payload, str(raised.exception))
        self.assertIsNone(raised.exception.output)

    def test_timeout_and_launch_tracebacks_do_not_disclose_original_payload(self):
        payload = "private-execution-value"
        for failure, expected in (
            (subprocess.TimeoutExpired([payload], 1, output=payload, stderr=payload), ProcessTimeoutError),
            (FileNotFoundError(2, payload, payload), ProcessLaunchError),
        ):
            with self.subTest(failure=type(failure).__name__):
                with patch("subprocess.run", side_effect=failure):
                    try:
                        SubprocessProcessRunner().run_text([payload])
                    except expected as exc:
                        self.assertNotIn(payload, "".join(traceback.format_exception(exc)))
                    else:
                        self.fail("Expected explicit process error")

    def test_timeout_partial_diagnostics_are_redacted(self):
        payload = "private-partial-output"
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired([payload], 2, payload, payload)):
            with self.assertRaises(subprocess.TimeoutExpired) as raised:
                run_process([payload], timeout=2)
        self.assertEqual("<redacted>", raised.exception.stdout)
        self.assertEqual("<redacted>", raised.exception.stderr)
        self.assertNotIn(payload, repr(raised.exception))

    def test_gateway_logs_do_not_disclose_unlabelled_credentials(self):
        from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway

        logger = Mock()
        payload = "opaque-private-value"
        runner = Mock()
        runner.run_text.return_value = subprocess.CompletedProcess([], 0, payload, payload)
        gateway = LxcManagerShellGateway(
            backend=ManagedLxcBackend.INCUS, manager_node="manager", timeout_seconds=1,
            logger=logger, process_runner=runner,
        )
        result = gateway.run_manager_shell(payload)
        self.assertEqual(payload, result.stdout)
        self.assertNotIn(payload, str(logger.mock_calls))

    def test_timeout_validation_happens_before_launch(self):
        for timeout in (0, -1, float("nan"), float("inf")):
            with self.subTest(timeout=timeout), patch("subprocess.run") as launch:
                with self.assertRaises(ValueError):
                    run_process(["tool"], timeout=timeout)
                launch.assert_not_called()

    def test_streaming_launch_traceback_is_sanitized(self):
        payload = "private-executable-path"
        with patch("subprocess.Popen", side_effect=FileNotFoundError(2, payload, payload)):
            try:
                run_bounded_process([payload], cwd=Path("."), env={}, timeout_seconds=1)
            except FileNotFoundError as exc:
                self.assertNotIn(payload, "".join(traceback.format_exception(exc)))
            else:
                self.fail("Expected launch failure")

    def test_streaming_timeout_terminates_and_preserves_tuple_contract(self):
        process = Mock(returncode=-15)
        process.communicate.side_effect = [subprocess.TimeoutExpired("tool", 1), (None, None)]
        with patch("subprocess.Popen", return_value=process), patch(
            "tiny_swarm_world.infrastructure.process.streaming.terminate_process"
        ) as terminate:
            result = run_bounded_process(["tool"], cwd=Path("."), env={}, timeout_seconds=1)
        self.assertEqual((-15, True, False), result)
        self.assertTrue(result.timed_out)
        terminate.assert_called_once_with(process)

    def test_streaming_exit_race_preserves_timeout_outcome(self):
        process = Mock(pid=2345, returncode=-15)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired("private-command", 1),
            subprocess.TimeoutExpired("private-command", 3),
            (None, None),
        ]
        with patch("subprocess.Popen", return_value=process), patch(
            "tiny_swarm_world.infrastructure.process.streaming.os.killpg",
            side_effect=[None, ProcessLookupError],
        ):
            result = run_bounded_process(["tool"], cwd=Path("."), env={}, timeout_seconds=1)
        self.assertEqual((-15, True, False), result)
        self.assertEqual(3, process.communicate.call_count)

    def test_streaming_interruption_is_explicit(self):
        process = Mock(returncode=-15)
        process.communicate.side_effect = KeyboardInterrupt
        with patch("subprocess.Popen", return_value=process), patch(
            "tiny_swarm_world.infrastructure.process.streaming.terminate_process"
        ) as cleanup:
            result = run_bounded_process(["tool"], cwd=Path("."), env={}, timeout_seconds=1)
        self.assertTrue(result.interrupted)
        self.assertFalse(result.timed_out)
        cleanup.assert_called_once_with(process)


class TestAsyncProcessContract(unittest.IsolatedAsyncioTestCase):
    async def test_success_and_nonzero_exit_preserve_functional_output(self):
        for code in (0, 23):
            process = Mock(returncode=code)
            process.communicate = AsyncMock(return_value=(b"private-output", b"private-error"))
            with patch("asyncio.create_subprocess_exec", return_value=process):
                result = await run_async_process(("tool",))
            self.assertEqual(code, result.returncode)
            self.assertEqual("private-output", result.stdout)
            self.assertNotIn("private-output", repr(result))
            self.assertNotIn("private-error", repr(result))

    async def test_launch_failure_classification_preserved_without_payload(self):
        for error, code, hint in (
            (FileNotFoundError, 127, "launch_executable_missing"),
            (PermissionError, 126, "launch_permission_denied"),
            (OSError, -1, "launch_os_error"),
        ):
            with patch("asyncio.create_subprocess_exec", side_effect=error("private-detail")):
                result = await run_async_process(("private-command",))
            self.assertEqual(code, result.returncode)
            self.assertEqual(hint, result.failure_hint)
            self.assertNotIn("private", repr(result))

    async def test_timeout_and_cancellation_cleanup_children(self):
        for error in (asyncio.TimeoutError, asyncio.CancelledError):
            process = Mock(returncode=None)
            process.communicate = AsyncMock(side_effect=error)
            with patch("asyncio.create_subprocess_exec", return_value=process), patch(
                "tiny_swarm_world.infrastructure.process.async_runner.terminate_async_process",
                new_callable=AsyncMock,
            ) as cleanup:
                if error is asyncio.CancelledError:
                    with self.assertRaises(asyncio.CancelledError):
                        await run_async_process(("tool",))
                else:
                    result = await run_async_process(("tool",))
                    self.assertTrue(result.timed_out)
                    self.assertEqual(124, result.returncode)
                cleanup.assert_awaited_once_with(process)

    async def test_kill_group_survives_session_leader_exit(self):
        process = Mock(pid=2345)
        process.wait = AsyncMock(side_effect=[asyncio.TimeoutError, None])
        with patch("tiny_swarm_world.infrastructure.process.async_runner.os.killpg") as killpg:
            await terminate_async_process(process)
        self.assertEqual([(2345, signal.SIGTERM), (2345, signal.SIGKILL)], [c.args for c in killpg.call_args_list])
        self.assertEqual(2, process.wait.await_count)

    async def test_invalid_timeout_never_spawns(self):
        with patch("asyncio.create_subprocess_exec") as launch:
            with self.assertRaises(ValueError):
                await run_async_process(("tool",), timeout=float("inf"))
            launch.assert_not_called()

"""Authentication-session compatibility without running privileged commands."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.incus_preparation import runtime as incus
from tiny_swarm_world.infrastructure.adapters.network_preparation import runtime as network
from tiny_swarm_world.infrastructure.process.async_runner import AsyncProcessResult, run_async_process


class LoginSessionProcessTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_session_identity_and_isolated_group_in_both_modes(self):
        body = "import json,os; print(json.dumps([os.getpid(),os.getsid(0),os.getpgrp()]))"
        for preserve in (False, True):
            with self.subTest(preserve=preserve):
                result = await run_async_process(
                    (sys.executable, "-c", body), preserve_login_session=preserve,
                )
                self.assertEqual(0, result.returncode)
                pid, sid, pgid = json.loads(result.stdout)
                self.assertEqual(pid, pgid)
                self.assertNotEqual(os.getpgrp(), pgid)
                self.assertEqual(os.getsid(0) if preserve else pid, sid)

    async def test_shell_session_opt_in_rejected_without_launch(self):
        with patch("asyncio.create_subprocess_shell") as launch:
            with self.assertRaisesRegex(ValueError, "direct argv"):
                await run_async_process("ignored", shell=True, preserve_login_session=True)
            launch.assert_not_called()

    async def test_group_mode_preserves_private_stdin_and_nonzero_outcome(self):
        process = AsyncMock(returncode=1)
        process.communicate.return_value = (b"private-output", b"authentication denied")
        with patch("asyncio.create_subprocess_exec", return_value=process) as launch:
            result = await run_async_process(
                ("/usr/bin/sudo", "-n", "--", "/usr/bin/true"),
                preserve_login_session=True, input_data=b"private-input",
            )
        self.assertFalse(launch.call_args.kwargs["start_new_session"])
        self.assertEqual(0, launch.call_args.kwargs["process_group"])
        self.assertEqual(asyncio.subprocess.PIPE, launch.call_args.kwargs["stdin"])
        process.communicate.assert_awaited_once_with(b"private-input")
        self.assertEqual(1, result.returncode)
        self.assertNotIn("private", repr(result))
        self.assertEqual(1, launch.call_count)

    async def test_real_timeout_cleans_descendants_after_leader_exit_in_both_modes(self):
        for preserve in (False, True):
            with self.subTest(preserve=preserve):
                await self._exercise_cleanup(preserve, cancel=False)

    async def test_real_cancellation_cleans_descendants_after_leader_exit_in_both_modes(self):
        for preserve in (False, True):
            with self.subTest(preserve=preserve):
                await self._exercise_cleanup(preserve, cancel=True)

    def test_process_observation_handles_disappearance_and_preserves_state(self):
        for error in (FileNotFoundError(), ProcessLookupError()):
            with self.subTest(error=type(error).__name__), patch.object(Path, "read_text", side_effect=error):
                self.assertFalse(self._running(123))
        for state, running in (("S", True), ("R", True), ("Z", False)):
            with self.subTest(state=state), patch.object(Path, "read_text", return_value=f"123 (child (worker)) {state} 1"):
                self.assertEqual(running, self._running(123))
        with patch.object(Path, "read_text", side_effect=PermissionError()):
            with self.assertRaises(PermissionError):
                self._running(123)

    def test_cleanup_handles_exit_before_signal_and_preserves_permission_errors(self):
        for error in (ProcessLookupError(), PermissionError()):
            with self.subTest(error=type(error).__name__), patch.object(self, "_running", return_value=True), patch.object(os, "kill", side_effect=error):
                if isinstance(error, PermissionError):
                    with self.assertRaises(PermissionError):
                        self._kill_if_running(123)
                else:
                    self._kill_if_running(123)

    async def _exercise_cleanup(self, preserve: bool, *, cancel: bool):
        parent_group = os.getpgrp()
        parent_session = os.getsid(0)
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "processes.json"
            ready = Path(directory) / "ready"
            body = (
                "import json,os,pathlib,subprocess,sys,time\n"
                "child=subprocess.Popen([sys.executable,'-c',"
                "'import pathlib,signal,sys,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
                "pathlib.Path(sys.argv[1]).write_text(\"ready\"); time.sleep(60)',sys.argv[2]])\n"
                "while not pathlib.Path(sys.argv[2]).exists(): time.sleep(0.01)\n"
                "pathlib.Path(sys.argv[1]).write_text(json.dumps([os.getpid(),child.pid]))\n"
                "time.sleep(60)\n"
            )
            task = asyncio.create_task(run_async_process(
                (sys.executable, "-c", body, str(marker), str(ready)), timeout=2,
                preserve_login_session=preserve,
            ))
            pids: list[int] = []
            try:
                async with asyncio.timeout(1.5):
                    while not marker.exists():
                        await asyncio.sleep(0.01)
                pids = json.loads(marker.read_text())
                self.assertNotEqual(os.getpgrp(), os.getpgid(pids[0]))
                if cancel:
                    task.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await task
                else:
                    result = await task
                    self.assertTrue(result.timed_out)
                    self.assertEqual(124, result.returncode)
                async with asyncio.timeout(2):
                    while any(self._running(pid) for pid in pids):
                        await asyncio.sleep(0.01)
                self.assertEqual(parent_group, os.getpgrp())
                self.assertEqual(parent_session, os.getsid(0))
            finally:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                for pid in pids:
                    self._kill_if_running(pid)

    def _kill_if_running(self, pid: int) -> None:
        if self._running(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # The observed process exited before the signal was sent.

    @staticmethod
    def _running(pid: int) -> bool:
        try:
            return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
        except (FileNotFoundError, ProcessLookupError):
            return False


class PreparationSessionSelectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_exact_noninteractive_sudo_prefix_selects_login_session(self):
        for module in (incus, network):
            for args, opted in (
                (("/usr/bin/sudo", "-n", "--", "/usr/bin/true"), True),
                (("/usr/bin/sudo", "--version"), False),
                (("/usr/bin/systemctl", "show", "incus.service"), False),
            ):
                with self.subTest(module=module.__name__, args=args):
                    with patch.object(module, "run_async_process", return_value=AsyncProcessResult(0)) as run:
                        await module.command(args, timeout=7)
                    self.assertEqual(opted, run.call_args.kwargs.get("preserve_login_session", False))
                    self.assertEqual(7, run.call_args.kwargs["timeout"])
                    self.assertEqual(args, run.call_args.args[0])

    async def test_missing_authentication_fails_once_without_interactive_fallback(self):
        for module, error in ((incus, IncusPreparationFailure), (network, NetworkPreparationFailure)):
            with self.subTest(module=module.__name__):
                with patch.object(module, "run_async_process", return_value=AsyncProcessResult(
                    1, stderr="sudo: interactive authentication is required",
                )) as run:
                    with self.assertRaises(error):
                        if module is incus:
                            await module.checked_command(("/usr/bin/sudo", "-n", "/usr/bin/true"))
                        else:
                            await module.command(("/usr/bin/sudo", "-n", "/usr/bin/true"))
                self.assertEqual(1, run.await_count)
                self.assertTrue(run.call_args.kwargs.get("preserve_login_session", False))

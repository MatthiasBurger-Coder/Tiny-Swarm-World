"""Retain terminal sudo timestamps without losing child-process cleanup."""
import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tiny_swarm_world.infrastructure.process.async_runner import AsyncProcessResult, run_async_process
from tiny_swarm_world.infrastructure.adapters.network_preparation import runtime as network
from tiny_swarm_world.infrastructure.adapters.incus_preparation import runtime as incus


class SudoSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_child_preserves_session_with_its_own_killable_group(self):
        probe = "import os,json; print(json.dumps([os.getsid(0),os.getpgrp(),os.getpid()]))"
        for preserve in (False, True):
            result = await run_async_process((sys.executable, "-c", probe), preserve_session=preserve)
            self.assertEqual(result.returncode, 0)
            session, group, pid = json.loads(result.stdout)
            self.assertEqual(group, pid)
            self.assertNotEqual(group, os.getpgrp())
            self.assertEqual(session, os.getsid(0) if preserve else pid)

    async def test_preserved_session_timeout_and_cancellation_still_cleanup(self):
        for failure in (asyncio.TimeoutError, asyncio.CancelledError):
            process = Mock(returncode=None)
            process.communicate = AsyncMock(side_effect=failure)
            with patch("asyncio.create_subprocess_exec", return_value=process) as spawn, patch(
                "tiny_swarm_world.infrastructure.process.async_runner.terminate_async_process",
                new_callable=AsyncMock,
            ) as cleanup:
                if failure is asyncio.CancelledError:
                    with self.assertRaises(asyncio.CancelledError):
                        await run_async_process(("sudo", "-n", "true"), preserve_session=True)
                else:
                    result = await run_async_process(("sudo", "-n", "true"), preserve_session=True)
                    self.assertTrue(result.timed_out)
                    self.assertEqual(result.returncode, 124)
                self.assertEqual(spawn.call_args.kwargs["process_group"], 0)
                self.assertNotIn("start_new_session", spawn.call_args.kwargs)
                cleanup.assert_awaited_once_with(process)

    async def test_network_and_incus_privileged_calls_keep_the_terminal(self):
        for module, args in ((network, ("sudo", "-n", "--", "/usr/bin/ss", "-H", "-ltnp")),
                             (incus, ("sudo", "-n", "/usr/bin/systemctl", "start", "incus.service"))):
            with patch.object(module, "run_async_process", return_value=AsyncProcessResult(0)) as runner:
                await module.command(args)
                self.assertTrue(runner.call_args.kwargs["preserve_session"])
                self.assertIn("-n", runner.call_args.args[0])

    async def test_unprivileged_commands_retain_default_session_isolation(self):
        for module in (network, incus):
            with patch.object(module, "run_async_process", return_value=AsyncProcessResult(0)) as runner:
                await module.command(("getent", "hosts", "localhost"))
                self.assertNotIn("preserve_session", runner.call_args.kwargs)

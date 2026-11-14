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
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner
from tiny_swarm_world.infrastructure.adapters.network_preparation.trusted_process import PROBE


class SudoSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_lxc_qualified_noninteractive_sudo_preserves_session_for_tuple_and_list_argv(self):
        commands = (
            (('/usr/bin/sudo', '-n', '--', '/usr/bin/ss', '-H', '-O', '-ltnp'), True),
            (('/usr/bin/sudo', '-n', '--', '/usr/bin/python3', '-I', '-B', '-c', PROBE, '201', '100', '202'), True),
            (('/usr/bin/ss', '-H', '-O', '-ltnp'), False),
            (('sudo', '-n', '--', '/usr/bin/ss', '-H', '-O', '-ltnp'), False),
            (('/usr/bin/sudo', '--', '/usr/bin/ss', '-H', '-O', '-ltnp'), False),
            (('/usr/bin/env', '/usr/bin/sudo', '-n', '--', '/usr/bin/ss', '-H', '-O', '-ltnp'), False),
        )
        outcome = AsyncProcessResult(124, 'partial output', 'diagnostic', True, 'timed_out')
        for sequence in (tuple, list):
            for command, preserve in commands:
                args = sequence(command)
                with self.subTest(command=command[:4], sequence=sequence.__name__), patch(
                        'tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command.run_async_process',
                        return_value=outcome) as runner:
                    result = await AsyncLxcNodeCommandRunner().run(args, 7.5)
                if preserve:
                    runner.assert_awaited_once_with(args, timeout=7.5, preserve_login_session=True)
                else:
                    runner.assert_awaited_once_with(args, timeout=7.5)
                self.assertIs(runner.call_args.args[0], args)
                self.assertEqual((result.returncode, result.stdout, result.stderr, result.timed_out, result.failure_hint),
                                 (124, 'partial output', 'diagnostic', True, 'timed_out'))

    async def test_real_child_preserves_session_with_its_own_killable_group(self):
        probe = "import os,json; print(json.dumps([os.getsid(0),os.getpgrp(),os.getpid()]))"
        for preserve in (False, True):
            result = await run_async_process((sys.executable, "-c", probe), preserve_login_session=preserve)
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
                        await run_async_process(("/usr/bin/sudo", "-n", "true"), preserve_login_session=True)
                else:
                    result = await run_async_process(("/usr/bin/sudo", "-n", "true"), preserve_login_session=True)
                    self.assertTrue(result.timed_out)
                    self.assertEqual(result.returncode, 124)
                self.assertEqual(spawn.call_args.kwargs["process_group"], 0)
                self.assertFalse(spawn.call_args.kwargs["start_new_session"])
                cleanup.assert_awaited_once_with(process)

    async def test_network_and_incus_privileged_calls_keep_the_terminal(self):
        for module, args in ((network, ("/usr/bin/sudo", "-n", "--", "/usr/bin/ss", "-H", "-ltnp")),
                             (incus, ("/usr/bin/sudo", "-n", "/usr/bin/systemctl", "start", "incus.service"))):
            with patch.object(module, "run_async_process", return_value=AsyncProcessResult(0)) as runner:
                await module.command(args)
                self.assertTrue(runner.call_args.kwargs["preserve_login_session"])
                self.assertIn("-n", runner.call_args.args[0])

    async def test_unprivileged_commands_retain_default_session_isolation(self):
        for module in (network, incus):
            with patch.object(module, "run_async_process", return_value=AsyncProcessResult(0)) as runner:
                await module.command(("getent", "hosts", "localhost"))
                self.assertNotIn("preserve_login_session", runner.call_args.kwargs)

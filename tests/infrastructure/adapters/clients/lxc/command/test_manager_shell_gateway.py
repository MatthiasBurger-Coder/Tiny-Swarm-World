import subprocess
import unittest
from unittest.mock import Mock

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import (
    LxcManagerShellGateway,
)


class TestLxcManagerShellGateway(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.gateway = LxcManagerShellGateway(
            backend=ManagedLxcBackend.INCUS,
            manager_node="swarm-manager",
            timeout_seconds=30,
            logger=self.logger,
        )

    def test_run_manager_shell_uses_backend_cli_and_manager_node(self):
        run = Mock(
            return_value=subprocess.CompletedProcess(
                [], 0, stdout="ok", stderr=""
            )
        )

        result = self.gateway.run_manager_shell("printf ok", run=run)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            run.call_args.args[0],
            ["incus", "exec", "swarm-manager", "--", "sh", "-lc", "printf ok"],
        )
        run.assert_called_once_with(
            ["incus", "exec", "swarm-manager", "--", "sh", "-lc", "printf ok"],
            input=None,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=30,
        )

    def test_run_node_shell_retries_transient_failure(self):
        transient = subprocess.CompletedProcess(
            [],
            255,
            stdout="",
            stderr="Failed to retrieve PID of executing child process",
        )
        success = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")
        run = Mock(side_effect=(transient, success))
        sleep = Mock()

        result = self.gateway.run_node_shell(
            "swarm-worker-1",
            "true",
            check=True,
            run=run,
            sleep=sleep,
        )

        self.assertEqual(result, success)
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(0.5)

    def test_run_node_shell_raises_for_failed_checked_command(self):
        run = Mock(
            return_value=subprocess.CompletedProcess(
                [], 17, stdout="", stderr="failure"
            )
        )

        with self.assertRaisesRegex(RuntimeError, "exit code 17"):
            self.gateway.run_node_shell("swarm-worker-1", "false", run=run)

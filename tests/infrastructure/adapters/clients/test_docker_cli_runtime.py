import subprocess
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.clients.docker_cli_runtime import DockerCliRuntime


class TestDockerCliRuntime(unittest.TestCase):
    def test_find_container_names_uses_argv_list_without_shell(self):
        completed_process = subprocess.CompletedProcess(
            args=["docker"],
            returncode=0,
            stdout="nexus-1\nnexus-2\n",
            stderr="",
        )
        with patch("tiny_swarm_world.infrastructure.adapters.clients.docker_cli_runtime.subprocess.run") as run:
            run.return_value = completed_process
            runtime = DockerCliRuntime(timeout_seconds=7)

            container_names = runtime.find_container_names("nexus")

        self.assertEqual(["nexus-1", "nexus-2"], container_names)
        run.assert_called_once()
        call_kwargs = run.call_args.kwargs
        self.assertEqual(
            ["docker", "ps", "--filter", "name=nexus", "--format", "{{.Names}}"],
            run.call_args.args[0],
        )
        self.assertFalse(call_kwargs["shell"])
        self.assertEqual(7, call_kwargs["timeout"])

    def test_file_exists_returns_false_without_raising_for_missing_file(self):
        completed_process = subprocess.CompletedProcess(
            args=["docker"],
            returncode=1,
            stdout="",
            stderr="not found",
        )
        with patch("tiny_swarm_world.infrastructure.adapters.clients.docker_cli_runtime.subprocess.run") as run:
            run.return_value = completed_process
            runtime = DockerCliRuntime()

            self.assertFalse(runtime.file_exists("nexus-1", "/nexus-data/admin.password"))

    def test_read_file_failure_does_not_include_stderr_or_command(self):
        completed_process = subprocess.CompletedProcess(
            args=["docker"],
            returncode=1,
            stdout="",
            stderr="secret=leaked",
        )
        with patch("tiny_swarm_world.infrastructure.adapters.clients.docker_cli_runtime.subprocess.run") as run:
            run.return_value = completed_process
            runtime = DockerCliRuntime()

            with self.assertRaises(RuntimeError) as raised:
                runtime.read_file("nexus-1", "/nexus-data/admin.password")

        message = str(raised.exception)
        self.assertIn("exit code 1", message)
        self.assertNotIn("secret=leaked", message)
        self.assertNotIn("docker exec", message)

    def test_timeout_failure_is_sanitized(self):
        with patch("tiny_swarm_world.infrastructure.adapters.clients.docker_cli_runtime.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd=["docker", "ps"], timeout=1)
            runtime = DockerCliRuntime(timeout_seconds=1)

            with self.assertRaises(RuntimeError) as raised:
                runtime.find_container_names("nexus")

        self.assertEqual("Docker runtime operation timed out.", str(raised.exception))

    def test_runtime_does_not_expose_image_build_or_push_methods(self):
        runtime = DockerCliRuntime()

        self.assertFalse(hasattr(runtime, "build_image"))
        self.assertFalse(hasattr(runtime, "push_image"))
        self.assertFalse(hasattr(runtime, "login"))

import subprocess
import unittest
from unittest.mock import Mock

from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    LxcSwarmStackRuntime,
)


class TestLxcSwarmStackRuntime(unittest.TestCase):
    def test_deploy_stack_preserves_prerequisite_asset_and_deploy_order(self):
        calls = []

        def run_manager_shell(script, **kwargs):
            calls.append(("shell", script, kwargs))
            return subprocess.CompletedProcess([], 0, stdout="", stderr="")

        def ensure_prerequisites(name, definition):
            calls.append(("prerequisites", name, definition.name))

        def prepare_assets(name, remote_dir):
            calls.append(("assets", name, remote_dir))

        runtime = LxcSwarmStackRuntime(
            remote_stack_root="/remote/stacks",
            service_list_timeout_seconds=30,
            run_manager_shell=run_manager_shell,
            run_node_shell=Mock(),
            prepare_stack_assets=prepare_assets,
            ensure_stack_prerequisites=ensure_prerequisites,
        )

        runtime.deploy_stack(
            StackDefinition(name="swagger", compose_content="services: {}"),
            stack_environment={"EXTRA": "value"},
        )

        self.assertEqual(calls[0], ("prerequisites", "swagger", "swagger"))
        self.assertEqual(calls[1][0], "shell")
        self.assertEqual(calls[2], ("assets", "swagger", "/remote/stacks/swagger"))
        self.assertEqual(calls[3][0], "shell")
        self.assertIn("EXTRA=value", calls[3][1])
        self.assertIn("docker stack deploy", calls[3][1])

    def test_list_stack_services_ignores_malformed_status_lines(self):
        run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess(
                [],
                0,
                stdout="good|1/2\nmalformed\nother|x/y\n",
                stderr="",
            )
        )
        runtime = LxcSwarmStackRuntime(
            remote_stack_root="/remote/stacks",
            service_list_timeout_seconds=30,
            run_manager_shell=run_manager_shell,
            run_node_shell=Mock(),
            prepare_stack_assets=Mock(),
            ensure_stack_prerequisites=Mock(),
        )

        services = runtime.list_stack_services("stack")

        self.assertEqual(len(services), 1)
        self.assertEqual(services[0].service_name, "good")

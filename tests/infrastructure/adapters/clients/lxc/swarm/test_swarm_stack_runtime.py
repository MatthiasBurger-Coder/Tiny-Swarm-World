import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import os
import shlex

from tiny_swarm_world.domain.deployment import StackDefinition
from pathlib import Path
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.stack_asset_transfer import StackAssetTransfer
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    LxcSwarmStackRuntime,
)


class TestLxcSwarmStackRuntime(unittest.TestCase):
    def test_explicit_portainer_pair_reaches_remote_interpolation_without_ambient_images(self):
        shell = Mock(return_value=subprocess.CompletedProcess([], 0, stdout='', stderr=''))
        runtime = LxcSwarmStackRuntime(remote_stack_root='/remote/stacks', service_list_timeout_seconds=30,
            run_manager_shell=shell, run_node_shell=Mock(), prepare_stack_assets=Mock(), ensure_stack_prerequisites=Mock())
        pins = {'TSW_PORTAINER_IMAGE': 'portainer/portainer-ce@sha256:' + '1' * 64,
                'TSW_PORTAINER_AGENT_IMAGE': 'portainer/agent@sha256:' + '2' * 64}
        definition = StackDefinition(name='portainer', compose_content='services: {portainer: {image: "${TSW_PORTAINER_IMAGE}"}}')
        with patch.dict(os.environ, {'TSW_PORTAINER_IMAGE': 'ambient:unapproved', 'TSW_NEXUS_IMAGE': 'excluded:unapproved'}):
            runtime.deploy_stack(definition, pins)
        upload, deploy = shell.call_args_list
        self.assertEqual(upload.kwargs['input_text'], definition.compose_content)
        tokens = shlex.split(deploy.args[0])
        assignments = dict(token.split('=', 1) for token in tokens[:tokens.index('docker')])
        self.assertEqual(assignments, {'TSW_REMOTE_STACK_ROOT': '/remote/stacks', **pins})
        self.assertIn('--resolve-image never', deploy.args[0])
        self.assertNotIn('ambient:', deploy.args[0])
        self.assertNotIn('TSW_NEXUS_IMAGE', deploy.args[0])

    def test_second_swagger_asset_failure_prevents_deployment(self):
        calls = []

        def run_shell(script, **kwargs):
            calls.append(script)
            if "target=/remote/stacks/swagger/nginx/default.conf" in script:
                raise RuntimeError("asset transfer failed")
            return subprocess.CompletedProcess([], 0, stdout="", stderr="")

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative, content in (("swagger/openapi.json", "{}"), ("nginx/default.conf", "server {}")):
            path = root / "infra/config/compose/swagger" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        assets = StackAssetTransfer(
            project_paths=ProjectPaths.from_roots(root), run_manager_shell=run_shell,
            render_service_access_dashboard=Mock(),
        )
        runtime = LxcSwarmStackRuntime(
            remote_stack_root="/remote/stacks", service_list_timeout_seconds=30,
            run_manager_shell=run_shell, run_node_shell=Mock(),
            prepare_stack_assets=assets.transfer_stack_assets, ensure_stack_prerequisites=Mock(),
        )
        with self.assertRaisesRegex(RuntimeError, "asset transfer failed"):
            runtime.deploy_stack(StackDefinition(name="swagger", compose_content="services: {}"), stack_environment={})
        self.assertTrue(any("target=/remote/stacks/swagger/swagger/openapi.json" in call for call in calls))
        self.assertFalse(any("docker stack deploy" in call for call in calls))

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

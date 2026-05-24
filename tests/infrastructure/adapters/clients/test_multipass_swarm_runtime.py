import unittest
from unittest.mock import patch

from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.infrastructure.adapters.clients.multipass_swarm_runtime import (
    MultipassSwarmRuntime,
)


class TestMultipassSwarmRuntime(unittest.TestCase):
    def test_deploy_stack_exports_remote_stack_root_for_compose_interpolation(self):
        runtime = MultipassSwarmRuntime(remote_stack_root="/custom/stacks")

        with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
            with patch.object(runtime, "_transfer_stack_assets") as transfer_stack_assets:
                runtime.deploy_stack(StackDefinition(name="swagger", compose_content="services: {}"))

        transfer_stack_assets.assert_called_once_with("swagger", "/custom/stacks/swagger")
        deploy_script = run_manager_shell.call_args_list[-1].args[0]
        self.assertIn("TSW_REMOTE_STACK_ROOT=/custom/stacks docker stack deploy", deploy_script)
        self.assertIn("-c /custom/stacks/swagger/docker-compose.yml swagger", deploy_script)


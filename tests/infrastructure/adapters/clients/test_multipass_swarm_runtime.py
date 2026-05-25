import subprocess
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

    def test_deploy_stack_exports_allowlisted_stack_environment(self):
        runtime = MultipassSwarmRuntime(remote_stack_root="/custom/stacks")

        with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
            with patch.object(runtime, "_transfer_stack_assets"):
                runtime.deploy_stack(
                    StackDefinition(name="service-access", compose_content="services: {}"),
                    {"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"},
                )

        deploy_script = run_manager_shell.call_args_list[-1].args[0]
        self.assertIn(
            "TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET=operator_defined",
            deploy_script,
        )
        self.assertIn("TSW_REMOTE_STACK_ROOT=/custom/stacks", deploy_script)

    def test_stack_exists_reads_docker_stack_names(self):
        runtime = MultipassSwarmRuntime()

        with patch.object(
            runtime,
            "_run_manager_shell",
            return_value=subprocess.CompletedProcess([], 0, stdout="portainer\nnexus\n"),
        ) as run_manager_shell:
            self.assertTrue(runtime.stack_exists("nexus"))

        run_manager_shell.assert_called_once_with(
            "docker stack ls --format '{{.Name}}'",
            check=False,
        )

    def test_stack_exists_returns_false_when_listing_fails(self):
        runtime = MultipassSwarmRuntime()

        with patch.object(
            runtime,
            "_run_manager_shell",
            return_value=subprocess.CompletedProcess([], 1, stdout=""),
        ):
            self.assertFalse(runtime.stack_exists("nexus"))

    def test_list_stack_services_parses_replica_counts(self):
        runtime = MultipassSwarmRuntime()

        with patch.object(
            runtime,
            "_run_manager_shell",
            return_value=subprocess.CompletedProcess(
                [],
                0,
                stdout="service-access_vaultwarden|1/1\nservice-access_nginx|0/1\n",
            ),
        ):
            services = runtime.list_stack_services("service-access")

        self.assertEqual(("service-access_vaultwarden", "service-access_nginx"), tuple(service.service_name for service in services))
        self.assertEqual((1, 0), tuple(service.current_replicas for service in services))
        self.assertEqual((1, 1), tuple(service.desired_replicas for service in services))

    def test_list_stack_services_returns_empty_when_listing_fails(self):
        runtime = MultipassSwarmRuntime()

        with patch.object(
            runtime,
            "_run_manager_shell",
            return_value=subprocess.CompletedProcess([], 1, stdout=""),
        ):
            self.assertEqual((), runtime.list_stack_services("service-access"))

    def test_external_secret_exists_uses_docker_secret_inspect(self):
        runtime = MultipassSwarmRuntime()

        with patch.object(
            runtime,
            "_run_manager_shell",
            return_value=subprocess.CompletedProcess([], 0, stdout=""),
        ) as run_manager_shell:
            self.assertTrue(runtime.external_secret_exists("tsw_vaultwarden_admin_token"))

        run_manager_shell.assert_called_once_with(
            "docker secret inspect tsw_vaultwarden_admin_token >/dev/null 2>&1",
            check=False,
        )

    def test_external_secret_exists_returns_false_when_inspect_fails(self):
        runtime = MultipassSwarmRuntime()

        with patch.object(
            runtime,
            "_run_manager_shell",
            return_value=subprocess.CompletedProcess([], 1, stdout=""),
        ):
            self.assertFalse(runtime.external_secret_exists("missing"))

    def test_transfers_swagger_openapi_and_nginx_config_assets(self):
        runtime = MultipassSwarmRuntime(remote_stack_root="/custom/stacks")

        with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
            runtime._transfer_stack_assets("swagger", "/custom/stacks/swagger")

        scripts = [call.args[0] for call in run_manager_shell.call_args_list]
        self.assertIn("cat > /custom/stacks/swagger/swagger/openapi.json", scripts[0])
        self.assertIn("cat > /custom/stacks/swagger/nginx/default.conf", scripts[1])
        self.assertIn("openapi", run_manager_shell.call_args_list[0].kwargs["input_text"].lower())
        self.assertIn("resolver 127.0.0.11", run_manager_shell.call_args_list[1].kwargs["input_text"])

import subprocess
import unittest
from unittest.mock import patch
from tests.support.sonar_safe_literals import ipv4_address

from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime import (
    LxcContainerRuntime,
    LxcSwarmRuntime,
    _lxc_manager_ip,
)


class TestLxcSwarmRuntime(unittest.TestCase):
    def test_deploy_stack_uses_lxc_exec_manager_shell(self):
        runtime = LxcSwarmRuntime(
            backend=ManagedLxcBackend.LXD,
            remote_stack_root="/custom/stacks",
        )

        with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
            with patch.object(runtime, "_transfer_stack_assets") as transfer_stack_assets:
                runtime.deploy_stack(
                    StackDefinition(name="swagger", compose_content="services: {}")
                )

        transfer_stack_assets.assert_called_once_with("swagger", "/custom/stacks/swagger")
        deploy_script = run_manager_shell.call_args_list[-1].args[0]
        self.assertIn("TSW_REMOTE_STACK_ROOT=/custom/stacks docker stack deploy", deploy_script)
        self.assertIn("-c /custom/stacks/swagger/docker-compose.yml swagger", deploy_script)

    def test_deploy_stack_reconciles_existing_host_published_ports(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)
        compose = """
services:
  nexus:
    image: sonatype/nexus3:3.75.1
    ports:
      - target: 8081
        published: 8081
        protocol: tcp
        mode: host
"""

        with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
            with patch.object(runtime, "_transfer_stack_assets"):
                runtime.deploy_stack(StackDefinition(name="nexus", compose_content=compose))

        scripts = [call.args[0] for call in run_manager_shell.call_args_list]
        self.assertIn(
            "docker service update --publish-rm 8081 nexus_nexus >/dev/null 2>&1 || true",
            scripts,
        )
        self.assertIn(
            "docker service update --publish-add published=8081,target=8081,protocol=tcp,mode=host nexus_nexus",
            scripts,
        )

    def test_stack_exists_reads_docker_stack_names_through_lxc(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)

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

    def test_list_stack_services_parses_replica_counts(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)

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

        self.assertEqual(
            ("service-access_vaultwarden", "service-access_nginx"),
            tuple(service.service_name for service in services),
        )
        self.assertEqual((1, 0), tuple(service.current_replicas for service in services))
        self.assertEqual((1, 1), tuple(service.desired_replicas for service in services))

    def test_container_runtime_runs_docker_inside_lxc_manager(self):
        runtime = LxcContainerRuntime(backend=ManagedLxcBackend.LXD)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout="nexus.1.abc\n"),
        ) as run:
            self.assertEqual(["nexus.1.abc"], runtime.find_container_names("nexus"))

        run.assert_called_once()
        self.assertEqual(
            ["lxc", "exec", "swarm-manager", "--", "docker"],
            run.call_args.args[0][:5],
        )

    def test_manager_ip_reads_lxc_eth0_not_docker_bridge_address(self):
        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime.subprocess.run",
            return_value=subprocess.CompletedProcess(
                [],
                0,
                stdout=f"{ipv4_address(10, 156, 143, 201)}\n",
            ),
        ) as run:
            self.assertEqual(
                ipv4_address(10, 156, 143, 201),
                _lxc_manager_ip(ManagedLxcBackend.LXD, "swarm-manager", 30),
            )

        self.assertEqual(
            [
                "lxc",
                "exec",
                "swarm-manager",
                "--",
                "sh",
                "-lc",
                "ip -4 -o addr show dev eth0 | awk '{print $4}' | cut -d/ -f1",
            ],
            run.call_args.args[0],
        )

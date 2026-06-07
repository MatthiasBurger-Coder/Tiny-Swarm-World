import subprocess
import unittest
from unittest.mock import patch

import requests
from tests.support.sonar_safe_literals import ipv4_address, operator_credential, sensitive_assignment

from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortainerAdminInitializationRejected,
)
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime import (
    LxcContainerRuntime,
    LxcPortainerAdminClient,
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

    def test_default_remote_stack_root_matches_committed_compose_fallback(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)

        self.assertEqual("/var/lib/tiny-swarm-world/stacks", runtime.remote_stack_root)

    def test_prepare_stack_assets_transfers_swagger_assets_to_remote_root(self):
        runtime = LxcSwarmRuntime(
            backend=ManagedLxcBackend.LXD,
            remote_stack_root="/custom/stacks",
        )

        with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
            runtime.prepare_stack_assets("swagger")

        scripts = [call.args[0] for call in run_manager_shell.call_args_list]
        self.assertIn("mkdir -p /custom/stacks/swagger/swagger", scripts[0])
        self.assertIn("cat > /custom/stacks/swagger/swagger/openapi.json", scripts[0])
        self.assertIn("mkdir -p /custom/stacks/swagger/nginx", scripts[1])
        self.assertIn("cat > /custom/stacks/swagger/nginx/default.conf", scripts[1])

    def test_deploy_stack_reconciles_existing_published_ports_to_ingress_mode(self):
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
            "docker service update --publish-add published=8081,target=8081,protocol=tcp,mode=ingress nexus_nexus",
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

    def test_external_secret_exists_inspects_secret_with_option_boundary(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)

        with patch.object(
            runtime,
            "_run_manager_shell",
            return_value=subprocess.CompletedProcess([], 0),
        ) as run_manager_shell:
            self.assertTrue(runtime.external_secret_exists("tsw_vaultwarden_admin_token"))

        run_manager_shell.assert_called_once_with(
            "docker secret inspect -- tsw_vaultwarden_admin_token >/dev/null 2>&1",
            check=False,
        )

    def test_ensure_external_secret_creates_missing_secret_without_leaking_value(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)

        with patch.object(
            runtime,
            "external_secret_exists",
            return_value=False,
        ) as external_secret_exists:
            with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
                runtime.ensure_external_secret(
                    "tsw_vaultwarden_admin_token",
                    operator_credential(),
                )

        external_secret_exists.assert_called_once_with("tsw_vaultwarden_admin_token")
        run_manager_shell.assert_called_once_with(
            "docker secret create -- tsw_vaultwarden_admin_token -",
            input_text=operator_credential(),
        )
        self.assertNotIn(operator_credential(), run_manager_shell.call_args.args[0])

    def test_ensure_external_secret_leaves_existing_secret_unchanged(self):
        runtime = LxcSwarmRuntime(backend=ManagedLxcBackend.LXD)

        with patch.object(runtime, "external_secret_exists", return_value=True):
            with patch.object(runtime, "_run_manager_shell") as run_manager_shell:
                runtime.ensure_external_secret(
                    "tsw_vaultwarden_admin_token",
                    operator_credential(),
                )

        run_manager_shell.assert_not_called()

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

    def test_portainer_admin_client_raises_typed_rejection_for_failed_init(self):
        session = _FakeSession(
            [
                _FakeResponse(409, {"message": sensitive_assignment()}),
                _FakeResponse(200, ValueError(sensitive_assignment())),
            ]
        )
        client = LxcPortainerAdminClient(backend=ManagedLxcBackend.LXD, session=session)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime._lxc_manager_ip",
            return_value=ipv4_address(10, 156, 143, 201),
        ):
            with self.assertRaises(PortainerAdminInitializationRejected) as raised:
                client.initialize_admin_user("admin", operator_credential())

        self.assertIn("HTTP 409", str(raised.exception))
        self.assertEqual(409, raised.exception.status_code)
        self.assertNotIn(sensitive_assignment(), str(raised.exception))

    def test_portainer_admin_client_rejects_409_when_auth_probe_fails(self):
        session = _FakeSession(
            [
                _FakeResponse(409, {"message": "admin already initialized"}),
                requests.ConnectionError("Portainer auth endpoint unavailable."),
            ]
        )
        client = LxcPortainerAdminClient(backend=ManagedLxcBackend.LXD, session=session)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime._lxc_manager_ip",
            return_value=ipv4_address(10, 156, 143, 201),
        ):
            with self.assertRaises(PortainerAdminInitializationRejected) as raised:
                client.initialize_admin_user("admin", operator_credential())

        self.assertEqual(409, raised.exception.status_code)
        self.assertEqual(2, len(session.post_calls))

    def test_portainer_admin_client_accepts_failed_init_when_authentication_works(self):
        password = operator_credential()
        session = _FakeSession(
            [
                _FakeResponse(409, {"message": "admin already initialized"}),
                _FakeResponse(200, {"jwt": "jwt-token"}),
            ]
        )
        client = LxcPortainerAdminClient(backend=ManagedLxcBackend.LXD, session=session)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime._lxc_manager_ip",
            return_value=ipv4_address(10, 156, 143, 201),
        ):
            client.initialize_admin_user("admin", password)

        self.assertEqual(2, len(session.post_calls))
        init_call, auth_call = session.post_calls
        self.assertTrue(str(init_call["url"]).endswith("/api/users/admin/init"))
        self.assertEqual({"username": "admin", "password": password}, init_call["json"])
        self.assertTrue(str(auth_call["url"]).endswith("/api/auth"))
        self.assertEqual({"Username": "admin", "Password": password}, auth_call["json"])

    def test_portainer_admin_client_clears_cookies_before_409_auth_probe(self):
        session = _FakeSession(
            [
                _FakeResponse(409, {"message": "admin already initialized"}),
                _FakeResponse(200, {"jwt": "jwt-token"}),
            ]
        )
        client = LxcPortainerAdminClient(backend=ManagedLxcBackend.LXD, session=session)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime._lxc_manager_ip",
            return_value=ipv4_address(10, 156, 143, 201),
        ):
            client.initialize_admin_user("admin", operator_credential())

        self.assertEqual(4, session.cookies.clear_calls)

    def test_portainer_admin_client_initializes_clean_state_without_followup_auth_probe(self):
        session = _FakeSession([_FakeResponse(200, {"message": "admin initialized"})])
        client = LxcPortainerAdminClient(backend=ManagedLxcBackend.LXD, session=session)

        with patch(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime._lxc_manager_ip",
            return_value=ipv4_address(10, 156, 143, 201),
        ):
            client.initialize_admin_user("admin", operator_credential())

        self.assertEqual(1, len(session.post_calls))
        self.assertTrue(str(session.post_calls[0]["url"]).endswith("/api/users/admin/init"))


class _FakeResponse:
    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self.payload = payload

    def json(self) -> object:
        if isinstance(self.payload, ValueError):
            raise self.payload
        return self.payload


class _FakeSession:
    def __init__(self, post_responses: list[_FakeResponse | requests.RequestException]):
        self.post_responses = list(post_responses)
        self.post_calls: list[dict[str, object]] = []
        self.cookies = _FakeCookies()

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.post_calls.append({"url": url, **kwargs})
        response = self.post_responses.pop(0)
        if isinstance(response, requests.RequestException):
            raise response
        return response


class _FakeCookies(dict[str, str]):
    def __init__(self):
        super().__init__()
        self.clear_calls = 0

    def clear(self) -> None:
        self.clear_calls += 1
        super().clear()

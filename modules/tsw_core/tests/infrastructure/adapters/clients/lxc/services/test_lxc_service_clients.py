import json
import unittest
from unittest.mock import Mock, patch

import requests

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import DeploymentStackRequest
from tiny_swarm_world.application.ports.clients.port_portainer_client import PortainerClientError
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_nexus_http_client import (
    LxcNexusHttpClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_admin_client import (
    LxcPortainerAdminClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client import (
    LxcPortainerHttpClient,
)


class TestLxcServiceClients(unittest.TestCase):
    def test_portainer_explicit_api_url_precedes_manager_ip_resolution(self):
        resolver = Mock(side_effect=AssertionError("local resolver must not run"))
        session = Mock()
        client = LxcPortainerHttpClient(
            backend=ManagedLxcBackend.LXD,
            username="admin",
            password="secret",
            api_url="https://portainer.example/api/",
            session=session,
            manager_ip_resolver=resolver,
        )

        delegate = client._client()

        self.assertEqual("https://portainer.example/api", delegate.base_url)
        self.assertIs(session, delegate.session)
        resolver.assert_not_called()

    def test_existing_stack_update_delegates_actual_put_without_pruning(self):
        session = Mock()
        session.post.return_value = Mock(status_code=200, json=Mock(return_value={"jwt": "jwt-token"}))
        session.request.side_effect = [
            Mock(status_code=200, json=Mock(return_value=[{"Name": "local", "Id": 7}])),
            Mock(status_code=200, json=Mock(return_value=[{"Name": "swagger", "Id": 42, "EndpointId": 7}])),
            Mock(status_code=200, json=Mock(return_value=[{"Name": "local", "Id": 7}])),
            Mock(status_code=200, json=Mock(return_value=[{"Name": "swagger", "Id": 42, "EndpointId": 7}])),
            Mock(status_code=200, json=Mock(return_value={})),
        ]
        client = LxcPortainerHttpClient(
            backend=ManagedLxcBackend.LXD, username="admin", password="secret",
            api_url="https://portainer.example", session=session,
        )
        request = DeploymentStackRequest(
            target_stack="swagger", stack_definition=StackDefinition(name="swagger", compose_content="services: {}"),
            stack_environment={"TSW_JENKINS_IMAGE": "jenkins:latest"},
        )
        with patch.object(client, "_run_manager_shell", side_effect=AssertionError("unexpected host command")) as shell:
            client.apply_stack(request)
        shell.assert_not_called()
        self.assertEqual(session.post.call_count, 1)
        self.assertEqual(session.request.call_count, 5)
        args, kwargs = session.request.call_args
        self.assertEqual(args, ("PUT", "https://portainer.example/api/stacks/42?endpointId=7"))
        self.assertEqual(kwargs["json"], {
            "env": [{"name": "TSW_JENKINS_IMAGE", "value": "jenkins:latest"}],
            "prune": False, "pullImage": False, "stackFileContent": "services: {}",
        })
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer jwt-token")
        self.assertEqual(kwargs["timeout"], 180)

    def test_both_apply_paths_reject_visible_conflicts_and_drift_before_effects(self):
        endpoint = [{"Name": "local", "Id": 7}]
        target = [{"Name": "swagger", "Id": 42, "EndpointId": 7}]
        cases = [
            ([{"Name": "local", "Id": True}], target, endpoint, target),
            ([{"Name": "local", "Id": 0}], target, endpoint, target),
            ([{"Name": "local", "Id": -1}], target, endpoint, target),
            ([{"Name": "local", "Id": "7"}], target, endpoint, target),
            ([{"Name": "primary", "Id": 7}, {"Name": "other", "Id": 8, "URL": "unix:///var/run/docker.sock"}], target, endpoint, target),
            ([{"Name": "other", "Id": 8}], target, endpoint, target),
            ([{"Name": "local", "Id": 7, "URL": "first"}], target,
             [{"Name": "local", "Id": 7, "URL": "second"}], target),
            ([{"Name": "local", "Id": 7, "Type": 1}], target,
             [{"Name": "local", "Id": 7, "Type": 2}], target),
            ([{"Name": "local", "Id": 7, "Status": 1}], target,
             [{"Name": "local", "Id": 7, "Status": 2}], target),
            ([{"Name": "local", "Id": 7}, {"Name": "local", "Id": 8}], target, endpoint, target),
            (endpoint, [{"Name": "swagger", "Id": True, "EndpointId": 7}], endpoint, target),
            (endpoint, [{"Name": "swagger", "Id": -1, "EndpointId": 7}], endpoint, target),
            (endpoint, [{"Name": "swagger", "Id": "42", "EndpointId": 7}], endpoint, target),
            (endpoint, [{"Name": "swagger", "Id": 42, "EndpointId": False}], endpoint, target),
            (endpoint, [{"Name": "swagger", "Id": 42}], endpoint, target),
            (endpoint, [{"Name": "swagger", "Id": 42, "EndpointId": 8}], endpoint, target),
            (endpoint, target + [{"Name": "swagger", "Id": 43, "EndpointId": 7}], endpoint, target),
            (endpoint, target + [{"Name": "other", "Id": 42, "EndpointId": 7}], endpoint, target),
            (endpoint, target, endpoint, []),
            (endpoint, [], [{"Name": "local", "Id": 8}], []),
            (endpoint, {"secret": "response-secret"}, endpoint, []),
        ]
        request = DeploymentStackRequest(
            target_stack="swagger", stack_definition=StackDefinition(name="swagger", compose_content="services: {}"),
        )
        for kind in ("direct", "lxc"):
            for values in cases:
                with self.subTest(kind=kind, values=values):
                    session = Mock()
                    session.post.return_value = Mock(status_code=200, json=Mock(return_value={"jwt": "token-secret"}))
                    session.request.side_effect = [
                        Mock(status_code=200, json=Mock(return_value=value)) for value in values
                    ]
                    if kind == "direct":
                        client = PortainerHttpClient("https://portainer.example", "admin", "password-secret", session=session)
                        with self.assertRaises(PortainerClientError) as raised:
                            client.apply_stack(request)
                    else:
                        client = LxcPortainerHttpClient(
                            backend=ManagedLxcBackend.LXD, username="admin", password="password-secret",
                            api_url="https://portainer.example", session=session,
                        )
                        with patch.object(client, "_ensure_external_overlay_networks") as network:
                            with self.assertRaises(PortainerClientError) as raised:
                                client.apply_stack(request)
                            network.assert_not_called()
                    self.assertNotIn("secret", str(raised.exception))
                    self.assertTrue(all(call.args[0] == "GET" for call in session.request.call_args_list))

    def test_inventory_errors_block_both_apply_paths_at_each_read(self):
        endpoint = [{"Name": "local", "Id": 7}]
        target = [{"Name": "swagger", "Id": 42, "EndpointId": 7}]
        request = DeploymentStackRequest(
            target_stack="swagger", stack_definition=StackDefinition(name="swagger", compose_content="services: {}"),
        )
        for kind in ("direct", "lxc"):
            for position in range(4):
                for failure in ("http", "redirect", "partial", "decode", "network"):
                    with self.subTest(kind=kind, position=position, failure=failure):
                        session = Mock()
                        session.post.return_value = Mock(status_code=200, json=Mock(return_value={"jwt": "jwt-secret"}))
                        responses = [
                            Mock(status_code=200, json=Mock(return_value=value))
                            for value in (endpoint, target, endpoint, target)
                        ]
                        if failure == "network":
                            responses[position] = requests.RequestException("network-secret")
                        elif failure == "decode":
                            responses[position] = Mock(status_code=200, json=Mock(side_effect=ValueError("json-secret")))
                        else:
                            responses[position] = Mock(status_code={"http": 500, "redirect": 302, "partial": 206}[failure])
                        session.request.side_effect = responses
                        if kind == "direct":
                            client = PortainerHttpClient("https://portainer.example", "admin", "password-secret", session=session)
                            with self.assertRaises(PortainerClientError) as raised:
                                client.apply_stack(request)
                        else:
                            client = LxcPortainerHttpClient(
                                backend=ManagedLxcBackend.LXD, username="admin", password="password-secret",
                                api_url="https://portainer.example", session=session,
                            )
                            with patch.object(client, "_ensure_external_overlay_networks") as network:
                                with self.assertRaises(PortainerClientError) as raised:
                                    client.apply_stack(request)
                                network.assert_not_called()
                        self.assertNotIn("secret", str(raised.exception))
                        self.assertTrue(all(call.args[0] == "GET" for call in session.request.call_args_list))
                        self.assertTrue(all(call.kwargs["allow_redirects"] is False for call in session.request.call_args_list))

    def test_inventory_redirects_are_not_followed_by_real_requests_session(self):
        class RedirectTransport(requests.adapters.BaseAdapter):
            def __init__(self, position):
                super().__init__()
                self.position = position
                self.calls = []

            def send(self, request, **kwargs):
                self.calls.append(request.url)
                response = requests.Response()
                response.request = request
                response.url = request.url
                response.status_code = 302 if len(self.calls) == self.position else 200
                response.headers["Location"] = "https://other.example/secret"
                value = [{"Name": "local", "Id": 7}] if request.url.endswith("/endpoints") else [
                    {"Name": "swagger", "Id": 42, "EndpointId": 7}
                ]
                response._content = json.dumps(value).encode()
                return response

            def close(self):
                pass

        request = DeploymentStackRequest(
            target_stack="swagger", stack_definition=StackDefinition(name="swagger", compose_content="services: {}"),
        )
        for kind in ("direct", "lxc"):
            for position in range(1, 5):
                with self.subTest(kind=kind, position=position):
                    session = requests.Session()
                    transport = RedirectTransport(position)
                    session.mount("https://", transport)
                    if kind == "direct":
                        client = PortainerHttpClient("https://portainer.example", "admin", "password", session=session)
                        client._jwt_token = "jwt-secret"
                        with self.assertRaises(PortainerClientError):
                            client.apply_stack(request)
                    else:
                        client = LxcPortainerHttpClient(
                            backend=ManagedLxcBackend.LXD, username="admin", password="password",
                            api_url="https://portainer.example", session=session,
                        )
                        client._client()._jwt_token = "jwt-secret"
                        with patch.object(client, "_ensure_external_overlay_networks") as network:
                            with self.assertRaises(PortainerClientError):
                                client.apply_stack(request)
                            network.assert_not_called()
                    self.assertEqual(len(transport.calls), position)
                    self.assertTrue(all("other.example" not in url for url in transport.calls))

    def test_direct_raw_update_bypasses_inventory_checks(self):
        session = Mock()
        session.post.return_value = Mock(status_code=200, json=Mock(return_value={"jwt": "token"}))
        session.request.return_value = Mock(status_code=200, json=Mock(return_value={}))
        client = PortainerHttpClient("https://portainer.example", "admin", "password", session=session)
        client.update_stack(42, StackDefinition(name="swagger", compose_content="services: {}"), 7)
        self.assertEqual([call.args[0] for call in session.request.call_args_list], ["PUT"])
        self.assertIs(session.request.call_args.kwargs["json"]["prune"], False)

    def test_create_error_does_not_add_uncertain_retry(self):
        for kind in ("direct", "lxc"):
            for failure in ("timeout", "server"):
                with self.subTest(kind=kind, failure=failure):
                    session = Mock()
                    session.post.return_value = Mock(status_code=200, json=Mock(return_value={"jwt": "token"}))
                    values = [
                        Mock(status_code=200, json=Mock(return_value=value)) for value in (
                            [{"Name": "local", "Id": 7}], [], [{"Name": "local", "Id": 7}], [],
                            {"Swarm": {"Cluster": {"ID": "swarm"}}},
                        )
                    ]
                    values.append(requests.Timeout("timeout-secret") if failure == "timeout" else Mock(status_code=500))
                    session.request.side_effect = values
                    request = DeploymentStackRequest(
                        target_stack="swagger", stack_definition=StackDefinition(name="swagger", compose_content="services: {}"),
                    )
                    if kind == "direct":
                        client = PortainerHttpClient("https://portainer.example", "admin", "password", session=session)
                        with self.assertRaises(PortainerClientError):
                            client.apply_stack(request)
                    else:
                        client = LxcPortainerHttpClient(
                            backend=ManagedLxcBackend.LXD, username="admin", password="password",
                            api_url="https://portainer.example", session=session,
                        )
                        with patch.object(client, "_ensure_external_overlay_networks"):
                            with self.assertRaises(PortainerClientError):
                                client.apply_stack(request)
                    self.assertEqual([call.args[0] for call in session.request.call_args_list].count("POST"), 1)

    def test_both_apply_paths_preserve_visible_absence_create_fallback(self):
        for kind in ("direct", "lxc"):
            for fallback in (404, 405):
                with self.subTest(kind=kind, fallback=fallback):
                    session = Mock()
                    session.post.return_value = Mock(status_code=200, json=Mock(return_value={"jwt": "token"}))
                    values = [
                        (200, [{"Name": "local", "Id": 7}]), (200, []),
                        (200, [{"Name": "local", "Id": 7}]), (200, []),
                        (200, {"Swarm": {"Cluster": {"ID": "swarm"}}}),
                        (fallback, {}), (200, {}),
                    ]
                    session.request.side_effect = [
                        Mock(status_code=status, json=Mock(return_value=value)) for status, value in values
                    ]
                    request = DeploymentStackRequest(
                        target_stack="swagger",
                        stack_definition=StackDefinition(name="swagger", compose_content="services: {}"),
                    )
                    if kind == "direct":
                        client = PortainerHttpClient("https://portainer.example", "admin", "password", session=session)
                        client.apply_stack(request)
                    else:
                        client = LxcPortainerHttpClient(
                            backend=ManagedLxcBackend.LXD, username="admin", password="password",
                            api_url="https://portainer.example", session=session,
                        )
                        with patch.object(client, "_ensure_external_overlay_networks") as network:
                            client.apply_stack(request)
                        network.assert_called_once()
                    self.assertEqual([call.args[0] for call in session.request.call_args_list],
                                     ["GET", "GET", "GET", "GET", "GET", "POST", "POST"])
                    self.assertTrue(session.request.call_args_list[-1].args[1].endswith("/api/stacks"))

    def test_portainer_explicit_api_url_rejects_embedded_credentials(self):
        client = LxcPortainerHttpClient(
            backend=ManagedLxcBackend.LXD,
            username="admin",
            password="secret",
            api_url="https://admin:secret@portainer.example/api",
            session=Mock(),
            manager_ip_resolver=Mock(return_value="10.0.0.5"),
        )

        with self.assertRaisesRegex(ValueError, "credentials") as raised:
            client._client()

        self.assertNotIn("secret", str(raised.exception))

    def test_nexus_wrapper_reuses_injected_session_across_delegates(self):
        session = Mock()
        client = LxcNexusHttpClient(
            backend=ManagedLxcBackend.LXD,
            session=session,
            manager_ip_resolver=Mock(return_value="10.0.0.5"),
        )

        first = client._client()
        second = client._client()

        self.assertIs(session, first.session)
        self.assertIs(session, second.session)

    def test_service_clients_use_injected_manager_ip_resolver(self):
        resolver = Mock(return_value="10.0.0.5")
        session = Mock()
        admin = LxcPortainerAdminClient(
            backend=ManagedLxcBackend.LXD,
            session=session,
            manager_ip_resolver=resolver,
        )
        nexus = LxcNexusHttpClient(
            backend=ManagedLxcBackend.LXD,
            session=session,
            manager_ip_resolver=resolver,
        )
        portainer = LxcPortainerHttpClient(
            backend=ManagedLxcBackend.LXD,
            username="admin",
            password="secret",
            session=session,
            manager_ip_resolver=resolver,
        )

        self.assertEqual(admin._base_url(), "http://10.0.0.5:10001")
        self.assertEqual(nexus._base_url(), "http://10.0.0.5:13081")
        self.assertEqual(portainer._base_url(), "http://10.0.0.5:10001")
        self.assertEqual(resolver.call_count, 3)

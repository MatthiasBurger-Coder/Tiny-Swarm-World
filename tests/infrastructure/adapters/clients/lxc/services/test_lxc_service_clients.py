import unittest
from unittest.mock import Mock

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

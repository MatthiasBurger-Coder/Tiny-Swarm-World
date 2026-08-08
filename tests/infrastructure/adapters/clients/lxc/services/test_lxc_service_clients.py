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

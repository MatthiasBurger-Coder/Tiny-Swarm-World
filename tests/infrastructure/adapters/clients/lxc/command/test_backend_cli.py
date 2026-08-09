import unittest

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.backend_cli import (
    BACKEND_CLI,
    backend_cli,
)


class TestBackendCli(unittest.TestCase):
    def test_resolves_incus_and_lxd_from_one_authoritative_mapping(self):
        self.assertEqual(backend_cli(ManagedLxcBackend.INCUS), "incus")
        self.assertEqual(backend_cli(ManagedLxcBackend.LXD), "lxc")
        self.assertEqual(dict(BACKEND_CLI), {
            ManagedLxcBackend.INCUS: "incus",
            ManagedLxcBackend.LXD: "lxc",
        })

    def test_mapping_is_immutable(self):
        with self.assertRaises(TypeError):
            BACKEND_CLI[ManagedLxcBackend.INCUS] = "unexpected"  # type: ignore[index]

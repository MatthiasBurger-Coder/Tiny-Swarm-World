import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository import (
    PortNetplanRepositoryYaml,
)


class TestPortNetplanRepositoryYaml(unittest.TestCase):
    def test_load_returns_nested_netplan_mapping(self):
        repository = PortNetplanRepositoryYaml(file_manager=_FakeFileManager())

        loaded = repository.load()

        self.assertEqual("networkd", loaded["network"]["renderer"])
        self.assertEqual(["10.0.0.2/24"], loaded["network"]["ethernets"]["ens3"]["addresses"])


class _FakeFileManager:
    def load(self, path: Path) -> str:
        return """
network:
  version: 2
  renderer: networkd
  ethernets:
    ens3:
      dhcp4: "no"
      addresses:
        - 10.0.0.2/24
"""

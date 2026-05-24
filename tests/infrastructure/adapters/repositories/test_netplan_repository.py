import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository import (
    PortNetplanRepositoryYaml,
)


class TestPortNetplanRepositoryYaml(unittest.TestCase):
    def test_load_returns_nested_netplan_mapping(self):
        repository = PortNetplanRepositoryYaml(file_manager=_FakeFileManager())

        loaded = repository.load()

        self.assertEqual("networkd", loaded["network"]["renderer"])
        self.assertEqual(["10.0.0.2/24"], loaded["network"]["ethernets"]["ens3"]["addresses"])

    def test_default_repository_writes_generated_netplan_under_local_state(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _create_repository_root(root)
            with patch.dict("os.environ", {"TSW_REPOSITORY_ROOT": str(root)}):
                repository = PortNetplanRepositoryYaml()

                repository.create(_network("10.0.0.2", "10.0.0.1"))
                repository.save()

                generated_file = root / ".tiny-swarm-world" / "generated" / "cloud-init-manager.yaml"
                self.assertTrue(generated_file.exists())
                self.assertNotIn("infra/config", str(repository.file).replace("\\", "/"))
                self.assertIn("10.0.0.2/24", generated_file.read_text(encoding="utf-8"))


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


def _create_repository_root(root: Path) -> None:
    (root / "AGENTS.md").write_text("# test\n", encoding="utf-8")
    (root / "QUALITY.md").write_text("# test\n", encoding="utf-8")
    (root / "src" / "tiny_swarm_world").mkdir(parents=True)
    (root / "infra" / "config").mkdir(parents=True)


def _network(address: str, gateway: str):
    from tiny_swarm_world.domain.network.ip_value import IpValue
    from tiny_swarm_world.domain.network.network import Network

    return Network(
        vm_instance="swarm-manager",
        ip_address=IpValue(ip_address=address),
        gateway=IpValue(ip_address=gateway),
    )

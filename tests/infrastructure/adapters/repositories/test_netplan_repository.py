import unittest
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tests.support.sonar_safe_literals import ipv4_address

from tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository import (
    PortNetplanRepositoryYaml,
)


class TestPortNetplanRepositoryYaml(unittest.TestCase):
    def test_load_returns_nested_netplan_mapping(self):
        repository = PortNetplanRepositoryYaml(file_manager=_FakeFileManager())

        loaded = repository.load()

        self.assertEqual("networkd", loaded["network"]["renderer"])
        self.assertEqual(
            [f"{ipv4_address(10, 0, 0, 2)}/24"],
            loaded["network"]["ethernets"]["ens3"]["addresses"],
        )

    def test_create_returns_static_netplan_mapping(self):
        repository = PortNetplanRepositoryYaml(file_manager=_FakeFileManager())

        generated = repository.create(
            _network(ipv4_address(10, 0, 0, 2), ipv4_address(10, 0, 0, 1))
        )

        ens3 = generated["network"]["ethernets"]["ens3"]
        self.assertEqual("no", ens3["dhcp4"])
        self.assertEqual([f"{ipv4_address(10, 0, 0, 2)}/24"], ens3["addresses"])
        self.assertEqual(
            [{"to": "0.0.0.0/0", "via": ipv4_address(10, 0, 0, 1)}],
            ens3["routes"],
        )
        self.assertEqual(["8.8.8.8", "8.8.4.4"], ens3["nameservers"]["addresses"])

    def test_create_replaces_previous_generated_configuration(self):
        repository = PortNetplanRepositoryYaml(file_manager=_FakeFileManager())

        repository.create(
            _network(ipv4_address(10, 0, 0, 2), ipv4_address(10, 0, 0, 1))
        )
        generated = repository.create(
            _network(ipv4_address(10, 0, 0, 3), ipv4_address(10, 0, 0, 1))
        )

        ens3 = generated["network"]["ethernets"]["ens3"]
        self.assertEqual([f"{ipv4_address(10, 0, 0, 3)}/24"], ens3["addresses"])

    def test_save_uses_injected_file_manager(self):
        file_manager = _FakeFileManager()
        repository = PortNetplanRepositoryYaml(
            file_name="netplan.yaml",
            file_manager=file_manager,
        )

        repository.create(
            _network(ipv4_address(10, 0, 0, 2), ipv4_address(10, 0, 0, 1))
        )
        repository.save()

        self.assertEqual(Path("netplan.yaml"), file_manager.saved_path)
        saved_data = file_manager.saved_data
        assert saved_data is not None
        self.assertIn(f"{ipv4_address(10, 0, 0, 2)}/24", saved_data)
        self.assertIn("nameservers:", saved_data)

    def test_default_repository_writes_generated_netplan_under_local_state(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _create_repository_root(root)
            with patch.dict("os.environ", {"TSW_REPOSITORY_ROOT": str(root)}):
                with patch(
                    "tiny_swarm_world.infrastructure.adapters.repositories.netplan_repository."
                    "LoggerFactory.get_logger",
                    return_value=getLogger("test-netplan-repository"),
                ):
                    repository = PortNetplanRepositoryYaml()

                repository.create(
                    _network(ipv4_address(10, 0, 0, 2), ipv4_address(10, 0, 0, 1))
                )
                repository.save()

                generated_file = root / ".tiny-swarm-world" / "generated" / "cloud-init-manager.yaml"
                self.assertTrue(generated_file.exists())
                self.assertNotIn("infra/config", str(repository.file).replace("\\", "/"))
                self.assertIn(f"{ipv4_address(10, 0, 0, 2)}/24", generated_file.read_text(encoding="utf-8"))


class _FakeFileManager:
    def __init__(self) -> None:
        self.saved_path: Path | None = None
        self.saved_data: str | None = None

    def load(self, path: Path) -> str:
        return f"""
network:
  version: 2
  renderer: networkd
  ethernets:
    ens3:
      dhcp4: "no"
      addresses:
        - {ipv4_address(10, 0, 0, 2)}/24
"""

    def save(self, path: Path, data: str) -> None:
        self.saved_path = path
        self.saved_data = data


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

from ipaddress import IPv4Address
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from tiny_swarm_world.application.ports.repositories.port_yaml_repository import PortYamlRepository
from tiny_swarm_world.domain.network.network import Network
from tiny_swarm_world.infrastructure.adapters.exceptions.exception_yaml_handling import YAMLHandlingError
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import local_state_file
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


GENERATED_NETPLAN_PATH = Path("generated/cloud-init-manager.yaml")
DEFAULT_NAMESERVERS = (
    str(IPv4Address(0x08080808)),
    str(IPv4Address(0x08080404)),
)


class PortNetplanRepositoryYaml(PortYamlRepository):
    """
    Manages the creation, validation, and saving of Netplan configuration using YamlFileManager.
    """

    def __init__(
        self,
        file_name: str | Path | None = None,
        file_manager: FileManager | None = None,
    ):
        self.file = (
            Path(file_name)
            if file_name is not None
            else local_state_file(relative_path=GENERATED_NETPLAN_PATH)
        )
        self.file_manager = file_manager
        self.yaml = YAML()  # Use ruamel.yaml
        self.yaml.default_flow_style = False  # Ensure correct indentation
        self.yaml.indent(mapping=2, sequence=4, offset=2)  # Better formatting
        self.logger = LoggerFactory.get_logger(self.__class__)
        self._generated_configuration: dict[str, Any] | None = None

    def create(self, data: Network) -> Any:
        """Creates a Netplan configuration with static IP, routes, and nameservers."""

        self.logger.info(f"Creating Netplan configuration: {data}")
        self._generated_configuration = {
            "network": {
                "version": 2,
                "renderer": "networkd",
                "ethernets": {
                    "ens3": {
                        "dhcp4": "no",
                        "addresses": [f"{data.ip_address.ip_address}/24"],
                        "routes": [
                            {"to": "0.0.0.0/0", "via": data.gateway.ip_address}
                        ],
                        "nameservers": {"addresses": list(DEFAULT_NAMESERVERS)},
                    }
                },
            }
        }
        return self._generated_configuration

    def load(self) -> Any:
        """Loads an existing Netplan configuration file."""
        try:
            content = self.file_manager.load(self.file) if self.file_manager is not None else self.file.read_text(encoding="utf-8")
            return self.yaml.load(content) or {}
        except FileNotFoundError:
            self.logger.error(f"Netplan configuration file {self.file} not found.")
            return {}

    def save(self) -> None:
        """Saves the generated Netplan configuration file."""
        self.logger.info(f"Saving Netplan configuration: {self._generated_configuration}")
        try:
            content = self._to_yaml(self._generated_configuration or {})
            if self.file_manager is not None:
                self.file_manager.save(self.file, content)
            else:
                self.file.parent.mkdir(parents=True, exist_ok=True)
                self.file.write_text(content, encoding="utf-8")
            self.logger.info(f"YAML file saved successfully: {self.file}")
        except Exception as e:
            self.logger.exception(f"Exception occurred while saving YAML: {str(e)}")
            raise YAMLHandlingError(self.file.name, e)

    def _to_yaml(self, data: dict[str, Any]) -> str:
        output = StringIO()
        self.yaml.dump(data, output)
        return output.getvalue()

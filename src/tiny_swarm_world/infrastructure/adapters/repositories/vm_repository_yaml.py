from pathlib import Path
from typing import List, Optional

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository
from tiny_swarm_world.domain.multipass.vm_entity import VmEntity
from tiny_swarm_world.domain.multipass.vm_type import VmType
from tiny_swarm_world.infrastructure.adapters.exceptions.exception_yaml_handling import YAMLHandlingError
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.yaml.yaml_builder import FluentYAMLBuilder
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory

CONFIG_PATH = "vm_repository.yaml"

class PortVmRepositoryYaml(PortVmRepository):
    """YAML-based VM repository using FluentYAMLBuilder."""

    def __init__(self ):
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.logger.info("Loading VM repository configuration from YAML file.")
        self.config_path = Path(CONFIG_PATH)
        self.file_manager = infra_core_container.resolve(FileManager)
        self.yaml_builder = FluentYAMLBuilder()
        self.yaml = YAML()
        self.loaded_data = self.yaml_builder.load_from_string(self.file_manager.load(self.config_path)).build()

    def save(self) -> None:
        """Saves the YAML configuration file."""
        try:
            self.file_manager.save(self.config_path, self.yaml_builder.to_yaml())
        except OSError as exc:
            self.logger.exception(f"Error saving YAML file: {str(exc)}")
            raise YAMLHandlingError(self.config_path.name, exc) from exc

    def get_all_vms(self) -> List[VmEntity]:
        """Retrieves all VMs as VmEntity objects."""
        self.logger.info("Retrieving all VMs from YAML file.")
        return [VmEntity(**vm) for vm in self.loaded_data.get("vms", [])]

    def get_vm_by_name(self, vm_instance: str) -> Optional[VmEntity]:
        """Finds a VM by its name."""
        for vm in self.get_all_vms():
            if vm.vm_instance == vm_instance:
                return vm
        return None

    def add_vm(self, vm: VmEntity) -> None:
        """Adds a new VM to the YAML configuration."""
        (self.yaml_builder
         .navigate_to(["vms"])
         .current.add_child(vm.model_dump()))
        self.save()

    def remove_vm(self, name: str) -> None:
        """Deletes a VM by name."""
        self.logger.info(f"Removing VM: {name}")
        all_vms = self.get_all_vms()
        self.logger.info(f"all_vms:{all_vms}")
        for vm in all_vms:
            self.logger.info(f"vm:{vm}")
            if vm.vm_instance == name:
                try:
                    self.logger.info(f"Try Deleting VM: {vm}")
                    self.yaml_builder.navigate_to([str(vm.vm_instance)]).delete_current()
                    self.logger.info(f"After Deleted VM: {vm}")
                    self.save()
                    return
                except KeyError as keyError:
                    self.logger.info(f"KeyError: {vm} {keyError}")
                    raise ValueError(f"VM {name} not found.")
            else:
                self.logger.info(f"Name {name} not found in vm.{vm.vm_instance}")
        raise ValueError(f"VM {name} not found.")

    def update_vm(self, vm: VmEntity) -> None:
        """Updates an existing VM by replacing its entire YAML entry if it matches by vm_instance."""
        self.logger.info(f"Updating VM: {vm}")

        updated = False
        vms_list = self.get_all_vms()
        self.logger.info(f"To be updated VM-List: {vms_list}")
        # Search for the existing VM entry by vm_instance and replace it
        for index, existing_vm in enumerate(vms_list):
            if existing_vm.vm_instance == vm.vm_instance:
                vms_list[index] = vm
                updated = True
                break
        self.logger.info(f"Updated VM-List: {vms_list}")
        if not updated:
            raise ValueError(f"VM {vm.vm_instance} not found for update.")

        self.yaml_builder.add_child("vms", vms_list, stay=True).build()
        self.save()

    def find_all_vms(self) -> List[VmEntity]:
        """Retrieves all VMs from the YAML file."""
        return self.get_all_vms()

    def find_vm_instances_by_type(self, vm_type: VmType) -> List[str]:
        """
        Returns a list of all vm_instance names that belong to specific vm_types.

        Args:
            :param vm_type: the vm_type to filter by.

        Returns:
            :rtype List[str]: List of all VM names that belong to these types.
        """

        # Filter and return matching vm_instance names
        return [
            vm.get("vm_instance")
            for vm in self.loaded_data.get("vms", [])
            if vm.get("vm_type") == vm_type.value and vm.get("vm_instance") is not None
        ]

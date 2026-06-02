from abc import ABC, abstractmethod
from typing import List, Optional

from tiny_swarm_world.domain.command.vm_entity import VmEntity
from tiny_swarm_world.domain.command.vm_type import VmType


class PortVmRepository(ABC):
    """Interface for managing VM entities."""

    @abstractmethod
    def get_all_vms(self) -> List[VmEntity]:
        pass

    @abstractmethod
    def get_vm_by_name(self, name: str) -> Optional[VmEntity]:
        pass

    @abstractmethod
    def add_vm(self, vm: VmEntity) -> None:
        pass

    @abstractmethod
    def remove_vm(self, name: str) -> None:
        pass

    @abstractmethod
    def update_vm(self, vm: VmEntity) -> None:
        pass

    @abstractmethod
    def find_all_vms(self) -> List[VmEntity]:
        pass

    @abstractmethod
    def find_vm_instances_by_type(self, vm_type: VmType) -> List[str]:
        pass

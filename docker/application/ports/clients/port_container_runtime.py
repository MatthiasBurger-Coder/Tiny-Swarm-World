from abc import ABC, abstractmethod


class PortContainerRuntime(ABC):
    @abstractmethod
    def find_container_names(self, name_filter: str) -> list[str]:
        pass

    @abstractmethod
    def file_exists(self, container_name: str, file_path: str) -> bool:
        pass

    @abstractmethod
    def read_file(self, container_name: str, file_path: str) -> str:
        pass

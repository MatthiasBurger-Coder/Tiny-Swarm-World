from abc import ABC, abstractmethod

from tiny_swarm_world.domain.artifacts import ContainerImageContract


class PortContainerImagePublisher(ABC):
    @abstractmethod
    def publish_image(self, contract: ContainerImageContract) -> None:
        pass

    @abstractmethod
    def image_available(self, contract: ContainerImageContract) -> bool:
        pass

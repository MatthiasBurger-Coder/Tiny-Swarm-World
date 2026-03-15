from abc import ABC, abstractmethod

class YAMLBuilderAction(ABC):
    @abstractmethod
    def execute(self):
        pass

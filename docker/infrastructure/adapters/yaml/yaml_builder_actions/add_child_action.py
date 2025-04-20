# yaml_builder/actions/add_child_action.py
from typing import Any

from infrastructure.logging.logger_factory import LoggerFactory
from .yaml_builder_action import YAMLBuilderAction
from infrastructure.adapters.yaml.yaml_node import YAMLNode

class AddChildAction(YAMLBuilderAction):
    def __init__(self, builder, name: str, value: Any = None, stay: bool = False):
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.builder = builder
        self.name = name
        self.value = value
        self.stay = stay

    def execute(self):
        """
        Adds a child node to the current node. If the root does not exist,
        creates the root with the given name and value.
        """
        if self.builder.root is None:
            # First child becomes the root node
            self.logger.info(f"root value to be saved: {self.value}")
            self.builder.root = YAMLNode(self.name, self.value)
            self.builder.current = self.builder.root
        else:
            self.logger.info(f"child value to be saved: {self.value}")
            new_child = self.builder.current.add_child(self.name, self.value)
            if not self.stay:
                self.builder.current = new_child

        return self.builder

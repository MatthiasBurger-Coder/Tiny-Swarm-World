# yaml_builder/actions/to_dict_action.py
from typing import Any, Dict, Optional

from infrastructure.logging.logger_factory import LoggerFactory
from .yaml_builder_action import YAMLBuilderAction
from infrastructure.adapters.yaml.yaml_node import YAMLNode

class ToDictAction(YAMLBuilderAction):
    def __init__(self, builder, node: Optional[YAMLNode] = None):
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.builder = builder
        self.node = node or builder.root

    def execute(self) -> Dict[str, Any]:
        """
        Convert the given YAMLNode and its subtree into a nested dictionary.
        Handles lists, custom value objects, and child node merging.
        """
        node = self.node

        if node is None:
            raise ValueError("Cannot convert an empty YAML builder to a dictionary")

        result: Dict[str, Any] = {}

        # If the node holds a list value, return it directly
        if isinstance(node.value, list):
            return {node.name: node.value}

        # If the node has a to_dict() method, use it
        if node.value and hasattr(node.value, "to_dict"):
            return {node.name: node.value.to_dict()}

        # Recursively convert child nodes
        for child in node.children:
            child_dict = ToDictAction(self.builder, child).execute()
            key, value = next(iter(child_dict.items()))

            if key in result:
                if isinstance(result[key], list):
                    result[key].append(value)
                else:
                    result[key] = [result[key], value]
            else:
                result[key] = value
        self.logger.info(f"result: {result} ")
        return {node.name: result} if result else {node.name: {}}

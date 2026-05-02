# yaml_builder/actions/navigate_to_action.py
from typing import List
from .yaml_builder_action import YAMLBuilderAction

class NavigateToAction(YAMLBuilderAction):
    def __init__(self, builder, path: List[str]):
        """
        Initialize the action with the path to navigate.

        :param builder: The FluentYAMLBuilder instance to operate on
        :param path: List of node names representing the navigation path
        """
        self.builder = builder
        self.path = path

    def execute(self):
        """
        Navigate from the root to the node specified by the path.
        If a segment is not found, a KeyError is raised.
        """
        node = self.builder.root
        traversed_path = []

        self.builder.logger.info(f"Navigating to path: {self.path}")

        for key in self.path:
            child = node.find_child(key)
            if child:
                node = child
                traversed_path.append(key)
            else:
                raise KeyError(
                    f"Path not found at segment '{key}' after traversing: {'/'.join(traversed_path)}"
                )

        self.builder.current = node
        return self.builder

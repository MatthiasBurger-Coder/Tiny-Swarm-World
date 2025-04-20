# yaml_builder/actions/navigate_to_recursively_action.py
from .yaml_builder_action import YAMLBuilderAction

class NavigateToRecursivelyAction(YAMLBuilderAction):
    def __init__(self, builder, name: str):
        """
        Initialize the action to recursively search for a node by name.

        :param builder: The FluentYAMLBuilder instance to operate on
        :param name: The name of the node to search for
        """
        self.builder = builder
        self.name = name

    def execute(self):
        """
        Recursively search for a node with the given name starting from the root.
        If found, set it as the current node. If not found, raise a KeyError.
        """

        def recursive_search(node, target_name):
            if node.name == target_name:
                return node
            for child in node.children:
                result = recursive_search(child, target_name)
                if result:
                    return result
            return None

        result = recursive_search(self.builder.root, self.name)
        if not result:
            raise KeyError(f"Node '{self.name}' not found in the tree.")
        self.builder.current = result
        return self.builder

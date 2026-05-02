# yaml_builder/actions/find_entry_action.py
from typing import Any, Dict, Optional
from .yaml_builder_action import YAMLBuilderAction

class FindEntryAction(YAMLBuilderAction):
    def __init__(self, builder, name: str):
        """
        Initialize the action to find an entry by its name.

        :param builder: The FluentYAMLBuilder instance to operate on
        :param name: The name of the entry to search for
        """
        self.builder = builder
        self.name = name
        self.result: Optional[Dict[str, Any]] = None

    def execute(self):
        """
        Search through the root's children for a node with the given name.
        If found, convert it to a dictionary and store it in self.result.
        """
        for child in self.builder.root.children:
            if child.name == self.name:
                self.result = self.builder.to_dict(child)
                return self.result

        self.result = None
        return self.result

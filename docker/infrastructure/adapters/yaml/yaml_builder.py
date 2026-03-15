from typing import Any, Dict, List, Optional

from infrastructure.adapters.yaml.yaml_builder_actions.add_child_action import AddChildAction
from infrastructure.adapters.yaml.yaml_builder_actions.delete_current_action import DeleteCurrentAction
from infrastructure.adapters.yaml.yaml_builder_actions.find_entry_action import FindEntryAction
from infrastructure.adapters.yaml.yaml_builder_actions.load_from_string_action import LoadFromStringAction
from infrastructure.adapters.yaml.yaml_builder_actions.navigate_to_action import NavigateToAction
from infrastructure.adapters.yaml.yaml_builder_actions.navigate_to_recursively_action import NavigateToRecursivelyAction
from infrastructure.adapters.yaml.yaml_builder_actions.to_dict_action import ToDictAction
from infrastructure.adapters.yaml.yaml_builder_actions.to_yaml_action import ToYAMLAction
from infrastructure.adapters.yaml.yaml_node import YAMLNode
from infrastructure.logging.logger_factory import LoggerFactory


class FluentYAMLBuilder:
    """Fluent API Builder for constructing properly formatted YAML structures using ruamel.yaml."""

    def __init__(self, root_name: Optional[str] = None):
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.root = YAMLNode(root_name) if root_name else None
        self.current = self.root

    def add_child(self, name: str, value: Any = None, stay: bool = False) -> "FluentYAMLBuilder":
        """Adds a child node and ensures that a root node exists if missing."""
        return AddChildAction(self, name, value, stay).execute()

    def navigate_to(self, path: List[str]) -> "FluentYAMLBuilder":
        """Navigate to a specific entry by path. Supports navigation into list items using string indexes."""
        return NavigateToAction(self, path).execute()

    def navigate_to_recursively(self, name: str) -> "FluentYAMLBuilder":
        """Recursively find a node by its name, starting from the root."""
        return NavigateToRecursivelyAction(self, name).execute()

    def delete_current(self) -> "FluentYAMLBuilder":
        """Deletes the current node and its subtree."""
        return DeleteCurrentAction(self).execute()

    def insert_at_current(self, name: str, value: Any = None) -> "FluentYAMLBuilder":
        """Inserts a new node at the current position."""
        self.current.add_child(name, value)
        return self

    def find_entry(self, name: str) -> Optional[Dict[str, Any]]:
        """Finds an entry by name and returns its dictionary representation."""
        return FindEntryAction(self, name).execute()

    def find_all_entries(self) -> List[Dict[str, Any]]:
        """Returns all entries as a list of dictionaries."""
        return [self.to_dict(child) for child in self.root.children]

    def up(self) -> "FluentYAMLBuilder":
        """Moves up one level in the tree if a parent exists."""
        if self.current.parent:
            self.current = self.current.parent
        return self

    def build(self):
        """Constructs the YAML dictionary."""
        return self.to_dict()

    def to_dict(self, node: Optional[YAMLNode] = None) -> Dict[str, Any]:
        """Converts the tree structure into a correctly formatted dictionary for YAML export."""
        return ToDictAction(self, node).execute()

    def to_yaml(self) -> str:
        return ToYAMLAction(self).execute()

    def load_from_string(self, yaml_content: str) -> "FluentYAMLBuilder":
        """Parses a YAML-formatted string and builds a corresponding tree structure using add_child()."""
        return LoadFromStringAction(self, yaml_content).execute()
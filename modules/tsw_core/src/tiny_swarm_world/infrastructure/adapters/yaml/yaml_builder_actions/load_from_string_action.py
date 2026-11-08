# yaml_builder/actions/load_from_string_action.py
from ruamel.yaml import YAML
from .yaml_builder_action import YAMLBuilderAction

class LoadFromStringAction(YAMLBuilderAction):
    def __init__(self, builder, yaml_content: str):
        """
        Initialize the action to load a YAML string into the internal tree structure.

        :param builder: The FluentYAMLBuilder instance to operate on
        :param yaml_content: The YAML content as a string
        """
        self.builder = builder
        self.yaml_content = yaml_content

    def execute(self):
        """
        Parses the YAML string and constructs a tree using FluentYAMLBuilder logic.
        Ensures the root matches or is created based on the YAML content.
        """
        yaml = YAML()
        data = yaml.load(self.yaml_content) or {}

        if not isinstance(data, dict):
            raise ValueError("Invalid YAML format, expected a dictionary with a root key.")

        root_key = next(iter(data.keys()))
        if self.builder.root is None:
            self.builder.add_child(root_key, stay=True)
        else:
            if self.builder.root.name != root_key:
                raise ValueError(
                    f"Root mismatch! Expected '{self.builder.root.name}', but found '{root_key}' in YAML."
                )

        # Recursively insert all content under the root
        self._parse_dict_to_tree(data[root_key])
        return self.builder

    def _parse_dict_to_tree(self, data):
        """
        Recursively walks through the data structure and builds the internal tree.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                self.builder.add_child(key, stay=True)
                self._parse_dict_to_tree(value)
                self.builder.up()
        elif isinstance(data, list):
            self.builder.current.value = data
        else:
            self.builder.current.value = type(self.builder.current.value)(data)

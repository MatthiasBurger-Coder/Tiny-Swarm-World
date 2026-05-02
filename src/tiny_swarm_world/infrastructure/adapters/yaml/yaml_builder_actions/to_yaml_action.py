# yaml_builder/actions/to_yaml_action.py
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from .yaml_builder_action import YAMLBuilderAction

class ToYAMLAction(YAMLBuilderAction):
    def __init__(self, builder):
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.builder = builder

    def execute(self) -> str:
        """
        Convert the builder's current tree structure to a properly formatted YAML string.
        """
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)

        output = StringIO()
        yaml.dump(self.builder.to_dict(), output)
        self.logger.info(f"Output:{output.getvalue()}")
        return output.getvalue()

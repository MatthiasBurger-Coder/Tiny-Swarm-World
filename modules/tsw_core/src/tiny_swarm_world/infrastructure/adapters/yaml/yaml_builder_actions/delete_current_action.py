# yaml_builder/actions/delete_current_action.py
from .yaml_builder_action import YAMLBuilderAction

class DeleteCurrentAction(YAMLBuilderAction):
    def __init__(self, builder):
        """
        Initialize the action to delete the current node.

        :param builder: The FluentYAMLBuilder instance to operate on
        """
        self.builder = builder

    def execute(self):
        """
        Deletes the current node and its subtree. If the current node is the root,
        an error is logged and a ValueError is raised.
        """
        if self.builder.current.parent:
            parent = self.builder.current.parent
            parent.remove_child(self.builder.current.name)
            self.builder.current = parent
        else:
            self.builder.logger.error("Cannot delete root node")
            raise ValueError("Cannot delete root node")

        return self.builder

"""Failure bridges for lifecycle configuration and evidence repositories."""
from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure


class RepositoryStorageError(OperationError, OSError):
    """Expected filesystem failure at a repository boundary."""


class RepositoryConfigurationError(OperationError, ValueError):
    """Expected invalid repository data with safe existing validation wording."""

    def __init__(self, message: str, *, failure: OperationFailure | None = None):
        super().__init__(failure or OperationFailure.for_cause("configuration.load", "repository", "configuration_invalid"))
        self.args = (message,)


class RepositoryNotFoundError(OperationError, FileNotFoundError):
    """Selected configuration is absent without exposing its filesystem path."""

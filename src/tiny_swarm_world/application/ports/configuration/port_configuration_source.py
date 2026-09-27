from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure

from abc import ABC, abstractmethod
from collections.abc import Mapping


class ConfigurationSourceLoadError(OperationError, ValueError):
    def __init__(self, message: str, *, safe_detail: str | None = None, failure: OperationFailure | None = None) -> None:
        super().__init__(failure or OperationFailure.for_cause("configuration.load", "configuration_source", "configuration_invalid"))
        self.args = (message,)
        self.safe_detail = safe_detail


class PortConfigurationSource(ABC):
    @abstractmethod
    def load(self) -> Mapping[str, str]:
        pass

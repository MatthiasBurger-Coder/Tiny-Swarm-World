from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.update import ClassicUpdatePlan, ClassicUpdateState


class PortUpdateStateStore(ABC):
    @abstractmethod
    def save(self, plan: ClassicUpdatePlan) -> ClassicUpdateState:
        pass

    @abstractmethod
    def load(self, stack_name: str, service_name: str) -> ClassicUpdateState | None:
        pass


class UpdateStateStorageError(OperationError, OSError):
    """Expected storage failure; retains the legacy OSError catch contract."""


class UpdateStateInvalidError(OperationError, ValueError):
    """Malformed persisted state; retains the legacy ValueError catch contract."""

from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class InfisicalBootstrapState(str, Enum):
    CREATED = "created"
    ALREADY_INITIALIZED = "already_initialized"


@dataclass(frozen=True)
class InfisicalBootstrapResult:
    state: InfisicalBootstrapState
    token_returned: bool = False
    organization: str = ""
    admin_email: str = ""


class PortInfisicalBootstrapClient(ABC):
    @abstractmethod
    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        pass


class InfisicalBootstrapError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""


class InfisicalBootstrapUnavailable(InfisicalBootstrapError):
    def __init__(self, status_code: int | None = None, reason: str = "not_ready", *, failure: OperationFailure | None = None):
        super().__init__(failure or OperationFailure.for_cause("service.ready", "infisical", "dependency_unavailable"))
        self.status_code = status_code
        self.reason = reason

    @classmethod
    def from_exception(cls, exc: Exception) -> "InfisicalBootstrapUnavailable":
        return cls(reason=exc.__class__.__name__)

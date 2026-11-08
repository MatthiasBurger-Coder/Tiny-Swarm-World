from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.preflight import HostPreparationResult


class PortHostPreparation(ABC):
    @abstractmethod
    def prepare(self) -> HostPreparationResult:
        """Apply the host-specific preparation contract."""

        raise NotImplementedError

    @abstractmethod
    def verify(self) -> HostPreparationResult:
        """Verify host preparation without changing state."""

        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> HostPreparationResult:
        """Remove only state owned by the host-preparation adapter."""

        raise NotImplementedError


class HostPreparationError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

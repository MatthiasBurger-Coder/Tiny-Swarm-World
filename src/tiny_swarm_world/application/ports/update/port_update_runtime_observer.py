from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.update import UpdateRuntimeObservation


class UpdateObservationError(OperationError, RuntimeError):
    """Runtime state could not be observed completely and safely."""

    def __init__(self, message: str, *, failure: OperationFailure | None = None):
        cause = "observation_changed" if isinstance(self, UpdateObservationChanged) else "observation_unavailable"
        super().__init__(failure or OperationFailure.for_cause("update.observe", "runtime_observer", cause))
        # Legacy reason codes remain available without accepting raw diagnostics.
        self.args = (message if message in {
            "invalid_service_identity", "runtime_observation_unavailable", "runtime_command_failed",
            "service_changed_during_observation", "runtime_identity_mismatch",
        } else self.failure.cause,)


class UpdateObservationChanged(UpdateObservationError):
    """The same service changed while its runtime snapshot was being read."""


class PortUpdateRuntimeObserver(ABC):
    @abstractmethod
    async def observe(
        self, stack_name: str, service_name: str
    ) -> UpdateRuntimeObservation:
        """Read service and task state without deploying or altering the runtime."""

from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass

from tiny_swarm_world.domain.deployment import StackDefinition


@dataclass(frozen=True)
class SwarmServiceStatus:
    service_name: str
    current_replicas: int
    desired_replicas: int

    @property
    def ready(self) -> bool:
        return self.desired_replicas > 0 and self.current_replicas >= self.desired_replicas


class PortSwarmStackRuntime(ABC):
    """Application port for the proven Docker Swarm deployment operations."""

    @abstractmethod
    def deploy_stack(
        self,
        stack_definition: StackDefinition,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    def stack_exists(self, stack_name: str) -> bool:
        pass

    @abstractmethod
    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        pass

    @abstractmethod
    def external_secret_exists(self, name: str) -> bool:
        pass

    @abstractmethod
    def ensure_external_secret(self, name: str, value: str) -> None:
        pass


class SwarmRuntimeError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

    def __init__(self, failure, *, exit_code: int | None = None, detail: str = ""):
        super().__init__(failure)
        allowed_details = {
            "", "Existing Traefik TLS secrets are not a verified owned pair.",
            "Partial Traefik TLS secret state is not verified as TSW-owned.",
            "Traefik TLS secret-pair reconciliation could not be verified.",
            "Traefik TLS secret-pair ownership could not be verified.",
            "Created Traefik TLS secret identifiers could not be verified.",
        }
        if detail not in allowed_details:
            raise ValueError("Runtime error detail must be a declared safe message.")
        if exit_code is not None and type(exit_code) is not int:
            raise TypeError("Process exit code must be numeric.")
        if failure.operation == "service.resolve":
            detail = {
                "process_timeout": "LXC manager IP lookup timed out.",
                "process_exit_failed": "LXC manager IP lookup failed.",
                "observation_unavailable": "LXC manager IP lookup returned no IPv4 address.",
            }.get(failure.cause, detail)
        elif failure.cause == "process_timeout":
            detail = "LXC Swarm operation timed out."
        if exit_code is not None:
            detail += f" Process failed with exit code {exit_code}."
        self.args = (f"{detail} {self.args[0]}".strip(),)

from __future__ import annotations

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

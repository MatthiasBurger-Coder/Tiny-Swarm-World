from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from tiny_swarm_world.domain.deployment import StackDefinition


class DeploymentStackUpdatePolicy(str, Enum):
    CREATE_OR_UPDATE = "create_or_update"


@dataclass(frozen=True)
class DeploymentStackRequest:
    target_stack: str
    stack_definition: StackDefinition
    stack_environment: Mapping[str, str] = field(default_factory=dict)
    update_policy: DeploymentStackUpdatePolicy = DeploymentStackUpdatePolicy.CREATE_OR_UPDATE


class PortDeploymentGateway(ABC):
    @abstractmethod
    def apply_stack(self, request: DeploymentStackRequest) -> None:
        pass

    @abstractmethod
    def stack_registered(self, stack_name: str) -> bool:
        pass

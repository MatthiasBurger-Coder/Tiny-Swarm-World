"""Authenticated management API and private journal seams."""
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.lifecycle.managed_stack import ManagedStackIntent
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership


@dataclass(frozen=True)
class ManagedStackSnapshot:
    ownership: PortainerOwnership
    definition: StackDefinition = field(repr=False)
    environment: Mapping[str, str] = field(repr=False)


@dataclass(frozen=True)
class ManagedStackReceipt:
    stack_id: int
    resource_control_id: int
    ownership_fingerprint: str


class ManagedStackApi(Protocol):
    def local_endpoint(self) -> int: ...
    def require_absent(self, name: str, endpoint: int) -> None: ...
    def inspect(self, name: str, endpoint: int, stack_id: int) -> ManagedStackSnapshot: ...
    def create(self, definition: StackDefinition, endpoint: int, environment: Mapping[str, str]) -> ManagedStackReceipt: ...
    def update(self, expected: ManagedStackSnapshot, definition: StackDefinition) -> None: ...


class ManagedStackJournal(Protocol):
    def load(self) -> ManagedStackIntent | None: ...
    def save(self, value: ManagedStackIntent) -> None: ...

"""Pure desired/current state projection and reconciliation planning."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from tiny_swarm_world.domain.inventory.desired_inventory import (
    DesiredInventory,
    VmDesiredState,
)
from tiny_swarm_world.domain.inventory.observed_inventory import (
    ArtifactRegistryObservedState,
    ObservedInventory,
    StackObservedState,
    VmObservedState,
)


@dataclass(frozen=True)
class DesiredState:
    """Reconciliation input describing the resources that should exist."""

    vms: tuple[VmDesiredState, ...] = field(default_factory=tuple)
    stacks: tuple[str, ...] = field(default_factory=tuple)
    artifact_registries: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "vms", tuple(self.vms))
        object.__setattr__(self, "stacks", tuple(self.stacks))
        object.__setattr__(self, "artifact_registries", tuple(self.artifact_registries))

    @classmethod
    def from_inventory(cls, inventory: DesiredInventory) -> "DesiredState":
        return cls(
            vms=inventory.vms,
            stacks=inventory.expected_stacks,
            artifact_registries=inventory.expected_artifact_registries,
        )


@dataclass(frozen=True)
class CurrentState:
    """Reconciliation input describing the observed resources."""

    vms: tuple[VmObservedState, ...] = field(default_factory=tuple)
    stacks: tuple[StackObservedState, ...] = field(default_factory=tuple)
    artifact_registries: tuple[ArtifactRegistryObservedState, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "vms", tuple(self.vms))
        object.__setattr__(self, "stacks", tuple(self.stacks))
        object.__setattr__(self, "artifact_registries", tuple(self.artifact_registries))

    @classmethod
    def from_inventory(cls, inventory: ObservedInventory) -> "CurrentState":
        return cls(
            vms=inventory.vms,
            stacks=inventory.stacks,
            artifact_registries=inventory.artifact_registries,
        )


class ReconcileActionKind(str, Enum):
    NOOP = "noop"
    CREATE = "create"
    UPDATE = "update"
    REMOVE = "remove"


class ReconcileResourceKind(str, Enum):
    VM = "vm"
    STACK = "stack"
    ARTIFACT_REGISTRY = "artifact_registry"
    INVENTORY = "inventory"


@dataclass(frozen=True)
class ReconcileAction:
    resource_kind: ReconcileResourceKind
    resource_name: str
    kind: ReconcileActionKind
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "resource_kind": self.resource_kind.value,
            "resource_name": self.resource_name,
            "kind": self.kind.value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ReconcilePlan:
    """Immutable, explainable output that an execution service may consume."""

    actions: tuple[ReconcileAction, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "actions", tuple(self.actions))

    @property
    def is_noop(self) -> bool:
        return all(action.kind is ReconcileActionKind.NOOP for action in self.actions)

    def to_dict(self) -> dict[str, object]:
        return {"actions": [action.to_dict() for action in self.actions]}


class ReconcileResultStatus(str, Enum):
    APPLIED = "applied"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class ReconcileResult:
    """Typed execution result kept separate from plan generation."""

    action: ReconcileAction
    status: ReconcileResultStatus
    message: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status is not ReconcileResultStatus.FAILED


class ReconcilePlanner:
    """Compare state values without I/O or infrastructure side effects."""

    def plan(self, desired: DesiredState, current: CurrentState) -> ReconcilePlan:
        actions = [
            *self._plan_vms(desired.vms, current.vms),
            *self._plan_named(
                ReconcileResourceKind.STACK,
                desired.stacks,
                (stack.name for stack in current.stacks),
            ),
            *self._plan_named(
                ReconcileResourceKind.ARTIFACT_REGISTRY,
                desired.artifact_registries,
                (registry.name for registry in current.artifact_registries),
            ),
        ]
        if not actions:
            actions.append(
                ReconcileAction(
                    ReconcileResourceKind.INVENTORY,
                    "platform",
                    ReconcileActionKind.NOOP,
                    "Desired and current state are both empty.",
                )
            )
        return ReconcilePlan(tuple(sorted(actions, key=_action_sort_key)))

    @staticmethod
    def _plan_vms(
        desired: tuple[VmDesiredState, ...],
        current: tuple[VmObservedState, ...],
    ) -> list[ReconcileAction]:
        desired_by_name = {vm.name: vm for vm in desired}
        current_by_name = {vm.name: vm for vm in current}
        actions: list[ReconcileAction] = []
        for name in sorted(set(desired_by_name) | set(current_by_name)):
            target = desired_by_name.get(name)
            observed = current_by_name.get(name)
            if target is None:
                actions.append(_action(ReconcileResourceKind.VM, name, ReconcileActionKind.REMOVE,
                                       "VM is not present in desired state."))
            elif observed is None:
                actions.append(_action(ReconcileResourceKind.VM, name, ReconcileActionKind.CREATE,
                                       "VM is missing from current state."))
            elif target.role != observed.role:
                actions.append(_action(ReconcileResourceKind.VM, name, ReconcileActionKind.UPDATE,
                                       "VM role differs from desired state."))
            else:
                actions.append(_action(ReconcileResourceKind.VM, name, ReconcileActionKind.NOOP,
                                       "VM matches the reconciled state."))
        return actions

    @staticmethod
    def _plan_named(
        resource_kind: ReconcileResourceKind,
        desired: tuple[str, ...],
        current: Iterable[str],
    ) -> list[ReconcileAction]:
        desired_names = set(desired)
        current_names = set(current)
        actions: list[ReconcileAction] = []
        for name in sorted(desired_names | current_names):
            if name not in current_names:
                kind, reason = ReconcileActionKind.CREATE, "Resource is missing from current state."
            elif name not in desired_names:
                kind, reason = ReconcileActionKind.REMOVE, "Resource is not present in desired state."
            else:
                kind, reason = ReconcileActionKind.NOOP, "Resource is present in both states."
            actions.append(_action(resource_kind, name, kind, reason))
        return actions


def _action(
    resource_kind: ReconcileResourceKind,
    resource_name: str,
    kind: ReconcileActionKind,
    reason: str,
) -> ReconcileAction:
    return ReconcileAction(resource_kind, resource_name, kind, reason)


def _action_sort_key(action: ReconcileAction) -> tuple[str, str, str]:
    return (action.resource_kind.value, action.resource_name, action.kind.value)

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


DESIRED_INVENTORY_FIELDS = frozenset(
    {
        "schema_version",
        "vms",
        "expected_stacks",
        "expected_artifact_registries",
    }
)
VM_DESIRED_STATE_FIELDS = frozenset(
    {
        "name",
        "role",
        "image",
        "memory",
        "disk",
        "cpu_count",
        "networks",
        "stacks",
    }
)


@dataclass(frozen=True)
class VmDesiredState:
    name: str
    role: str = "manager"
    image: str = ""
    memory: str = ""
    disk: str = ""
    cpu_count: int | None = None
    networks: tuple[str, ...] = field(default_factory=tuple)
    stacks: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("desired VM name must not be empty")
        object.__setattr__(self, "networks", _string_tuple(self.networks))
        object.__setattr__(self, "stacks", _string_tuple(self.stacks))

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "role": self.role,
            "image": self.image,
            "memory": self.memory,
            "disk": self.disk,
            "cpu_count": self.cpu_count,
            "networks": list(self.networks),
            "stacks": list(self.stacks),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "VmDesiredState":
        _reject_unknown_fields(data, VM_DESIRED_STATE_FIELDS, "desired VM state")
        return cls(
            name=str(data.get("name", "")),
            role=str(data.get("role", "manager")),
            image=str(data.get("image", "")),
            memory=str(data.get("memory", "")),
            disk=str(data.get("disk", "")),
            cpu_count=_optional_int(data.get("cpu_count")),
            networks=_string_sequence(data.get("networks", ())),
            stacks=_string_sequence(data.get("stacks", ())),
        )


@dataclass(frozen=True)
class DesiredInventory:
    vms: tuple[VmDesiredState, ...] = field(default_factory=tuple)
    expected_stacks: tuple[str, ...] = field(default_factory=tuple)
    expected_artifact_registries: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "vms", tuple(self.vms))
        object.__setattr__(self, "expected_stacks", _string_tuple(self.expected_stacks))
        object.__setattr__(
            self,
            "expected_artifact_registries",
            _string_tuple(self.expected_artifact_registries),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "vms": [vm.to_dict() for vm in self.vms],
            "expected_stacks": list(self.expected_stacks),
            "expected_artifact_registries": list(self.expected_artifact_registries),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "DesiredInventory":
        _reject_unknown_fields(data, DESIRED_INVENTORY_FIELDS, "desired inventory")
        return cls(
            schema_version=str(data.get("schema_version", "1")),
            vms=tuple(VmDesiredState.from_dict(vm) for vm in _mapping_sequence(data.get("vms", ()))),
            expected_stacks=_string_sequence(data.get("expected_stacks", ())),
            expected_artifact_registries=_string_sequence(
                data.get("expected_artifact_registries", ())
            ),
        )


def _string_tuple(values: Sequence[object]) -> tuple[str, ...]:
    if isinstance(values, str):
        raise ValueError("inventory collection fields must not be strings")
    return tuple(str(value) for value in values)


def _object_sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError("inventory collection fields must be sequences")
    return tuple(value)


def _string_sequence(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in _object_sequence(value))


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    items = _object_sequence(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError("inventory state entries must be mappings")
    return tuple(item for item in items if isinstance(item, Mapping))


def _reject_unknown_fields(
    data: Mapping[str, object],
    allowed_fields: frozenset[str],
    context: str,
) -> None:
    unknown_fields = sorted(str(key) for key in data if str(key) not in allowed_fields)
    if unknown_fields:
        raise ValueError(f"{context} contains unsupported fields: {unknown_fields}")


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError("integer inventory fields must be integers or strings")

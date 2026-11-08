"""Typed observed-node and teardown models used by the LXC facade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeSpec
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import (
    LxcNodeCommandResult,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.node.safety import (
    IMAGE_ALIAS_MARKER,
    MANAGED_MARKER,
    NODE_MARKER,
    has_unsafe_instance_config,
    has_unsafe_instance_devices,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfig,
    NodeProviderNodeConfig,
)


@dataclass(frozen=True)
class TeardownNodePlan:
    node: NodeSpec
    backend: ManagedLxcBackend
    config: NodeProviderConfig


@dataclass(frozen=True)
class ObservedNode:
    name: str
    status: str
    instance_type: str
    profiles: tuple[str, ...]
    config: Mapping[str, str]
    devices: Mapping[str, Mapping[str, str]]

    @property
    def running(self) -> bool:
        return self.status.casefold() == "running"

    def matches_expected(self, node_config: NodeProviderNodeConfig) -> bool:
        return not self.mismatch_reasons(node_config)

    def mismatch_reasons(
        self,
        node_config: NodeProviderNodeConfig,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.instance_type.casefold() != "container":
            reasons.append("instance_type_not_container")
        if any(profile not in self.profiles for profile in node_config.expected_profiles):
            reasons.append("expected_profile_missing")
        if self.config.get(MANAGED_MARKER) != "true":
            if MANAGED_MARKER in self.config:
                reasons.append("managed_marker_not_true")
            else:
                reasons.append("managed_marker_missing")
        if self.config.get(NODE_MARKER) != node_config.spec.name:
            reasons.append("node_marker_mismatch")
        if self.config.get(IMAGE_ALIAS_MARKER) != node_config.image_alias:
            reasons.append("image_alias_marker_mismatch")
        if has_unsafe_instance_config(self.config):
            reasons.append("unsafe_instance_config")
        if has_unsafe_instance_devices(self.devices):
            reasons.append("unsafe_instance_devices")
        return tuple(reasons)


@dataclass(frozen=True)
class NodeLookup:
    returncode: int
    node: ObservedNode | None = None
    timed_out: bool = False
    parse_failed: bool = False

    @property
    def failed(self) -> bool:
        return self.timed_out or self.parse_failed or self.returncode != 0

    @classmethod
    def failed_result(cls, result: LxcNodeCommandResult) -> NodeLookup:
        return cls(returncode=result.returncode, timed_out=result.timed_out)

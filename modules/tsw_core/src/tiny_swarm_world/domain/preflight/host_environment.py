"""Compatibility exports for the side-effect-free host environment domain model."""

from tiny_swarm_world.domain.host_environment import (
    HOST_FIELD_MAX_LENGTH,
    SIGNAL_TEXT_MAX_LENGTH,
    HostEnvironmentKind,
    HostEnvironmentReport,
    HostEnvironmentSignals,
    SetupPath,
    classify_host_environment,
)

__all__ = [
    "HOST_FIELD_MAX_LENGTH",
    "SIGNAL_TEXT_MAX_LENGTH",
    "HostEnvironmentKind",
    "HostEnvironmentReport",
    "HostEnvironmentSignals",
    "SetupPath",
    "classify_host_environment",
]

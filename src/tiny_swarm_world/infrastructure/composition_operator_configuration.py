"""Composition-boundary loader for the optional operator override file."""

from __future__ import annotations

from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.configuration import (
    ShellEnvFileConfigurationSource,
)


def load_operator_configuration(path: Path) -> dict[str, str]:
    """Load operator values without exposing a concrete adapter to callers."""
    return dict(ShellEnvFileConfigurationSource(path).load())

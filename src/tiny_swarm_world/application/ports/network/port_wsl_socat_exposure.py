from __future__ import annotations

from tiny_swarm_world.application.ports.operation_result import OperationError

from typing import Protocol


class PortWslSocatExposure(Protocol):
    """Infrastructure boundary for optional WSL Socat process exposure."""

    async def is_available(self) -> bool:
        """Return whether the optional Socat executable is available."""

    async def process_exists(self, command: str) -> bool:
        """Return whether the requested forwarding command already exists."""

    async def start(self, command: str) -> bool:
        """Start the requested forwarding command and report launch success."""


class SocatExposureError(OperationError, RuntimeError):
    """Declared capability failure with safe operation context."""

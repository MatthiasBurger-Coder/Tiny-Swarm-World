from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.preflight.readiness import (
    ReadinessCheckResult,
    ReadinessProbeRequest,
)


class PortLiveReadiness(ABC):
    """Application boundary for one bounded, read-only live observation."""

    @abstractmethod
    def check(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        """Return a typed, redacted result without performing mutation."""

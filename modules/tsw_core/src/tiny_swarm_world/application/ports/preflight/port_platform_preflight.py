from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.preflight import LiveConsent, PreflightResult


class PortPlatformPreflight(ABC):
    """Read-only platform prerequisite validation used before mutation."""

    @abstractmethod
    async def run(self, live_consent: LiveConsent | None = None) -> PreflightResult:
        """Return checks, collaborator coverage and summary-persistence state.

        Legacy check success does not imply complete qualification or release
        evidence acceptance. Implementations must report these boundaries
        explicitly without applying platform state.
        """

        raise NotImplementedError

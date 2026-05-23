from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.inventory import VerificationResult


class PortVerificationEvidenceRepository(ABC):
    @abstractmethod
    def append(self, result: VerificationResult) -> None:
        """Append a local verification result without storing raw command output."""

    @abstractmethod
    def list_all(self) -> tuple[VerificationResult, ...]:
        """Return recorded local verification results."""

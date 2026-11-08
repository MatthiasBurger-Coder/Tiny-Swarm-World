from __future__ import annotations

from abc import ABC, abstractmethod

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.preflight.secret_storage import SecretStorageInspection


class PortSecretStorageProbe(ABC):
    @abstractmethod
    def effective_identity(self) -> tuple[int, int]:
        """Return the uid and gid that must own mutable live secrets."""

    @abstractmethod
    def inspect(
        self,
        path: str,
        host_environment: HostEnvironmentKind,
    ) -> SecretStorageInspection:
        """Return safe filesystem facts for a live secret path."""

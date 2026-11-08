"""Typed boundary for validated secret manifest configuration."""
from abc import ABC, abstractmethod

from tiny_swarm_world.domain.configuration.secret_manifest import SecretManifestEntry


class PortSecretManifestRepository(ABC):
    @abstractmethod
    def load(self) -> tuple[SecretManifestEntry, ...]:
        """Return validated entries or raise SecretManifestValidationError."""

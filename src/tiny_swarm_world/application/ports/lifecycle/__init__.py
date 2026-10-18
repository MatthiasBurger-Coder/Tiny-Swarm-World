"""Lifecycle storage and catalog ports."""
from dataclasses import dataclass
from typing import Protocol

from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, InstallationManifest


class LifecycleStateError(ValueError):
    """Sanitized, actionable lifecycle-state diagnostic."""


@dataclass(frozen=True)
class ManifestSnapshot:
    manifest: InstallationManifest | None
    token: str | None
    diagnostics: tuple[str, ...] = ()


class ManifestRepository(Protocol):
    def load(self) -> ManifestSnapshot: ...
    def save(self, manifest: InstallationManifest, *, expected_token: str | None) -> ManifestSnapshot: ...


class CatalogRepository(Protocol):
    def load(self) -> ComponentCatalog: ...

"""Sanitized, read-only projection of a v1 migration policy preview."""
from __future__ import annotations

from tiny_swarm_world.application.ports.lifecycle import CatalogRepository, ManifestRepository
from tiny_swarm_world.domain.lifecycle.manifest_v2 import preview_migration


CLASSIC_STACK_IDS = frozenset({
    "traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger", "infisical", "service-access",
})
_CLASSIC_IDS = CLASSIC_STACK_IDS | {"incus", "portainer"}


class MigrationPreviewService:
    """Use existing read-only ports; never return the domain snapshot."""

    def __init__(self, manifests: ManifestRepository, catalog: CatalogRepository) -> None:
        self._manifests = manifests
        self._catalog = catalog

    def preview(self) -> dict[str, object]:
        snapshot = self._manifests.load()
        if snapshot.manifest is None:
            raise ValueError("Migration preview unavailable.")
        catalog = self._catalog.load()
        if any(service.service_id not in _CLASSIC_IDS for service in catalog.services):
            raise ValueError("Migration preview unavailable.")
        preview = preview_migration(snapshot.manifest, catalog)
        if any(name not in CLASSIC_STACK_IDS or owner != "swarm" for name, owner in preview.stack_policies):
            raise ValueError("Migration preview unavailable.")
        return {
            "status": "PREVIEW", "source": "operator_local_unverified", "applied": False, "qualified": False,
            "project": "UNKNOWN", "profile": "UNKNOWN", "route": "UNKNOWN", "owner": "UNKNOWN",
            "swagger_exposure": preview.swagger_exposure.value,
            "stack_policies": [{"service_id": name, "owner": "swarm"} for name, _ in preview.stack_policies],
        }

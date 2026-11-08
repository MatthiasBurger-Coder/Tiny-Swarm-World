"""Read-only lifecycle inspection and explicit adoption, outside execution engines."""
from tiny_swarm_world.application.ports.lifecycle import (
    CatalogRepository, LifecycleStateError, ManifestRepository, ManifestSnapshot,
)
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest


class InstallationLifecycleService:
    def __init__(self, manifests: ManifestRepository, catalog: CatalogRepository):
        self.manifests = manifests
        self.catalog = catalog

    def inspect(self) -> dict[str, object]:
        catalog = self.catalog.load()
        snapshot = self.manifests.load()
        manifest = snapshot.manifest
        if manifest is not None:
            try:
                catalog.validate_manifest(manifest)
            except ValueError:
                raise LifecycleStateError("Installation/catalog mismatch; inspect selection and bundle inventory before mutation.") from None
        return {
            "status": "adoption_required" if manifest is None else "inspected",
            "manifest": None if manifest is None else manifest.model_dump(mode="json"),
            "diagnostics": list(snapshot.diagnostics),
            "catalog": catalog.model_dump(mode="json"),
            "components": [] if manifest is None else [
                {"component_id": item.component_id, "service_id": item.service_id,
                 "desired": item.desired.model_dump(mode="json"),
                 "observed": None if item.observed is None else item.observed.model_dump(mode="json"),
                 "drift": list(item.drift())} for item in manifest.components
            ],
        }

    def adopt(self, manifest: InstallationManifest, *, approved: bool = False, preview: bool = True) -> ManifestSnapshot:
        """Admit an explicitly inventoried instance, never infer it from directory presence.

        Callers own acquisition/verification of product and configuration references.
        Adoption records supplied observations, never asserts runtime convergence.
        """
        try:
            manifest = InstallationManifest.model_validate(manifest.model_dump())
            self.catalog.load().validate_manifest(manifest)
        except ValueError:
            raise LifecycleStateError("Invalid adoption inventory; inspect schema, dependencies, preset and every selected component.") from None
        existing = self.manifests.load()
        if existing.manifest is not None:
            if existing.manifest == manifest:
                return existing
            raise LifecycleStateError("Existing installation identity/state differs; adoption cannot overwrite it.")
        if existing.diagnostics and any(note.startswith("interrupted_write") for note in existing.diagnostics):
            raise LifecycleStateError("Interrupted adoption is ambiguous; inspect retained state before adopting.")
        if preview:
            return ManifestSnapshot(manifest, None, ("adoption_preview: no state written; observations remain unverified",))
        if not approved:
            raise LifecycleStateError("Explicit local adoption approval required; preview and verify inventory first.")
        return self.manifests.save(manifest, expected_token=None)

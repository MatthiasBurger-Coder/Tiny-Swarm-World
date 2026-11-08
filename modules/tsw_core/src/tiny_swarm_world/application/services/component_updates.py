"""Read-only component use cases; all state and metadata arrive through ports."""
from tiny_swarm_world.application.ports.lifecycle import CatalogRepository, LifecycleStateError, ManifestRepository
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, ComponentUpdateTarget, InstallationManifest, ServiceDefinition
from tiny_swarm_world.domain.lifecycle.update_planning import ComponentUpdatePlan, plan_component_updates, selected_services


class ComponentUpdateService:
    def __init__(self, manifests: ManifestRepository, catalog: CatalogRepository):
        self.manifests = manifests
        self.catalog = catalog

    def _installation(self) -> tuple[ComponentCatalog, InstallationManifest, str | None, tuple[str, ...]]:
        catalog = self.catalog.load()
        snapshot = self.manifests.load()
        if snapshot.manifest is None:
            raise LifecycleStateError("Installation adoption required; installed services and versions are unknown.")
        try:
            catalog.validate_manifest(snapshot.manifest)
        except ValueError:
            raise LifecycleStateError("Installation/catalog mismatch; inspect selection and component inventory.") from None
        return catalog, snapshot.manifest, snapshot.token, snapshot.diagnostics

    def discover(self, requested: tuple[str, ...] | None = None) -> dict[str, object]:
        catalog, manifest, token, diagnostics = self._installation()
        order = selected_services(catalog, manifest, requested)
        definitions = {item.service_id: item for item in catalog.services}
        return {
            "status": "discovered", "runtime_profile": manifest.runtime_profile, "host": manifest.host,
            "manifest_token": token, "diagnostics": list(diagnostics),
            "observation_source": "recorded-manifest-not-live",
            "metadata_status": "local-catalog-only; registry/release lookup not performed (offline safe)",
            "services": [self._discovery_item(definitions[name], manifest) for name in order],
        }

    @staticmethod
    def _discovery_item(service: ServiceDefinition, manifest: InstallationManifest) -> dict[str, object]:
        components = sorted((item for item in manifest.components if item.service_id == service.service_id),
                            key=lambda item: item.component_id)
        supported = {item.target_id for item in service.update_transitions}
        def compatible(target: ComponentUpdateTarget) -> bool:
            return manifest.host in target.hosts and manifest.service_preset in target.presets
        return {
            "service_id": service.service_id, "lifecycle_owner": service.lifecycle_owner,
            "migration_policy": service.migration_policy, "backup_policy": service.backup_policy,
            "components": [{"component_id": item.component_id,
                            "installed": None if item.observed is None else item.observed.model_dump(mode="json"),
                            "desired": item.desired.model_dump(mode="json"), "drift": list(item.drift()),
                            "observation_status": "missing" if item.observed is None else "recorded-unverified",
                            "digest_status": "unavailable" if item.observed is None or item.observed.image_digest is None else "recorded"}
                           for item in components],
            "available_supported_targets": [item.model_dump(mode="json") for item in service.update_targets
                                            if item.target_id in supported and item.qualification == "qualified-transition"
                                            and compatible(item)],
            "catalog_references": [dict(item.model_dump(mode="json"), compatible=compatible(item))
                                   for item in service.update_targets],
            "transition_policy": [item.model_dump(mode="json") for item in service.update_transitions],
            "restriction": ("host-operator: Incus package upgrades unsupported" if service.lifecycle_owner == "host-operator"
                            else "dedicated Portainer upgrade adapter required" if service.lifecycle_owner == "portainer-adapter"
                            else "Only explicit source-to-target transitions are supported; upstream latest is never qualification."),
        }

    def preview(self, requested: tuple[str, ...], target_id: str | None = None) -> ComponentUpdatePlan:
        catalog, manifest, token, diagnostics = self._installation()
        plan = plan_component_updates(catalog, manifest, requested, target_id)
        if diagnostics:
            return plan.model_copy(update={"status": "blocked", "manifest_token": token, "diagnostics": diagnostics})
        return plan.model_copy(update={"manifest_token": token})

"""Read-only selection previews and explicitly approved local metadata persistence."""
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease, InstallationOperationLock, installation_operation
from tiny_swarm_world.application.ports.lifecycle import (
    CatalogRepository, LifecycleStateError, ManifestRepository, ManifestSnapshot,
)
from tiny_swarm_world.domain.lifecycle.models import migrate_manifest_v1, ComponentState, CredentialReference, ConfigurationReference
from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan, plan_selection
from tiny_swarm_world.application.services.selection_commit import selection_candidate


class ServiceSelectionService:
    def __init__(self, manifests: ManifestRepository, catalog: CatalogRepository, *,
                 operation_lock: InstallationOperationLock | None = None):
        self.manifests = manifests
        self.catalog = catalog
        self.operation_lock = operation_lock

    def preview(
        self, requested: tuple[str, ...] | None = None, configured: tuple[str, ...] | None = None,
        *, minimal: bool = False, preset: str | None = None, remove: tuple[str, ...] = (),
        add: bool = False, available_capabilities: tuple[str, ...] | None = None,
    ) -> SelectionPlan:
        catalog = self.catalog.load()
        snapshot = self.manifests.load()
        if snapshot.manifest is not None:
            try:
                catalog.validate_manifest(snapshot.manifest)
            except ValueError:
                raise LifecycleStateError("Installation/catalog mismatch; inspect persisted selection and component inventory.") from None
        plan = plan_selection(
            catalog, requested, configured, persisted=snapshot.manifest, minimal=minimal,
            preset=preset, remove=remove, add=add, available_capabilities=available_capabilities,
        )
        return plan.model_copy(update={"manifest_token": snapshot.token, "diagnostics": snapshot.diagnostics})

    def persist(self, plan: SelectionPlan, *, approved: bool = False, component_inventory: tuple[ComponentState, ...] | None = None,
                credential_inventory: tuple[CredentialReference, ...] | None = None,
                configuration_inventory: tuple[ConfigurationReference, ...] | None = None,
                operation_lease: InstallationLease | None = None, verified_migration: bool = False) -> ManifestSnapshot:
        if not approved:
            raise LifecycleStateError("Explicit local selection approval is required before persistence.")
        with installation_operation(self.operation_lock, 'selection', operation_lease):
            return self._persist(plan, approved=approved, component_inventory=component_inventory,
                                 credential_inventory=credential_inventory, configuration_inventory=configuration_inventory,
                                 verified_migration=verified_migration)

    def _persist(self, plan: SelectionPlan, *, approved: bool = False, component_inventory: tuple[ComponentState, ...] | None = None,
                credential_inventory: tuple[CredentialReference, ...] | None = None,
                configuration_inventory: tuple[ConfigurationReference, ...] | None = None, verified_migration: bool = False) -> ManifestSnapshot:
        """Save desired metadata only; this does not install or verify any service."""
        if not approved:
            raise LifecycleStateError("Explicit local selection approval is required before persistence.")
        if plan.removals or plan.source == "remove":
            raise LifecycleStateError("Removal apply is unsupported; retain deployments and data and inspect removal impact.")
        snapshot = self.manifests.load()
        if snapshot.manifest is None:
            raise LifecycleStateError("Adopt and verify the installation identity before persisting selection.")
        if snapshot.token != plan.manifest_token:
            raise LifecycleStateError("Selection preview is stale; inspect the current installation and preview again.")
        catalog = self.catalog.load()
        manifest = selection_candidate(catalog, snapshot.manifest, plan, component_inventory,
                                       credential_inventory, configuration_inventory)
        if manifest == snapshot.manifest:
            return snapshot
        if verified_migration:
            manifest = migrate_manifest_v1(manifest)
        catalog.validate_manifest(manifest)
        return self.manifests.save(manifest, expected_token=snapshot.token)

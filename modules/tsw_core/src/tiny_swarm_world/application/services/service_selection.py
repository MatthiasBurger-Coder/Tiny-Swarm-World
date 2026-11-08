"""Read-only selection previews and explicitly approved local metadata persistence."""
from tiny_swarm_world.application.ports.lifecycle import (
    CatalogRepository, LifecycleStateError, ManifestRepository, ManifestSnapshot,
)
from tiny_swarm_world.domain.lifecycle.models import ComponentState, CredentialReference, ConfigurationReference, InstallationManifest
from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan, plan_selection


class ServiceSelectionService:
    def __init__(self, manifests: ManifestRepository, catalog: CatalogRepository):
        self.manifests = manifests
        self.catalog = catalog

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
                configuration_inventory: tuple[ConfigurationReference, ...] | None = None) -> ManifestSnapshot:
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
        catalog.validate_manifest(snapshot.manifest)
        changed_preset = plan.service_preset != snapshot.manifest.service_preset
        validated = plan_selection(
            catalog, plan.requested_services if plan.requested_services else None,
            persisted=snapshot.manifest, minimal=not plan.requested_services,
            preset=plan.service_preset if changed_preset else None,
        )
        if (validated.resolved_services != plan.resolved_services
                or validated.selection_reasons != plan.selection_reasons
                or validated.service_preset != plan.service_preset
                or validated.resources != plan.resources):
            raise LifecycleStateError("Selection/catalog changed since preview; inspect and preview again.")
        if not set(snapshot.manifest.resolved_services) <= set(plan.resolved_services):
            raise LifecycleStateError("Implicit removal is unsupported; use removal-impact preview.")
        existing = {item.component_id: item for item in snapshot.manifest.components}
        components = tuple(existing.get(item.component_id, item)
                           for name in plan.resolved_services for service in catalog.services
                           if service.service_id == name for item in service.components)
        if component_inventory is not None:
            proposed = {item.component_id: item for item in component_inventory}
            if (len(proposed) != len(component_inventory) or set(proposed) != {item.component_id for item in components}
                    or any(proposed[name] != item for name, item in existing.items())):
                raise LifecycleStateError("Effective inventory cannot change existing component identity or desired state during addition.")
            components = component_inventory
        payload = snapshot.manifest.model_dump()
        payload.update(requested_services=plan.requested_services, resolved_services=plan.resolved_services,
                       selection_reasons=plan.selection_reasons, service_preset=plan.service_preset,
                       components=components)
        for key, inventory in (("credential_references", credential_inventory), ("configuration_references", configuration_inventory)):
            if inventory is not None:
                if any(item not in inventory for item in getattr(snapshot.manifest, key)):
                    raise LifecycleStateError("Addition cannot discard existing configuration or credential provenance.")
                payload[key] = inventory
        manifest = InstallationManifest.model_validate(payload)
        catalog.validate_manifest(manifest)
        if manifest == snapshot.manifest:
            return snapshot
        return self.manifests.save(manifest, expected_token=snapshot.token)

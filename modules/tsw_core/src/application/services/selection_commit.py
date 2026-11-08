"""Pure validated selection candidates; no locking, persistence or runtime effects."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest, PortainerOwnership, SwarmOwnership, migrate_manifest_v1
from tiny_swarm_world.domain.lifecycle.selection import plan_selection


def validate_selection(catalog, current, plan):
    catalog.validate_manifest(current)
    changed_preset = plan.service_preset != current.service_preset
    validated = plan_selection(
        catalog, plan.requested_services if plan.requested_services else None,
        persisted=current, minimal=not plan.requested_services,
        preset=plan.service_preset if changed_preset else None, service_exposure=plan.service_exposure,
    )
    if (validated.resolved_services != plan.resolved_services
            or validated.selection_reasons != plan.selection_reasons
            or validated.service_preset != plan.service_preset
            or validated.resources != plan.resources or validated.service_exposure != plan.service_exposure):
        raise LifecycleStateError("Selection/catalog changed since preview; inspect and preview again.")
    optional = set(plan.resolved_services) - {'incus', 'portainer'}
    modes = plan.stack_owners or {name: 'swarm' for name in optional}
    if set(modes) != optional or any(modes.get(name) != owner.owner for name, owner in current.effective_stack_ownership().items()):
        raise LifecycleStateError('Selection cannot change existing stack ownership or omit desired modes.')
    if not set(current.resolved_services) <= set(plan.resolved_services):
        raise LifecycleStateError("Implicit removal is unsupported; use removal-impact preview.")


def selected_components(catalog, current, plan, component_inventory):
    existing = {item.component_id: item for item in current.components}
    components = tuple(existing.get(item.component_id, item)
                       for name in plan.resolved_services for service in catalog.services
                       if service.service_id == name for item in service.components)
    if component_inventory is not None:
        proposed = {item.component_id: item for item in component_inventory}
        if (len(proposed) != len(component_inventory) or set(proposed) != {item.component_id for item in components}
                or any(proposed[name] != item for name, item in existing.items())):
            raise LifecycleStateError("Effective inventory cannot change existing component identity or desired state during addition.")
        components = component_inventory
    return components


def selection_payload(current, plan, components, credential_inventory, configuration_inventory):
    payload = current.model_dump()
    payload.update(requested_services=plan.requested_services, resolved_services=plan.resolved_services,
                   selection_reasons=plan.selection_reasons, service_preset=plan.service_preset,
                   components=components)
    for key, inventory in (("credential_references", credential_inventory), ("configuration_references", configuration_inventory)):
        if inventory is not None:
            if any(item not in inventory for item in getattr(current, key)):
                raise LifecycleStateError("Addition cannot discard existing configuration or credential provenance.")
            payload[key] = inventory
    return payload


def extend_policy(current, plan, payload):
    if current.schema_version == 2 or 'internal' in plan.service_exposure.values():
        exposure = dict(plan.service_exposure)
        owners = current.effective_stack_ownership()
        for name in plan.resolved_services:
            if name == 'swagger':
                exposure.setdefault(name, 'published')
            if name not in {'incus', 'portainer'}:
                owners.setdefault(name, SwarmOwnership())
        if current.installation_profile is not None and plan.resolved_services != current.resolved_services:
            raise LifecycleStateError('Bound-profile selection changes require the admitted profile lifecycle before commit.')
        payload.update(schema_version=2, service_exposure=exposure, stack_ownership=owners,
                       installation_profile=current.installation_profile)


def selection_candidate(catalog, current, plan, component_inventory, credential_inventory, configuration_inventory, stack_ownership_inventory=None):
    validate_selection(catalog, current, plan)
    components = selected_components(catalog, current, plan, component_inventory)
    payload = selection_payload(current, plan, components, credential_inventory, configuration_inventory)
    extend_policy(current, plan, payload)
    modes = plan.stack_owners or {name: owner.owner for name, owner in current.effective_stack_ownership().items()}
    wanted = {name for name, mode in modes.items() if mode == 'portainer'}
    baseline = current.effective_stack_ownership()
    observed = baseline if stack_ownership_inventory is None else stack_ownership_inventory
    if any(name not in observed or not isinstance(observed[name], PortainerOwnership) for name in wanted):
        raise LifecycleStateError('Portainer ownership requires verified IDs, saved definition and converged tasks before selection commit.')
    if stack_ownership_inventory is not None:
        if set(observed) != set(plan.resolved_services) - {'incus', 'portainer'} or any(observed[name] != value for name, value in baseline.items()):
            raise LifecycleStateError('Verified ownership cannot adopt/rewrite existing stacks or omit selected services.')
        migrated = migrate_manifest_v1(InstallationManifest.model_validate(payload))
        payload = migrated.model_dump()
        payload['stack_ownership'] = observed
    manifest = InstallationManifest.model_validate(payload)
    catalog.validate_manifest(manifest)
    return manifest

"""Pure Classic component discovery and source-to-target admission policy."""
from typing import Literal

from tiny_swarm_world.domain.lifecycle.models import (
    ComponentCatalog, ComponentState, ComponentUpdateTarget, Contract,
    InstallationManifest, ServiceDefinition, VersionIdentity,
)
from tiny_swarm_world.domain.lifecycle.selection import plan_selection, validate_ids


class UninstalledServiceError(ValueError):
    """An otherwise valid service is not in the installed selection."""


class ComponentChange(Contract):
    component_id: str
    desired: VersionIdentity
    observed: VersionIdentity | None
    target: VersionIdentity | None
    desired_change: bool
    drift: tuple[str, ...]


class ServiceUpdatePlan(Contract):
    service_id: str
    status: Literal["planned", "no_op", "unsupported", "blocked", "dedicated_upgrade"]
    reason: str
    lifecycle_owner: str
    target: ComponentUpdateTarget | None
    components: tuple[ComponentChange, ...]
    dependencies: tuple[str, ...]
    affected_dependents: tuple[str, ...]
    backup_required: bool
    migrations: tuple[str, ...]
    availability_impact: str
    recovery_limit: str


class ComponentUpdatePlan(Contract):
    status: Literal["preview", "blocked", "no_op"]
    requested_services: tuple[str, ...]
    dependency_order: tuple[str, ...]
    services: tuple[ServiceUpdatePlan, ...]
    execution: Literal["not performed (read-only preview)"] = "not performed (read-only preview)"
    observation_source: Literal["recorded-manifest-not-live"] = "recorded-manifest-not-live"
    diagnostics: tuple[str, ...] = ()
    manifest_token: str | None = None


def selected_services(catalog: ComponentCatalog, manifest: InstallationManifest,
                      requested: tuple[str, ...] | None) -> tuple[str, ...]:
    catalog.validate_manifest(manifest)
    definitions = {item.service_id: item for item in catalog.services}
    chosen = validate_ids(manifest.resolved_services if requested is None else requested, definitions)
    if not chosen:
        raise ValueError("Select at least one installed service.")
    if not set(chosen) <= set(manifest.resolved_services):
        raise UninstalledServiceError("Uninstalled service requested; inspect services list and install it explicitly first.")
    # Reuse selection's dependency validation and stable topological ordering.
    order = plan_selection(catalog, chosen, persisted=manifest).resolved_services
    return tuple(name for name in order if name in chosen)


def _matches(actual: VersionIdentity | None, expected: VersionIdentity) -> bool:
    return actual is not None and all(
        value is None or getattr(actual, key) == value
        for key, value in expected.model_dump().items()
    )


def _bundle_matches(components: tuple[ComponentState, ...], versions: dict[str, VersionIdentity],
                    *, observed: bool) -> bool:
    return all(_matches(item.observed if observed else item.desired, versions[item.component_id])
               for item in components)


def _resolve_target(service: ServiceDefinition, components: tuple[ComponentState, ...],
                    target_id: str | None) -> ComponentUpdateTarget | None:
    if target_id is not None:
        return next((item for item in service.update_targets if item.target_id == target_id), None)
    admitted = {item.target_id for item in service.update_transitions
                if _bundle_matches(components, item.source_versions, observed=False)}
    candidates = [item for item in service.update_targets if item.target_id in admitted]
    if not candidates:
        candidates = [item for item in service.update_targets if item.qualification == "qualified-transition"]
    if not candidates:
        candidates = list(service.update_targets)
    return candidates[0] if len(candidates) == 1 else None


def _admission(service: ServiceDefinition, components: tuple[ComponentState, ...],
               target: ComponentUpdateTarget | None, manifest: InstallationManifest):
    if service.lifecycle_owner == "host-operator":
        return "unsupported", "Incus host-package upgrades belong to the host operator; generic component updates are unsupported.", None
    if service.lifecycle_owner == "portainer-adapter":
        return "dedicated_upgrade", "Portainer requires the dedicated qualified upgrade/backup/recovery adapter (W07).", None
    if target is None:
        return "unsupported", "Unknown or ambiguous catalog target; select one explicit supported target with --to.", None
    if manifest.host not in target.hosts or manifest.service_preset not in target.presets:
        return "unsupported", "Target is incompatible with the installation host or service preset.", None
    immutable = all(item.image_digest and item.image_repository for item in target.versions.values())
    drifted = any(item.drift() for item in components)
    if immutable and _bundle_matches(components, target.versions, observed=False):
        if drifted or not _bundle_matches(components, target.versions, observed=True):
            return "blocked", "Target observations are missing or drifted; a no-op cannot be verified from recorded state.", None
        return "no_op", "Recorded desired and observed immutable identities already match; execution must revalidate live state.", None
    transitions = [item for item in service.update_transitions if item.target_id == target.target_id
                   and _bundle_matches(components, item.source_versions, observed=False)]
    if len(transitions) != 1:
        return "unsupported", "No qualified source-to-target transition; upgrades/downgrades and data migrations are not inferred from tags.", None
    transition = transitions[0]
    if drifted or not _bundle_matches(components, transition.source_versions, observed=True):
        return "blocked", "Source observations are missing or drifted; inspect runtime before updating.", transition
    return "planned", "Explicit catalog transition admitted for this Classic host and preset; backup/migration gates remain mandatory.", transition


def _service_plan(service: ServiceDefinition, manifest: InstallationManifest,
                  catalog: ComponentCatalog, target_id: str | None) -> ServiceUpdatePlan:
    components = tuple(sorted((item for item in manifest.components if item.service_id == service.service_id),
                              key=lambda item: item.component_id))
    target = _resolve_target(service, components, target_id)
    status, reason, transition = _admission(service, components, target, manifest)
    changes = tuple(ComponentChange(
        component_id=item.component_id, desired=item.desired, observed=item.observed,
        target=None if target is None else target.versions[item.component_id],
        desired_change=target is not None and not _matches(item.desired, target.versions[item.component_id]),
        drift=item.drift(),
    ) for item in components)
    return ServiceUpdatePlan(
        service_id=service.service_id, status=status, reason=reason, lifecycle_owner=service.lifecycle_owner,
        target=target, components=changes, dependencies=tuple(sorted(service.dependencies)),
        affected_dependents=tuple(sorted(item.service_id for item in catalog.services
                                        if item.service_id in manifest.resolved_services
                                        and service.service_id in item.dependencies)),
        backup_required=(transition.backup_required if transition else
                         service.backup_policy == "required-before-stateful-transition"),
        migrations=transition.migrations if transition else (),
        availability_impact=(transition.availability_impact if transition else
                             "No restart admitted; downtime is unqualified without a supported transition."),
        recovery_limit=(transition.recovery_limit if transition else
                        "No qualified migration/recovery path. Image rollback is not a persistent-data restore."),
    )


def plan_component_updates(catalog: ComponentCatalog, manifest: InstallationManifest,
                           requested: tuple[str, ...], target_id: str | None = None) -> ComponentUpdatePlan:
    if target_id is not None and len(requested) != 1:
        raise ValueError("--to requires exactly one selected service.")
    order = selected_services(catalog, manifest, requested)
    definitions = {item.service_id: item for item in catalog.services}
    plans = tuple(_service_plan(definitions[name], manifest, catalog, target_id) for name in order)
    status: Literal["preview", "blocked", "no_op"] = "preview"
    if any(item.status not in {"planned", "no_op"} for item in plans):
        status = "blocked"
    elif all(item.status == "no_op" for item in plans):
        status = "no_op"
    return ComponentUpdatePlan(status=status, requested_services=tuple(sorted(requested)),
                               dependency_order=order, services=plans)

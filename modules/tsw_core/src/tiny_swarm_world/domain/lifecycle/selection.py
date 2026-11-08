"""Deterministic Classic selection planning without execution or storage effects."""
from __future__ import annotations

import heapq
import re
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import Field

from tiny_swarm_world.domain.lifecycle.models import (
    ComponentCatalog, Contract, InstallationManifest, ServiceDefinition,
)


class SelectionError(ValueError):
    """An invalid selection or catalog cannot be planned safely."""


class SelectionResources(Contract):
    declarations: dict[str, dict[str, dict[str, object]]]
    totals: dict[str, str | int | None]
    unknowns: tuple[str, ...]
    qualification: Literal["native-declarations-only"] = "native-declarations-only"


class SelectionPlan(Contract):
    requested_services: tuple[str, ...]
    resolved_services: tuple[str, ...]
    selection_reasons: dict[str, tuple[str, ...]]
    service_preset: Literal["default", "service-access"]
    source: Literal["explicit", "configuration", "persisted", "preset", "minimal", "add", "remove"]
    additions: tuple[str, ...]
    removals: tuple[str, ...]
    removal_impact: dict[str, tuple[str, ...]]
    retained_data: bool = True
    resources: SelectionResources
    manifest_token: str | None = None
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


def validate_ids(values: tuple[str, ...], services: dict[str, ServiceDefinition]) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise SelectionError("Duplicate service IDs are not allowed.")
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", name) for name in values):
        raise SelectionError("Use canonical lowercase service IDs; empty entries and wildcards are invalid.")
    if not set(values) <= services.keys():
        raise SelectionError("Unknown service ID; inspect services list for canonical IDs.")
    return tuple(sorted(values))


def _catalog_services(catalog: ComponentCatalog) -> dict[str, ServiceDefinition]:
    services = {item.service_id: item for item in catalog.services}
    if len(services) != len(catalog.services):
        raise SelectionError("Catalog has duplicate service identities.")
    if not {"incus", "portainer"} <= services.keys():
        raise SelectionError("Catalog is missing Classic foundations incus or portainer.")
    for service in services.values():
        validate_ids(service.dependencies, services)
    _topological(set(services), services)
    return services


def _topological(selected: set[str], services: dict[str, ServiceDefinition]) -> tuple[str, ...]:
    dependencies = {name: set(services[name].dependencies) & selected for name in selected}
    ready = [name for name, parents in dependencies.items() if not parents]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        name = heapq.heappop(ready)
        ordered.append(name)
        for child in sorted(dependencies):
            if name in dependencies[child]:
                dependencies[child].remove(name)
                if not dependencies[child]:
                    heapq.heappush(ready, child)
    if len(ordered) != len(selected):
        raise SelectionError("Catalog dependency cycle; correct the catalog before planning.")
    return tuple(ordered)


def _closure(requested: tuple[str, ...], services: dict[str, ServiceDefinition]) -> tuple[set[str], dict[str, tuple[str, ...]]]:
    selected = set(requested) | {name for name, item in services.items() if item.mandatory} | {"incus", "portainer"}
    pending = list(selected)
    while pending:
        for dependency in services[pending.pop()].dependencies:
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    reasons = {}
    for name in sorted(selected - set(requested)):
        parents = tuple(sorted(parent for parent in selected if name in services[parent].dependencies))
        reasons[name] = parents or (name,)
    return selected, reasons


def _select_source(
    services: dict[str, ServiceDefinition], requested: tuple[str, ...] | None,
    configured: tuple[str, ...] | None, persisted: InstallationManifest | None,
    minimal: bool, preset: str | None, add: bool,
) -> tuple[tuple[str, ...], str, Literal["default", "service-access"]]:
    if preset is not None and preset not in {"default", "service-access"}:
        raise SelectionError("Unsupported service preset; use default or service-access.")
    if minimal and (requested is not None or configured is not None or preset is not None or add):
        raise SelectionError("Minimal selection conflicts with services, configuration, additions or an explicit preset.")
    effective: Literal["default", "service-access"] = "default" if preset == "default" else "service-access"
    if persisted is not None and preset is None:
        effective = persisted.service_preset
    if add:
        if persisted is None or not requested:
            raise SelectionError("Service additions require an adopted installation and explicit services.")
        validate_ids(requested, services)
        return tuple(sorted(set(persisted.requested_services) | set(requested))), "add", effective
    if minimal:
        return (), "minimal", effective
    chosen = requested if requested is not None else configured
    if chosen is not None:
        if not chosen:
            raise SelectionError("Empty service selection is invalid; use --minimal.")
        return validate_ids(chosen, services), "explicit" if requested is not None else "configuration", effective
    if persisted is not None:
        return validate_ids(persisted.requested_services, services), "persisted", effective
    return tuple(sorted(name for name, item in services.items() if effective in item.presets and not item.mandatory)), "preset", effective


def _check_support(selected: set[str], services: dict[str, ServiceDefinition], preset: str,
                   capabilities: tuple[str, ...] | None) -> None:
    for name in sorted(selected):
        if preset not in services[name].presets:
            raise SelectionError("Selected service is unsupported by the service preset.")
        if capabilities is not None and not set(services[name].capabilities) <= set(capabilities):
            raise SelectionError("Required service capabilities are unavailable; inspect catalog prerequisites.")


def _resource_number(value: object, memory: bool) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([kmgt]i?b?|b)?", str(value).lower())
    if match is None or (not memory and match[2]):
        return None
    try:
        number = Decimal(match[1])
        unit = match[2] or "b"
        return number * (1024 ** ("kmgt".index(unit[0]) + 1) if memory and unit[0] in "kmgt" else 1)
    except InvalidOperation:
        return None


def _resources(ordered: tuple[str, ...], services: dict[str, ServiceDefinition]) -> SelectionResources:
    declarations = {name: services[name].resources.declared for name in ordered}
    totals: dict[str, str | int | None] = {}
    unknowns = []
    for category in ("limits", "reservations"):
        for metric in ("cpus", "memory"):
            total = Decimal(0)
            known = True
            for name in ordered:
                components = declarations[name] or {name: {}}
                for component, declaration in sorted(components.items()):
                    limits = declaration.get(category, {})
                    number = _resource_number(limits.get(metric), metric == "memory") if isinstance(limits, dict) else None
                    if number is None:
                        known = False
                        unknowns.append(f"{name}.{component}.{category}.{metric}")
                    else:
                        total += number
            totals[f"{category}_{metric}"] = (str(total) if metric == "cpus" else int(total)) if known else None
    return SelectionResources(declarations=declarations, totals=totals, unknowns=tuple(sorted(unknowns)))


def plan_selection(
    catalog: ComponentCatalog, requested: tuple[str, ...] | None = None,
    configured: tuple[str, ...] | None = None, *, persisted: InstallationManifest | None = None,
    minimal: bool = False, preset: str | None = None, remove: tuple[str, ...] = (),
    add: bool = False, available_capabilities: tuple[str, ...] | None = None,
) -> SelectionPlan:
    services = _catalog_services(catalog)
    removed = validate_ids(remove, services)
    if set(removed) & ({"incus", "portainer"} | {name for name, item in services.items() if item.mandatory}):
        raise SelectionError("Classic foundations incus and portainer cannot be removed; retain host/provider and management access.")
    if removed and (persisted is None or requested is not None or configured is not None or minimal or add or preset is not None):
        raise SelectionError("Removal impact requires an adopted installation and no conflicting selection flags.")
    chosen, source, effective = _select_source(services, requested, configured, persisted, minimal, preset, add)
    selected, reasons = _closure(chosen, services)
    if preset is not None and source in {"explicit", "configuration", "add"}:
        expected = {name for name, item in services.items() if effective in item.presets}
        if selected != expected:
            raise SelectionError("Explicit service preset conflicts with the requested selection.")
    _check_support(selected, services, effective, available_capabilities)
    ordered = _topological(selected, services)
    previous = set(persisted.resolved_services) if persisted is not None else set()
    if removed and not set(removed) <= previous:
        raise SelectionError("Removal impact requires services selected in the installation.")
    impact = {name: tuple(sorted(candidate for candidate in previous - {name}
                                if name in _closure((candidate,), services)[0])) for name in removed}
    return SelectionPlan(
        requested_services=chosen, resolved_services=ordered, selection_reasons=reasons,
        service_preset=effective, source="remove" if removed else source,  # type: ignore[arg-type]
        additions=tuple(name for name in ordered if name not in previous),
        removals=removed or tuple(sorted(previous - selected)), removal_impact=impact,
        resources=_resources(ordered, services),
    )

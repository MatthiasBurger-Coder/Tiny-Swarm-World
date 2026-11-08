"""Unadopted desired-v2 conversion; no persistence or host observations."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from pydantic import BaseModel

from tiny_swarm_world.domain.lifecycle.manifest_v2 import SwaggerExposure, UnknownIdentity, preview_migration
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, InstallationManifest
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import (
    PolicyStatus, ScopedPolicyReference, ScopedRoute, matches_scoped_reference, scoped_route_reference,
)


class ConversionStatus(Enum):
    DESIRED = "DESIRED"
    AUTHORITY_GAP = "AUTHORITY_GAP"


@dataclass(frozen=True, slots=True, init=False)
class DesiredManifestV2:
    """Immutable desired values, never a validated persisted installation."""

    v1_snapshot: Mapping[str, object]
    desired_profile_name: str
    desired_routes: tuple[ScopedRoute, ...]
    stack_policies: tuple[tuple[str, str], ...]
    swagger_exposure: SwaggerExposure
    desired_project: str = field(default="default", init=False)
    desired_schema_version: int = field(default=2, init=False)
    actual_project: UnknownIdentity = field(default=UnknownIdentity.UNKNOWN, init=False)
    actual_profile: UnknownIdentity = field(default=UnknownIdentity.UNKNOWN, init=False)
    actual_route: UnknownIdentity = field(default=UnknownIdentity.UNKNOWN, init=False)
    actual_owner: UnknownIdentity = field(default=UnknownIdentity.UNKNOWN, init=False)
    actual_host: UnknownIdentity = field(default=UnknownIdentity.UNKNOWN, init=False)
    runtime_source: UnknownIdentity = field(default=UnknownIdentity.UNKNOWN, init=False)
    applied: bool = field(default=False, init=False)
    qualified: bool = field(default=False, init=False)

    def __init__(self) -> None:
        raise TypeError("Desired values must be created by conversion.")


@dataclass(frozen=True, slots=True)
class ConversionPlan:
    status: ConversionStatus
    desired: DesiredManifestV2 | None = None

    def __post_init__(self) -> None:
        if (type(self.status) is not ConversionStatus
                or (self.status is ConversionStatus.DESIRED and type(self.desired) is not DesiredManifestV2)
                or (self.status is ConversionStatus.AUTHORITY_GAP and self.desired is not None)):
            raise ValueError("Invalid conversion plan.")


_GAP = ConversionPlan(status=ConversionStatus.AUTHORITY_GAP)


def _detach(value: object) -> object:
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValueError("Invalid snapshot.")
        return MappingProxyType({key: _detach(child) for key, child in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_detach(child) for child in value)
    if value is None or type(value) in {str, bool, int, float}:
        return value
    raise ValueError("Invalid snapshot.")


def _make_desired(snapshot: Mapping[str, object], reference: ScopedPolicyReference,
                  stack_policies: tuple[tuple[str, str], ...], exposure: SwaggerExposure) -> DesiredManifestV2:
    detached = _detach(snapshot)
    if not isinstance(detached, Mapping) or type(reference.profile_name) is not str:
        raise ValueError("Invalid desired values.")
    result = object.__new__(DesiredManifestV2)
    fields = {
        "v1_snapshot": detached, "desired_profile_name": reference.profile_name,
        "desired_routes": reference.routes, "stack_policies": stack_policies, "swagger_exposure": exposure,
        "desired_project": "default", "desired_schema_version": 2,
        "actual_project": UnknownIdentity.UNKNOWN, "actual_profile": UnknownIdentity.UNKNOWN,
        "actual_route": UnknownIdentity.UNKNOWN, "actual_owner": UnknownIdentity.UNKNOWN,
        "actual_host": UnknownIdentity.UNKNOWN, "runtime_source": UnknownIdentity.UNKNOWN,
        "applied": False, "qualified": False,
    }
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _reject_unknown_fields(value: object, active: set[int]) -> None:
    """Detect extras model_dump could silently omit, including nested models."""
    if not isinstance(value, (BaseModel, dict, list, tuple)):
        return
    identity = id(value)
    if identity in active:
        raise ValueError("Cyclic input.")
    active.add(identity)
    try:
        children: Iterable[object]
        if isinstance(value, BaseModel):
            fields = type(value).model_fields
            if set(value.__dict__) != set(fields) or value.__pydantic_extra__:
                raise ValueError("Invalid model fields.")
            children = value.__dict__.values()
        elif isinstance(value, dict):
            children = value.values()
        else:
            children = value
        for child in children:
            _reject_unknown_fields(child, active)
    finally:
        active.remove(identity)


def plan_desired_manifest_v2(manifest: object, catalog: object, *, exposure: object,
                             listen_address: object, **unsupported: object) -> ConversionPlan:
    """Derive detached desired values from one validated input snapshot."""
    try:
        if unsupported or type(manifest) is not InstallationManifest or type(catalog) is not ComponentCatalog:
            return _GAP
        _reject_unknown_fields(manifest, set())
        _reject_unknown_fields(catalog, set())
        manifest_data = manifest.model_dump(mode="python", warnings="error")
        catalog_data = catalog.model_dump(mode="python", warnings="error")
        checked_manifest = InstallationManifest.model_validate(manifest_data, strict=True)
        checked_catalog = ComponentCatalog.model_validate(catalog_data, strict=True)
        preview = preview_migration(checked_manifest, checked_catalog)
        reference = scoped_route_reference(checked_manifest, checked_catalog,
                                           exposure=exposure, listen_address=listen_address)
        if (type(reference) is not ScopedPolicyReference or reference.status is not PolicyStatus.REFERENCE
                or type(reference.policy_version) is not str or reference.policy_version != "scoped-route-policy-v2"
                or type(reference.profile_algorithm) is not str or reference.profile_algorithm != "profile-name-v1"
                or type(reference.installation_id) is not str
                or reference.installation_id != preview.v1_snapshot["installation_id"]
                or type(reference.profile_name) is not str
                or type(reference.routes) is not tuple
                or any(type(route) is not ScopedRoute for route in reference.routes)
                or reference.runtime_source is not UnknownIdentity.UNKNOWN
                or reference.host is not UnknownIdentity.UNKNOWN
                or reference.project is not UnknownIdentity.UNKNOWN
                or reference.ownership is not UnknownIdentity.UNKNOWN
                or reference.applied is not False or reference.qualified is not False
                or not matches_scoped_reference(reference, checked_manifest, checked_catalog,
                                                exposure=exposure, listen_address=listen_address)):
            return _GAP
        desired = _make_desired(preview.v1_snapshot, reference, preview.stack_policies, preview.swagger_exposure)
        return ConversionPlan(status=ConversionStatus.DESIRED, desired=desired)
    except Exception:
        return _GAP

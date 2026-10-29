"""Immutable, unadopted policy preview for a strictly validated v1 manifest."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, InstallationManifest
from tiny_swarm_world.domain.lifecycle.selection import _catalog_services


class UnknownIdentity(Enum):
    """An identity that has not been discovered or adopted."""

    UNKNOWN = "unknown"


class SwaggerExposure(Enum):
    """Compatibility policy, not evidence of a live route."""

    PUBLISHED = "published"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class MigrationPreview:
    """Detached compatibility preview; never a validated schema-2 manifest."""

    v1_snapshot: Mapping[str, object]
    stack_policies: tuple[tuple[str, str], ...]
    swagger_exposure: SwaggerExposure
    project: UnknownIdentity = UnknownIdentity.UNKNOWN
    profile: UnknownIdentity = UnknownIdentity.UNKNOWN
    route: UnknownIdentity = UnknownIdentity.UNKNOWN
    owner: UnknownIdentity = UnknownIdentity.UNKNOWN


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    if value is None or type(value) in {str, int, bool, float}:
        return value
    raise ValueError("Unsupported snapshot value.")


def preview_migration(manifest: object, catalog: object) -> MigrationPreview:
    """Validate all supplied values and return a detached, unadopted preview."""
    try:
        if type(manifest) is not InstallationManifest or type(catalog) is not ComponentCatalog:
            raise ValueError("Invalid input type.")
        # Dump to plain data before validation so nested model_construct and
        # model_copy(update=...) objects cannot bypass Pydantic validation.
        manifest_data = manifest.model_dump(mode="python", warnings="error")
        catalog_data = catalog.model_dump(mode="python", warnings="error")
        checked_manifest = InstallationManifest.model_validate(manifest_data, strict=True)
        checked_catalog = ComponentCatalog.model_validate(catalog_data, strict=True)
        if (type(checked_manifest.schema_version) is not int or checked_manifest.schema_version != 1
                or type(checked_catalog.schema_version) is not int or checked_catalog.schema_version != 1
                or type(checked_manifest.catalog_version) is not int or checked_manifest.catalog_version != 1
                or type(checked_catalog.catalog_version) is not int or checked_catalog.catalog_version != 1):
            raise ValueError("Unsupported version.")
        services = checked_catalog.services
        service_ids = [service.service_id for service in services]
        if len(service_ids) != len(set(service_ids)):
            raise ValueError("Ambiguous catalog services.")
        components = [component for service in services for component in service.components]
        component_ids = [component.component_id for component in components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("Ambiguous catalog components.")
        if any(component.service_id != service.service_id
               for service in services for component in service.components):
            raise ValueError("Ambiguous component ownership.")
        by_name = _catalog_services(checked_catalog)
        if ("incus" not in by_name or by_name["incus"].kind != "host-prerequisite"
                or "portainer" not in by_name or by_name["portainer"].kind != "managed-foundation"):
            raise ValueError("Invalid Classic foundations.")
        checked_catalog.validate_manifest(checked_manifest)
        selected = set(checked_manifest.resolved_services)
        if "swagger" in selected and by_name["swagger"].kind != "stack":
            raise ValueError("Invalid Swagger classification.")
        policies = tuple((name, "swarm") for name in sorted(selected)
                         if name not in {"incus", "portainer"} and by_name[name].kind == "stack")
        exposure = SwaggerExposure.PUBLISHED if "swagger" in selected else SwaggerExposure.NOT_APPLICABLE
        snapshot = _freeze(checked_manifest.model_dump(mode="python", warnings="error"))
        if not isinstance(snapshot, Mapping):
            raise ValueError("Invalid snapshot.")
        return MigrationPreview(v1_snapshot=snapshot, stack_policies=policies, swagger_exposure=exposure)
    except Exception:
        raise ValueError("Invalid v1 migration input.") from None

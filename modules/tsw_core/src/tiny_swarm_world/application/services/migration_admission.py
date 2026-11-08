"""Fail-closed, read-only scoped migration admission preparation."""
from __future__ import annotations

from collections.abc import Mapping

from tiny_swarm_world.application.ports.lifecycle import CatalogRepository, ManifestRepository, ManifestSnapshot
from tiny_swarm_world.application.ports.lifecycle.migration_admission import (
    MigrationAdmissionRequest, MigrationAdmissionResult, MigrationAdmissionStatus,
)
from tiny_swarm_world.domain.lifecycle.desired_manifest_v2 import (
    ConversionPlan, ConversionStatus, DesiredManifestV2, plan_desired_manifest_v2,
)
from tiny_swarm_world.domain.lifecycle import incus_capability
from tiny_swarm_world.domain.lifecycle.incus_capability import CapabilityResult, IntentKind
from tiny_swarm_world.domain.lifecycle.manifest_v2 import UnknownIdentity, preview_migration
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, InstallationManifest
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import (
    PolicyStatus, ScopedPolicyReference, ScopedRoute, SwaggerMode, scoped_route_reference,
)


_UNKNOWN = MigrationAdmissionResult(MigrationAdmissionStatus.BLOCKED_UNKNOWN)
_UNSUPPORTED = MigrationAdmissionResult(MigrationAdmissionStatus.BLOCKED_UNSUPPORTED)


def _same_values(actual: object, expected: object) -> bool:
    if isinstance(actual, Mapping) and isinstance(expected, dict):
        return (all(type(key) is str for key in actual) and set(actual) == set(expected)
                and all(_same_values(actual[key], expected[key]) for key in expected))
    if type(actual) is tuple and type(expected) is tuple:
        return len(actual) == len(expected) and all(_same_values(a, b) for a, b in zip(actual, expected))
    return type(actual) is type(expected) and actual == expected


def _strict_stack_policies(value: object) -> bool:
    return (type(value) is tuple and all(
        type(entry) is tuple and len(entry) == 2 and all(type(item) is str for item in entry) for entry in value))


def _strict_route(route: object) -> bool:
    if type(route) is not ScopedRoute:
        return False
    text = (route.service_id, route.device_name, route.protocol, route.listen_address, route.connect_address, route.bind)
    return (all(type(value) is str for value in text)
            and type(route.listen_port) is int and type(route.connect_port) is int
            and type(route.nat) is bool and type(route.proxy_protocol) is bool)


def _matches_request(desired: DesiredManifestV2, manifest: InstallationManifest, catalog: ComponentCatalog,
                     request: MigrationAdmissionRequest) -> bool:
    preview = preview_migration(manifest, catalog)
    reference = scoped_route_reference(manifest, catalog, exposure=request.exposure, listen_address=request.listen_address)
    return (type(reference) is ScopedPolicyReference and reference.status is PolicyStatus.REFERENCE
            and type(reference.policy_version) is str and reference.policy_version == "scoped-route-policy-v2"
            and type(reference.profile_algorithm) is str and reference.profile_algorithm == "profile-name-v1"
            and reference.runtime_source is UnknownIdentity.UNKNOWN
            and reference.host is UnknownIdentity.UNKNOWN and reference.project is UnknownIdentity.UNKNOWN
            and reference.ownership is UnknownIdentity.UNKNOWN and reference.applied is False and reference.qualified is False
            and type(reference.routes) is tuple and all(_strict_route(item) for item in reference.routes)
            and type(desired.desired_profile_name) is str
            and desired.desired_profile_name == reference.profile_name
            and type(desired.desired_routes) is tuple and all(_strict_route(item) for item in desired.desired_routes)
            and desired.desired_routes == reference.routes
            and _strict_stack_policies(desired.stack_policies) and desired.stack_policies == preview.stack_policies
            and desired.swagger_exposure is preview.swagger_exposure)


class MigrationAdmissionService:
    """Inspect only injected read ports; all results deny admission."""

    def __init__(self, manifests: ManifestRepository, catalog: CatalogRepository) -> None:
        self._manifests = manifests
        self._catalog = catalog

    def evaluate(self, request: object) -> MigrationAdmissionResult:
        try:
            snapshot = self._manifests.load()
            catalog = self._catalog.load()
            if (type(snapshot) is not ManifestSnapshot or type(snapshot.manifest) is not InstallationManifest
                    or type(snapshot.token) is not str or not snapshot.token
                    or type(snapshot.diagnostics) is not tuple
                    or any(type(item) is not str for item in snapshot.diagnostics)
                    or type(catalog) is not ComponentCatalog
                    or type(request) is not MigrationAdmissionRequest
                    or type(request.version) is not str or type(request.exposure) is not SwaggerMode
                    or type(request.listen_address) is not str):
                return _UNKNOWN
            plan = plan_desired_manifest_v2(snapshot.manifest, catalog, exposure=request.exposure,
                                            listen_address=request.listen_address)
            if type(plan) is not ConversionPlan or plan.status is not ConversionStatus.DESIRED:
                return _UNKNOWN
            desired = plan.desired
            if (type(desired) is not DesiredManifestV2
                    or not _same_values(desired.v1_snapshot, snapshot.manifest.model_dump(mode="python", warnings="error"))
                    or type(desired.desired_project) is not str or desired.desired_project != "default"
                    or type(desired.desired_schema_version) is not int or desired.desired_schema_version != 2
                    or desired.actual_project is not UnknownIdentity.UNKNOWN
                    or desired.actual_profile is not UnknownIdentity.UNKNOWN
                    or desired.actual_route is not UnknownIdentity.UNKNOWN
                    or desired.actual_owner is not UnknownIdentity.UNKNOWN
                    or desired.actual_host is not UnknownIdentity.UNKNOWN
                    or desired.runtime_source is not UnknownIdentity.UNKNOWN
                    or desired.applied is not False or desired.qualified is not False
                    or not _matches_request(desired, snapshot.manifest, catalog, request)):
                return _UNKNOWN
            if type(incus_capability.SUPPORTED_VERSIONS) is not frozenset or incus_capability.SUPPORTED_VERSIONS:
                return _UNKNOWN
            capability = incus_capability.classify_incus_capability(IntentKind.INSTALLATION_SCOPED, request.version)
            return _UNSUPPORTED if capability is CapabilityResult.UNSUPPORTED else _UNKNOWN
        except Exception:
            return _UNKNOWN

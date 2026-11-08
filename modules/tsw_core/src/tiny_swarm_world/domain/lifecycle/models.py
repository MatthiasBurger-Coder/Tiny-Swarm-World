"""Strict, parser-independent lifecycle values. No credential values belong here."""
from __future__ import annotations

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_.-]*$", max_length=100)]
Identity = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:+/@-]*$", max_length=300)]
Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
Revision = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("schema_version", "catalog_version", mode="before", check_fields=False)
    @classmethod
    def exact_schema_number(cls, value: object) -> int:
        if type(value) is not int:
            raise ValueError("Schema/catalog version must be an integer.")
        return value


class VersionIdentity(Contract):
    upstream_version: Identity | None = None
    image_tag: Identity | None = None
    image_digest: Digest | None = None
    build_identity: Identity | None = None
    image_repository: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9./:_-]*$")] | None = None

    @model_validator(mode="after")
    def coherent_image(self) -> Self:
        if (self.image_tag or self.image_digest) and not self.image_repository:
            raise ValueError("Image identity requires its repository.")
        return self


class ProductIdentity(Contract):
    release: Identity
    revision: Revision
    dependency_lock: Digest
    config_schema: Annotated[int, Field(ge=1)] = 1
    installation_model: Literal["prepared-git"] = "prepared-git"


class CredentialReference(Contract):
    key: Annotated[str, Field(pattern=r"^TSW_[A-Z0-9]+(?:_[A-Z0-9]+)+$")]
    source: Literal["internal_test_catalog", "external_user_secret", "placeholder_only"]


class ComponentState(Contract):
    component_id: Identifier
    service_id: Identifier
    desired: VersionIdentity
    observed: VersionIdentity | None = None

    def drift(self) -> tuple[str, ...]:
        if self.observed is None:
            return ("observation_missing",)
        differences = []
        for field in VersionIdentity.model_fields:
            wanted = getattr(self.desired, field)
            actual = getattr(self.observed, field)
            if wanted is not None and wanted != actual:
                differences.append(field + ("_unknown" if actual is None else "_mismatch"))
        if self.desired.image_repository and self.observed.image_digest is None:
            differences.append("resolved_image_unknown")
        return tuple(differences)


class ConfigurationReference(Contract):
    """Symbolic provenance, never arbitrary effective configuration values."""
    key: Identifier
    source: Literal["operator_override", "native_asset", "environment", "managed_default"]
    reference: Identifier


class InstallationManifest(Contract):
    schema_version: Literal[1] = 1
    catalog_version: Literal[1] = 1
    installation_id: Annotated[str, Field(min_length=36, max_length=36)]
    host: Literal["native-linux", "wsl2"]
    runtime_profile: Literal["classic"] = "classic"
    service_preset: Literal["default", "service-access"]
    product: ProductIdentity
    requested_services: tuple[Identifier, ...]
    resolved_services: tuple[Identifier, ...]
    selection_reasons: dict[Identifier, tuple[Identifier, ...]] = Field(default_factory=dict)
    components: tuple[ComponentState, ...]
    credential_references: tuple[CredentialReference, ...] = ()
    configuration_references: tuple[ConfigurationReference, ...] = ()
    operation_reference: Identifier | None = None
    checkpoint_reference: Identifier | None = None

    @model_validator(mode="after")
    def coherent_installation(self) -> Self:
        UUID(self.installation_id)
        requested, resolved = set(self.requested_services), set(self.resolved_services)
        if len(requested) != len(self.requested_services) or len(resolved) != len(self.resolved_services):
            raise ValueError("Selections must contain unique service IDs.")
        if not requested <= resolved or not {"incus", "portainer"} <= resolved:
            raise ValueError("Selection requires requested services and Classic foundations.")
        if set(self.selection_reasons) != resolved - requested:
            raise ValueError("Every added service requires selection provenance.")
        if any(not reasons or not set(reasons) <= resolved for reasons in self.selection_reasons.values()):
            raise ValueError("Selection reasons must reference resolved services.")
        ids = [item.component_id for item in self.components]
        if len(ids) != len(set(ids)) or any(item.service_id not in resolved for item in self.components):
            raise ValueError("Component identities must be unique and selected.")
        keys = [item.key for item in self.credential_references]
        if len(keys) != len(set(keys)):
            raise ValueError("Credential references must be unique.")
        return self


class ResourceRequirements(Contract):
    """Native declarations only; absent limits are unknown, never zero capacity."""
    declared: dict[Identifier, dict[str, object]] = Field(default_factory=dict)
    qualification: Literal["native-declarations-only"] = "native-declarations-only"


class ComponentUpdateTarget(Contract):
    """A complete service bundle, never an arbitrary registry tag selection."""
    target_id: Identifier
    versions: dict[Identifier, VersionIdentity]
    qualification: Literal["installation-baseline", "candidate-transition", "qualified-transition"]
    metadata_source: Identifier
    hosts: tuple[Literal["native-linux", "wsl2"], ...] = ("native-linux", "wsl2")
    presets: tuple[Literal["default", "service-access"], ...] = ("default", "service-access")


class ComponentUpdateTransition(Contract):
    """Explicit source admission and recovery limits owned by release policy."""
    target_id: Identifier
    source_versions: dict[Identifier, VersionIdentity]
    migrations: tuple[Identifier, ...]
    backup_required: bool
    availability_impact: Annotated[str, Field(min_length=1)]
    recovery_limit: Annotated[str, Field(min_length=1)]


class ServiceDefinition(Contract):
    service_id: Identifier
    kind: Literal["host-prerequisite", "managed-foundation", "stack"]
    mandatory: bool = False
    dependencies: tuple[Identifier, ...]
    capabilities: tuple[Identifier, ...]
    components: tuple[ComponentState, ...]
    resources: ResourceRequirements
    native_asset: str | None
    presets: tuple[Literal["default", "service-access"], ...]
    profile_support: Literal["classic-only"] = "classic-only"
    lifecycle_owner: Literal["host-operator", "portainer-adapter", "stack-update"]
    migration_policy: Literal["no-qualified-transition", "explicit-transitions"] = "no-qualified-transition"
    backup_policy: Literal["required-before-stateful-transition", "not-applicable"]
    update_targets: tuple[ComponentUpdateTarget, ...] = ()
    update_transitions: tuple[ComponentUpdateTransition, ...] = ()

    @model_validator(mode="after")
    def coherent_update_policy(self) -> Self:
        members = {item.component_id for item in self.components}
        targets = {item.target_id: item for item in self.update_targets}
        if len(targets) != len(self.update_targets):
            raise ValueError("Duplicate update target IDs.")
        for target in self.update_targets:
            if set(target.versions) != members:
                raise ValueError("Update targets must cover the entire service bundle.")
            if target.qualification in {"candidate-transition", "qualified-transition"} and any(
                not version.image_digest or not version.image_repository for version in target.versions.values()
            ):
                raise ValueError("Transition targets require immutable image identities for every component.")
            if any((version.image_tag or "").lower() == "latest" for version in target.versions.values()):
                raise ValueError("Mutable latest is not a supported update target.")
        if self.update_transitions and self.migration_policy != "explicit-transitions":
            raise ValueError("Transitions require explicit migration policy.")
        for transition in self.update_transitions:
            transition_target = targets.get(transition.target_id)
            if transition_target is None or transition_target.qualification not in {
                "candidate-transition", "qualified-transition",
            }:
                raise ValueError("Transitions require an admitted candidate or qualified target.")
            if set(transition.source_versions) != members or any(
                not version.image_digest or not version.image_repository for version in transition.source_versions.values()
            ):
                raise ValueError("Transitions require exact immutable source bundle identities.")
            if self.backup_policy == "required-before-stateful-transition" and not transition.backup_required:
                raise ValueError("Stateful transitions require a backup.")
        return self


class ComponentCatalog(Contract):
    schema_version: Literal[1] = 1
    catalog_version: Literal[1] = 1
    services: tuple[ServiceDefinition, ...]

    def validate_manifest(self, manifest: InstallationManifest) -> None:
        services = {service.service_id: service for service in self.services}
        selected = set(manifest.resolved_services)
        if not selected <= services.keys():
            raise ValueError("Unknown service; inspect the Classic catalog before adopting.")
        for name in selected:
            service = services[name]
            if manifest.service_preset not in service.presets:
                raise ValueError("Service is unsupported by the installation preset.")
            if not set(service.dependencies) <= selected:
                raise ValueError("Selected service dependencies are missing.")
        expected = {(component.component_id, name) for name in selected for component in services[name].components}
        actual = {(component.component_id, component.service_id) for component in manifest.components}
        if actual != expected:
            raise ValueError("Component inventory is incomplete or ambiguous; inspect every selected bundle.")

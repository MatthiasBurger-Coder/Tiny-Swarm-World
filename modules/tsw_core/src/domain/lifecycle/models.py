"""Strict, parser-independent lifecycle values. No credential values belong here."""
from __future__ import annotations

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SerializerFunctionWrapHandler, field_validator, model_serializer, model_validator

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


class SwarmOwnership(Contract):
    owner: Literal['swarm'] = 'swarm'


class PortainerOwnership(Contract):
    owner: Literal['portainer']
    endpoint_id: Annotated[int, Field(gt=0)]
    stack_id: Annotated[int, Field(gt=0)]
    resource_control_id: Annotated[int, Field(gt=0)]
    ownership_fingerprint: Digest
    definition_fingerprint: Digest


StackOwnership = Annotated[SwarmOwnership | PortainerOwnership, Field(discriminator='owner')]


class ProxyRoute(Contract):
    device_name: Identifier
    device_type: Literal['proxy'] = 'proxy'
    bind: Literal['host'] = 'host'
    listen_protocol: Literal['tcp'] = 'tcp'
    listen_address: Literal['0.0.0.0', '127.0.0.1']
    listen_port: Annotated[int, Field(ge=1, le=65535)]
    connect_protocol: Literal['tcp'] = 'tcp'
    connect_address: Literal['127.0.0.1'] = '127.0.0.1'
    connect_port: Annotated[int, Field(ge=1, le=65535)]
    nat: Literal[False] = False
    proxy_protocol: Literal[False] = False

    @model_validator(mode='before')
    @classmethod
    def exact_options(cls, value: object) -> object:
        if isinstance(value, dict) and any(key in value and type(value[key]) is not bool for key in ('nat', 'proxy_protocol')):
            raise ValueError('Proxy flags require exact boolean values.')
        return value

    @model_validator(mode='after')
    def named_route(self) -> Self:
        if self.device_name != f'tsw-proxy-{self.listen_port}':
            raise ValueError('Route device differs from its declared listener.')
        return self


def installation_profile_name(installation_id: str) -> str:
    import hashlib

    canonical = str(UUID(installation_id))
    return 'tsw-manager-' + hashlib.sha256(canonical.encode('ascii')).hexdigest()[:24]


class InstallationProfileBinding(Contract):
    project: Literal['default'] = 'default'
    profile_name: Identifier
    routes: tuple[ProxyRoute, ...]

    @model_validator(mode='after')
    def unique_routes(self) -> Self:
        keys = [(route.device_name, route.listen_address, route.listen_port) for route in self.routes]
        listeners = [(route.listen_address, route.listen_port) for route in self.routes]
        if keys != sorted(set(keys)) or len({route.device_name for route in self.routes}) != len(keys) or len(set(listeners)) != len(keys):
            raise ValueError('Profile routes must be unique and ordered.')
        return self


class InstallationManifest(Contract):
    schema_version: Literal[1, 2] = 1
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
    service_exposure: dict[Identifier, Literal['published', 'internal']] | None = None
    stack_ownership: dict[Identifier, StackOwnership] | None = None
    installation_profile: InstallationProfileBinding | None = None

    @model_serializer(mode='wrap')
    def schema_serialization(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        result = handler(self)
        if self.schema_version == 1:
            for key in ('service_exposure', 'stack_ownership', 'installation_profile'):
                result.pop(key, None)
        return result

    def effective_exposure(self) -> dict[str, Literal['published', 'internal']]:
        if self.schema_version == 2:
            return dict(self.service_exposure or {})
        return {'swagger': 'published'} if 'swagger' in self.resolved_services else {}

    def effective_stack_ownership(self) -> dict[str, SwarmOwnership | PortainerOwnership]:
        if self.schema_version == 2:
            return dict(self.stack_ownership or {})
        return {name: SwarmOwnership() for name in self.resolved_services if name not in {'incus', 'portainer'}}

    @model_validator(mode="after")
    def coherent_installation(self) -> Self:
        policy_fields = {'service_exposure', 'stack_ownership', 'installation_profile'}
        if self.schema_version == 1 and policy_fields.intersection(self.model_fields_set):
            raise ValueError('Schema one cannot declare schema two policy.')
        if self.schema_version == 2 and not policy_fields.issubset(self.model_fields_set):
            raise ValueError('Schema two requires explicit installation policy.')
        UUID(self.installation_id)
        if self.schema_version == 2:
            exposure_keys = {'swagger'} if 'swagger' in self.resolved_services else set()
            if self.service_exposure is None or set(self.service_exposure) != exposure_keys:
                raise ValueError('Exposure must cover exactly selected Swagger.')
            stacks = set(self.resolved_services) - {'incus', 'portainer'}
            if self.stack_ownership is None or set(self.stack_ownership) != stacks:
                raise ValueError('Stack ownership must cover selected optional stacks.')
            if self.installation_profile is not None and self.installation_profile.profile_name != installation_profile_name(self.installation_id):
                raise ValueError('Profile identity differs from the installation.')
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
        if manifest.schema_version == 2:
            stack_ids = {name for name in selected if services[name].kind == 'stack' and services[name].native_asset is not None}
            if set(manifest.stack_ownership or {}) != stack_ids:
                raise ValueError('Ownership keys must identify selected native optional stacks.')
        expected = {(component.component_id, name) for name in selected for component in services[name].components}
        actual = {(component.component_id, component.service_id) for component in manifest.components}
        if actual != expected:
            raise ValueError("Component inventory is incomplete or ambiguous; inspect every selected bundle.")


def migrate_manifest_v1(manifest: InstallationManifest) -> InstallationManifest:
    """Pure policy-preserving migration; callers own verified commit and locking."""
    if manifest.schema_version == 2:
        return InstallationManifest.model_validate(manifest.model_dump())
    payload = manifest.model_dump()
    payload.update(schema_version=2, service_exposure=manifest.effective_exposure(),
                   stack_ownership=manifest.effective_stack_ownership(), installation_profile=None)
    return InstallationManifest.model_validate(payload)


def comparable_manifest(manifest: InstallationManifest) -> dict[str, object]:
    """Compare only the exact policy-preserving legacy migration."""
    return migrate_manifest_v1(manifest).model_dump()


class InstallationProfileIntent(Contract):
    operation_id: Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
    operation_kind: Literal['setup', 'add', 'component-update', 'product-upgrade', 'portainer-upgrade', 'recovery', 'cleanup']
    installation_id: Annotated[str, Field(min_length=36, max_length=36)]
    controller_revision: Revision
    product_source_revision: Revision
    product_target_revision: Revision | None
    incus_version: Annotated[str, Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.+-]{0,63}$')]
    manifest_token: Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')] | None
    requested_services: tuple[Identifier, ...]
    resolved_services: tuple[Identifier, ...]
    service_exposure: dict[Identifier, Literal['published', 'internal']]
    stack_ownership: dict[Identifier, StackOwnership]
    profile: InstallationProfileBinding | None
    stage: Literal['intent', 'profile-configured', 'instance-initialized', 'routes-verified', 'instance-started', 'completed', 'recoverable'] = 'intent'

    @model_validator(mode='after')
    def coherent_intent(self) -> Self:
        if str(UUID(self.installation_id)) != self.installation_id:
            raise ValueError('Intent installation identity must be canonical.')
        if (len(set(self.requested_services)) != len(self.requested_services)
                or len(set(self.resolved_services)) != len(self.resolved_services)
                or not set(self.requested_services) <= set(self.resolved_services)
                or not {'incus', 'portainer'} <= set(self.resolved_services)
                or set(self.service_exposure) != ({'swagger'} if 'swagger' in self.resolved_services else set())
                or set(self.stack_ownership) != set(self.resolved_services) - {'incus', 'portainer'}):
            raise ValueError('Intent policy and selection differ.')
        if self.profile is not None and self.profile.profile_name != installation_profile_name(self.installation_id):
            raise ValueError('Intent profile differs from installation identity.')
        if self.stage not in {'intent', 'completed', 'recoverable'} and self.profile is None:
            raise ValueError('Profile lifecycle stages require a bound profile.')
        return self

    def validate_manifest(self, manifest: InstallationManifest) -> None:
        if (self.installation_id != str(UUID(manifest.installation_id))
                or self.requested_services != manifest.requested_services
                or self.resolved_services != manifest.resolved_services
                or self.service_exposure != manifest.effective_exposure()
                or self.stack_ownership != manifest.effective_stack_ownership()
                or self.profile != manifest.installation_profile
                or self.product_source_revision != manifest.product.revision):
            raise ValueError('Checkpoint intent differs from the admitted installation.')


def legacy_runtime_compatible(manifest: InstallationManifest) -> bool:
    """New policy is data-only until its separate capability implementation is admitted."""
    return (manifest.installation_profile is None
            and all(mode == 'published' for mode in manifest.effective_exposure().values())
            and all(owner.owner == 'swarm' for owner in manifest.effective_stack_ownership().values()))

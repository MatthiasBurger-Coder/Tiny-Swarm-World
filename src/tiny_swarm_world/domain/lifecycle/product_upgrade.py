"""Bounded Classic product release policy, distinct from component updates."""
from typing import Annotated, Literal, Self
from pydantic import Field, SerializerFunctionWrapHandler, field_validator, model_serializer, model_validator

from tiny_swarm_world.domain.lifecycle.models import InstallationProfileIntent, Contract, Identifier, InstallationManifest, ProductIdentity, migrate_manifest_v1

SOURCE_RELEASE = '0.4.0'
SOURCE_REVISION = '346f4a43dbdc43380e7bc703ab185bc06746965b'
TARGET_RELEASE = '0.5.0'
TARGET_REVISION = 'b3de7fa16e24c5702d61f855851c6c3255871489'
MIGRATIONS = ('protected-infra-v1', 'installation-product-v1')


class ProductRelease(Contract):
    product: ProductIdentity
    package_version: str
    supported_manifest_schemas: tuple[Annotated[int, Field(strict=True, ge=1, le=2)], ...] = (1,)

    @model_serializer(mode='wrap')
    def legacy_serialization(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        result = handler(self)
        if self.supported_manifest_schemas == (1,):
            result.pop('supported_manifest_schemas', None)
        return result

    @field_validator('supported_manifest_schemas', mode='after')
    @classmethod
    def strict_schemas(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value or list(value) != sorted(set(value)):
            raise ValueError('Unsupported target manifest reader metadata.')
        return value

    @model_validator(mode='after')
    def pinned_reader(self) -> Self:
        if self.product.revision in {SOURCE_REVISION, TARGET_REVISION} and self.supported_manifest_schemas != (1,):
            raise ValueError('Pinned released readers support only manifest schema one.')
        return self


class ProductConfigurationSource(Contract):
    kind: Literal['external-infra'] = 'external-infra'
    reference: Identifier
    policy: Literal['provider-memory-v1'] = 'provider-memory-v1'


class ProductPlan(Contract):
    source: ProductRelease
    target: ProductRelease
    manifest: InstallationManifest
    manifest_token: str | None
    adoption: bool
    configuration_changes: tuple[str, ...] = ()
    migrations: tuple[str, ...] = MIGRATIONS
    component_changes: tuple[str, ...] = ()
    resource_bytes: int = 2147483648
    configuration_source: ProductConfigurationSource | None = None
    profile_intent: InstallationProfileIntent | None = None

    @model_serializer(mode='wrap')
    def legacy_serialization(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        result = handler(self)
        if self.profile_intent is None:
            result.pop('profile_intent', None)
        return result

    @model_validator(mode='after')
    def coherent_profile_intent(self) -> Self:
        if self.manifest.schema_version not in self.target.supported_manifest_schemas:
            raise ValueError('Target reader cannot preserve the admitted manifest schema.')
        if self.profile_intent is not None:
            if 2 not in self.target.supported_manifest_schemas:
                raise ValueError('Target reader cannot preserve bound profile intent.')
            self.profile_intent.validate_manifest(self.manifest)
            if (self.profile_intent.operation_kind not in {'product-upgrade', 'recovery'}
                    or self.profile_intent.manifest_token != self.manifest_token
                    or self.profile_intent.product_target_revision != self.target.product.revision):
                raise ValueError('Product intent target differs from the admitted release.')
        return self

    def committed_manifest(self) -> InstallationManifest:
        original = migrate_manifest_v1(self.manifest) if 2 in self.target.supported_manifest_schemas else self.manifest
        return original.model_copy(update={'product': self.target.product})

    def preview(self) -> dict[str, object]:
        return {
            'status': 'preview',
            'product_changes': {'source': self.source.model_dump(mode='json'),
                                'target': self.target.model_dump(mode='json')},
            'dependency_changes': {'source_lock': self.source.product.dependency_lock,
                                   'target_lock': self.target.product.dependency_lock,
                                   'installation': 'new isolated environment, hash-locked requirements'},
            'configuration_changes': list(self.configuration_changes),
            'state_changes': list(self.migrations), 'component_changes': list(self.component_changes),
            'resolved_services': list(self.manifest.resolved_services), 'adoption_required': self.adoption,
            'required_free_bytes': self.resource_bytes,
            'configuration_source': (self.configuration_source.model_dump(mode='json')
                                     if self.configuration_source else None),
            'manifest_migration': 'v1-to-v2' if self.manifest.schema_version == 1 and 2 in self.target.supported_manifest_schemas else 'none',
            'service_exposure': self.manifest.effective_exposure(),
            'stack_ownership': {key: value.model_dump(mode='json') for key, value in self.manifest.effective_stack_ownership().items()},
            'recovery': 'resume pinned operation with --recover; no downgrade or data restore',
        }


class ProductCheckpoint(Contract):
    plan: ProductPlan
    stage: Literal['admitted', 'staging', 'staged', 'migrating', 'migrated', 'verifying', 'verified', 'switching', 'switched', 'committing', 'completed']
    service_identities: dict[str, str]


def admit_release_pair(source: ProductRelease, target: ProductRelease) -> None:
    if (source.product.release != SOURCE_RELEASE or source.product.revision != SOURCE_REVISION
            or source.package_version != '0.2.0' or target.product.release != TARGET_RELEASE
            or target.product.revision != TARGET_REVISION or target.package_version != '0.2.0'
            or source.product.config_schema != 1 or target.product.config_schema != 1):
        raise ValueError('Unsupported product transition; only official 0.4.0 to 0.5.0 is admitted. Downgrade is unsupported.')
    if source.product.revision == target.product.revision:
        raise ValueError('Product upgrade must change product revision.')

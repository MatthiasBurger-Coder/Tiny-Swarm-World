"""Bounded Classic product release policy, distinct from component updates."""
from typing import Literal

from tiny_swarm_world.domain.lifecycle.models import Contract, InstallationManifest, ProductIdentity

SOURCE_RELEASE = '0.4.0'
SOURCE_REVISION = '346f4a43dbdc43380e7bc703ab185bc06746965b'
TARGET_RELEASE = '0.5.0'
TARGET_REVISION = 'b3de7fa16e24c5702d61f855851c6c3255871489'
MIGRATIONS = ('protected-infra-v1', 'installation-product-v1')


class ProductRelease(Contract):
    product: ProductIdentity
    package_version: str


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

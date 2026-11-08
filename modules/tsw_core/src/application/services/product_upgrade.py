"""Ordered, restartable product upgrades through existing lifecycle boundaries."""
import asyncio

from tiny_swarm_world.application.services.product_upgrade_preview import preview_product_upgrade

from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease, InstallationOperationLock, installation_operation
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestRepository
from tiny_swarm_world.application.ports.lifecycle.product_upgrade import ProductInstallation, ProductRuntime, ProductUpgradeJournal
from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductCheckpoint, ProductPlan, TARGET_RELEASE
from tiny_swarm_world.domain.preflight import LiveConsent


from tiny_swarm_world.application.services.shared.settled_blocking import settled_blocking as _blocking


class ProductUpgradeService:
    def __init__(self, manifests: ManifestRepository, installation: ProductInstallation,
                 journal: ProductUpgradeJournal, runtime: ProductRuntime, *,
                 operation_lock: InstallationOperationLock | None = None, operation_lease: InstallationLease | None = None,
                 profile_runtime_factory=None):
        self.manifests = manifests
        self.installation = installation
        self.journal = journal
        self.runtime = runtime
        self.operation_lock, self.operation_lease = operation_lock, operation_lease
        self.profile_runtime_factory = profile_runtime_factory

    async def preview(self, target: str, *, recovery: bool = False) -> dict[str, object]:
        return await preview_product_upgrade(self.installation, self.journal, target, recovery=recovery)

    async def run(self, target: str, *, consent: LiveConsent, recovery: bool = False) -> dict[str, object]:
        if not consent.accepted:
            return {'status': 'refused', 'diagnostics': list(consent.missing_reasons)}
        if target != TARGET_RELEASE:
            raise LifecycleStateError('Unsupported product release or downgrade; use target 0.5.0.')
        with installation_operation(self.operation_lock, 'product-upgrade', self.operation_lease) as lease, lease.journal('product'), self.journal.exclusive():
            from tiny_swarm_world.application.services.runtime_policy import admit_runtime_policy

            installed = self.manifests.load().manifest
            profile_operation = None if installed is None else await admit_runtime_policy(
                installed, lease, 'recovery' if recovery else 'product-upgrade', consent, self.profile_runtime_factory)
            checkpoint = self.journal.load()
            if checkpoint is not None:
                ProductCheckpoint.model_validate(checkpoint.model_dump())
            if checkpoint is not None and checkpoint.plan.target.product.release != target:
                raise LifecycleStateError('Another product target owns the checkpoint.')
            if checkpoint is not None and checkpoint.stage == 'completed':
                await self._verify_completed(checkpoint)
                return {'status': 'no_op', 'product': checkpoint.plan.target.product.model_dump(mode='json'),
                        'resolved_services': list(checkpoint.plan.manifest.resolved_services)}
            if checkpoint is None:
                if recovery:
                    raise LifecycleStateError('No product checkpoint to recover.')
                plan = await asyncio.to_thread(self.installation.plan, target)
                ProductPlan.model_validate(plan.model_dump())
                await _blocking(self.installation.validate, plan)
                identities = await self.runtime.verify(plan.manifest, plan=plan)
                checkpoint = ProductCheckpoint(plan=plan, stage='admitted', service_identities=identities)
                self.journal.save(checkpoint)
            elif not recovery:
                raise LifecycleStateError('Interrupted upgrade requires explicit --recover with the original target.')
            return await self._execute(checkpoint, profile_operation)

    async def _execute(self, checkpoint: ProductCheckpoint, profile_operation=None) -> dict[str, object]:
        from tiny_swarm_world.application.services.runtime_policy import recheck_runtime_policy

        await recheck_runtime_policy(profile_operation)
        plan = checkpoint.plan
        await _blocking(self.installation.validate, plan)
        stages = ('admitted', 'staging', 'staged', 'migrating', 'migrated', 'verifying', 'verified',
                  'switching', 'switched', 'committing', 'completed')
        index = stages.index(checkpoint.stage)
        if index <= 1:
            checkpoint = self._save(checkpoint, 'staging')
            await recheck_runtime_policy(profile_operation)
            await _blocking(self.installation.stage, plan)
            checkpoint = self._save(checkpoint, 'staged')
        if index <= 3:
            checkpoint = self._save(checkpoint, 'migrating')
            await recheck_runtime_policy(profile_operation)
            await _blocking(self.installation.migrate, plan)
            checkpoint = self._save(checkpoint, 'migrated')
        # Verification is always fresh, including after an interrupted switch/commit.
        checkpoint = self._save(checkpoint, 'verifying')
        await _blocking(self.installation.verify_product, plan)
        await _blocking(self.installation.verify_target_runtime, plan)
        identities = await self.runtime.verify(plan.manifest, plan=plan)
        if identities != checkpoint.service_identities:
            raise LifecycleStateError('Installed service identities changed; preserve checkpoint and inspect runtime drift.')
        checkpoint = self._save(checkpoint, 'verified')
        checkpoint = self._save(checkpoint, 'switching')
        await recheck_runtime_policy(profile_operation)
        await _blocking(self.installation.activate, plan)
        checkpoint = self._save(checkpoint, 'switched')
        checkpoint = self._save(checkpoint, 'committing')
        await recheck_runtime_policy(profile_operation)
        self._commit(plan)
        self._save(checkpoint, 'completed')
        return {'status': 'completed', 'product': plan.target.product.model_dump(mode='json'),
                'resolved_services': list(plan.manifest.resolved_services),
                'recovery': 'previous checkout/environment retained; downgrade/data restore unsupported'}

    def _save(self, checkpoint, stage):
        updated = checkpoint.model_copy(update={'stage': stage})
        self.journal.save(updated)
        return updated

    def _commit(self, plan: ProductPlan) -> None:
        snapshot = self.manifests.load()
        desired = plan.committed_manifest()
        if snapshot.manifest == desired:
            return
        if snapshot.token != plan.manifest_token or (snapshot.manifest is not None and snapshot.manifest != plan.manifest):
            raise LifecycleStateError('Installation state changed; preserve product checkpoint and inspect drift.')
        self.manifests.save(desired, expected_token=plan.manifest_token)

    async def _verify_completed(self, checkpoint: ProductCheckpoint) -> None:
        plan = checkpoint.plan
        snapshot = self.manifests.load()
        if snapshot.manifest != plan.committed_manifest():
            raise LifecycleStateError('Completed product state drifted; inspect manifest before retrying.')
        await asyncio.to_thread(self.installation.validate, plan)
        await asyncio.to_thread(self.installation.verify_product, plan)
        await asyncio.to_thread(self.installation.verify_target_runtime, plan)
        await asyncio.to_thread(self.installation.verify_active, plan)
        if await self.runtime.verify(snapshot.manifest, plan=plan) != checkpoint.service_identities:
            raise LifecycleStateError('Completed product runtime drifted; no-op cannot be verified.')

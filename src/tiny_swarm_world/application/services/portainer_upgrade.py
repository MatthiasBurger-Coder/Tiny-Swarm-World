"""Dedicated Portainer stages within the existing lifecycle/consent contract."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestRepository
from tiny_swarm_world.application.ports.lifecycle.portainer_upgrade import PortainerUpgradeJournal, PortainerUpgradeRuntime
from tiny_swarm_world.domain.lifecycle.models import ConfigurationReference
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import (
    SOURCE_VERSION, TARGET_ID, TARGET_VERSION, versions,
)
from tiny_swarm_world.domain.preflight import LiveConsent


class PortainerUpgradeService:
    def __init__(self, manifests: ManifestRepository, journal: PortainerUpgradeJournal, runtime: PortainerUpgradeRuntime):
        self.manifests, self.journal, self.runtime = manifests, journal, runtime

    async def run(self, *, target: str | None, consent: LiveConsent, recovery: bool = False) -> dict[str, object]:
        if not consent.accepted:
            return {'status': 'refused', 'diagnostics': list(consent.missing_reasons)}
        if target not in {None, TARGET_ID} or (recovery and target is not None):
            raise LifecycleStateError('Unsupported Portainer target; recovery uses the original checkpoint.')
        with self.journal.exclusive():
            snapshot = self.manifests.load()
            if snapshot.manifest is None or snapshot.diagnostics or snapshot.token is None:
                raise LifecycleStateError('Portainer upgrade requires a valid adopted Classic installation.')
            checkpoint = self.journal.load()
            if checkpoint is not None and checkpoint.installation_id != snapshot.manifest.installation_id:
                raise LifecycleStateError('Portainer recovery belongs to another installation.')
            if checkpoint is not None and not checkpoint.settled:
                self._validate_manifest(checkpoint, snapshot.manifest)
            if recovery:
                return await self._recover(checkpoint)
            if checkpoint is not None and not checkpoint.settled:
                raise LifecycleStateError('Interrupted Portainer operation; recover before another upgrade.')
            before = await self.runtime.inspect()
            members = {item.component_id: item for item in snapshot.manifest.components if item.service_id == 'portainer'}
            if set(members) != set(versions(before.version)):
                raise LifecycleStateError('Portainer manifest bundle is incomplete.')
            for name, item in members.items():
                expected = versions(before.version)[name]
                if item.desired.image_repository != expected.image_repository or (item.desired.image_digest != expected.image_digest
                        and (item.desired.image_digest is not None or item.desired.image_tag != before.version)):
                    raise LifecycleStateError('Portainer manifest/runtime drift; inspect before mutation.')
            if before.version == TARGET_VERSION:
                return {'status': 'no_op', 'version': TARGET_VERSION}
            raise LifecycleStateError('Portainer upgrade blocked: persisted ownership proof is unavailable.')

    async def _recover(self, checkpoint):
        if checkpoint is None:
            raise LifecycleStateError('No Portainer operation exists to recover.')
        if checkpoint.stage == 'completed':
            raise LifecycleStateError('Completed upgrades cannot be downgraded through interruption recovery.')
        if checkpoint.stage in {'recovering', 'cancel_in_progress', 'recovered'}:
            await self._inspect_recovery(checkpoint)
            return {'status': 'unknown', 'reason': 'manual_reconciliation_required'}
        if checkpoint.stage == 'recovery_pending_proof':
            if not await self._inspect_recovery(checkpoint):
                return {'status': 'unknown', 'reason': 'manual_reconciliation_required'}
            return {'status': 'recovery_pending_proof'}
        if checkpoint.backup_digest is None:
            if checkpoint.stage != 'admitted':
                raise LifecycleStateError('No verified backup exists for this stage; no restore admitted.')
            checkpoint = checkpoint.model_copy(update={'stage': 'cancel_in_progress'})
            self._save_recovery(checkpoint)
            if not await self._run_recovery_effect(self.runtime.cancel_backup, checkpoint):
                return {'status': 'unknown', 'reason': 'manual_reconciliation_required'}
        else:
            if checkpoint.stage not in {'backed_up', 'upgrading', 'verified'}:
                raise LifecycleStateError('Portainer recovery stage is not admitted.')
            checkpoint = checkpoint.model_copy(update={'stage': 'recovering'})
            self._save_recovery(checkpoint)
            if not await self._run_recovery_effect(self.runtime.restore, checkpoint):
                return {'status': 'unknown', 'reason': 'manual_reconciliation_required'}
        if not await self._inspect_recovery(checkpoint):
            return {'status': 'unknown', 'reason': 'manual_reconciliation_required'}
        self._save_recovery(checkpoint.model_copy(update={'stage': 'recovery_pending_proof'}))
        return {'status': 'recovery_pending_proof'}

    async def _run_recovery_effect(self, effect, checkpoint):
        try:
            await effect(checkpoint)
            return True
        except Exception:
            return False

    async def _inspect_recovery(self, checkpoint):
        try:
            await self.runtime.inspect_recovery(checkpoint.before)
            return True
        except Exception:
            return False

    def _save_recovery(self, checkpoint):
        try:
            self.journal.save(checkpoint)
        except Exception:
            raise LifecycleStateError('Portainer recovery checkpoint unavailable; manual reconciliation required.') from None

    def _commit(self, snapshot, version):
        manifest = snapshot.manifest
        identities = versions(version)
        components = tuple(item.model_copy(update={'desired': identities[item.component_id], 'observed': identities[item.component_id]})
                           if item.service_id == 'portainer' else item for item in manifest.components)
        references = tuple(item for item in manifest.configuration_references
                           if item.key not in {'component-update.' + name for name in identities})
        references += tuple(ConfigurationReference(key='component-update.' + name, source='managed_default', reference=name)
                            for name in identities)
        self.manifests.save(manifest.model_copy(update={'components': components, 'configuration_references': references}),
                            expected_token=snapshot.token)


    @staticmethod
    def _validate_manifest(checkpoint, manifest):
        def normalized(value):
            payload = value.model_dump(mode='json')
            payload['components'] = [item for item in payload['components'] if item['service_id'] != 'portainer']
            payload['configuration_references'] = [item for item in payload['configuration_references']
                if item['key'] not in {'component-update.portainer', 'component-update.portainer-agent'}]
            return payload
        if normalized(manifest) != normalized(checkpoint.original):
            raise LifecycleStateError('Installation changed outside Portainer upgrade; inspect before recovery.')
        identities = {item.component_id: item for item in manifest.components if item.service_id == 'portainer'}
        if set(identities) != set(versions(SOURCE_VERSION)):
            raise LifecycleStateError('Portainer installation bundle changed; inspect before recovery.')

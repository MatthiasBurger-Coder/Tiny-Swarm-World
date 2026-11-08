"""Dedicated Portainer stages within the existing lifecycle/consent contract."""
from uuid import uuid4

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestRepository
from tiny_swarm_world.application.ports.lifecycle.portainer_upgrade import PortainerUpgradeJournal, PortainerUpgradeRuntime
from tiny_swarm_world.domain.lifecycle.models import ConfigurationReference
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import (
    PortainerCheckpoint, SOURCE_VERSION, TARGET_ID, TARGET_VERSION, versions,
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
            checkpoint = PortainerCheckpoint(operation_id=uuid4().hex, installation_id=snapshot.manifest.installation_id,
                                             before=before, manifest_token=snapshot.token, original=snapshot.manifest)
            self.journal.save(checkpoint)
            digest = await self.runtime.backup(checkpoint)
            checkpoint = checkpoint.model_copy(update={'backup_digest': digest, 'stage': 'backed_up'})
            self.journal.save(checkpoint)
            checkpoint = checkpoint.model_copy(update={'stage': 'upgrading'})
            self.journal.save(checkpoint)
            await self.runtime.upgrade(checkpoint)
            await self.runtime.verify(before, recovery=False)
            checkpoint = checkpoint.model_copy(update={'stage': 'verified'})
            self.journal.save(checkpoint)
            self._commit(snapshot, TARGET_VERSION)
            self.journal.save(checkpoint.model_copy(update={'stage': 'completed'}))
            return {'status': 'completed', 'version': TARGET_VERSION, 'stages': ['backup', 'upgrade', 'verify', 'managed-update', 'commit']}

    async def _recover(self, checkpoint):
        if checkpoint is None:
            raise LifecycleStateError('No Portainer operation exists to recover.')
        if checkpoint.stage == 'recovered':
            current = await self.runtime.inspect()
            if (current.version, current.volume, current.endpoints, current.ownership, current.server_id, current.agent_id, current.swarm_id) != (checkpoint.before.version, checkpoint.before.volume, checkpoint.before.endpoints, checkpoint.before.ownership, checkpoint.before.server_id, checkpoint.before.agent_id, checkpoint.before.swarm_id):
                raise LifecycleStateError('Recovered Portainer state drifted.')
            return {'status': 'no_op', 'version': SOURCE_VERSION}
        if checkpoint.settled:
            raise LifecycleStateError('Completed upgrades cannot be downgraded through interruption recovery.')
        if checkpoint.backup_digest is None:
            if checkpoint.stage != 'admitted':
                raise LifecycleStateError('No verified backup exists for this stage; no restore admitted.')
            # Admission is persisted before stopping the source. Until a checked
            # backup is durable, target mutation is impossible. Resume only the
            # independently verified original source, without restoring data.
            await self.runtime.cancel_backup(checkpoint)
        else:
            checkpoint = checkpoint.model_copy(update={'stage': 'recovering'})
            self.journal.save(checkpoint)
            await self.runtime.restore(checkpoint)
        await self.runtime.verify(checkpoint.before, recovery=True)
        snapshot = self.manifests.load()
        self._commit(snapshot, SOURCE_VERSION)
        self.journal.save(checkpoint.model_copy(update={'stage': 'recovered'}))
        return {'status': 'recovered', 'version': SOURCE_VERSION}

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

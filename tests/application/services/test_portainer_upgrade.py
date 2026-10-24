"""Dedicated gateway lifecycle with real journal and manifest persistence."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock

from tests.domain.lifecycle.test_update_planning import update_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.portainer_upgrade import PortainerUpgradeService
from tiny_swarm_world.domain.lifecycle.models import ConfigurationReference
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import PortainerObservation, images, versions
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_journal import JsonPortainerJournal

CONSENT = LiveConsent(True, confirmed=True)


class PortainerUpgradeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        _, manifest = update_fixture()
        identities = versions('2.45.0')
        manifest = manifest.model_copy(update={'configuration_references': (ConfigurationReference(
            key='custom.routing', source='operator_override', reference='portainer'),), 'components': tuple(
            item.model_copy(update={'desired': identities[item.component_id], 'observed': identities[item.component_id]})
            if item.service_id == 'portainer' else item for item in manifest.components)})
        self.manifests = JsonManifestRepository(self.root / 'manifest.json')
        self.manifests.save(manifest, expected_token=None)
        self.original = manifest
        self.journal = JsonPortainerJournal(self.root / 'portainer-upgrade.json')
        self.before = PortainerObservation(version='2.45.0', server_image=images('2.45.0')['portainer'],
                                           agent_image=images('2.45.0')['portainer-agent'], volume='portainer_portainer_data', server_id='server-id', agent_id='agent-id', swarm_id='swarm-id',
                                           endpoints=('endpoint-fingerprint',), ownership=('owner-fingerprint',))
        self.runtime = Mock()
        self.runtime.inspect = AsyncMock(return_value=self.before)
        self.runtime.backup = AsyncMock(return_value='sha256:' + 'a' * 64)
        self.runtime.upgrade = AsyncMock()
        self.runtime.verify = AsyncMock()
        self.runtime.restore = AsyncMock()
        self.runtime.cancel_backup = AsyncMock()
        self.service = PortainerUpgradeService(self.manifests, self.journal, self.runtime)

    async def test_upgrade_commits_whole_bundle_preserving_other_installation_state(self):
        result = await self.service.run(target=None, consent=CONSENT)
        self.assertEqual(result['status'], 'completed')
        after = self.manifests.load().manifest
        self.assertEqual({item.component_id: item.desired for item in after.components if item.service_id == 'portainer'}, versions('2.45.1'))
        self.assertEqual(tuple(item for item in after.components if item.service_id != 'portainer'),
                         tuple(item for item in self.original.components if item.service_id != 'portainer'))
        self.assertEqual(after.credential_references, self.original.credential_references)
        self.assertTrue(set(self.original.configuration_references) <= set(after.configuration_references))
        self.assertEqual(after.resolved_services, self.original.resolved_services)
        self.assertEqual(self.journal.load().stage, 'completed')
        self.runtime.verify.assert_awaited_once_with(self.before, recovery=False)
        self.assertEqual(self.journal.path.stat().st_mode & 0o777, 0o600)

    async def test_failure_keeps_recoverable_checkpoint_and_restores_before_verifying(self):
        self.runtime.upgrade.side_effect = LifecycleStateError('failed')
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT)
        self.assertEqual(self.journal.load().stage, 'upgrading')
        self.assertEqual(self.manifests.load().manifest, self.original)
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT)
        result = await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.assertEqual(result['status'], 'recovered')
        self.runtime.restore.assert_awaited_once()
        self.runtime.verify.assert_awaited_once_with(self.before, recovery=True)
        self.assertEqual(self.journal.load().stage, 'recovered')
        self.assertEqual({item.component_id: item.desired for item in self.manifests.load().manifest.components
                          if item.service_id == 'portainer'}, versions('2.45.0'))

    async def test_backup_failure_or_missing_backup_never_admits_upgrade_or_restore(self):
        self.runtime.backup.side_effect = LifecycleStateError('backup failed')
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT)
        self.runtime.upgrade.assert_not_called()
        await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.runtime.cancel_backup.assert_awaited_once()
        self.runtime.restore.assert_not_called()

    async def test_verification_failure_never_commits_and_recovery_failure_never_settles(self):
        self.runtime.verify.side_effect = LifecycleStateError('owner mismatch')
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT)
        self.assertEqual(self.manifests.load().manifest, self.original)
        self.runtime.restore.side_effect = LifecycleStateError('backup missing')
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.assertEqual(self.journal.load().stage, 'recovering')

    async def test_no_consent_unknown_target_and_noop_have_no_mutations(self):
        result = await self.service.run(target=None, consent=LiveConsent(False))
        self.assertEqual(result['status'], 'refused')
        self.runtime.inspect.assert_not_called()
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target='latest', consent=CONSENT)
        snapshot = self.manifests.load()
        self.service._commit(snapshot, '2.45.1')
        self.runtime.inspect.return_value = self.before.model_copy(update={'version': '2.45.1'})
        result = await self.service.run(target=None, consent=CONSENT)
        self.assertEqual(result['status'], 'no_op')
        self.runtime.backup.assert_not_called()
        self.runtime.upgrade.assert_not_called()
        self.runtime.verify.assert_not_called()

    async def test_manifest_source_drift_blocks_before_backup(self):
        snapshot = self.manifests.load()
        manifest = snapshot.manifest.model_copy(update={'components': tuple(item.model_copy(update={
            'desired': item.desired.model_copy(update={'image_digest': 'sha256:' + 'b' * 64})})
            if item.component_id == 'portainer' else item for item in snapshot.manifest.components)})
        self.manifests.save(manifest, expected_token=snapshot.token)
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT)
        self.runtime.backup.assert_not_called()

    async def test_cross_installation_checkpoint_cannot_recover(self):
        self.runtime.upgrade.side_effect = LifecycleStateError('failed')
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT)
        snapshot = self.manifests.load()
        changed = snapshot.manifest.model_copy(update={'installation_id': '12345678-1234-1234-1234-123456789012'})
        self.manifests.save(changed, expected_token=snapshot.token)
        with self.assertRaisesRegex(LifecycleStateError, 'another installation'):
            await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.runtime.restore.assert_not_called()

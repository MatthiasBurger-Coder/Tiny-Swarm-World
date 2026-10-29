"""Dedicated gateway lifecycle with real journal and manifest persistence."""
import asyncio
import multiprocessing
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tests.domain.lifecycle.test_update_planning import update_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.portainer_upgrade import PortainerUpgradeService
from tiny_swarm_world.domain.lifecycle.models import ConfigurationReference
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import PortainerCheckpoint, PortainerObservation, images, versions
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
        self.runtime.inspect_recovery = AsyncMock()
        self.service = PortainerUpgradeService(self.manifests, self.journal, self.runtime)

    def checkpoint(self, stage='admitted', backup=False):
        snapshot = self.manifests.load()
        checkpoint = PortainerCheckpoint(
            operation_id='operation', installation_id=self.original.installation_id,
            before=self.before, original=self.original, manifest_token=snapshot.token,
            stage=stage, backup_digest='sha256:' + 'a' * 64 if backup else None,
        )
        self.journal.save(checkpoint)
        return checkpoint

    async def test_upgrade_blocks_even_when_visible_ownership_matches(self):
        with self.assertRaisesRegex(LifecycleStateError, 'ownership proof'):
            await self.service.run(target=None, consent=CONSENT)
        self.assertIsNone(self.journal.load())
        self.assertEqual(self.manifests.load().manifest, self.original)
        self.runtime.backup.assert_not_called()
        self.runtime.upgrade.assert_not_called()
        self.runtime.verify.assert_not_called()

    async def test_backed_up_stages_restore_once_then_remain_pending(self):
        for stage in ('backed_up', 'upgrading', 'verified'):
            with self.subTest(stage=stage):
                self.checkpoint(stage, backup=True)
                self.runtime.restore.reset_mock()
                result = await self.service.run(target=None, consent=CONSENT, recovery=True)
                self.assertEqual(result['status'], 'recovery_pending_proof')
                self.assertEqual(self.journal.load().stage, 'recovery_pending_proof')
                self.runtime.restore.assert_awaited_once()
                self.assertEqual(self.manifests.load().manifest, self.original)
                await self.service.run(target=None, consent=CONSENT, recovery=True)
                self.runtime.restore.assert_awaited_once()
                self.runtime.verify.assert_not_called()

    async def test_admitted_cancel_then_pending_no_replay(self):
        self.checkpoint()
        self.assertEqual((await self.service.run(target=None, consent=CONSENT, recovery=True))['status'],
                         'recovery_pending_proof')
        await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.runtime.cancel_backup.assert_awaited_once()
        self.runtime.restore.assert_not_called()
        self.assertEqual(self.journal.load().stage, 'recovery_pending_proof')

    async def test_interrupted_and_legacy_recovered_are_unknown_without_replay(self):
        for stage in ('recovering', 'cancel_in_progress', 'recovered'):
            with self.subTest(stage=stage):
                self.checkpoint(stage, backup=stage != 'cancel_in_progress')
                self.assertEqual((await self.service.run(target=None, consent=CONSENT, recovery=True))['status'], 'unknown')
                self.assertEqual(self.journal.load().stage, stage)
                self.runtime.cancel_backup.assert_not_called()
                self.runtime.restore.assert_not_called()

    async def test_inspection_failure_retains_marker_without_manifest_commit(self):
        self.checkpoint('upgrading', backup=True)
        self.runtime.inspect_recovery.side_effect = LifecycleStateError('inspection failed')
        result = await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(self.journal.load().stage, 'recovering')
        self.assertEqual(self.manifests.load().manifest, self.original)
        self.runtime.inspect_recovery.side_effect = None
        self.assertEqual((await self.service.run(target=None, consent=CONSENT, recovery=True))['status'], 'unknown')
        self.runtime.restore.assert_awaited_once()

    async def test_marker_save_failure_prevents_effect(self):
        for stage, backup in (('admitted', False), ('upgrading', True)):
            with self.subTest(stage=stage):
                self.checkpoint(stage, backup=backup)
                with patch.object(self.journal, 'save', side_effect=OSError('failure')):
                    with self.assertRaises(LifecycleStateError):
                        await self.service.run(target=None, consent=CONSENT, recovery=True)
                self.runtime.cancel_backup.assert_not_called()
                self.runtime.restore.assert_not_called()
                self.assertEqual(self.journal.load().stage, stage)

    async def test_uncertain_pending_save_reopens_old_or_new_without_replay(self):
        for replace_visible in (False, True):
            with self.subTest(replace_visible=replace_visible):
                self.checkpoint('upgrading', backup=True)
                self.runtime.restore.reset_mock()
                save = self.journal.save
                def uncertain(checkpoint):
                    if checkpoint.stage == 'recovery_pending_proof':
                        if replace_visible:
                            save(checkpoint)
                        raise OSError('uncertain')
                    save(checkpoint)
                with patch.object(self.journal, 'save', side_effect=uncertain):
                    with self.assertRaises(LifecycleStateError):
                        await self.service.run(target=None, consent=CONSENT, recovery=True)
                stage = self.journal.load().stage
                self.assertEqual(stage, 'recovery_pending_proof' if replace_visible else 'recovering')
                result = await self.service.run(target=None, consent=CONSENT, recovery=True)
                self.assertEqual(result['status'], 'recovery_pending_proof' if replace_visible else 'unknown')
                self.runtime.restore.assert_awaited_once()
                self.assertEqual(self.manifests.load().manifest, self.original)

    async def test_atomic_pending_save_failure_before_replace_and_at_directory_fsync(self):
        for stage, backup in (('admitted', False), ('upgrading', True)):
            for mode in ('before_replace', 'directory_fsync'):
                with self.subTest(stage=stage, mode=mode):
                    self.checkpoint(stage, backup=backup)
                    self.runtime.restore.reset_mock()
                    self.runtime.cancel_backup.reset_mock()
                    original_save = self.journal.save
                    original_fsync = os.fsync
                    original_replace = os.replace
                    def interrupted(checkpoint):
                        if checkpoint.stage != 'recovery_pending_proof':
                            return original_save(checkpoint)
                        if mode == 'before_replace':
                            with patch('os.replace', side_effect=OSError('replace failed')):
                                return original_save(checkpoint)
                        def fsync(fd):
                            if os.path.isdir('/proc/self/fd/' + str(fd)):
                                raise OSError('directory sync failed')
                            original_fsync(fd)
                        with patch('os.fsync', side_effect=fsync), patch('os.replace', wraps=original_replace):
                            return original_save(checkpoint)
                    with patch.object(self.journal, 'save', side_effect=interrupted):
                        with self.assertRaises(LifecycleStateError):
                            await self.service.run(target=None, consent=CONSENT, recovery=True)
                    marker = 'recovering' if backup else 'cancel_in_progress'
                    self.assertEqual(self.journal.load().stage,
                                     marker if mode == 'before_replace' else 'recovery_pending_proof')
                    result = await self.service.run(target=None, consent=CONSENT, recovery=True)
                    self.assertEqual(result['status'], 'unknown' if mode == 'before_replace' else 'recovery_pending_proof')
                    (self.runtime.restore if backup else self.runtime.cancel_backup).assert_awaited_once()

    async def test_effect_exception_is_redacted_and_never_replayed(self):
        for stage, backup, effect, marker in (
            ('admitted', False, self.runtime.cancel_backup, 'cancel_in_progress'),
            ('upgrading', True, self.runtime.restore, 'recovering'),
        ):
            with self.subTest(stage=stage):
                self.checkpoint(stage, backup=backup)
                effect.reset_mock()
                effect.side_effect = RuntimeError('credential-secret')
                result = await self.service.run(target=None, consent=CONSENT, recovery=True)
                self.assertEqual(result['status'], 'unknown')
                self.assertNotIn('secret', str(result))
                self.assertEqual(self.journal.load().stage, marker)
                effect.side_effect = None
                await self.service.run(target=None, consent=CONSENT, recovery=True)
                effect.assert_awaited_once()

    async def test_cancel_pending_save_uncertainty_retains_old_or_new_without_replay(self):
        for replace_visible in (False, True):
            with self.subTest(replace_visible=replace_visible):
                self.checkpoint('admitted')
                self.runtime.cancel_backup.reset_mock()
                save = self.journal.save
                def interrupted(checkpoint):
                    if checkpoint.stage == 'recovery_pending_proof':
                        if replace_visible:
                            save(checkpoint)
                        raise OSError('secret')
                    save(checkpoint)
                with patch.object(self.journal, 'save', side_effect=interrupted):
                    with self.assertRaises(LifecycleStateError) as raised:
                        await self.service.run(target=None, consent=CONSENT, recovery=True)
                self.assertNotIn('secret', str(raised.exception))
                self.assertEqual(self.journal.load().stage,
                                 'recovery_pending_proof' if replace_visible else 'cancel_in_progress')
                result = await self.service.run(target=None, consent=CONSENT, recovery=True)
                self.assertEqual(result['status'], 'recovery_pending_proof' if replace_visible else 'unknown')
                self.runtime.cancel_backup.assert_awaited_once()

    async def test_process_crash_before_and_after_each_recovery_effect_never_replays(self):
        context = multiprocessing.get_context('fork')
        for stage, backup, marker in (
            ('admitted', False, 'cancel_in_progress'), ('upgrading', True, 'recovering'),
        ):
            for when in ('before', 'after'):
                with self.subTest(stage=stage, when=when):
                    self.checkpoint(stage, backup=backup)
                    self.runtime.cancel_backup.reset_mock()
                    self.runtime.restore.reset_mock()
                    effect_file = self.root / ('effect-' + stage + '-' + when)
                    def child():
                        if when == 'before':
                            save = self.journal.save
                            def save_then_crash(checkpoint):
                                save(checkpoint)
                                if checkpoint.stage == marker:
                                    os._exit(71)
                            self.journal.save = save_then_crash
                        else:
                            async def effect_then_crash(checkpoint):
                                with effect_file.open('a') as stream:
                                    stream.write('effect\n')
                                    stream.flush()
                                    os.fsync(stream.fileno())
                                os._exit(72)
                            if backup:
                                self.runtime.restore.side_effect = effect_then_crash
                            else:
                                self.runtime.cancel_backup.side_effect = effect_then_crash
                        getattr(asyncio.events, '_set_running_loop')(None)
                        asyncio.run(self.service.run(target=None, consent=CONSENT, recovery=True))
                    process = context.Process(target=child)
                    process.start()
                    process.join(10)
                    if process.is_alive():
                        process.terminate()
                        process.join()
                        self.fail('recovery subprocess did not exit')
                    self.assertEqual(process.exitcode, 71 if when == 'before' else 72)
                    self.assertEqual(effect_file.read_text() if effect_file.exists() else '', '' if when == 'before' else 'effect\n')
                    self.assertEqual(self.journal.load().stage, marker)
                    result = await self.service.run(target=None, consent=CONSENT, recovery=True)
                    self.assertEqual(result['status'], 'unknown')
                    self.runtime.cancel_backup.assert_not_called()
                    self.runtime.restore.assert_not_called()
                    self.assertEqual(effect_file.read_text() if effect_file.exists() else '', '' if when == 'before' else 'effect\n')

    async def test_missing_and_malformed_checkpoint_fail_closed_on_reopen(self):
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.journal.path.write_text('{"stage":"recovery_pending_proof"')
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.runtime.cancel_backup.assert_not_called()
        self.runtime.restore.assert_not_called()

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
        self.checkpoint('upgrading', backup=True)
        snapshot = self.manifests.load()
        changed = snapshot.manifest.model_copy(update={'installation_id': '12345678-1234-1234-1234-123456789012'})
        self.manifests.save(changed, expected_token=snapshot.token)
        with self.assertRaisesRegex(LifecycleStateError, 'another installation'):
            await self.service.run(target=None, consent=CONSENT, recovery=True)
        self.runtime.restore.assert_not_called()

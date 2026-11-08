"""Real private journals arbitrate Add with every existing installation writer."""
from pathlib import Path
import tempfile
import unittest

from tests.application.services.test_profile_change import fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileLifecycleCheckpoint, ProfileChangeCheckpoint
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import JsonProfileChangeJournal
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal


class ProfileChangeJournalTests(unittest.TestCase):
    def prepare(self, root, intent=None):
        if intent is None:
            intent, manifest = fixture()
        else:
            manifest = intent.before_manifest
        lock = JsonInstallationOperationLock(root)
        creation = JsonProfileLifecycleJournal(root)
        with lock.exclusive('profile-lifecycle') as lease:
            with creation.exclusive(lease):
                creation.save(ProfileLifecycleCheckpoint(intent=intent.before, stage='completed', previous_stage='completed',
                    installation_committed=True, observation_sha256='a' * 64, instance_uuid=intent.instance_uuid), expected=None, lease=lease)
            JsonManifestRepository(root / '.tiny-swarm-world/installation/manifest.json').save(manifest, expected_token=None)
        return intent, lock

    def test_pending_add_blocks_all_other_writers_and_full_cas_preserves_creation_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intent, lock = self.prepare(root)
            path = root / '.tiny-swarm-world/installation/profile-operation.json'
            original = path.read_bytes()
            journal = JsonProfileChangeJournal(root)
            checkpoint = ProfileChangeCheckpoint(intent=intent, stage='pending', observation_sha256='b' * 64)
            with lock.exclusive('profile-change') as lease, journal.exclusive(lease):
                journal.save(checkpoint, expected=None, lease=lease)
                with self.assertRaises(LifecycleStateError):
                    journal.save(checkpoint.model_copy(update={'generation': 1}), expected=None, lease=lease)
            for operation in ('setup', 'add', 'selection', 'component-update', 'product-upgrade', 'portainer-upgrade', 'platform', 'deployment'):
                with self.subTest(operation=operation), self.assertRaises(LifecycleStateError):
                    with lock.exclusive(operation):
                        self.fail('Pending profile change admitted an independent writer')
            with lock.exclusive('profile-recovery') as lease, journal.exclusive(lease):
                self.assertEqual(journal.load(), checkpoint)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(journal.path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(LifecycleStateError):
                journal.save(checkpoint, expected=checkpoint, lease=lease)

    def test_unsafe_change_file_and_replaced_parent_refuse_without_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intent, lock = self.prepare(root)
            journal = JsonProfileChangeJournal(root)
            with lock.exclusive('profile-change') as lease, journal.exclusive(lease):
                journal.save(ProfileChangeCheckpoint(intent=intent, observation_sha256='b' * 64), expected=None, lease=lease)
            journal.path.chmod(0o644)
            with self.assertRaises(LifecycleStateError):
                journal.load()
            self.assertEqual(journal.path.stat().st_mode & 0o777, 0o644)
            journal.path.chmod(0o600)
            parent = journal.path.parent
            retained = parent.with_name('installation-retained')
            parent.rename(retained)
            parent.symlink_to(retained, target_is_directory=True)
            with self.assertRaises(LifecycleStateError):
                journal.load()
            self.assertTrue(parent.is_symlink())


    def test_new_stack_first_durable_identity_cannot_be_replaced_by_direct_journal_cas(self):
        from tests.application.services.test_profile_change import owned_change_fixture, ownership_fixture
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intent, lock = self.prepare(root, owned_change_fixture(existing=False))
            journal = JsonProfileChangeJournal(root)
            owner = ownership_fixture()
            checkpoint = ProfileChangeCheckpoint(intent=intent, stage='verified', observation_sha256='b' * 64,
                verified_stack_ownership={'swagger': owner})
            with lock.exclusive('profile-change') as lease, journal.exclusive(lease):
                journal.save(checkpoint, expected=None, lease=lease)
                original = journal.path.read_bytes()
                for changes in ({'endpoint_id': 4}, {'stack_id': 5}, {'resource_control_id': 6},
                                {'ownership_fingerprint': 'sha256:' + 'e' * 64}):
                    with self.subTest(changes=changes), self.assertRaises(LifecycleStateError):
                        journal.save(checkpoint.model_copy(update={'generation': 1,
                            'verified_stack_ownership': {'swagger': owner.model_copy(update=changes)}}), expected=checkpoint, lease=lease)
                    self.assertEqual(journal.path.read_bytes(), original)
                with self.assertRaises(LifecycleStateError):
                    journal.save(checkpoint.model_copy(update={'generation': 1, 'verified_stack_ownership': {}}),
                                 expected=checkpoint, lease=lease)
                changed = checkpoint.model_copy(update={'generation': 1, 'verified_stack_ownership': {
                    'swagger': owner.model_copy(update={'definition_fingerprint': 'sha256:' + 'f' * 64})}})
                journal.save(changed, expected=checkpoint, lease=lease)
                self.assertEqual(journal.load(), changed)

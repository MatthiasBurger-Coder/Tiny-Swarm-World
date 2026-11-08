"""Real private checkpoint persistence, complete CAS and central writer exclusion."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import intent_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileLifecycleCheckpoint
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal


class ProfileJournalTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.lock = JsonInstallationOperationLock(self.root)
        self.journal = JsonProfileLifecycleJournal(self.root)
        self.checkpoint = ProfileLifecycleCheckpoint(intent=intent_fixture(), observation_sha256='1' * 64)

    def test_read_creates_nothing_and_save_requires_explicit_same_anchor_lease(self):
        self.assertIsNone(self.journal.load())
        self.assertFalse(self.journal.path.parent.exists())
        with self.assertRaises(LifecycleStateError):
            self.journal.save(self.checkpoint, expected=None, lease=None)
        with self.lock.exclusive('profile-lifecycle') as lease, self.journal.exclusive(lease):
            self.journal.save(self.checkpoint, expected=None, lease=lease)
            self.assertEqual(self.journal.load(), self.checkpoint)
            self.assertEqual(self.journal.path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(self.journal.path.parent.stat().st_mode & 0o777, 0o700)
        with self.assertRaises(LifecycleStateError):
            self.journal.save(self.checkpoint, expected=self.checkpoint, lease=lease)

    def test_pending_profile_blocks_all_ordinary_writers_until_explicit_recovery(self):
        with self.lock.exclusive('profile-lifecycle') as lease, self.journal.exclusive(lease):
            self.journal.save(self.checkpoint, expected=None, lease=lease)
        for operation in ('adoption', 'selection', 'setup', 'component-update', 'portainer-upgrade',
                          'product-upgrade', 'recovery', 'cleanup', 'platform', 'deployment', 'classic-update'):
            with self.subTest(operation=operation), self.assertRaises(LifecycleStateError):
                with self.lock.exclusive(operation):
                    self.fail('ordinary writer admitted pending profile state')
        with self.lock.exclusive('profile-recovery') as lease, self.journal.exclusive(lease):
            self.assertEqual(self.journal.load(), self.checkpoint)
        self.assertEqual(self.journal.path.read_bytes(), self.checkpoint.model_dump_json(indent=2).encode() + b'\n')

    def test_complete_state_cas_rejects_same_generation_tamper_before_overwrite(self):
        with self.lock.exclusive('profile-lifecycle') as lease, self.journal.exclusive(lease):
            self.journal.save(self.checkpoint, expected=None, lease=lease)
            changed = self.checkpoint.model_copy(update={'observation_sha256': '2' * 64})
            self.journal.path.write_text(changed.model_dump_json())
            content = self.journal.path.read_bytes()
            proposed = self.checkpoint.model_copy(update={'generation': 1})
            with self.assertRaises(LifecycleStateError):
                self.journal.save(proposed, expected=self.checkpoint, lease=lease)
            self.assertEqual(self.journal.path.read_bytes(), content)

    def test_foreign_anchor_lease_and_unsafe_files_refuse_without_repair(self):
        with TemporaryDirectory() as other:
            with JsonInstallationOperationLock(Path(other)).exclusive('profile-lifecycle') as lease:
                with self.assertRaises(LifecycleStateError):
                    with self.journal.exclusive(lease):
                        self.fail('foreign lease acquired journal')
        with self.lock.exclusive('profile-lifecycle') as lease, self.journal.exclusive(lease):
            self.journal.save(self.checkpoint, expected=None, lease=lease)
        self.journal.path.chmod(0o644)
        with self.assertRaises(LifecycleStateError):
            self.journal.load()
        self.assertEqual(self.journal.path.stat().st_mode & 0o777, 0o644)

    def test_profile_completed_does_not_authorize_uncommitted_installation_or_forged_commit(self):
        done = self.checkpoint.model_copy(update={'stage': 'completed', 'previous_stage': 'completed',
            'instance_uuid': '11111111-1111-1111-1111-111111111111'})
        with self.lock.exclusive('profile-lifecycle') as lease, self.journal.exclusive(lease):
            self.journal.save(done, expected=None, lease=lease)
        with self.assertRaises(LifecycleStateError):
            with self.lock.exclusive('platform'):
                self.fail('uncommitted installation admitted')
        forged = done.model_copy(update={'installation_committed': True})
        self.journal.path.write_text(forged.model_dump_json())
        with self.assertRaises(LifecycleStateError):
            with self.lock.exclusive('platform'):
                self.fail('forged completed installation admitted')

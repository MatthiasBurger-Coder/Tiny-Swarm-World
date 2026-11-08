"""Private checkpoint durability and immutable unsettled intent contracts."""
import os
from pathlib import Path
import tempfile
import unittest

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.managed_stack import ManagedStackIntent
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_journal import JsonManagedStackJournal


class Lease:
    operation_id = 'd' * 32
    def require_active(self):
        pass


class ManagedJournalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.path = root / 'private' / 'managed-stack-swagger.json'
        self.journal = JsonManagedStackJournal(self.path, Lease())
        self.intent = ManagedStackIntent(installation_id='11111111-1111-1111-1111-111111111111',
            operation_id='a' * 32, stack_name='swagger', endpoint_id=1, target_fingerprint='sha256:' + 'b' * 64)
    def test_atomic_roundtrip_is_private(self):
        self.journal.save(self.intent)
        self.assertEqual(self.journal.load(), self.intent)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(list(self.path.parent.glob('.managed-stack-*')), [])
    def test_unsettled_intent_cannot_change_operation_or_target(self):
        self.journal.save(self.intent)
        before = self.path.read_bytes()
        for changes in ({'operation_id': 'c' * 32}, {'target_fingerprint': 'sha256:' + 'e' * 64}):
            with self.subTest(changes=changes), self.assertRaises(LifecycleStateError):
                self.journal.save(self.intent.model_copy(update=changes))
        self.assertEqual(self.path.read_bytes(), before)
    def test_symlink_file_is_not_followed(self):
        self.path.parent.mkdir(mode=0o700)
        target = self.path.parent / 'outside'
        target.write_text('preserve')
        self.path.symlink_to(target)
        with self.assertRaises(LifecycleStateError):
            self.journal.load()
        self.assertEqual(target.read_text(), 'preserve')
    def test_broad_permissions_and_oversized_record_block(self):
        self.journal.save(self.intent)
        os.chmod(self.path, 0o644)
        with self.assertRaises(LifecycleStateError):
            self.journal.load()
        os.chmod(self.path, 0o600)
        self.path.write_bytes(b'x' * 65537)
        with self.assertRaises(LifecycleStateError):
            self.journal.load()
    def test_parent_alias_and_public_directory_block(self):
        self.path.parent.mkdir(mode=0o755)
        with self.assertRaises(LifecycleStateError):
            self.journal.save(self.intent)
        self.path.parent.rmdir()
        self.path.parent.symlink_to(self.path.parent.parent, target_is_directory=True)
        with self.assertRaises(LifecycleStateError):
            self.journal.save(self.intent)

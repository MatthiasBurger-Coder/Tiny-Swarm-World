"""Exercise the original-window production adapter without a host driver."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Any, Callable
import unittest
from unittest.mock import patch

from modules.tsw_core.tools.linux.qualification import wsl_original_runtime_window as window


class MemoryJournal:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(exist_ok=True)

    def exists(self, name: str) -> bool:
        return (self.directory / name).exists()

    def names(self) -> list[str]:
        return sorted(item.name for item in self.directory.iterdir())

    def save(self, name: str, value: Any) -> None:
        (self.directory / name).write_bytes(window.canonical(value))

    def read(self, name: str) -> Any:
        return json.loads((self.directory / name).read_bytes())


class DriverFixture(ModuleType):
    """Explicit callable surface of the injected immutable-driver module."""

    Journal: type[MemoryJournal]
    canonical: Callable[[Any], bytes]
    strict: Callable[[bytes], Any]
    validate_baseline: Callable[[Any], None]
    initial_statuses: Callable[[Any], dict[str, str]]
    compare: Callable[..., None]
    read_proposal: Callable[[Any], bytes]
    prepare: Callable[[Any, Any], None]
    quiesce: Callable[[Any, Any, Any], dict[str, Any]]
    restore: Callable[[Any, Any], dict[str, Any]]
    validate_go: Callable[..., None]
    verify_observation: Callable[..., None]
    PRIVATE: Path


class RuntimeWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name) / 'fixture'
        self.home.mkdir()
        self.baseline = {'runtime': 'original', 'label': 'grüße'}
        self.port = SimpleNamespace(settle=lambda: None, snapshot=lambda: self.baseline)
        self.effects: list[str] = []
        self.legacy = DriverFixture('fake_fixed_driver')
        self.legacy.Journal = MemoryJournal
        self.legacy.canonical = window.canonical
        self.legacy.strict = json.loads
        self.legacy.validate_baseline = lambda value: None
        self.legacy.initial_statuses = lambda value: {'original': 'Running'}
        self.legacy.compare = lambda *args: None
        self.legacy.read_proposal = lambda journal: window.canonical(journal.read('proposal.json'))
        self.legacy.prepare = self.prepare
        self.legacy.quiesce = self.quiesce
        self.legacy.restore = self.restore
        self.legacy.validate_go = self.validate_inner
        self.legacy.verify_observation = self.verify
        self.value: dict[str, Any] = {
            'schema_version': 1, 'run_id': 'a' * 32, 'window': 'fixture', 'source_commit': 'b' * 40,
            'scenario_sha256': 'c' * 64, 'adapter_sha256': 'd' * 64, 'machine_sha256': 'e' * 64,
            'proposal_sha256': window.sha(window.canonical(self.baseline)), 'backup_sha256': 'f' * 64,
            'registration_sha256': '1' * 64, 'legacy_lock_inode': 42,
            'parent_switch_sha256': window.ZERO, 'parent_bridge_sha256': window.ZERO,
            'parent_switch': None, 'parent_bridge': None,
        }
        self.witness = {'device': 4, 'inode': 42, 'machine_sha256': 'e' * 64, 'boot_sha256': '2' * 64}
        self.addCleanup(patch.stopall)
        patch.object(window, 'private_read', lambda path: path.read_bytes()).start()
        patch.object(window, 'create_private', self.publish).start()

    @staticmethod
    def publish(path: Path, raw: bytes) -> None:
        with path.open('xb') as stream:
            stream.write(raw)

    def prepare(self, port: Any, journal: Any) -> None:
        journal.save('proposal.json', port.snapshot())

    def validate_inner(self, go: Any, *_args: Any) -> None:
        if go != {'fresh': True}:
            raise ValueError('expired inner approval')

    def quiesce(self, _port: Any, journal: Any, _go: Any) -> dict[str, Any]:
        self.effects.append('quiesce')
        journal.save('quiesce-started.json', {})
        return {'decision': 'QUIESCED', 'proposal_sha256': self.value['proposal_sha256']}

    def restore(self, _port: Any, journal: Any) -> dict[str, Any]:
        self.effects.append('restore')
        result = {'decision': 'RESTORED', 'proposal_sha256': self.value['proposal_sha256']}
        journal.save('restored.json', result)
        return result

    def verify(self, _baseline: Any, _current: Any, journal: Any, *, restored: bool) -> None:
        if restored and not journal.exists('restored.json'):
            raise ValueError('restore not proved')

    def go(self, phase: str, *, inner: Any = None) -> dict[str, Any]:
        return {'schema_version': 1, 'decision': 'GO', 'phase': phase,
                'scenario_sha256': self.value['scenario_sha256'], 'source_commit': self.value['source_commit'],
                'proposal_sha256': '3' * 64, 'evidence_sha256': '',
                'expires_at_utc': (datetime.now(timezone.utc) + timedelta(seconds=2500)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'original_context_sha256': window.sha(window.canonical(self.value)),
                'original_proposal_sha256': self.value['proposal_sha256'],
                'original_lock_witness': dict(self.witness), 'legacy_go': inner,
                'legacy_go_sha256': window.sha(window.canonical(inner)) if inner is not None else window.ZERO}

    def execute(self, mode: str, go: Any = None) -> dict[str, Any]:
        return window.execute(mode, self.value, go, self.legacy, self.port, self.home, witness=self.witness)

    def prepared(self) -> None:
        self.execute('prepare', self.go('PrepareOriginal'))

    def bytes(self) -> dict[str, bytes]:
        return {str(item.relative_to(self.home)): item.read_bytes() for item in self.home.rglob('*') if item.is_file()}

    def test_inspect_and_invalid_approval_create_nothing(self) -> None:
        self.assertEqual(self.execute('inspect')['proposal_sha256'], self.value['proposal_sha256'])
        self.assertEqual(self.bytes(), {})
        approval = self.go('PrepareOriginal')
        approval['original_context_sha256'] = '0' * 64
        with self.assertRaises(window.WindowError):
            self.execute('prepare', approval)
        self.assertEqual(self.bytes(), {})
        self.assertEqual(self.effects, [])

    def test_complete_window_preserves_context_and_never_changes_legacy_globals(self) -> None:
        self.legacy.PRIVATE = Path('/never-retarget')
        self.prepared()
        original = self.bytes()
        self.assertEqual(self.execute('prepared')['status'], 'ORIGINAL_PREPARED')
        self.execute('quiesce', self.go('QuiesceOriginal', inner={'fresh': True}))
        self.execute('restore', self.go('RestoreOriginal'))
        self.assertEqual(self.execute('restored')['status'], 'ORIGINAL_RESTORED')
        for name, raw in original.items():
            self.assertEqual(self.bytes()[name], raw)
        self.assertEqual(self.effects, ['quiesce', 'restore'])
        self.assertEqual(self.legacy.PRIVATE, Path('/never-retarget'))

    def test_stale_inner_approval_has_no_effect_and_fresh_renewal_reuses_same_context(self) -> None:
        self.prepared()
        original = self.bytes()
        with self.assertRaises(ValueError):
            self.execute('quiesce', self.go('QuiesceOriginal', inner={'fresh': False}))
        self.assertEqual(self.bytes(), original)
        self.assertEqual(self.effects, [])
        self.execute('quiesce', self.go('QuiesceOriginal', inner={'fresh': True}))
        self.assertEqual(self.bytes()['context.json'], original['context.json'])

    def test_restore_approval_independent_of_expired_quiesce_and_remount_device(self) -> None:
        self.prepared()
        immutable = self.bytes()['context.json']
        self.execute('quiesce', self.go('QuiesceOriginal', inner={'fresh': True}))
        old = self.go('RestoreOriginal')
        self.witness['device'] = 900
        with self.assertRaises(window.WindowError):
            self.execute('restore', old)
        self.execute('restore', self.go('RestoreOriginal'))
        self.assertEqual(self.bytes()['context.json'], immutable)
        self.assertNotIn('legacy_go', json.loads(immutable))

    def test_expired_outer_approval_retains_exact_files(self) -> None:
        self.prepared()
        before = self.bytes()
        approval = self.go('RestoreOriginal')
        approval['expires_at_utc'] = '2000-01-01T00:00:00Z'
        with self.assertRaises(window.WindowError):
            self.execute('restore', approval)
        self.assertEqual(self.bytes(), before)
        self.assertEqual(self.effects, [])

    def test_partial_prepare_is_not_recreated_or_credited_as_prepared(self) -> None:
        self.legacy.prepare = lambda *_: (_ for _ in ()).throw(ValueError('snapshot CAS'))
        with self.assertRaises(ValueError):
            self.prepared()
        before = self.bytes()
        self.assertIn('context.json', before)
        with self.assertRaises(window.WindowError):
            self.prepared()
        with self.assertRaises(FileNotFoundError):
            self.execute('prepared')
        self.assertEqual(self.bytes(), before)
        self.assertEqual(self.effects, [])

    def test_missing_outer_restore_receipt_requires_own_go_and_no_effect_replay(self) -> None:
        self.prepared()
        MemoryJournal(self.home / 'legacy-journal').save('restored.json', {'decision': 'RESTORED'})
        with self.assertRaises(FileNotFoundError):
            self.execute('restored')
        self.execute('restore', self.go('ReconcileEffects'))
        self.assertEqual(self.effects, [])
        self.assertEqual(self.execute('restored')['status'], 'ORIGINAL_RESTORED')
        (self.home / 'final.json').write_bytes(b'{')
        before = self.bytes()
        for mode in ('restored', 'restore'):
            with self.assertRaises(ValueError):
                self.execute(mode, self.go('RestoreOriginal') if mode == 'restore' else None)
        self.assertEqual(self.bytes(), before)

    def test_readonly_legacy_journal_refuses_hidden_verification_write(self) -> None:
        self.prepared()
        before = self.bytes()
        def bad_verify(_baseline: Any, _current: Any, journal: Any, **_kwargs: Any) -> None:
            journal.save('unexpected.json', {})
        self.legacy.verify_observation = bad_verify
        with self.assertRaises(window.WindowError):
            self.execute('quiescent')
        self.assertEqual(self.bytes(), before)

    def test_product_cannot_prepare_without_actual_immutable_fixture_final(self) -> None:
        self.value.update(window='product', parent_switch_sha256='5' * 64, parent_bridge_sha256='6' * 64)
        with patch.object(window, 'BASE', Path(self.temporary.name)):
            with self.assertRaises(FileNotFoundError):
                self.prepared()
        self.assertEqual(self.bytes(), {})
        self.assertEqual(self.effects, [])

    def test_managed_readonly_lock_never_creates_and_excludes_competing_owner(self) -> None:
        missing = self.home / 'window.lock'
        with patch.object(window, 'trusted', lambda path, **kwargs: path.lstat()):
            with self.assertRaises(FileNotFoundError):
                with window.managed_lock(missing):
                    self.fail('missing lock was admitted')
            self.assertFalse(missing.exists())
            missing.touch(mode=0o600)
            with patch.object(window.os, 'fstat', side_effect=lambda fd: SimpleNamespace(
                    st_mode=0o100600, st_uid=0, st_nlink=1)):
                with patch.object(window.fcntl, 'flock', side_effect=BlockingIOError):
                    with self.assertRaises(BlockingIOError):
                        with window.managed_lock(missing):
                            self.fail('contended lock was admitted')
        self.assertEqual(missing.read_bytes(), b'')

    def test_exact_pinned_main_signal_dispatch_is_reused(self) -> None:
        native = ModuleType('synthetic_native')
        class InventoryError(Exception):
            pass
        native.InventoryError = InventoryError  # type: ignore[attr-defined]
        module = ModuleType('pinned_main_fixture')
        module.native = native  # type: ignore[attr-defined]
        exec('def main():\n def interrupted(signum, frame):\n  raise native.InventoryError("interrupted")\n', module.__dict__)
        handlers: dict[int, Any] = {}
        with patch.object(window.signal, 'signal', side_effect=lambda number, handler: handlers.update({number: handler})):
            window.install_legacy_signal_handler(module)
        for number in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM):
            with self.assertRaises(InventoryError):
                handlers[number](number, None)

    def test_context_rejects_mutable_authority_and_noninteger_lock(self) -> None:
        self.assertEqual(window.context(self.value), self.value)
        for changed in (self.value | {'legacy_go': {}}, self.value | {'legacy_lock_inode': 42.0}):
            with self.assertRaises(window.WindowError):
                window.context(changed)

    def test_real_existing_legacy_lock_excludes_contender_without_create(self) -> None:
        lock = self.home / 'lock'
        lock.touch(mode=0o600)
        private = self.home
        value = self.value | {'legacy_lock_inode': lock.stat().st_ino}
        before = lock.stat()
        with (patch.object(window, 'LEGACY_PRIVATE', private),
              patch.object(window, 'trusted', lambda path, **kwargs: path.lstat())):
            owner = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    with window.lock_existing(value):
                        self.fail('competing legacy owner admitted')
            finally:
                os.close(owner)
            with window.lock_existing(value):
                self.assertEqual(lock.read_bytes(), b'')
        self.assertEqual((lock.stat().st_dev, lock.stat().st_ino), (before.st_dev, before.st_ino))

    def test_partial_prepare_has_append_only_metadata_recovery_under_fresh_go(self) -> None:
        original_prepare = self.legacy.prepare
        self.legacy.prepare = lambda *_: (_ for _ in ()).throw(ValueError('snapshot lost'))
        with self.assertRaises(ValueError):
            self.prepared()
        old = self.bytes()
        self.legacy.prepare = original_prepare
        self.execute('recover-prepare', self.go('ReconcileEffects'))
        self.assertEqual(self.execute('prepared')['status'], 'ORIGINAL_PREPARED')
        for name, raw in old.items():
            self.assertEqual(self.bytes()[name], raw)
        self.assertEqual(self.effects, [])
        MemoryJournal(self.home / 'legacy-journal').save('quiesce-started.json', {})
        before = self.bytes()
        with self.assertRaises(window.WindowError):
            self.execute('recover-prepare', self.go('ReconcileEffects'))
        self.assertEqual(self.bytes(), before)

    def test_actual_staging_projection_refuses_replayed_go_with_altered_target(self) -> None:
        import re
        import time
        source = (Path(__file__).resolve().parents[2] / 'tools/qualification/wsl_acceptance_guest_switch.ps1').read_text()
        body = re.search(r'def validate_staging\(.*?(?=\ndef trusted\()', source, re.S)
        self.assertIsNotNone(body)
        assert body is not None
        def need(value: Any) -> None:
            if not value:
                raise ValueError('staging refused')
        namespace: dict[str, Any] = {'json': json, 'time': time, 'need': need,
                                    'canon': window.canonical, 'sha': window.sha}
        exec(compile(body.group(), '<actual-fixed-stage-projection>', 'exec'), namespace)
        approval = self.go('StageOriginal')
        approval['expires_at_utc'] = (datetime.now(timezone.utc) + timedelta(seconds=1000)).strftime('%Y-%m-%dT%H:%M:%SZ')
        args = [window.canonical(self.value), window.canonical(approval), self.value['run_id'], 'fixture',
                self.value['source_commit'], self.value['adapter_sha256'], self.value['scenario_sha256'],
                window.sha(window.canonical(self.value)), self.value['proposal_sha256'], self.value['machine_sha256']]
        self.assertEqual(namespace['validate_staging'](*args)[0], self.value)
        for index in range(2, 10):
            altered = list(args)
            altered[index] = 'foreign'
            with self.subTest(index=index), self.assertRaises(ValueError):
                namespace['validate_staging'](*altered)
        altered_context = self.value | {'window': 'product'}
        altered = list(args)
        altered[0] = window.canonical(altered_context)
        with self.assertRaises(ValueError):
            namespace['validate_staging'](*altered)
        self.assertEqual(self.bytes(), {})

    def test_fixture_to_product_parent_chain_preserves_exact_predecessor(self) -> None:
        root = Path(self.temporary.name)
        self.home = root / self.value['run_id'] / 'original-windows/fixture'
        self.home.mkdir(parents=True)
        self.prepared()
        self.execute('restore', self.go('RestoreOriginal'))
        fixture_home = self.home
        predecessor = self.bytes()
        switch = {'schema_version': 3, 'window': 'fixture', 'stage': 'restored', 'pending': '',
                  'run_id': self.value['run_id'], 'source_commit': self.value['source_commit'],
                  'scenario_sha256': self.value['scenario_sha256'],
                  'original_context_sha256': window.sha(window.canonical(self.value)),
                  'bridge_scenario_sha256': '7' * 64}
        bridge = {'schema_version': 1, 'window': 'fixture', 'run_id': self.value['run_id'],
                  'source_commit': self.value['source_commit'], 'descriptor_sha256': '8' * 64,
                  'archive_sha256': '9' * 64, 'registration_sha256': 'a' * 64,
                  'registration_state_sha256': self.value['registration_sha256'],
                  'scenario_sha256': switch['bridge_scenario_sha256'], 'phase': 'restored',
                  'phase_intent': '', 'transaction_id': ''}
        self.value = self.value | {'window': 'product', 'scenario_sha256': 'a' * 64,
                                   'parent_switch': switch, 'parent_bridge': bridge,
                                   'parent_switch_sha256': window.sha(window.canonical(switch)),
                                   'parent_bridge_sha256': window.sha(window.canonical(bridge))}
        self.home = fixture_home.parent / 'product'
        self.home.mkdir()
        with patch.object(window, 'BASE', root):
            self.prepared()
        product_context = (self.home / 'context.json').read_bytes()
        self.assertEqual(json.loads(product_context)['window'], 'product')
        for name, raw in predecessor.items():
            self.assertEqual((fixture_home / name).read_bytes(), raw)
        self.assertEqual(self.effects, ['restore'])
        # A matching digest does not make an unrestored parent authoritative.
        bridge['phase_intent'] = 'ResumeOriginal'
        self.value['parent_bridge_sha256'] = window.sha(window.canonical(bridge))
        self.home = fixture_home.parent / 'rejected-product'
        self.home.mkdir()
        with patch.object(window, 'BASE', root), self.assertRaises(window.WindowError):
            self.prepared()
        self.assertEqual(self.bytes(), {})

    def test_verified_source_loader_rejects_bytes_and_api_before_effects(self) -> None:
        import sys
        driver = self.home / 'fixed-driver.py'
        private = self.home / 'original-private'
        source = ('from pathlib import Path\nPRIVATE=Path(' + repr(str(private)) + ')\n'
                  'effects=[]\nclass RealPort:\n def __init__(self, machine): pass\n'
                  'class Journal:\n def __init__(self, directory): pass\n'
                  'def prepare(port, journal): effects.append("prepare")\n'
                  'def quiesce(port, journal, go): effects.append("quiesce")\n'
                  'def restore(port, journal): effects.append("restore")\n'
                  'def verify_observation(baseline, current, journal, *, restored): pass\n'
                  'def validate_go(go, baseline, proposal, now): pass\n'
                  'def validate_baseline(value): pass\n'
                  'def read_proposal(journal): pass\n'
                  'def strict(raw): pass\n').encode()
        driver.write_bytes(source)
        driver.chmod(0o600)
        with (patch.object(window, 'LEGACY', driver), patch.object(window, 'LEGACY_PRIVATE', private),
              patch.object(window, 'trusted', lambda path, **kwargs: path.lstat()), patch.dict(sys.modules)):
            with patch.object(window, 'LEGACY_SHA', window.sha(source)):
                loaded = window.load_legacy()
                self.assertEqual(loaded.PRIVATE, private)
                self.assertEqual(loaded.effects, [])
                driver.write_bytes(source + b'raise RuntimeError("must not execute")\n')
                with self.assertRaises(window.WindowError):
                    window.load_legacy()
            broken = source.replace(b'def restore(port, journal)', b'def restore(wrong, journal)')
            driver.write_bytes(broken)
            with patch.object(window, 'LEGACY_SHA', window.sha(broken)), self.assertRaises(window.WindowError):
                window.load_legacy()
            self.assertNotIn('tsw_original_immutable_window', sys.modules)
        self.assertFalse((self.home / '__pycache__').exists())

    def test_existing_legacy_lock_replacement_is_detected_and_foreign_bytes_retained(self) -> None:
        lock = self.home / 'lock'
        lock.touch(mode=0o600)
        value = self.value | {'legacy_lock_inode': lock.stat().st_ino}
        with (patch.object(window, 'LEGACY_PRIVATE', self.home),
              patch.object(window, 'trusted', lambda path, **kwargs: path.lstat())):
            with self.assertRaises(window.WindowError):
                with window.lock_existing(value):
                    # Simulate a foreign owner replacing the path while our fd
                    # still holds the original inode. Cleanup must not unlink it.
                    lock.rename(self.home / 'preserved-original-lock')
                    lock.write_bytes(b'foreign replacement')
            self.assertEqual(lock.read_bytes(), b'foreign replacement')
            self.assertEqual((self.home / 'preserved-original-lock').read_bytes(), b'')

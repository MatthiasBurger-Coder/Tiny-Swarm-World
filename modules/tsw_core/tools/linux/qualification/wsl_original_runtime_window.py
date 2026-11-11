"""Closed fixture/product windows over the immutable original-runtime driver.

This qualification adapter never changes legacy globals or selects executable
paths from input. The old CLI and every new window share the existing lock.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
from types import CodeType, FunctionType, ModuleType
from uuid import UUID, uuid4
from typing import Any, Iterator

LEGACY = Path('/root/tsw440-wsl-r7-20261108/epic440-wsl-runtime-window.py')
LEGACY_PRIVATE = LEGACY.parent / 'runtime-window'
LEGACY_SHA = 'fcf16059dced9a3ed07ea54e1d346e7b67726cfe873de2849b58a202519962bd'
BASE = Path('/root/tsw440-acceptance')
WINDOWS = ('fixture', 'product')
HEX = re.compile(r'[0-9a-f]{64}\Z')
RUN = re.compile(r'[0-9a-f]{32}\Z')
REVISION = re.compile(r'[0-9a-f]{40}\Z')
ZERO = '0' * 64
LIMIT = 131072
BUDGETS = {'recover-prepare': 300, 'prepared': 300, 'inspect': 180, 'prepare': 300, 'quiesce': 1200, 'restore': 1200, 'quiescent': 300, 'restored': 300}
CONTEXT_KEYS = {'schema_version', 'run_id', 'window', 'source_commit', 'scenario_sha256', 'adapter_sha256',
                'machine_sha256', 'proposal_sha256', 'backup_sha256', 'parent_switch_sha256',
                'parent_bridge_sha256', 'registration_sha256', 'legacy_lock_inode', 'parent_switch', 'parent_bridge'}


class WindowError(Exception):
    """Redacted fail-closed error."""


def require(value: Any, code: str = 'WINDOW_UNPROVEN') -> None:
    if not value:
        raise WindowError(code)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def strict(raw: bytes) -> Any:
    require(len(raw) <= LIMIT, 'WINDOW_INPUT_BOUND')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'WINDOW_DUPLICATE_KEY')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: require(False, 'WINDOW_JSON'))


def trusted(path: Path, *, directory: bool = False) -> os.stat_result:
    for item in (path, *path.parents):
        info = item.lstat()
        require(info.st_uid == 0 and not stat.S_ISLNK(info.st_mode) and not info.st_mode & 0o022, 'WINDOW_PATH_UNTRUSTED')
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'WINDOW_PATH_TYPE')
    if not directory:
        require(info.st_nlink == 1, 'WINDOW_FILE_LINKS')
    return info


def file_identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_uid, info.st_gid, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def private_read(path: Path) -> bytes:
    info = trusted(path)
    require(stat.S_IMODE(info.st_mode) == 0o600 and info.st_size <= LIMIT, 'WINDOW_PRIVATE_FILE')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        current = os.fstat(fd)
        require(file_identity(current) == file_identity(info), 'WINDOW_FILE_CAS')
        raw = os.read(fd, LIMIT + 1)
        require(len(raw) == current.st_size and len(raw) <= LIMIT and file_identity(os.fstat(fd)) == file_identity(current) and file_identity(path.lstat()) == file_identity(current), 'WINDOW_FILE_CAS')
        return raw
    finally:
        os.close(fd)


def create_private(path: Path, raw: bytes) -> None:
    require(len(raw) <= LIMIT, 'WINDOW_INPUT_BOUND')
    trusted(path.parent, directory=True)
    temporary = path.parent / ('.write-' + uuid4().hex)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    identity = os.fstat(fd)
    try:
        require(identity.st_nlink == 1, 'WINDOW_FILE_LINKS')
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(fd)
        os.link(temporary, path, follow_symlinks=False)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.close(fd)
        current = temporary.lstat()
        require((current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino), 'WINDOW_TEMP_CAS')
        temporary.unlink()


def context(value: Any) -> dict[str, Any]:
    require(type(value) is dict and set(value) == CONTEXT_KEYS, 'WINDOW_CONTEXT_FIELDS')
    require(type(value['schema_version']) is int and value['schema_version'] == 1, 'WINDOW_CONTEXT_SCHEMA')
    require(type(value['run_id']) is str and RUN.fullmatch(value['run_id']) and value['window'] in WINDOWS, 'WINDOW_IDENTITY')
    require(type(value['source_commit']) is str and REVISION.fullmatch(value['source_commit']), 'WINDOW_SOURCE')
    for key in CONTEXT_KEYS - {'schema_version', 'run_id', 'window', 'source_commit', 'legacy_lock_inode', 'parent_switch', 'parent_bridge'}:
        require(type(value[key]) is str and HEX.fullmatch(value[key]), 'WINDOW_CONTEXT_DIGEST')
    require(value['backup_sha256'] != ZERO and value['adapter_sha256'] != ZERO, 'WINDOW_REQUIRED_PROOF')
    if value['window'] == 'fixture':
        require(value['parent_switch_sha256'] == value['parent_bridge_sha256'] == ZERO and value['parent_switch'] is None and value['parent_bridge'] is None, 'WINDOW_FIXTURE_PARENT')
    else:
        require(value['parent_switch_sha256'] != ZERO and value['parent_bridge_sha256'] != ZERO and type(value['parent_switch']) is dict and type(value['parent_bridge']) is dict and sha(canonical(value['parent_switch'])) == value['parent_switch_sha256'] and sha(canonical(value['parent_bridge'])) == value['parent_bridge_sha256'], 'WINDOW_PRODUCT_PARENT')
    require(type(value['legacy_lock_inode']) is int and value['legacy_lock_inode'] > 0, 'WINDOW_LEGACY_LOCK')
    return value


def paths(value: dict[str, Any]) -> tuple[Path, Path, Path]:
    home = BASE / value['run_id'] / 'original-windows' / value['window']
    return home, home / 'legacy-journal', home / 'adapter.py'


def verify_api(legacy: ModuleType) -> None:
    import inspect
    for name in ('RealPort', 'Journal'):
        require(callable(getattr(legacy, name, None)), 'WINDOW_LEGACY_API')
        inspect.signature(getattr(legacy, name)).bind(object())
    required = {'prepare': ('port', 'journal'), 'quiesce': ('port', 'journal', 'go'),
                'restore': ('port', 'journal'), 'verify_observation': ('baseline', 'current', 'journal'),
                'validate_go': ('go', 'baseline', 'proposal', 'now'), 'validate_baseline': ('value',),
                'read_proposal': ('journal',), 'strict': ('raw',)}
    for name, names in required.items():
        function = getattr(legacy, name, None)
        require(callable(function), 'WINDOW_LEGACY_API')
        actual = tuple(inspect.signature(function).parameters)
        # Constructors are inspected through the public class signature.
        require(actual[:len(names)] == names, 'WINDOW_LEGACY_API')
    require(getattr(legacy, 'PRIVATE', None) == LEGACY_PRIVATE, 'WINDOW_LEGACY_PRIVATE')


def load_legacy() -> ModuleType:
    info = trusted(LEGACY)
    require(stat.S_IMODE(info.st_mode) == 0o600 and info.st_size <= 1048576, 'WINDOW_LEGACY_FILE')
    raw = LEGACY.read_bytes()
    require(sha(raw) == LEGACY_SHA, 'WINDOW_LEGACY_SOURCE')
    module = ModuleType('tsw_original_immutable_window')
    module.__file__ = str(LEGACY)
    # Compile verified source directly; ignored bytecode cannot replace it.
    sys.modules[module.__name__] = module
    try:
        exec(compile(raw, str(LEGACY), 'exec', dont_inherit=True), module.__dict__)
        verify_api(module)
    except BaseException:
        sys.modules.pop(module.__name__, None)
        raise
    return module


@contextmanager
def lock_existing(value: dict[str, Any]) -> Iterator[None]:
    path = LEGACY_PRIVATE / 'lock'
    info = trusted(path)
    require(stat.S_IMODE(info.st_mode) == 0o600 and info.st_ino == value['legacy_lock_inode'], 'WINDOW_LEGACY_LOCK_IDENTITY')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(fd)
        require(opened == info, 'WINDOW_LEGACY_LOCK_CAS')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(path.lstat() == opened, 'WINDOW_LEGACY_LOCK_CAS')
        yield
        current = path.lstat()
        require((current.st_dev, current.st_ino, current.st_mode, current.st_nlink, current.st_uid) ==
                (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_nlink, opened.st_uid), 'WINDOW_LEGACY_LOCK_CAS')
    finally:
        os.close(fd)


@contextmanager
def managed_lock(path: Path) -> Iterator[None]:
    trusted(path.parent, directory=True)
    trusted(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600, 'WINDOW_LOCK')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(path.lstat() == info, 'WINDOW_LOCK_CAS')
        yield
    finally:
        os.close(fd)


class ReadOnlyJournal:
    """Expose legacy reads without making predecessor verification writable."""
    def __init__(self, journal: Any):
        self._journal = journal

    def exists(self, name: str) -> bool:
        return self._journal.exists(name)

    def read(self, name: str) -> Any:
        return self._journal.read(name)

    def names(self) -> Any:
        return self._journal.names()

    def save(self, *_args: Any, **_kwargs: Any) -> None:
        raise WindowError('WINDOW_READ_ONLY_JOURNAL')


def approval(go: Any, value: dict[str, Any], mode: str, *, witness: dict[str, Any], now: datetime | None = None) -> None:
    require(type(go) is dict and set(go) == {'schema_version', 'decision', 'phase', 'scenario_sha256', 'source_commit',
                                           'proposal_sha256', 'expires_at_utc', 'evidence_sha256', 'original_context_sha256', 'original_proposal_sha256', 'original_lock_witness', 'legacy_go', 'legacy_go_sha256'}, 'WINDOW_OUTER_GO')
    phase = {'prepare': ('PrepareOriginal',), 'recover-prepare': ('ReconcileEffects',), 'quiesce': ('QuiesceOriginal',),
             'restore': ('RestoreOriginal', 'ReturnFixture', 'ReconcileEffects')}[mode]
    require(type(go['schema_version']) is int and go['schema_version'] == 1 and go['decision'] == 'GO' and go['phase'] in phase
            and go['source_commit'] == value['source_commit'] and go['scenario_sha256'] == value['scenario_sha256'], 'WINDOW_OUTER_GO')
    require(type(go['proposal_sha256']) is str and HEX.fullmatch(go['proposal_sha256']) and
            type(go['evidence_sha256']) is str and (go['evidence_sha256'] == '' or HEX.fullmatch(go['evidence_sha256'])) and
            go['original_context_sha256'] == sha(canonical(value)) and go['original_proposal_sha256'] == value['proposal_sha256'] and go['original_lock_witness'] == witness, 'WINDOW_OUTER_GO')
    if mode == 'quiesce':
        require(type(go['legacy_go']) is dict and go['legacy_go_sha256'] == sha(canonical(go['legacy_go'])), 'WINDOW_INNER_GO')
    else:
        require(go['legacy_go'] is None and go['legacy_go_sha256'] == ZERO, 'WINDOW_INNER_GO')
    expiry = datetime.strptime(go['expires_at_utc'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    remaining = (expiry - (now or datetime.now(timezone.utc))).total_seconds()
    require(BUDGETS[mode] <= remaining <= 3000, 'WINDOW_GO_EXPIRED')


def verify_parent(value: dict[str, Any], legacy: ModuleType, port: Any) -> None:
    if value['window'] == 'fixture':
        return
    parent = BASE / value['run_id'] / 'original-windows' / 'fixture'
    original = context(strict(private_read(parent / 'context.json')))
    require(original['window'] == 'fixture' and original['run_id'] == value['run_id'] and
            original['machine_sha256'] == value['machine_sha256'] and original['registration_sha256'] == value['registration_sha256'], 'WINDOW_PARENT_IDENTITY')
    final = strict(private_read(parent / 'final.json'))
    require(type(final) is dict and final == {'schema_version': 1, 'context_sha256': sha(canonical(original)),
            'proposal_sha256': original['proposal_sha256'], 'decision': 'RESTORED'}, 'WINDOW_PARENT_FINAL')
    switch = value['parent_switch']
    require(switch.get('schema_version') == 3 and switch.get('window') == 'fixture' and switch.get('stage') == 'restored' and switch.get('pending') == '' and switch.get('run_id') == value['run_id'] and switch.get('source_commit') == original['source_commit'] and switch.get('scenario_sha256') == original['scenario_sha256'] and switch.get('original_context_sha256') == sha(canonical(original)), 'WINDOW_PARENT_SWITCH')
    bridge = value['parent_bridge']
    require(set(bridge) == {'schema_version', 'window', 'run_id', 'source_commit', 'descriptor_sha256', 'archive_sha256', 'registration_sha256', 'registration_state_sha256', 'scenario_sha256', 'phase', 'phase_intent', 'transaction_id'} and type(bridge['schema_version']) is int and bridge['schema_version'] == 1 and bridge['window'] == 'fixture' and bridge['run_id'] == value['run_id'] and bridge['source_commit'] == original['source_commit'] and bridge['registration_state_sha256'] == value['registration_sha256'] and type(bridge['registration_sha256']) is str and HEX.fullmatch(bridge['registration_sha256']) and bridge['scenario_sha256'] == switch.get('bridge_scenario_sha256') and bridge['phase'] == 'restored' and bridge['phase_intent'] == bridge['transaction_id'] == '' and all(type(bridge[k]) is str and HEX.fullmatch(bridge[k]) for k in ('descriptor_sha256', 'archive_sha256')), 'WINDOW_PARENT_BRIDGE')
    require(original['adapter_sha256'] == value['adapter_sha256'] and original['source_commit'] == value['source_commit'], 'WINDOW_PARENT_SOURCE')
    journal = ReadOnlyJournal(legacy.Journal(parent / 'legacy-journal'))
    baseline = legacy.strict(legacy.read_proposal(journal))
    legacy.verify_observation(baseline, port.snapshot(), journal, restored=True)


def execute(mode: str, value: dict[str, Any], go: Any, legacy: ModuleType, port: Any, home: Path, *, witness: dict[str, Any]) -> dict[str, Any]:
    """Journal-parametric delegation; caller holds legacy and window locks."""
    journal_path = home / 'legacy-journal'
    if mode == 'inspect':
        port.settle()
        baseline = port.snapshot()
        legacy.validate_baseline(baseline)
        verify_parent(value, legacy, port)
        return {'status': 'ORIGINAL_INSPECTED', 'proposal_sha256': sha(legacy.canonical(baseline))}
    if mode in {'prepare', 'recover-prepare'}:
        approval(go, value, mode, witness=witness)
        if mode == 'prepare':
            require(not os.path.lexists(home / 'context.json') and not os.path.lexists(journal_path), 'WINDOW_CREATE_ONLY')
        elif os.path.lexists(home / 'context.json'):
            require(context(strict(private_read(home / 'context.json'))) == value, 'WINDOW_CONTEXT_DRIFT')
        else:
            require(not os.path.lexists(journal_path), 'WINDOW_PARTIAL_PREPARATION')
        port.settle()
        verify_parent(value, legacy, port)
        baseline = port.snapshot()
        legacy.validate_baseline(baseline)
        require(sha(legacy.canonical(baseline)) == value['proposal_sha256'], 'WINDOW_PROPOSAL_DRIFT')
        if not os.path.lexists(home / 'context.json'):
            create_private(home / 'context.json', canonical(value))
        if not os.path.lexists(journal_path):
            journal_path.mkdir(mode=0o700)
        journal = legacy.Journal(journal_path)
        require(set(journal.names()) <= {'proposal.json'}, 'WINDOW_PARTIAL_PREPARATION')
        if not journal.exists('proposal.json'):
            legacy.prepare(port, journal)
        require(sha(legacy.read_proposal(journal)) == value['proposal_sha256'], 'WINDOW_PROPOSAL_DRIFT')
        return {'status': 'ORIGINAL_PREPARED', 'proposal_sha256': value['proposal_sha256']}
    saved = context(strict(private_read(home / 'context.json')))
    require(saved == value, 'WINDOW_CONTEXT_DRIFT')
    journal = legacy.Journal(journal_path)
    raw = legacy.read_proposal(journal)
    require(sha(raw) == value['proposal_sha256'], 'WINDOW_PROPOSAL_DRIFT')
    baseline = legacy.strict(raw)
    legacy.validate_baseline(baseline)
    final = {'schema_version': 1, 'context_sha256': sha(canonical(value)), 'proposal_sha256': value['proposal_sha256'], 'decision': 'RESTORED'}
    if mode == 'restored' or os.path.lexists(home / 'final.json'):
        require(strict(private_read(home / 'final.json')) == final, 'WINDOW_FINAL_RECEIPT')
    if mode == 'prepared':
        require(set(journal.names()) == {'proposal.json'}, 'WINDOW_PARTIAL_PREPARATION')
        port.settle()
        legacy.compare(baseline, port.snapshot(), legacy.initial_statuses(baseline), ReadOnlyJournal(journal))
        return {'status': 'ORIGINAL_PREPARED', 'proposal_sha256': value['proposal_sha256']}
    if mode in {'quiescent', 'restored'}:
        port.settle()
        legacy.verify_observation(baseline, port.snapshot(), ReadOnlyJournal(journal), restored=mode == 'restored')
        return {'status': 'ORIGINAL_RESTORED' if mode == 'restored' else 'ORIGINAL_QUIESCENT', 'proposal_sha256': value['proposal_sha256']}
    approval(go, value, mode, witness=witness)
    try:
        if mode == 'quiesce':
            legacy.validate_go(go['legacy_go'], baseline, raw, time.time())
            result = legacy.quiesce(port, journal, go['legacy_go'])
        elif journal.exists('restored.json'):
            # Applied-but-unreported restore: verify persisted native receipts
            # and actual state before finalizing only the outer receipt.
            port.settle()
            legacy.verify_observation(baseline, port.snapshot(), ReadOnlyJournal(journal), restored=True)
            result = {'scope': 'WSL_EXACT_GUEST_RUNTIME_WINDOW_ONLY', 'decision': 'RESTORED', 'proposal_sha256': value['proposal_sha256']}
        else:
            result = legacy.restore(port, journal)
        require(result.get('decision') == ('QUIESCED' if mode == 'quiesce' else 'RESTORED') and
                result.get('proposal_sha256') == value['proposal_sha256'], 'WINDOW_RESULT')
        if mode == 'restore' and not os.path.lexists(home / 'final.json'):
            create_private(home / 'final.json', canonical(final))
        return result
    finally:
        port.settle()


def lock_witness(value: dict[str, Any]) -> dict[str, Any]:
    info = trusted(LEGACY_PRIVATE / 'lock')
    require(stat.S_IMODE(info.st_mode) == 0o600 and info.st_ino == value['legacy_lock_inode'], 'WINDOW_LEGACY_LOCK_IDENTITY')
    machine = Path('/etc/machine-id').read_bytes().strip()
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(re.fullmatch(b'[0-9a-f]{32}', machine) and sha(machine) == value['machine_sha256'] and str(UUID(boot)) == boot, 'WINDOW_MACHINE_BOOT')
    return {'device': info.st_dev, 'inode': info.st_ino, 'machine_sha256': sha(machine), 'boot_sha256': sha(boot.encode())}


def install_legacy_signal_handler(legacy: ModuleType) -> None:
    """Reuse the hash-pinned main guard without invoking the legacy CLI."""
    handlers = [item for item in legacy.main.__code__.co_consts
                if isinstance(item, CodeType) and item.co_name == 'interrupted']
    require(len(handlers) == 1 and not handlers[0].co_freevars, 'WINDOW_LEGACY_SIGNAL_ABI')
    handler = FunctionType(handlers[0], legacy.__dict__)
    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM):
        signal.signal(number, handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=(*BUDGETS, 'witness'))
    parser.add_argument('--context-base64', required=True)
    parser.add_argument('--expected-context-sha256', required=True)
    parser.add_argument('--approval-base64')
    parser.add_argument('--expected-approval-sha256')
    args = parser.parse_args(argv)
    try:
        os.umask(0o077)
        require(os.geteuid() == 0, 'WINDOW_ROOT_REQUIRED')
        def interrupted(_signum: int, _frame: Any) -> None:
            raise WindowError('WINDOW_INTERRUPTED_UNCERTAIN')
        signal.signal(signal.SIGINT, interrupted)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGALRM, interrupted)
        signal.alarm(BUDGETS.get(args.mode, 60))
        raw = base64.b64decode(args.context_base64, validate=True)
        require(type(args.expected_context_sha256) is str and HEX.fullmatch(args.expected_context_sha256)
                and sha(raw) == args.expected_context_sha256 and raw == canonical(strict(raw)), 'WINDOW_CONTEXT_WIRE')
        value = context(strict(raw))
        home, _journal, adapter = paths(value)
        trusted(adapter)
        require(Path(__file__).resolve() == adapter and sha(adapter.read_bytes()) == value['adapter_sha256'], 'WINDOW_ADAPTER_SOURCE')
        trusted(home, directory=True)
        check = subprocess.run(['/usr/bin/findmnt', '-T', str(home), '-n', '-o', 'FSTYPE'],
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
                               env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, check=False)
        require(check.returncode == 0 and check.stdout == b'ext4\n' and not check.stderr, 'WINDOW_PRIVATE_EXT4')
        oldfs = subprocess.run(['/usr/bin/findmnt', '-T', str(LEGACY_PRIVATE / 'lock'), '-n', '-o', 'FSTYPE'],
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
                               env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, check=False)
        require(oldfs.returncode == 0 and oldfs.stdout == b'ext4\n' and not oldfs.stderr, 'WINDOW_LEGACY_EXT4')
        witness = lock_witness(value)
        go = None
        if args.mode in {'prepare', 'recover-prepare', 'quiesce', 'restore'}:
            require(args.approval_base64 is not None and args.expected_approval_sha256 is not None, 'WINDOW_APPROVAL_REQUIRED')
            body = base64.b64decode(args.approval_base64, validate=True)
            require(sha(body) == args.expected_approval_sha256 and body == canonical(strict(body)), 'WINDOW_APPROVAL_WIRE')
            go = strict(body)
            approval(go, value, args.mode, witness=witness)
        else:
            require(args.approval_base64 is None and args.expected_approval_sha256 is None, 'WINDOW_READ_ONLY_ARGUMENTS')
        with lock_existing(value), managed_lock(home.parent / ('machine-' + value['machine_sha256'] + '.lock')), managed_lock(home / 'window.lock'):
            require(lock_witness(value) == witness, 'WINDOW_LOCK_WITNESS_DRIFT')
            if args.mode == 'witness':
                result = {'status': 'ORIGINAL_LOCK_WITNESS', 'legacy_lock_witness': witness}
            else:
                legacy = load_legacy()
                install_legacy_signal_handler(legacy)
                port = legacy.RealPort(value['machine_sha256'])
                try:
                    result = execute(args.mode, value, go, legacy, port, home, witness=witness)
                finally:
                    port.settle()
        result = dict(result)
        current_witness = lock_witness(value)
        result.update(window_schema_version=1, run_id=value['run_id'], window=value['window'], context_sha256=sha(canonical(value)), source_commit=value['source_commit'], boot_id_sha256=current_witness['boot_sha256'], machine_id_sha256=current_witness['machine_sha256'])
        print(canonical(result).decode())
        return 0
    except Exception:
        print('{"status":"WINDOW_REFUSED_OR_UNCERTAIN","recovery_required":true}')
        return 2
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Closed fresh/add acceptance in one coordinator-owned WSL guest.

No guest switching, VM shutdown, LXD maintenance or network disposal. Each case
uses its own immutable checkout/installation anchor and restores shared Incus
metadata after deleting only independently receipted case UUIDs.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
import copy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any, Iterator, Protocol, cast
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .incus_profile_listener_fixture import ACTIVE_WORKFLOW
    from . import native_runtime_inventory as inventory
    from . import owned_case_disposal as disposal
    from . import product_upgrade_cases as upgrades
    from .preserving_product_acceptance import RECIPES, validate_preview, operator_credentials, validate_host_artifacts, CAPABILITY_HOSTS
else:
    prefix = __package__ + '.' if __package__ else ''
    ACTIVE_WORKFLOW = importlib.import_module(prefix + 'incus_profile_listener_fixture').ACTIVE_WORKFLOW
    inventory = importlib.import_module(prefix + 'native_runtime_inventory')
    disposal = importlib.import_module(prefix + 'owned_case_disposal')
    upgrades = importlib.import_module(prefix + 'product_upgrade_cases')
    recipes = importlib.import_module(prefix + 'preserving_product_acceptance')
    RECIPES, validate_preview = recipes.RECIPES, recipes.validate_preview
    operator_credentials, validate_host_artifacts, CAPABILITY_HOSTS = recipes.operator_credentials, recipes.validate_host_artifacts, recipes.CAPABILITY_HOSTS

ROOT = Path(__file__).resolve().parents[5]
BASE = Path('/root/tsw440-acceptance')
SCRIPT = 'modules/tsw_core/tools/linux/qualification/wsl_product_acceptance.py'
CAPABILITY = 'modules/tsw_core/infra/config/incus-profile-capabilities.json'
FILES = (SCRIPT, 'modules/tsw_core/tools/linux/qualification/owned_case_disposal.py',
         'modules/tsw_core/tools/linux/qualification/preserving_product_acceptance.py',
         'modules/tsw_core/tools/linux/qualification/native_runtime_inventory.py',
         'modules/tsw_core/tools/linux/qualification/native_lxd_snap_provenance.py', CAPABILITY, upgrades.SCRIPT,
         upgrades.CATALOG, 'modules/tsw_core/src/infrastructure/adapters/lifecycle/catalog.py',
         ACTIVE_WORKFLOW, upgrades.CLI_MAIN, upgrades.CLI_RELEASE)
CASE_RECIPES = RECIPES | upgrades.RECIPES
LIMIT = 8 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z')
RUN = re.compile(r'[0-9a-f]{32}\Z')
BUDGETS = {'prepare': 1200, 'admit': 300, 'case': 5400, 'disposal': 900, 'final': 300, 'recover': 900}
REVIEWS = {'requirements', 'architecture', 'security', 'devops', 'test_evidence'}
FUTURE = {'prepare': 0, 'admit': 6600, 'case': 1200, 'disposal': 300, 'final': 0, 'recover': 0}
ENV = {'LC_ALL': 'C', 'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root',
       'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_OPTIONAL_LOCKS': '0'}
BOOTSTRAP = upgrades.CLI_BOOTSTRAP
GATE = "import os,sys;f=int(sys.argv[1]);p=os.read(f,1);os.close(f);os.execvpe(sys.argv[2],sys.argv[2:],os.environ) if p==b'G' else sys.exit(125)"


class CaseError(Exception):
    """Only bounded symbolic reasons are persisted."""


def need(ok: Any, code: str) -> None:
    if not ok:
        raise CaseError(code)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reason(exc: BaseException) -> str:
    text = str(exc)
    return text if re.fullmatch(r'[A-Z][A-Z0-9_]{0,95}', text) else 'CASE_FAILURE_REDACTED'


def trusted(path: Path, *, directory: bool = False) -> None:
    for parent in (path, *path.parents):
        info = parent.lstat()
        need(info.st_uid == 0 and not stat.S_ISLNK(info.st_mode) and not info.st_mode & 0o022, 'CASE_PATH_UNSAFE')
    need(path.is_dir() if directory else path.is_file(), 'CASE_PATH_UNSAFE')


def private(path: Path) -> bytes:
    trusted(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == 0o600
             and before.st_size <= LIMIT, 'CASE_PRIVATE_UNSAFE')
        raw = stream.read(LIMIT + 1)
        after = os.fstat(stream.fileno())
        need(len(raw) <= LIMIT and (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
             == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'CASE_PRIVATE_DRIFT')
        return raw


class Journal:
    def __init__(self, directory: Path):
        trusted(directory, directory=True)
        need(stat.S_IMODE(directory.stat().st_mode) == 0o700, 'CASE_JOURNAL_MODE')
        self.directory = directory

    def save(self, name: str, value: Any) -> None:
        need(bool(re.fullmatch(r'[a-z0-9-]+\.json', name)), 'CASE_JOURNAL_NAME')
        raw = canonical(value)
        need(len(raw) <= LIMIT, 'CASE_JOURNAL_BOUND')
        fd = os.open(self.directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


@dataclass(frozen=True)
class Intent:
    run_id: str
    case: str
    source_commit: str
    machine_id_sha256: str
    boot_id_sha256: str
    new_guid: str
    new_vhd_sha256: str
    windows_host: str
    bridge_bundle_id: str
    ubuntu_fingerprint: str
    configuration_sha256: str
    prepared_sha256: str
    bound_sha256: str
    capability_sha256: str

    @classmethod
    def parse(cls, value: Any) -> 'Intent':
        need(isinstance(value, dict) and set(value) == set(cls.__dataclass_fields__)
             and all(type(v) is str for v in value.values()), 'CASE_INTENT_SCHEMA')
        need(bool(RUN.fullmatch(value['run_id'])) and value['case'] in CASE_RECIPES
             and bool(inventory.HEX40.fullmatch(value['source_commit']))
             and bool(re.fullmatch(r'\{[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\}', value['new_guid']))
             and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,62}', value['windows_host'])), 'CASE_INTENT_IDENTITY')
        need(all(bool(HEX.fullmatch(value[k])) for k in cls.__dataclass_fields__ if k.endswith('_sha256')
                 or k == 'ubuntu_fingerprint') and bool(re.fullmatch(r'[0-9A-F]{64}', value['bridge_bundle_id'])), 'CASE_INTENT_DIGEST')
        return cls(**value)

    @property
    def home(self) -> Path:
        return BASE / self.run_id

    @property
    def checkout(self) -> Path:
        return self.home / 'cases' / self.case / 'checkout'


def approval(value: Any, intent: Intent, proposal: dict[str, Any], raw_sha: str, *, recover: bool = False,
             engine_recovery: bool = False, now: datetime | None = None) -> datetime:
    fields = {'schema_version', 'decision', 'phase', 'intent_sha256', 'proposal_sha256', 'source_commit', 'pins', 'budgets',
              'expires_at_utc', 'reviews'}
    selected_budgets = upgrades.budgets(intent.case, 'wsl', engine_recovery=engine_recovery)
    if engine_recovery:
        fields.add('engine_binding')
    need(not (recover and engine_recovery) and isinstance(value, dict) and set(value) == fields and type(value['schema_version']) is int
         and value['schema_version'] == 1 and value['decision'] == 'GO'
         and value['phase'] == ('wsl-engine-recovery' if engine_recovery else 'wsl-case-recover' if recover else 'wsl-case-run'), 'CASE_GO_SCHEMA')
    need(value['intent_sha256'] == sha(canonical(asdict(intent))) and value['proposal_sha256'] == raw_sha
         and value['source_commit'] == intent.source_commit and value['pins'] == proposal['pins']
         and value['budgets'] == selected_budgets and all(type(v) is int for v in value['budgets'].values()), 'CASE_GO_BINDING')
    need(isinstance(value['reviews'], dict) and set(value['reviews']) == REVIEWS
         and all(v == 'APPROVED' for v in value['reviews'].values()), 'CASE_GO_REVIEWS')
    try:
        expiry = datetime.fromisoformat(value['expires_at_utc'])
        seconds = (expiry - (now if now is not None else datetime.now(timezone.utc))).total_seconds()
    except (TypeError, ValueError) as exc:
        raise CaseError('CASE_GO_EXPIRY') from exc
    minimum = BUDGETS['recover'] if recover else sum(selected_budgets[k] for k in ('admit', 'case', 'disposal', 'final'))
    need(expiry.tzinfo is not None and minimum <= seconds <= minimum + 300, 'CASE_GO_EXPIRY')
    return expiry


class CasePort(Protocol):
    def phase(self, name: str) -> None: ...
    def admit(self, proposal: dict[str, Any]) -> None: ...
    def run(self) -> None: ...
    def dispose(self) -> None: ...
    def final(self, baseline: dict[str, Any]) -> None: ...
    def settled(self) -> bool: ...
    def event(self, stage: str, value: dict[str, Any]) -> None: ...


def execute(port: CasePort, proposal: dict[str, Any], *, recover: bool = False) -> dict[str, Any]:
    failure: str | None = None
    if not recover:
        port.phase('admit'); port.admit(proposal)
        port.event('execution-intent', {'proposal_sha256': sha(canonical(proposal))})
        port.phase('case')
        try:
            port.run()
        except BaseException as exc:
            failure = reason(exc)
            port.event('execution-failed', {'reason': failure})
    try:
        need(port.settled(), 'CASE_WORKER_UNSETTLED')
        port.phase('recover' if recover else 'disposal')
        port.dispose()
        # Recovery's independent 900s includes its final capture; do not reset it.
        if not recover:
            port.phase('final')
        port.final(proposal['baseline'])
    except BaseException as exc:
        port.event('recovery-required', {'reason': reason(exc)})
        raise
    result = {'status': upgrades.outcome(failure, recovered=recover),
              'failure': failure, 'scope': 'WSL_UPGRADE_ONLY' if getattr(getattr(port, 'intent', None), 'case', None) in upgrades.RECIPES else 'WSL_FRESH_ADD_ONLY', 'epic_complete': False}
    port.event('outcome', result)
    return result


class DetailRunner(inventory.Runner):
    def __init__(self) -> None:
        super().__init__()
        self.details: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}

    def run(self, argv: list[str], **kwargs: Any) -> tuple[int, bytes, bytes]:
        result = super().run(argv, **kwargs)
        command = kwargs['command_id']
        if result[0] == 0 and (command.endswith(('_show', '_config_show', '_config_show_expanded')) or '_server_root_' in command):
            envelope = inventory.strict_json(result[1])
            row = envelope.get('metadata') if isinstance(envelope, dict) else None
            if isinstance(row, dict):
                self.details[(command, tuple(kwargs.get('safe_args', [])))] = row
        return result


def projection(artifact: dict[str, Any], details: dict[Any, Any], owned: disposal.DisposalIntent | None,
               fingerprint: str, baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    """Only already authenticated case nodes/profile/root refs may be removed."""
    result = copy.deepcopy({key: artifact[key] for key in ('incus_projects', 'incus_pools', 'incus_admission', 'incus_units',
        'lxd_projects', 'lxd_pools', 'lxd_units', 'lxd_admission', 'sockets')})
    names = set() if owned is None else {row.name for row in owned.nodes}
    if owned is not None:
        bound = owned
        for project in result['incus_projects']:
            if project['project'] != 'default':
                continue
            project['instances'] = [r for r in project['instances'] if r['name'] not in names]
            project['profiles'] = [r for r in project['profiles'] if r['name'] != owned.profile_name]
            for pool in project['pools']:
                pool['volumes'] = [r for r in pool['volumes'] if not (pool['name'] == owned.pool
                    and r['name'] in names and r['type'] == 'container' and r['owner_project'] == 'default')]
        def links(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == 'used_by' and isinstance(child, list):
                        value[key] = [r for r in child if not disposal.own_reference(r, bound)]
                    else:
                        links(child)
            elif isinstance(value, list):
                for child in value:
                    links(child)
        links(result)
    metadata = {}
    for (command, args), raw in details.items():
        own = owned is not None and (command in {'incus_instance_config_show', 'incus_instance_config_show_expanded'}
            and len(args) == 2 and args[0] in names and args[1] == 'default'
            or command == 'incus_profile_show' and args == (owned.profile_name, 'default')
            or command == 'incus_storage_volume_show' and len(args) == 4
            and args[0] == owned.pool and args[1] == 'container' and args[2] in names and args[3] == 'default')
        if own:
            continue
        row = ({'config': raw['config']} if '_server_root_' in command else
               {k: v for k, v in raw.items() if k != 'used_by' and not (command == 'incus_image_show' and k == 'last_used_at')})
        metadata[command + ':' + ':'.join(args)] = sha(canonical(row))
    result['metadata'] = metadata
    # A cache creation is an exact bounded permitted addition, never deleted.
    if baseline is not None:
        for project in result['incus_projects']:
            old = next(p for p in baseline['incus_projects'] if p['project'] == project['project'])
            for pool in project['pools']:
                previous = next(p for p in old['pools'] if p['name'] == pool['name'])
                if pool['name'] == 'default' and not any(c['fingerprint'] == fingerprint for c in previous['image_cache']):
                    added = [c for c in pool['image_cache'] if c['fingerprint'] == fingerprint]
                    need(len(added) <= 1 and all(c['owner_project'] == 'default' and c['content_type'] == 'filesystem'
                         for c in added), 'CASE_CACHE_ADDITION_INVALID')
                    if added:
                        pool['image_cache'] = [c for c in pool['image_cache'] if c['fingerprint'] != fingerprint]
                        pool['used_by'] = [r for r in pool['used_by'] if r != {'kind': 'images', 'name': fingerprint, 'project': 'default'}]
                        result['metadata'].pop('incus_image_cache_show:' + pool['name'] + ':' + fingerprint + ':default', None)
                        for global_pool in result['incus_pools']:
                            if global_pool['name'] == pool['name']:
                                global_pool['used_by'] = [r for r in global_pool['used_by'] if r !=
                                    {'kind': 'images', 'name': fingerprint, 'project': 'default'}]
    return result


def operations_empty(value: Any) -> bool:
    keys = {'type', 'status', 'status_code', 'operation', 'error_code', 'error', 'metadata'}
    need(isinstance(value, dict) and set(value) == keys and value['type'] == 'sync' and value['status'] == 'Success'
         and type(value['status_code']) is int and value['status_code'] == 200 and value['operation'] == ''
         and type(value['error_code']) is int and value['error_code'] == 0 and value['error'] == '', 'CASE_OPERATIONS_SCHEMA')
    states = {'operation created', 'started', 'stopped', 'running', 'cancelling', 'pending', 'success', 'failure',
              'cancelled', 'starting', 'stopping', 'aborting', 'freezing', 'frozen', 'thawed', 'error', 'ready'}
    rows = value['metadata']
    need(isinstance(rows, dict) and set(rows) <= states and len(rows) <= 17, 'CASE_OPERATIONS_SCHEMA')
    for entries in rows.values():
        need(isinstance(entries, list) and len(entries) <= 1024 and all(type(entry) is str and re.fullmatch(
            r'/1\.0/operations/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', entry) for entry in entries), 'CASE_OPERATIONS_SCHEMA')
    return not any(rows.values())


class WslCasePort:
    """Fixed real adapter. Inputs are data/receipts, never commands or callbacks."""
    def __init__(self, intent: Intent, journal: Journal):
        self.intent, self.journal = intent, journal
        self.purpose_budgets = upgrades.budgets(intent.case, 'wsl')
        self.engine_recovery = False
        self.upgrade_baseline = False
        self.upgrade_fault_armed = False
        self.upgrade_fault_observed = False
        self.cache_unknown = False
        self.total_deadline: float | None = None
        self.deadline = time.monotonic() + BUDGETS['prepare']
        self.active_phase = 'prepare'
        self.used_phases = {'prepare'}
        self.authorized_until: float | None = None
        self.worker_settled = True
        self.owned: disposal.DisposalIntent | None = None
        self.lease: Any = None
        self.artifact: dict[str, Any] = {}
        self.details: dict[Any, Any] = {}
        self.proposal: dict[str, Any] | None = None
        self.cli_pins: dict[str, str] = {}
        self.cli_approval: dict[str, str] | None = None
        self.cli_activation = None
        self.cli_versions: tuple[str, str] | None = None
        self.cli_final: dict[str, Any] | None = None
        self.cli_selection: dict[str, Any] | None = None

    def phase(self, name: str) -> None:
        need(name in self.purpose_budgets, 'CASE_PHASE')
        if name == self.active_phase:
            return
        need(name not in self.used_phases, 'CASE_PHASE_REPLAY')
        if self.authorized_until is not None:
            need(self.authorized_until - time.monotonic() >= self.purpose_budgets[name] + self.future(name), 'CASE_AUTHORIZATION_RESERVE')
        self.deadline = time.monotonic() + self.purpose_budgets[name]
        if self.total_deadline is not None:
            need(self.deadline <= self.total_deadline, 'UPGRADE_TOTAL_RESERVE')
        self.active_phase = name
        self.used_phases.add(name)

    def future(self, name: str) -> int:
        if name == 'admit':
            return self.purpose_budgets['case'] + 1200
        return FUTURE[name]

    def reserve(self, seconds: int) -> None:
        need(self.deadline - time.monotonic() >= seconds, 'CASE_PHASE_EXPIRED')
        if self.authorized_until is not None:
            need(self.authorized_until - time.monotonic() >= seconds + self.future(self.active_phase), 'CASE_AUTHORIZATION_RESERVE')

    def event(self, stage: str, value: dict[str, Any]) -> None:
        self.journal.save(stage + '-' + uuid4().hex + '.json', value | {'run_id': self.intent.run_id,
            'source_commit': self.intent.source_commit, 'case': self.intent.case})

    def command(self, argv: list[str], timeout: int, *, public: bool = False, extra_env: dict[str, str] | None = None) -> bytes:
        """Gate every mutation worker until its PID/starttime intent is durable."""
        self.reserve(timeout + 10)
        need(self.worker_settled, 'CASE_WORKER_UNSETTLED')
        values = self.operator_values() if public else {}
        if public and self.upgrade_baseline:
            values |= upgrades.baseline_environment(self.intent.case)
        env = ENV | values
        env['WSL_DISTRO_NAME'] = 'TSW-Q440-' + self.intent.run_id
        interop = os.environ.get('WSL_INTEROP', '')
        if re.fullmatch(r'/run/WSL/[0-9]+_interop', interop):
            need(stat.S_ISSOCK(Path(interop).lstat().st_mode), 'CASE_INTEROP_SOCKET')
            env['WSL_INTEROP'] = interop
        if extra_env is not None:
            need(set(extra_env) == {'INCUS_SOCKET'} and extra_env['INCUS_SOCKET'] in {'/run/incus/unix.socket', '/var/lib/incus/unix.socket'}, 'CASE_EFFECT_ENV')
            env |= extra_env
        # Scope is assigned AFTER every credential/transport merge. Operator
        # files cannot redirect anchors, TLS state, evidence, policy or consent.
        env |= {'TSW_REPOSITORY_ROOT': str(ROOT), 'TSW_INFRA_ROOT': str(self.intent.home / 'infra'),
                'TSW_INSTALL_ENV_FILE': str(self.intent.home / 'infra/operator.env'),
                'TSW_LIVE_EVIDENCE_ROOT': str(self.journal.directory), 'TSW_LOCAL_TLS_STATE_ROOT': self.tls_root()}
        key = 'child-' + uuid4().hex
        args = upgrades.cli_args(argv) if public else None
        receipt = None if args is None else upgrades.CliReceipt(self.journal, key,
            upgrades.cli_binding(self, 'wsl', ACTIVE_WORKFLOW), argv, args)
        if receipt is not None:
            receipt.require_approval()
        self.journal.save(key + '-intent.json', {'argv_sha256': sha(canonical(argv)), 'timeout': timeout, 'public': public})
        if argv[0].endswith('.exe'):
            need(len(subprocess.list2cmdline(argv).encode('utf-16-le')) // 2 + 1 <= 30000, 'CASE_WINDOWS_COMMAND_BOUND')
        reader, writer = os.pipe(); child = None; released = False
        selector = selectors.DefaultSelector(); output = bytearray(); error = bytearray()
        output_complete = False
        self.worker_settled = False
        try:
            child = subprocess.Popen([self.interpreter(), '-E', '-s', '-B', '-c', GATE, str(reader), *argv],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True, pass_fds=(reader,))
            os.close(reader); reader = -1
            identity = {'pid': child.pid, 'start_time': start_time(child.pid)}
            self.journal.save(key + '-pid.json', identity)
            if receipt is not None:
                receipt.start(identity, start_time(os.getpid()))
            if child.stdout is None or child.stderr is None:
                raise CaseError('CASE_PIPE_MISSING')
            os.write(writer, b'G'); released = True; os.close(writer); writer = -1
            if receipt is not None:
                receipt.release()
            selector.register(child.stdout, selectors.EVENT_READ, output)
            selector.register(child.stderr, selectors.EVENT_READ, error)
            end = time.monotonic() + timeout
            while selector.get_map():
                if receipt is not None and upgrades.cli_fault_candidate(self, receipt):
                    upgrades.poll_fault(self, child, before_signal=receipt.prepare_fault)
                need(time.monotonic() < end, 'CASE_COMMAND_TIMEOUT')
                for selected, _event in selector.select(.2):
                    chunk = os.read(selected.fd, 65536)
                    selected.data.extend(chunk)
                    need(len(output) + len(error) <= LIMIT, 'CASE_COMMAND_OUTPUT_BOUND')
                    if not chunk:
                        selector.unregister(selected.fileobj)
            status = child.wait(timeout=max(.01, end - time.monotonic()))
            output_complete = True
            self.journal.save(key + '-outcome.json', {'return_code': status,
                'stdout_sha256': sha(bytes(output)), 'stderr_sha256': sha(bytes(error))})
            need(status == 0, 'CASE_COMMAND_FAILED')
            return bytes(output)
        except upgrades.FaultObserved as exc:
            if receipt is not None:
                receipt.fault = exc.receipt
            raise
        finally:
            selector.close()
            if reader >= 0:
                os.close(reader)
            if writer >= 0:
                os.close(writer)
            if child is None:
                self.worker_settled = True
                self.journal.save(key + '-launch-refused.json', {'released': False})
            else:
                if child.poll() is None:
                    if receipt is None or receipt.fault is None:
                        os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=5)
                self.worker_settled = group_absent(child.pid)
                if self.worker_settled:
                    self.journal.save(key + '-settled.json', {'pid': child.pid, 'released': released, 'group_absent': True})
                for stream in (child.stdout, child.stderr):
                    if stream is not None:
                        stream.close()
                if receipt is not None and self.worker_settled and child.returncode is not None:
                    if receipt.fault is not None and child.returncode != -receipt.fault['signal']:
                        self.upgrade_fault_observed = False
                    receipt.settle(child.pid, child.returncode, output_complete, sha(bytes(output)), sha(bytes(error)))

    def settled(self) -> bool:
        if not self.worker_settled:
            return False
        paths = list(self.journal.directory.glob('child-*-intent.json'))
        need(len(paths) <= 1024, 'CASE_CHILD_EVENT_BOUND')
        for path in paths:
            stem = path.name.removesuffix('-intent.json')
            pid_path = self.journal.directory / (stem + '-pid.json')
            if not pid_path.exists():
                refused = self.journal.directory / (stem + '-launch-refused.json')
                if refused.exists() and inventory.strict_json(private(refused)) == {'released': False}:
                    continue
                return False
            row = inventory.strict_json(private(pid_path))
            need(isinstance(row, dict) and set(row) == {'pid', 'start_time'} and type(row['pid']) is int
                 and row['pid'] > 1 and type(row['start_time']) is int, 'CASE_CHILD_RECORD')
            if not group_absent(row['pid']):
                return False
        return True

    def interpreter(self) -> str:
        path = ROOT / '.venv/bin/python'
        trusted(ROOT / '.venv', directory=True); trusted(path.parent, directory=True)
        trusted(path.resolve())
        need(path.exists() and Path(sys.executable).absolute() == path, 'CASE_PINNED_RUNTIME_REQUIRED')
        return str(path)

    def source(self) -> dict[str, str]:
        need(os.geteuid() == 0 and ROOT == self.intent.checkout, 'CASE_CHECKOUT_BINDING')
        trusted(ROOT, directory=True); trusted(ROOT / '.git', directory=True)
        need(stat.S_IMODE(ROOT.stat().st_mode) == 0o700, 'CASE_CHECKOUT_NOT_PRIVATE')
        git = ['/usr/bin/git', '--no-optional-locks', '-C', str(ROOT), '-c', 'core.fsmonitor=false',
               '-c', 'core.hooksPath=/dev/null', '-c', 'core.untrackedCache=false']
        need(self.command(git + ['rev-parse', 'HEAD'], 10).decode().strip() == self.intent.source_commit, 'CASE_SOURCE_HEAD')
        # Any local filter configuration is refused before status/blob reads.
        local = self.command(git + ['config', '--local', '--includes', '--null', '--list'], 10)
        need(not re.search(rb'(?:^|\x00)filter\.', local), 'CASE_SOURCE_FILTER')
        need(not self.command(git + ['status', '--porcelain=v1', '--untracked-files=all'], 10), 'CASE_SOURCE_DIRTY')
        pins = {}
        for relative in FILES:
            path = ROOT / relative; trusted(path)
            raw = path.read_bytes(); need(len(raw) <= 2 * 1024 * 1024, 'CASE_SOURCE_BOUND')
            need(raw == self.command(git + ['show', self.intent.source_commit + ':' + relative], 10), 'CASE_SOURCE_BLOB')
            pins[relative] = sha(raw)
        need(self.command(git + ['rev-parse', 'HEAD'], 10).decode().strip() == self.intent.source_commit, 'CASE_SOURCE_HEAD')
        need(not self.command(git + ['status', '--porcelain=v1', '--untracked-files=all'], 10), 'CASE_SOURCE_DIRTY')
        return pins

    def identity(self) -> dict[str, str]:
        need('microsoft' in Path('/proc/sys/kernel/osrelease').read_text().lower()
             and os.environ.get('WSL_DISTRO_NAME') == 'TSW-Q440-' + self.intent.run_id, 'CASE_WSL_IDENTITY')
        os_release = importlib.import_module('platform').freedesktop_os_release()
        need(os.uname().machine == 'x86_64' and os_release.get('ID') == 'ubuntu' and os_release.get('VERSION_ID') == '26.04'
             and os_release.get('VERSION', '').startswith('26.04.1'), 'CASE_GUEST_OS_UNSUPPORTED')
        machine_raw = Path('/etc/machine-id').read_bytes().strip()
        boot_raw = Path('/proc/sys/kernel/random/boot_id').read_bytes().strip()
        need(bool(RUN.fullmatch(machine_raw.decode('ascii'))) and str(UUID(boot_raw.decode('ascii'))) == boot_raw.decode('ascii'), 'CASE_GUEST_IDENTITY_INVALID')
        machine = sha(machine_raw)
        boot = sha(boot_raw)
        need(machine == self.intent.machine_id_sha256 and boot == self.intent.boot_id_sha256, 'CASE_GUEST_IDENTITY_DRIFT')
        raw = self.command(['/usr/bin/findmnt', '-T', str(self.journal.directory), '-n', '-o', 'FSTYPE'], 10)
        need(raw == b'ext4\n', 'CASE_PRIVATE_EXT4_REQUIRED')
        # Receipts are actual coordinator outputs, independently hash-bound in GO.
        prepared = private(self.intent.home / 'preparation.json')
        bound = private(self.intent.home / 'bridge-bound.json')
        need(sha(prepared) == self.intent.prepared_sha256 and sha(bound) == self.intent.bound_sha256, 'CASE_COORDINATOR_RECEIPT_DRIFT')
        prep, bridge = inventory.strict_json(prepared), inventory.strict_json(bound)
        need(isinstance(prep, dict) and set(prep) == {'schema_version', 'run_id', 'source_commit', 'kind', 'package_versions', 'python_version'}
             and type(prep['schema_version']) is int and prep['schema_version'] == 1
             and isinstance(bridge, dict) and set(bridge) == {'schema_version', 'scope', 'phase', 'status', 'changed', 'recovery_required', 'application_ready', 'error'}
             and type(bridge['schema_version']) is int and bridge['schema_version'] == 1
             and bridge['scope'] == 'PRESERVING_ACCEPTANCE_BRIDGE' and bridge['phase'] == 'Bind'
             and bridge['changed'] is True and bridge['recovery_required'] is False and bridge['error'] == 'NONE', 'CASE_COORDINATOR_RECEIPT_SCHEMA')
        need(prep['kind'] == 'NEW_GUEST_PREPARATION' and prep['run_id'] == self.intent.run_id
             and bridge['status'] == 'NEW_BINDING_READY'
             and bridge['application_ready'] is False, 'CASE_COORDINATOR_NOT_READY')
        qualification = self.qualification_revision(prep['source_commit'])
        windows = windows_scope(self.intent)
        observed = inventory.strict_json(self.command(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
            '-NoProfile', '-NonInteractive', '-Command', windows], 30))
        need(observed == {'guid': self.intent.new_guid, 'vhd_sha256': self.intent.new_vhd_sha256,
             'name': 'TSW-Q440-' + self.intent.run_id, 'host': self.intent.windows_host,
             'bundle_id': self.intent.bridge_bundle_id, 'sole_running': True}, 'CASE_WINDOWS_SCOPE_DRIFT')
        return {'machine_id_sha256': machine, 'boot_id_sha256': boot, 'new_guid': self.intent.new_guid,
                'new_vhd_sha256': self.intent.new_vhd_sha256, 'qualification_source_commit': qualification,
                'product_source_commit': self.intent.source_commit}

    def qualification_revision(self, qualification: Any) -> str:
        """Keep the original receipt; only one data-only admission commit may follow it."""
        need(isinstance(qualification, str) and bool(inventory.HEX40.fullmatch(qualification)), 'CASE_QUALIFICATION_SOURCE')
        product = self.intent.source_commit
        if qualification != product:
            git = ['/usr/bin/git', '--no-optional-locks', '-C', str(ROOT)]
            parents = self.command(git + ['rev-list', '--parents', '-n', '1', product], 10).decode('ascii').split()
            changes = self.command(git + ['diff', '--name-only', '--no-renames', qualification, product, '--'], 10).decode('ascii').splitlines()
            need(parents == [product, qualification] and changes == [CAPABILITY], 'CASE_QUALIFICATION_PROMOTION')
        return qualification

    def prerequisites(self) -> None:
        capability = ROOT / CAPABILITY; trusted(capability)
        need(sha(capability.read_bytes()) == self.intent.capability_sha256, 'CASE_CAPABILITY_DRIFT')
        matrix = importlib.import_module('tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository')
        actual = matrix.IncusProfileCapabilityRepository(ROOT).load()
        need(actual.admits('6.0.5', '6.0.5'), 'CASE_BOTH_HOST_CAPABILITY_MISSING')
        entry = next(r for r in actual.admitted_versions if r.client_version == r.server_version == '6.0.5')
        record = inventory.strict_json(private(self.intent.home / 'both-host-profile-capability.json'))
        artifacts = {host: private(self.intent.home / ('profile-capability-' + host + '.json')) for host in CAPABILITY_HOSTS}
        try:
            sources = validate_host_artifacts(record, self.intent.capability_sha256, entry.fixture_sha256, artifacts)
        except ValueError as exc:
            raise CaseError(str(exc)) from exc
        revisions = (entry.fixture_source_revision, *sources.values())
        for revision in revisions:
            blob = self.command(['/usr/bin/git', '--no-optional-locks', 'show', revision +
                ':modules/tsw_core/tools/linux/qualification/incus_profile_listener_fixture.py'], 10)
            need(sha(blob) == entry.fixture_sha256, 'CASE_CAPABILITY_SOURCE_DRIFT')
        self.operator_values()
        infra = self.intent.home / 'infra'
        resource = importlib.import_module((__package__ + '.' if __package__ else '') + 'native_resource_admission')
        resource.selection(private(infra / 'config/node-providers/provider_config.yaml'))
        configuration = importlib.import_module('tiny_swarm_world.infrastructure.adapters.incus_preparation.configuration')
        need(configuration.load_requirements(infra / 'config/node-providers/provider_config.yaml').storage == 'default', 'CASE_STORAGE_SCOPE')

    def configuration_bytes(self) -> bytes:
        """Rehash complete approved tree; return the operator bytes from THAT read."""
        infra = self.intent.home / 'infra'; trusted(infra, directory=True)
        paths: list[Path] = []
        for path in infra.rglob('*'):
            need(len(paths) < 4096, 'CASE_CONFIGURATION_BOUND'); paths.append(path)
        rows: list[tuple[str, str]] = []
        total = 0; operator: bytes | None = None
        for path in sorted(paths):
            trusted(path, directory=path.is_dir())
            if path.is_file():
                need(path.stat().st_size <= LIMIT and len(rows) < 2048, 'CASE_CONFIGURATION_BOUND')
                raw = private(path) if path == infra / 'operator.env' else path.read_bytes()
                total += len(raw); need(total <= 64 * 1024 * 1024, 'CASE_CONFIGURATION_BOUND')
                rows.append((str(path.relative_to(infra)), sha(raw)))
                if path == infra / 'operator.env':
                    operator = raw
        need(bool(rows) and sha(canonical(rows)) == self.intent.configuration_sha256, 'CASE_CONFIGURATION_DRIFT')
        if operator is None:
            raise CaseError('CASE_OPERATOR_MISSING')
        return operator

    def operator_values(self) -> dict[str, str]:
        raw = self.configuration_bytes()
        try:
            return operator_credentials(raw)
        except ValueError as exc:
            raise CaseError('CASE_OPERATOR_ENV') from exc

    def tls_root(self) -> str:
        trusted(self.journal.directory, directory=True)
        need(stat.S_IMODE(self.journal.directory.stat().st_mode) == 0o700, 'CASE_TLS_ROOT_UNSAFE')
        path = self.journal.directory / 'tls'
        need(not path.is_symlink(), 'CASE_TLS_ROOT_UNSAFE')
        if path.exists():
            trusted(path, directory=True)
            need(stat.S_IMODE(path.stat().st_mode) == 0o700, 'CASE_TLS_ROOT_UNSAFE')
        return str(path)

    def capture(self) -> None:
        self.reserve(35)
        self.identity()
        self.reserve(35)
        runner = DetailRunner()
        remaining = min(300.0, self.deadline - time.monotonic() - 5)
        runner.started = runner.clock() - (inventory.MAX_WALL_SECONDS - remaining)
        artifact = inventory.capture(self.intent.source_commit, runner=runner, image_aware=True)
        inventory._validate_artifact(artifact)
        need(artifact['schema_version'] == 6 and len(artifact['incus_executables']) == 1
             and not artifact['lxd_executables'] and not artifact['lxd_projects']
             and [p['project'] for p in artifact['incus_projects']] == ['default'], 'CASE_DAEMON_SCOPE')
        need(artifact['incus_admission']['initial'] == artifact['incus_admission']['final']
             and artifact['incus_admission']['initial']['server_version'] == '6.0.5', 'CASE_API_ADMISSION')
        self.artifact, self.details = artifact, runner.details

    def operations(self) -> None:
        end = min(self.deadline - 5, time.monotonic() + 25)
        while time.monotonic() < end:
            env = self.incus_env()
            result = inventory._detail(inventory.Runner(), ['/usr/bin/incus', '--force-local'], 'server-root', (),
                'default', command_id='wsl_case_root', env=env, safe_args=[])
            inventory._validate_server_root(result, incus=True, cli_version='6.0.5')
            code, raw, _err = inventory.Runner().run(['/usr/bin/incus', '--force-local', 'query', '--request', 'GET',
                '--raw', '/1.0/operations?all-projects=true'], env=env, command_id='wsl_case_operations', safe_args=[])
            envelope = inventory.strict_json(raw)
            need(code == 0, 'CASE_OPERATIONS_SCHEMA')
            if operations_empty(envelope):
                return
            time.sleep(.25)
        raise CaseError('CASE_OPERATIONS_NOT_SETTLED')

    def incus_env(self) -> dict[str, str]:
        runner = inventory.Runner()
        row = inventory._systemctl_show(runner, 'incus.service')
        need(row['active_state'] == 'active' and row['sub_state'] == 'running'
             and inventory._resolve_executable(runner, row) == ('incus_system', 'system:incus'), 'CASE_INCUS_BINDING')
        socket = inventory._systemctl_show(runner, 'incus.socket')
        kind = socket['listen']
        need(kind in {'incus_run', 'incus_var_lib'}, 'CASE_INCUS_SOCKET')
        path = '/run/incus/unix.socket' if kind == 'incus_run' else '/var/lib/incus/unix.socket'
        need(inventory._endpoint(runner, path, unit='incus.service')[1], 'CASE_INCUS_ENDPOINT')
        inventory._require_full_local_access(path, incus=True)
        return inventory.ENV_BASE | {'INCUS_SOCKET': path}

    def prepare(self) -> dict[str, Any]:
        self.phase('prepare')
        need(self.command(['/usr/bin/findmnt', '-T', str(ROOT), '-n', '-o', 'FSTYPE'], 10) == b'ext4\n', 'CASE_PRIVATE_EXT4_REQUIRED')
        pins = self.source(); self.prerequisites(); identity = self.identity(); self.operations(); self.capture()
        if self.intent.case in upgrades.RECIPES:
            self.upgrade_validate_inputs()
        project = self.artifact['incus_projects'][0]
        need(not project['instances'] and not any(p['name'].startswith('tsw-manager-') for p in project['profiles'])
             and not any(p['volumes'] or p['snapshots'] for p in project['pools'])
             and not (ROOT / '.tiny-swarm-world/installation/manifest.json').exists()
             and not (ROOT / '.tiny-swarm-world/installation/profile-operation.json').exists(), 'CASE_FRESH_REQUIRED')
        need(any(i['fingerprint'] == self.intent.ubuntu_fingerprint and i['type'] == 'container' for i in project['images']), 'CASE_IMAGE_PREREQUISITE')
        image = self.details.get(('incus_image_show', (self.intent.ubuntu_fingerprint, 'default')))
        need(isinstance(image, dict) and image.get('architecture') == 'x86_64'
             and image.get('properties', {}).get('os', '').casefold() == 'ubuntu'
             and image.get('properties', {}).get('release') in {'24.04', 'noble'}, 'CASE_UBUNTU_IMAGE_METADATA')
        env = self.incus_env()
        envelope = inventory._parse_json_command(inventory.Runner(), ['/usr/bin/incus', '--force-local', 'query',
            '--request', 'GET', '--raw', '/1.0/images/aliases/ubuntu-24.04?project=default'], env=env,
            command_id='wsl_case_image_alias', safe_args=[])
        need(isinstance(envelope, dict) and set(envelope) == {'type', 'status', 'status_code', 'operation', 'error_code', 'error', 'metadata'}
             and envelope['type'] == 'sync' and envelope['status'] == 'Success' and type(envelope['status_code']) is int
             and envelope['status_code'] == 200 and envelope['operation'] == '' and type(envelope['error_code']) is int
             and envelope['error_code'] == 0 and envelope['error'] == '' and isinstance(envelope['metadata'], dict), 'CASE_IMAGE_ALIAS_SCHEMA')
        alias = envelope['metadata']
        need(set(alias) == {'name', 'target', 'type', 'description'} and alias['name'] == 'ubuntu-24.04'
             and alias['target'] == self.intent.ubuntu_fingerprint and alias['type'] == 'container'
             and type(alias['description']) is str, 'CASE_IMAGE_ALIAS_DRIFT')
        self.incus_env()
        recipe = CASE_RECIPES[self.intent.case]
        preview = validate_preview(self.public(recipe.args(preview=True), timeout=120), recipe)
        baseline = projection(self.artifact, self.details, None, self.intent.ubuntu_fingerprint)
        path = self.intent.home / 'product-campaign-baseline.json'
        if path.exists():
            record = inventory.strict_json(private(path))
            need(set(record) == {'run_id', 'source_commit', 'configuration_sha256', 'ubuntu_fingerprint', 'baseline'}
                 and all(record[k] == getattr(self.intent, k) for k in ('run_id', 'source_commit', 'configuration_sha256', 'ubuntu_fingerprint')), 'CASE_CAMPAIGN_BINDING')
            baseline = record['baseline']
            self.cache_receipt(baseline, record=False)
            need(projection(self.artifact, self.details, None, self.intent.ubuntu_fingerprint, baseline) == baseline, 'CASE_CAMPAIGN_PRESERVATION_DRIFT')
        else:
            Journal(self.intent.home).save(path.name, {k: getattr(self.intent, k) for k in
                ('run_id', 'source_commit', 'configuration_sha256', 'ubuntu_fingerprint')} | {'baseline': baseline})
        return {'schema_version': 1, 'intent_sha256': sha(canonical(asdict(self.intent))), 'pins': pins,
                'identity': identity, 'preview_sha256': sha(canonical(preview)), 'baseline': baseline}

    def admit(self, proposal: dict[str, Any]) -> None:
        need(self.source() == proposal['pins'], 'CASE_SOURCE_DRIFT'); self.prerequisites()
        need(self.identity() == proposal['identity'], 'CASE_IDENTITY_DRIFT')
        self.capture()
        self.cache_receipt(proposal['baseline'], record=False)
        need(projection(self.artifact, self.details, None, self.intent.ubuntu_fingerprint, proposal['baseline']) == proposal['baseline'], 'CASE_BASELINE_DRIFT')
        recipe = CASE_RECIPES[self.intent.case]
        value = validate_preview(self.public(recipe.args(preview=True), timeout=120), recipe)
        need(sha(canonical(value)) == proposal['preview_sha256'], 'CASE_PREVIEW_DRIFT')
        self.proposal = proposal

    def public(self, args: list[str], *, timeout: int, helper: bool = False) -> bytes:
        if not helper and self.intent.case in upgrades.RECIPES:
            upgrades.require_cache_settled(self)
        self.identity()
        if not helper:
            self.cli_pins = self.source()
            if self.proposal is not None:
                need(self.cli_pins == self.proposal['pins'], 'CASE_SOURCE_DRIFT')
            self.reserve(35)
            env = self.incus_env()
            status, raw, error = inventory.Runner().run(['/usr/bin/incus', '--force-local', 'version'],
                command_id='wsl_cli_incus_version', env=env, safe_args=[])
            need(status == 0 and not error and self.incus_env() == env, 'CASE_CLI_INCUS_VERSION_DRIFT')
            self.cli_versions = upgrades.cli_incus_versions(raw)
            need(self.cli_versions == ('6.0.5', '6.0.5'), 'CASE_CLI_INCUS_VERSION_DRIFT')
        argv = [self.interpreter(), '-E', '-s', '-B']
        argv += [str(ROOT / SCRIPT), *args] if helper else ['-c', BOOTSTRAP, *args]
        return self.command(argv, timeout, public=True)

    def upgrade_validate_inputs(self) -> None:
        values = self.operator_values()
        upgrades.proof_credentials(self.intent.case, self.intent.home / 'infra', values)

    def upgrade_children_settled(self) -> bool:
        return self.settled()

    def upgrade_helper(self, stage: str) -> dict[str, Any]:
        self.source(); self.identity()
        raw = self.command([self.interpreter(), '-E', '-s', '-B', str(ROOT / upgrades.SCRIPT),
                            '--case', self.intent.case, '--stage', stage], min(650, max(1, int(self.deadline - time.monotonic() - 20))) if stage == 'cache-targets' else 180, public=True)
        return inventory.strict_json(raw)

    def upgrade_original_proof(self) -> dict[str, Any]:
        return upgrades.original_proof(self)

    def run(self) -> None:
        if self.intent.case in upgrades.RECIPES:
            upgrades.run(self, engine_recovery=self.engine_recovery)
            return
        recipe = CASE_RECIPES[self.intent.case]
        self.public(recipe.args(), timeout=4500)
        if recipe.add_traefik:
            self.public(recipe.args(add=True), timeout=600)
        self.public(['observe'], helper=True, timeout=180)
        model = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.manifest')
        manifest_raw = private(ROOT / '.tiny-swarm-world/installation/manifest.json')
        manifest = model.decode_manifest(manifest_raw)
        wanted = set(recipe.services) | ({'traefik'} if recipe.add_traefik else set())
        need(manifest.schema_version == 2 and set(manifest.requested_services) == wanted
             and manifest.effective_exposure().get('swagger') == (recipe.exposure if 'swagger' in wanted else None)
             and all(o.owner == recipe.owner for o in manifest.effective_stack_ownership().values()), 'CASE_MANIFEST_DRIFT')
        self.cli_selection = upgrades.selection_evidence(manifest, sha(manifest_raw))

    @contextmanager
    def installation_lease(self) -> Iterator[None]:
        module = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock')
        with module.JsonInstallationOperationLock(ROOT).exclusive('cleanup') as lease:
            self.lease = lease
            try:
                yield
            finally:
                self.lease = None

    def prepare_disposal(self) -> None:
        if self.intent.case in upgrades.RECIPES:
            upgrades.require_cache_settled(self)
        saved = self.journal.directory / 'disposal-intent.json'
        if saved.exists():
            value = inventory.strict_json(private(saved))
            value['nodes'] = tuple(disposal.OwnedNode(**row) for row in value['nodes'])
            self.owned = disposal.DisposalIntent(**value)
            return
        checkpoint = ROOT / '.tiny-swarm-world/installation/profile-operation.json'
        if not checkpoint.exists():
            need(not (ROOT / '.tiny-swarm-world/installation/manifest.json').exists(), 'CASE_CREATION_RECEIPT_MISSING')
            self.capture(); need(not self.artifact['incus_projects'][0]['instances'], 'CASE_CREATE_OUTCOME_UNCERTAIN')
            return
        raw, creation = disposal.read_creation(ROOT)
        intended = creation['intent']
        manifest_path = ROOT / '.tiny-swarm-world/installation/manifest.json'
        if manifest_path.exists():
            manifests = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.manifest')
            profile_change = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change')
            manifest = manifests.decode_manifest(private(manifest_path))
            current, manager_uuid, worker_uuids = profile_change.current_evidence(ROOT, manifest)
            need(manager_uuid == creation['instance_uuid'] and worker_uuids == creation['worker_uuids'], 'CASE_CREATION_HISTORY_DRIFT')
            intended = current.model_dump(mode='json')
        models = importlib.import_module('tiny_swarm_world.domain.lifecycle.profile_lifecycle')
        template = models.ManagerCreateIntent.model_validate_json(canonical(intended))
        need(template.image_fingerprint == self.intent.ubuntu_fingerprint and all(w.image_fingerprint == self.intent.ubuntu_fingerprint
             for w in template.workers), 'CASE_CREATION_IMAGE_DRIFT')
        uuids = creation['worker_uuids'] | ({'swarm-manager': creation['instance_uuid']} if creation['instance_uuid'] else {})
        self.capture()
        instances = {a[0]: row for (c, a), row in self.details.items() if c == 'incus_instance_config_show' and a[1:] == ('default',)}
        need(set(instances) == set(uuids), 'CASE_CREATE_OUTCOME_UNCERTAIN')
        binding = template.profile.profile
        if binding is None:
            raise CaseError('CASE_PROFILE_BINDING_MISSING')
        profile_name = binding.profile_name
        profile = self.details.get(('incus_profile_show', (profile_name, 'default')))
        observations = importlib.import_module('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.observations')
        for name, row in instances.items():
            if name == 'swarm-manager':
                state, uuid, exact = observations.owned_instance(row, template)
                need(state in {'running', 'stopped'} and uuid == uuids[name] and exact, 'CASE_CREATE_IDENTITY_DRIFT')
            else:
                observed = observations.worker_state(row, template, observations.worker_intent(template, name))
                need(observed.state in {'running', 'stopped'} and observed.instance_uuid == uuids[name] and observed.no_proxy, 'CASE_CREATE_IDENTITY_DRIFT')
        expected = {'name': profile_name, 'project': 'default', 'description': 'Tiny Swarm World installation profile',
                    'config': template.markers(), 'devices': template.devices()}
        need(profile is None and not instances or profile is not None and all(profile[k] == expected[k]
             for k in ('description', 'config', 'devices')), 'CASE_PROFILE_IDENTITY_DRIFT')
        self.owned = disposal.DisposalIntent(template.profile.installation_id, template.profile.operation_id,
            sha(raw), profile_name, disposal.profile_identity(profile or expected), template.storage_pool,
            tuple(disposal.OwnedNode(n, uuids[n], disposal.specification(instances[n])) for n in disposal.NAMES if n in instances))
        disposal.validate_case_graph(self.graph(self.owned), self.owned)
        self.journal.save('disposal-intent.json', asdict(self.owned))

    def graph(self, intent: disposal.DisposalIntent) -> dict[str, Any]:
        project = self.artifact['incus_projects'][0]
        pool = next(p for p in project['pools'] if p['name'] == intent.pool)
        names = {n.name for n in intent.nodes}
        return {'instances': {a[0]: row for (c, a), row in self.details.items() if c == 'incus_instance_config_show' and a[1:] == ('default',)},
                'profile': self.details.get(('incus_profile_show', (intent.profile_name, 'default'))),
                'volumes': [r for r in pool['volumes'] if r['name'] in names],
                'snapshots': [r for r in pool['snapshots'] if r['parent'] in names],
                'checkpoint_sha256': sha(private(ROOT / '.tiny-swarm-world/installation/profile-operation.json'))}

    def cache_receipt(self, baseline: dict[str, Any], *, record: bool) -> None:
        before = next(p for p in baseline['incus_projects'][0]['pools'] if p['name'] == 'default')['image_cache']
        if any(c['fingerprint'] == self.intent.ubuntu_fingerprint for c in before):
            return
        pool = next(p for p in self.artifact['incus_projects'][0]['pools'] if p['name'] == 'default')
        rows = [c for c in pool['image_cache'] if c['fingerprint'] == self.intent.ubuntu_fingerprint]
        path = self.intent.home / 'product-image-cache-addition.json'
        if path.exists():
            receipt = inventory.strict_json(private(path))
            need(set(receipt) == {'run_id', 'source_commit', 'pool', 'cache'} and receipt['run_id'] == self.intent.run_id
                 and receipt['source_commit'] == self.intent.source_commit and receipt['pool'] == 'default'
                 and rows == [receipt['cache']], 'CASE_IMAGE_CACHE_DRIFT')
        elif rows:
            need(record and self.owned is not None and self.owned.pool == 'default' and len(rows) == 1
                 and rows[0]['owner_project'] == 'default' and rows[0]['content_type'] == 'filesystem', 'CASE_IMAGE_CACHE_UNPROVEN')
            Journal(self.intent.home).save(path.name, {'run_id': self.intent.run_id, 'source_commit': self.intent.source_commit,
                'pool': 'default', 'cache': rows[0]})

    def case_graph(self, intent: disposal.DisposalIntent) -> dict[str, Any]:
        self.operations(); self.capture()
        graph = self.graph(intent); disposal.validate_case_graph(graph, intent)
        if self.proposal is None:
            raise CaseError('CASE_PROPOSAL_MISSING')
        self.cache_receipt(self.proposal['baseline'], record=True)
        need(projection(self.artifact, self.details, intent, self.intent.ubuntu_fingerprint,
             self.proposal['baseline']) == self.proposal['baseline'], 'CASE_FOREIGN_GRAPH_DRIFT')
        return graph

    def incus_effect(self, args: list[str], timeout: int) -> None:
        if self.owned is None or self.lease is None or not self.settled():
            raise CaseError('CASE_DISPOSAL_AUTHORITY_MISSING')
        owned = self.owned
        self.lease.require_active(); self.identity(); self.source()
        names = {n.name for n in owned.nodes}
        allowed = args[:2] == ['--project', 'default'] and (
            len(args) == 6 and args[2] == 'stop' and args[3] in names and args[4:] == ['--timeout', '60']
            or len(args) == 4 and args[2] == 'delete' and args[3] in names
            or args[2:] == ['profile', 'delete', owned.profile_name])
        need(allowed, 'CASE_DISPOSAL_COMMAND_REFUSED')
        env = self.incus_env()
        self.command(['/usr/bin/incus', '--force-local', *args], timeout, extra_env={'INCUS_SOCKET': env['INCUS_SOCKET']})
        self.incus_env()

    def dispose(self) -> None:
        need(self.settled(), 'CASE_WORKER_UNSETTLED'); self.operations(); self.prepare_disposal()
        if self.owned is not None:
            with self.installation_lease():
                disposal.dispose(disposal.IncusDisposalPort(self, self.owned, cast(Any, self.journal)), self.owned)

    def final(self, baseline: dict[str, Any]) -> None:
        self.operations(); self.capture()
        project = self.artifact['incus_projects'][0]
        need(not project['instances'] and not any(p['volumes'] or p['snapshots'] for p in project['pools'])
             and not any(p['name'].startswith('tsw-manager-') for p in project['profiles']), 'CASE_NODES_REMAIN')
        self.cache_receipt(baseline, record=False)
        observed = projection(self.artifact, self.details, self.owned, self.intent.ubuntu_fingerprint, baseline)
        need(observed == baseline, 'CASE_FINAL_PRESERVATION_DRIFT')
        self.cli_final = observed


def start_time(pid: int) -> int:
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    need(len(fields) > 19 and fields[19].isdigit(), 'CASE_CHILD_IDENTITY')
    return int(fields[19])


def group_absent(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
        return False
    except ProcessLookupError:
        return True


def windows_scope(intent: Intent) -> str:
    """Fixed read-only host identity, active binding and running-VHD identity."""
    name = 'TSW-Q440-' + intent.run_id
    # Every interpolated token is a strict identifier/hash; no arbitrary source.
    return r'''$ErrorActionPreference='Stop';$key=Get-Item -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\GUID';
if([Environment]::MachineName -cne 'HOST' -or $key.GetValue('DistributionName') -cne 'NAME' -or $key.GetValue('Version') -ne 2){throw 'scope'};
$names=@((& (Join-Path ([Environment]::GetFolderPath('System')) 'wsl.exe') --list --running --quiet).Replace([string][char]0,'') -split '\r?\n'|Where-Object{$_});
if($LASTEXITCODE -ne 0 -or $names.Count -ne 1 -or $names[0] -cne 'NAME'){throw 'running'};
Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;using Microsoft.Win32.SafeHandles;public static class WslCaseIdentity{[StructLayout(LayoutKind.Sequential,Pack=4)]struct I{public uint a;public long c,t,w;public uint v,h,l,n,ih,il;}[DllImport("kernel32.dll",CharSet=CharSet.Unicode)]static extern SafeFileHandle CreateFile(string p,uint a,uint s,IntPtr x,uint d,uint f,IntPtr t);[DllImport("kernel32.dll")]static extern bool GetFileInformationByHandle(SafeFileHandle h,out I i);public static string Read(string p){using(var h=CreateFile(p,128,7,IntPtr.Zero,3,0x02200000,IntPtr.Zero)){I i;if(h.IsInvalid||!GetFileInformationByHandle(h,out i)||(i.a&1024)!=0||i.n!=1)throw new Exception("identity");return i.v.ToString("x8")+":"+i.ih.ToString("x8")+i.il.ToString("x8")+":"+i.a.ToString("x8")+":"+i.n.ToString("x8");}}}';
$disk=[string]$key.GetValue('VhdFileName','ext4.vhdx');if($disk -cnotmatch '\A[A-Za-z0-9_.-]+\.vhdx\z'){throw 'disk'};
$id=[WslCaseIdentity]::Read((Join-Path ([string]$key.GetValue('BasePath')) $disk));$bytes=[Text.Encoding]::ASCII.GetBytes('"'+$id+'"');
$sha=[Security.Cryptography.SHA256]::Create();try{$hash=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()};
$root=Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)) 'TinySwarmWorld\WslBridge';$state=Join-Path $root 'bridge-state.json';
$service=Get-Service -Name TinySwarmWorldWslBridge;if($service.Status -ne 'Running'){throw 'bridge'};
$item=Get-Item -LiteralPath $state -Force;if($item.Length -gt 2097152 -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'state'};
$s=Get-Content -LiteralPath $state -Raw|ConvertFrom-Json;if($s.bundleId -cne 'BUNDLE' -or $s.agentMode -cne 'windows-service' -or $s.agentStatus -cne 'ready' -or [DateTimeOffset]::Parse([string]$s.generatedAt) -lt [DateTimeOffset]::UtcNow.AddMinutes(-5)){throw 'binding'};
@{guid='GUID';vhd_sha256=$hash;name='NAME';host=[Environment]::MachineName;bundle_id=$s.bundleId;sole_running=$true}|ConvertTo-Json -Compress
'''.replace('GUID', intent.new_guid).replace('HOST', intent.windows_host).replace('NAME', name).replace('BUNDLE', intent.bridge_bundle_id)


def helper(kind: str) -> None:
    if kind == 'prerequisites':
        module = importlib.import_module('tiny_swarm_world.infrastructure.composition_native_preparation')
        async def inspect() -> None:
            incus = await module.build_incus_preparation_service(service_profile='service-access').plan()
            network = await module.build_network_preparation_service(service_profile='service-access').plan()
            need(incus.verified and not incus.actions and not incus.blockers and network.verified
                 and not network.actions and not network.blockers, 'CASE_SHARED_PREPARATION_REQUIRED')
        asyncio.run(inspect())
    else:
        lifecycle = importlib.import_module('tiny_swarm_world.infrastructure.composition_lifecycle').build_installation_lifecycle_service(ROOT)
        manifest = lifecycle.manifests.load().manifest
        need(manifest is not None, 'CASE_MANIFEST_MISSING')
        lock = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock')
        profile = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup')
        management = importlib.import_module('tiny_swarm_world.infrastructure.composition_management')
        consent = importlib.import_module('tiny_swarm_world.domain.preflight').LiveConsent
        backend = importlib.import_module('tiny_swarm_world.domain.node_provider').ManagedLxcBackend.INCUS
        async def observe() -> None:
            with lock.JsonInstallationOperationLock(ROOT).exclusive('recovery') as lease:
                operation = await profile.for_runtime(ROOT, lifecycle, lease, 'recovery', consent(live_flag=True, confirmed=True))
                await operation.verify_effective_routes()
                await management.verify_completed_stacks(ROOT, manifest, backend, node_names=('swarm-manager', 'swarm-worker-1', 'swarm-worker-2'))
        asyncio.run(observe())
    print('{"status":"READ_ONLY_VERIFIED"}')


def finish(port: WslCasePort) -> dict[str, Any]:
    """All original/current case metadata stays retained for coordinator reset."""
    port.phase('recover'); port.source(); port.prerequisites(); identity = port.identity(); port.operations(); port.capture()
    project = port.artifact['incus_projects'][0]
    need(not project['instances'] and not any(p['volumes'] or p['snapshots'] for p in project['pools'])
         and not any(p['name'].startswith('tsw-manager-') for p in project['profiles']), 'CASE_FINISH_NOT_EMPTY')
    if port.proposal is None:
        raise CaseError('CASE_PROPOSAL_MISSING')
    baseline = port.proposal['baseline']
    port.cache_receipt(baseline, record=False)
    need(projection(port.artifact, port.details, None, port.intent.ubuntu_fingerprint, baseline) == baseline, 'CASE_CAMPAIGN_PRESERVATION_DRIFT')
    case_directories = list((port.intent.home / 'cases').iterdir())
    need(len(case_directories) <= len(CASE_RECIPES) and all(path.name in CASE_RECIPES and path.is_dir()
         and not path.is_symlink() for path in case_directories), 'CASE_FINISH_UNKNOWN_CASE')
    ledger = []
    for case in CASE_RECIPES:
        directory = port.intent.home / 'cases' / case / 'journal'
        if not directory.exists():
            continue
        journal = Journal(directory)
        temporary = WslCasePort(port.intent, journal)
        need(temporary.settled(), 'CASE_WORKER_UNSETTLED')
        outcomes = list(directory.glob('outcome-*.json'))
        if not outcomes:
            need(not any(directory.glob('execution-intent-*.json')), 'CASE_FINISH_OUTCOME_UNCERTAIN')
            raw_intent = inventory.strict_json(private(directory.parent / 'intent.json'))
            unexecuted = Intent.parse(raw_intent)
            need(unexecuted.run_id == port.intent.run_id and unexecuted.source_commit == port.intent.source_commit
                 and unexecuted.case == case, 'CASE_FINISH_OUTCOME_UNCERTAIN')
            journal.save('outcome-' + uuid4().hex + '.json', {'status': 'CASE_NOT_IMPLEMENTED' if case in upgrades.RECIPES and upgrades.RECIPES[case].kind == 'product' else 'CASE_NOT_EXECUTED', 'run_id': port.intent.run_id,
                'source_commit': port.intent.source_commit, 'case': case, 'epic_complete': False})
            outcomes = list(directory.glob('outcome-*.json'))
        need(len(outcomes) == 1, 'CASE_FINISH_OUTCOME_UNCERTAIN')
        raw = private(outcomes[0]); value = inventory.strict_json(raw)
        need(value['status'] in {'CASE_PASS_DISPOSED', 'CASE_FAILED_DISPOSED', 'CASE_RECOVERED', 'CASE_NOT_EXECUTED', 'CASE_NOT_EXERCISED', 'CASE_NOT_IMPLEMENTED'} and value['run_id'] == port.intent.run_id
             and value['source_commit'] == port.intent.source_commit and value['case'] == case, 'CASE_FINISH_OUTCOME_UNCERTAIN')
        ledger.append({'case': case, 'outcome_sha256': sha(raw)})
    need(bool(ledger), 'CASE_FINISH_NO_CASES')
    raw = canonical({'schema_version': 2 if any(row['case'] in upgrades.RECIPES for row in ledger) else 1, 'run_id': port.intent.run_id, 'source_commit': port.intent.source_commit, 'cases': ledger})
    campaign = Journal(port.intent.home)
    campaign.save('product-case-ledger.json', inventory.strict_json(raw))
    receipt = {'schema_version': 1, 'run_id': port.intent.run_id, 'source_commit': port.intent.source_commit,
               'kind': 'OWNED_CASES_DISPOSED', 'case_journal_sha256': sha(raw), **{k: identity[k] for k in ('machine_id_sha256', 'boot_id_sha256')}}
    campaign.save('new-case-stop.json', receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'run-case', 'recover', 'prepare-engine-recovery', 'engine-recovery', 'finish', 'observe', 'prerequisites'))
    parser.add_argument('--run-id'); parser.add_argument('--case', choices=tuple(CASE_RECIPES)); parser.add_argument('--intent-sha256'); parser.add_argument('--go-sha256')
    args = parser.parse_args(argv)
    try:
        need(os.geteuid() == 0, 'CASE_ROOT_REQUIRED')
        def interrupted(_number: int, _frame: Any) -> None:
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        sys.path.insert(0, str(ROOT / 'modules/tsw_core/src'))
        if args.mode in {'observe', 'prerequisites'}:
            need(all(v is None for v in (args.run_id, args.case, args.intent_sha256, args.go_sha256)), 'CASE_ARGUMENTS')
            helper(args.mode); return 0
        need(args.run_id is not None and bool(RUN.fullmatch(args.run_id)) and args.case in CASE_RECIPES
             and args.intent_sha256 is not None and bool(HEX.fullmatch(args.intent_sha256)), 'CASE_ARGUMENTS')
        home = BASE / args.run_id / 'cases' / args.case
        raw = private(home / 'intent.json'); need(sha(raw) == args.intent_sha256, 'CASE_INTENT_HASH')
        intent = Intent.parse(inventory.strict_json(raw))
        need(intent.run_id == args.run_id and intent.case == args.case, 'CASE_INTENT_BINDING')
        if intent.case in upgrades.RECIPES and upgrades.RECIPES[intent.case].kind == 'product':
            print(json.dumps({'status': 'NOT_IMPLEMENTED', 'case': intent.case, 'requires': 'S-U2', 'epic_complete': False})); return 2
        journal = Journal(home / 'journal'); port = WslCasePort(intent, journal)
        import fcntl
        fd = os.open(intent.home / 'product-acceptance.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd); need(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                and stat.S_IMODE(info.st_mode) == 0o600, 'CASE_LOCK_UNSAFE')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.mode == 'prepare':
                need(args.go_sha256 is None, 'CASE_ARGUMENTS'); proposal = port.prepare(); journal.save('proposal.json', proposal)
                print(json.dumps({'status': 'PREPARED_READ_ONLY', 'proposal_sha256': sha(canonical(proposal))})); return 0
            if args.mode == 'prepare-engine-recovery':
                port.proposal = inventory.strict_json(private(journal.directory / 'proposal.json'))
                binding = upgrades.engine_binding(port)
                journal.save('engine-recovery-proposal.json', binding)
                print(json.dumps({'status': 'PREPARED_ENGINE_RECOVERY_READ_ONLY', 'engine_binding': binding})); return 0
            need(args.go_sha256 is not None and bool(HEX.fullmatch(args.go_sha256)), 'CASE_GO_HASH')
            proposal_raw = private(journal.directory / 'proposal.json'); proposal = inventory.strict_json(proposal_raw)
            go_raw = private(home / ('engine-recovery-go.json' if args.mode == 'engine-recovery' else 'recovery-go.json' if args.mode in {'recover', 'finish'} else 'run-go.json'))
            need(sha(go_raw) == args.go_sha256, 'CASE_GO_HASH')
            accepted_at = datetime.now(timezone.utc)
            go = inventory.strict_json(go_raw)
            expiry = approval(go, intent, proposal, sha(proposal_raw), recover=args.mode in {'recover', 'finish'},
                              engine_recovery=args.mode == 'engine-recovery', now=accepted_at)
            port.cli_approval = upgrades.approval_receipt(go_raw, go, accepted_at.isoformat())
            port.authorized_until = time.monotonic() + (expiry - datetime.now(timezone.utc)).total_seconds()
            port.proposal = proposal
            if args.mode not in {'recover', 'finish'}:
                port.engine_recovery = args.mode == 'engine-recovery'
                port.purpose_budgets = upgrades.budgets(intent.case, 'wsl', engine_recovery=port.engine_recovery)
                port.total_deadline = time.monotonic() + sum(port.purpose_budgets[k] for k in ('admit', 'case', 'disposal', 'final'))
            if port.engine_recovery:
                need(inventory.strict_json(go_raw)['engine_binding'] == upgrades.engine_binding(port) ==
                    inventory.strict_json(private(journal.directory / 'engine-recovery-proposal.json')), 'UPGRADE_RECOVERY_BINDING_DRIFT')
            if args.mode in {'recover', 'finish'}:
                port.phase('recover')
                need(port.source() == proposal['pins'] and port.identity() == proposal['identity'], 'CASE_RECOVERY_BINDING')
            if args.mode == 'recover' and intent.case in upgrades.RECIPES:
                upgrades.reconcile_cache(port)
            if args.mode == 'finish':
                result = finish(port)
            else:
                need(args.mode in {'recover', 'engine-recovery'} or not any(journal.directory.glob('execution-intent-*.json')), 'CASE_EXECUTION_ALREADY_ATTEMPTED')
                if args.mode == 'recover' and list(journal.directory.glob('outcome-*.json')):
                    port.phase('recover'); need(port.settled(), 'CASE_WORKER_UNSETTLED'); port.final(proposal['baseline'])
                    result = {'status': 'CASE_ALREADY_DISPOSED', 'epic_complete': False}
                else:
                    if port.engine_recovery:
                        port.phase('admit'); port.source(); port.identity()
                        need(port.settled(), 'CASE_WORKER_UNSETTLED')
                        journal.save('engine-recovery-started.json', {'go_sha256': sha(go_raw), 'binding': inventory.strict_json(go_raw)['engine_binding']})
                        port.phase('case')
                        upgrades.run(port, engine_recovery=True)
                        port.phase('disposal'); port.dispose(); port.phase('final'); port.final(proposal['baseline'])
                        result = {'status': 'CASE_RECOVERED', 'scope': 'ENGINE_RECOVERY_ONLY', 'epic_complete': False}
                        port.event('outcome', result)
                    else:
                        result = execute(port, proposal, recover=args.mode == 'recover')
            if result['status'] == 'CASE_PASS_DISPOSED' or args.mode == 'engine-recovery' and result['status'] == 'CASE_RECOVERED':
                upgrades.save_cli_case_result(port, result | {'run_id': intent.run_id,
                    'case': intent.case, 'source_commit': intent.source_commit})
            print(json.dumps(result)); return 0 if result.get('status') not in {'CASE_FAILED_DISPOSED', 'CASE_NOT_EXERCISED', 'CASE_NOT_IMPLEMENTED'} else 2
        finally:
            os.close(fd)
    except BaseException as exc:
        print(json.dumps({'status': 'BLOCKED', 'reason': reason(exc), 'epic_complete': False})); return 2


if __name__ == '__main__':
    raise SystemExit(main())

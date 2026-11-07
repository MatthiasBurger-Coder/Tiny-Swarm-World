#!/usr/bin/env python3
"""One preserving native maintenance transaction; no object adoption or deletion."""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
import fcntl
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
from uuid import uuid4

if TYPE_CHECKING:
    from . import native_runtime_inventory as inventory
    from . import native_lxd_snap_provenance as provenance
    from . import incus_profile_listener_fixture as fixture
else:
    module_prefix = (__package__ + '.') if __package__ else ''
    inventory = importlib.import_module(module_prefix + 'native_runtime_inventory')
    provenance = importlib.import_module(module_prefix + 'native_lxd_snap_provenance')
    fixture = importlib.import_module(module_prefix + 'incus_profile_listener_fixture')

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / fixture.PRIVATE_EVIDENCE_REL
HOST = '192.168.178.33'
DAEMON = 'snap.lxd.daemon.service'
SOCKET = 'snap.lxd.daemon.unix.socket'
NODES = ('swarm-worker-2', 'swarm-worker-1', 'swarm-manager')
SOCKET_PATH = '/var/snap/lxd/common/lxd/unix.socket'
ENV = {'LC_ALL': 'C', 'PATH': '/usr/bin:/bin'}
HEX = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
RUN_ID = re.compile(r'[0-9a-f]{32}\Z', re.ASCII)
FILES = (
    'tools/linux/qualification/native_lxd_maintenance.py',
    'tests/tools/test_native_lxd_maintenance.py',
    'tools/linux/qualification/native_runtime_inventory.py',
    'tools/linux/qualification/native_lxd_snap_provenance.py',
    'tools/linux/qualification/incus_profile_listener_fixture.py',
    'tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py',
    'documentation/handbook/05-development/workflow/issues/issue-449/workflow.md',
)
LIMIT = 8 * 1024 * 1024
HOST_LOCK_PARENT = Path('/run/tsw-epic440-native-maintenance')


class MaintenanceError(Exception):
    """Only fixed symbolic reasons cross the public boundary."""


def require(condition: Any, code: str) -> None:
    if not condition:
        raise MaintenanceError(code)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_private(path: Path) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1
                and info.st_size <= LIMIT, 'PRIVATE_FILE_UNSAFE')
        raw = stream.read(LIMIT + 1)
        require(len(raw) <= LIMIT, 'PRIVATE_FILE_BOUND')
        after = os.fstat(stream.fileno())
        require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                'PRIVATE_FILE_DRIFT')
        return raw


def private_directory(path: Path) -> None:
    require(path.is_absolute(), 'PRIVATE_DIRECTORY_UNSAFE')
    for parent in reversed((path, *path.parents)):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                and not info.st_mode & 0o022, 'PRIVATE_DIRECTORY_UNSAFE')
    require(stat.S_IMODE(path.stat().st_mode) == 0o700, 'PRIVATE_DIRECTORY_MODE')
    # Exact mount observation, not a path-prefix filesystem assumption.
    result = subprocess.run(['/usr/bin/findmnt', '-T', str(path), '-n', '-o', 'FSTYPE'],
                            env=ENV, stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
    require(result.returncode == 0 and result.stdout == b'ext4\n', 'PRIVATE_FILESYSTEM_UNSAFE')


class Journal:
    def __init__(self, directory: Path):
        private_directory(directory)
        self.directory = directory

    def save(self, name: str, value: Any) -> None:
        require(bool(re.fullmatch(r'[a-z0-9-]+\.json', name)), 'JOURNAL_NAME_INVALID')
        raw = canonical(value)
        require(len(raw) <= LIMIT, 'JOURNAL_BOUND')
        fd = os.open(self.directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        directory = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def stopped_nodes(self) -> set[str]:
        paths = list(self.directory.glob('event-*.json'))
        require(len(paths) <= 1024, 'JOURNAL_EVENT_BOUND')
        result: set[str] = set()
        total = 0
        for path in paths:
            raw = read_private(path)
            total += len(raw)
            require(total <= 256 * 1024, 'JOURNAL_EVENT_BOUND')
            value = inventory.strict_json(raw)
            require(isinstance(value, dict) and set(value) == {'intent', 'node', 'utc'}
                    and value['node'] in ('', *NODES), 'JOURNAL_EVENT_INVALID')
            if value['intent'] == 'stop-node':
                require(value['node'] in NODES, 'JOURNAL_EVENT_INVALID')
                result.add(value['node'])
        return result

    def event(self, action: str, node: str = '') -> None:
        require(action in {'stop-node', 'stop-socket', 'shutdown', 'fixture', 'start-daemon',
                           'restore-socket', 'start-node', 'qualification-failed', 'recovery-failed'},
                'JOURNAL_ACTION_INVALID')
        require(node in ('', *NODES), 'NODE_NOT_ALLOWED')
        self.save('event-' + uuid4().hex + '.json', {'intent': action, 'node': node,
                  'utc': datetime.now(timezone.utc).isoformat()})


class Port(Protocol):
    def begin_recovery(self) -> None: ...
    def snapshot(self) -> dict[str, Any]: ...
    def check_binding(self, baseline: dict[str, Any], *, active: bool) -> None: ...
    def node(self, name: str) -> dict[str, str]: ...
    def unit(self, name: str) -> str: ...
    def stop_node(self, name: str) -> None: ...
    def start_node(self, name: str) -> None: ...
    def stop_socket(self) -> None: ...
    def shutdown(self) -> None: ...
    def wait_inactive(self) -> None: ...
    def start_daemon(self) -> None: ...
    def restore_socket(self, state: str) -> None: ...
    def run_fixture(self) -> None: ...


class EventPort(Protocol):
    def stopped_nodes(self) -> set[str]: ...
    def event(self, action: str, node: str = '') -> None: ...


def validate_snapshot(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == {'nodes', 'socket', 'preserve', 'binding'},
            'PRESTATE_SCHEMA_INVALID')
    require(isinstance(value['nodes'], dict) and set(value['nodes']) == set(NODES), 'PRESTATE_NODES_INVALID')
    for row in value['nodes'].values():
        require(isinstance(row, dict) and set(row) == {'status', 'identity'}
                and row['status'] in {'Running', 'Stopped'} and isinstance(row['identity'], str)
                and HEX.fullmatch(row['identity']), 'PRESTATE_NODE_INVALID')
    require(value['socket'] in {'active', 'inactive'} and isinstance(value['binding'], dict)
            and isinstance(value['preserve'], dict), 'PRESTATE_SCHEMA_INVALID')
    return value


class Transaction:
    """Effects have durable intent first; recovery re-observes instead of replaying."""
    def __init__(self, port: Port, journal: EventPort, baseline: dict[str, Any]):
        self.port, self.journal, self.baseline = port, journal, validate_snapshot(baseline)
        self.stops = journal.stopped_nodes()

    def checked_node(self, name: str) -> dict[str, str]:
        row = self.port.node(name)
        require(row.get('identity') == self.baseline['nodes'][name]['identity']
                and row.get('status') in {'Running', 'Stopped'}, 'NODE_IDENTITY_DRIFT')
        return row

    def recover(self) -> None:
        self.port.begin_recovery()
        # Reconcile uncertain shutdown/start outcomes before the next effect.
        state = self.port.unit(DAEMON)
        require(state in {'active', 'inactive'}, 'DAEMON_TRANSITION_UNCERTAIN')
        self.port.check_binding(self.baseline, active=(state == 'active'))
        if state == 'inactive':
            self.journal.event('start-daemon')
            self.port.start_daemon()
        require(self.port.unit(DAEMON) == 'active', 'DAEMON_RECOVERY_FAILED')
        self.port.check_binding(self.baseline, active=True)
        node_failure = False
        for name in reversed(NODES):
            try:
                wanted = self.baseline['nodes'][name]['status']
                current = self.checked_node(name)['status']
                if wanted == 'Running' and current == 'Stopped' and name in self.stops:
                    self.journal.event('start-node', name)
                    self.port.start_node(name)
                    require(self.checked_node(name)['status'] == 'Running', 'NODE_RECOVERY_FAILED')
                else:
                    require(current == wanted, 'NODE_RECOVERY_STATE_DRIFT')
            except Exception:
                # A foreign/drifted node cannot prevent recovery of other own stops.
                node_failure = True
        if self.port.unit(SOCKET) != self.baseline['socket']:
            self.journal.event('restore-socket')
            self.port.restore_socket(self.baseline['socket'])
        require(not node_failure, 'NODE_RECOVERY_STATE_DRIFT')
        require(self.port.snapshot() == self.baseline, 'PRESERVATION_OR_RECOVERY_MISMATCH')

    def execute(self) -> dict[str, str]:
        require(self.port.snapshot() == self.baseline, 'PRESTATE_DRIFT')
        failure = False
        try:
            for name in NODES:
                self.port.check_binding(self.baseline, active=True)
                observed = self.checked_node(name)['status']
                require(observed == self.baseline['nodes'][name]['status'], 'NODE_PRE_EFFECT_STATE_DRIFT')
                if observed == 'Running':
                    self.journal.event('stop-node', name)
                    self.stops.add(name)
                    self.port.stop_node(name)
                    require(self.checked_node(name)['status'] == 'Stopped', 'NODE_STOP_UNCERTAIN')
            stopped = copy.deepcopy(self.baseline)
            for row in stopped['nodes'].values():
                row['status'] = 'Stopped'
            for project in stopped['preserve'].get('lxd_projects', []):
                for instance in project['instances']:
                    instance['status'] = 'Stopped'
            require(self.port.snapshot() == stopped, 'GLOBAL_SHUTDOWN_PRESTATE_DRIFT')
            if self.baseline['socket'] == 'active':
                self.port.check_binding(self.baseline, active=True)
                self.journal.event('stop-socket')
                self.port.stop_socket()
            require(self.port.unit(SOCKET) == 'inactive', 'SOCKET_STOP_UNCERTAIN')
            self.port.check_binding(self.baseline, active=True)
            self.journal.event('shutdown')
            self.port.shutdown()
            self.port.wait_inactive()
            self.port.check_binding(self.baseline, active=False)
            require(self.port.unit(DAEMON) == 'inactive' and self.port.unit(SOCKET) == 'inactive',
                    'DAEMON_REACTIVATED')
            self.journal.event('fixture')
            self.port.run_fixture()
            require(self.port.unit(DAEMON) == 'inactive' and self.port.unit(SOCKET) == 'inactive',
                    'DAEMON_REACTIVATED')
        except BaseException:
            failure = True
            try:
                self.journal.event('qualification-failed')
            except OSError:
                pass  # No further qualification effect; recovery still runs.
        finally:
            try:
                self.recover()
            except BaseException as exc:
                self.journal.event('recovery-failed')
                raise MaintenanceError('RECOVERY_REQUIRED') from exc
        return {'status': 'QUALIFICATION_FAILED_RECOVERED' if failure else 'PASS'}


def bounded(argv: list[str], timeout: int, *, lxd: bool = False, interrupt_grace: int = 0) -> bytes:
    """Only fixed internal callers; terminate owned client processes, never daemons."""
    child_env = ENV | ({'LXD_SOCKET': SOCKET_PATH} if lxd else {})
    if argv[0] == '/usr/bin/git':
        child_env |= {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}
    process = subprocess.Popen(argv, cwd=ROOT, env=child_env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               shell=False, start_new_session=True)
    selector = selectors.DefaultSelector()
    assert process.stdout is not None and process.stderr is not None
    selector.register(process.stdout, selectors.EVENT_READ)
    selector.register(process.stderr, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    output = bytearray()
    total = 0
    timed_out = False
    try:
        while selector.get_map():
            if time.monotonic() >= deadline and interrupt_grace and not timed_out:
                os.killpg(process.pid, signal.SIGINT)
                timed_out = True
                deadline = time.monotonic() + interrupt_grace
            require(time.monotonic() < deadline, 'COMMAND_TIMEOUT_UNCERTAIN')
            for key, _ in selector.select(min(.2, max(.001, deadline - time.monotonic()))):
                chunk = os.read(key.fd, 65536)
                total += len(chunk)
                require(total <= 2 * 1024 * 1024, 'COMMAND_OUTPUT_BOUND')
                if not chunk:
                    selector.unregister(key.fileobj)
                elif key.fileobj is process.stdout:
                    output.extend(chunk)
        status = process.wait(timeout=max(.01, deadline - time.monotonic()))
        require(not timed_out, 'COMMAND_TIMEOUT_UNCERTAIN')
        require(status == 0, 'COMMAND_FAILED_UNCERTAIN')
        return bytes(output)
    finally:
        selector.close()
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def config_projection(row: dict[str, Any], *, instance: bool = False) -> dict[str, Any]:
    # Consumer sets are independently canonicalized by the complete graph.
    result = {key: value for key, value in row.items() if key != 'used_by'}
    if instance:
        for field in ('status', 'status_code', 'last_used_at'):
            result.pop(field, None)
        for field in ('config', 'expanded_config'):
            result[field] = {key: value for key, value in row.get(field, {}).items()
                             if not key.startswith('volatile.') or key in {'volatile.uuid', 'volatile.uuid.generation'}}
        result['expanded_devices'] = row.get('expanded_devices', {})
    return result


class ConfigRunner(inventory.Runner):
    """Retain configuration hashes, never raw metadata, from existing capture calls."""
    def __init__(self) -> None:
        super().__init__()
        self.configs: dict[str, str] = {}

    def run(self, argv: list[str], **kwargs: Any) -> tuple[int, bytes, bytes]:
        result = super().run(argv, **kwargs)
        command = kwargs['command_id']
        if command.endswith(('_show', '_config_show', '_config_show_expanded')) or '_server_root_' in command:
            value = inventory.strict_json(result[1])
            row = value.get('metadata') if isinstance(value, dict) else None
            if isinstance(row, dict) and 'config' in row:
                key = command + ':' + ':'.join(kwargs.get('safe_args', []))
                projection = {'config': row['config']} if '_server_root_' in command else config_projection(row, instance='instance' in command)
                self.configs[key] = digest(canonical(projection))
        return result


class NativePort:
    def __init__(self, source: str, fixture_sha: str, deadline: float):
        self.source, self.fixture_sha, self.deadline = source, fixture_sha, deadline
        self.baseline: dict[str, Any] | None = None
        self.recovering = False

    def budget(self) -> None:
        require(time.monotonic() < self.deadline, 'MAINTENANCE_DEADLINE')

    def command(self, argv: list[str], timeout: int, *, lxd: bool = False, interrupt_grace: int = 0) -> bytes:
        self.budget()
        remaining = int(self.deadline - time.monotonic())
        require(remaining > interrupt_grace, 'MAINTENANCE_DEADLINE')
        return bounded(argv, min(timeout, remaining - interrupt_grace), lxd=lxd, interrupt_grace=interrupt_grace)

    def begin_recovery(self) -> None:
        # Separate reserve; an exhausted qualification budget cannot consume it.
        self.deadline = time.monotonic() + 600
        self.recovering = True

    def unit(self, name: str) -> str:
        self.budget()
        require(name in {DAEMON, SOCKET}, 'UNIT_NOT_ALLOWED')
        row = inventory._systemctl_show(inventory.Runner(), name)
        require(row['load_state'] == 'loaded', 'UNIT_LOAD_DRIFT')
        allowed = {('active', 'running' if name == DAEMON else 'listening'), ('inactive', 'dead')}
        require((row['active_state'], row['sub_state']) in allowed, 'UNIT_TRANSITION_UNCERTAIN')
        return str(row['active_state'])

    def installed_binding(self) -> dict[str, Any]:
        self.budget()
        revision = Path('/snap/lxd/current').resolve(strict=True)
        require(bool(re.fullmatch(r'/snap/lxd/[1-9][0-9]{0,18}', str(revision))), 'SNAP_REVISION_INVALID')
        require(not os.path.lexists('/var/snap/lxd/common/lxd.debug'), 'DEBUG_OVERRIDE_PRESENT')
        fs = provenance.LocalReadOnlyFS()
        values: dict[str, Any] = {}
        for relative in ('meta/snap.yaml', 'commands/lxd', 'commands/daemon.start', 'commands/daemon.stop', 'bin/lxd'):
            observation = fs.observe(str(revision / relative), limit=None if relative == 'bin/lxd' else 1024 * 1024)
            provenance._Proof.trusted(observation, executable=relative != 'meta/snap.yaml', readonly=True)
            values[relative] = {'device': observation.device, 'inode': observation.inode,
                                'sha256': None if relative == 'bin/lxd' else digest(observation.data)}
            if relative == 'meta/snap.yaml':
                metadata = provenance.yaml.load(observation.data, Loader=provenance._UniqueLoader)
                app = metadata['apps']['lxd']
                require(isinstance(app, dict) and app.get('command') == 'commands/lxd'
                        and 'command-chain' not in app, 'SHUTDOWN_APP_UNSUPPORTED')
        values['revision'] = revision.name
        for fixed in (provenance.UNIT_FILE, provenance.DROP_IN,
                      '/etc/systemd/system/' + SOCKET):
            if not os.path.lexists(fixed):
                values[fixed] = None
                continue
            observation = fs.observe(fixed, limit=65536)
            provenance._Proof.trusted(observation)
            values[fixed] = digest(observation.data)
        require(os.readlink('/snap/bin/lxd') == '/usr/bin/snap', 'SNAP_ALIAS_UNVERIFIED')
        raw = self.command(['/usr/bin/systemctl', 'show', DAEMON,
                       '--property=ExecStop,Restart,TimeoutStopUSec,KillMode,SendSIGKILL', '--no-pager'], 10)
        pairs = [line.split('=', 1) for line in raw.decode('ascii').splitlines()]
        require(all(len(pair) == 2 for pair in pairs), 'STOP_PROPERTIES_INVALID')
        props = dict(pairs)
        require(len(props) == len(pairs), 'STOP_PROPERTIES_INVALID')
        require(set(props) == {'ExecStop', 'Restart', 'TimeoutStopUSec', 'KillMode', 'SendSIGKILL'}, 'STOP_PROPERTIES_INVALID')
        pattern = provenance._EXEC_START.pattern.replace('run lxd\\.daemon', 'run --command=stop lxd\\.daemon')
        require(re.fullmatch(pattern, props['ExecStop'], re.ASCII) is not None
                and props['Restart'] == 'on-failure' and props['TimeoutStopUSec'] == '10min'
                and props['KillMode'] == 'control-group' and props['SendSIGKILL'] == 'yes', 'STOP_PROPERTIES_UNSUPPORTED')
        values['stop_properties'] = {key: value for key, value in props.items() if key != 'ExecStop'}
        return values

    def check_binding(self, baseline: dict[str, Any], *, active: bool) -> None:
        self.budget()
        require(self.installed_binding() == baseline['binding']['installed'], 'INSTALLED_BINDING_DRIFT')
        runner = inventory.Runner()
        incus = inventory._systemctl_show(runner, 'incus.service')
        require(incus == baseline['binding']['incus_unit'], 'INCUS_SERVICE_DRIFT')
        require(inventory._resolve_executable(runner, incus) == ('incus_system', 'system:incus'), 'INCUS_IDENTITY_DRIFT')
        row = inventory._systemctl_show(runner, DAEMON)
        require(row['active_state'] == ('active' if active else 'inactive'), 'DAEMON_STATE_DRIFT')
        if active:
            if not self.recovering:
                require(row['main_pid'] == baseline['binding']['lxd_initial_pid'], 'LXD_PROCESS_DRIFT')
            require(inventory._resolve_executable(runner, row) == ('lxd_snap', 'snap:lxd'), 'LXD_IDENTITY_DRIFT')
            fs = provenance.LocalReadOnlyFS()
            installed = baseline['binding']['installed']
            for relative in ('meta/snap.yaml', 'commands/lxd', 'bin/lxd'):
                path = f"/proc/{row['main_pid']}/root/snap/lxd/{installed['revision']}/{relative}"
                observation = fs.observe(path, limit=None if relative == 'bin/lxd' else 1024 * 1024)
                provenance._Proof.trusted(observation, executable=relative != 'meta/snap.yaml', readonly=True)
                seen = {'device': observation.device, 'inode': observation.inode,
                        'sha256': None if relative == 'bin/lxd' else digest(observation.data)}
                require(seen == installed[relative], 'SHUTDOWN_PROCESS_VIEW_DRIFT')
            require(inventory._endpoint(runner, SOCKET_PATH, unit=DAEMON)[1], 'LXD_ENDPOINT_DRIFT')
            inventory._require_full_local_access(SOCKET_PATH, incus=False)

    def node(self, name: str) -> dict[str, str]:
        self.budget()
        require(name in NODES, 'NODE_NOT_ALLOWED')
        if self.baseline is not None:
            self.check_binding(self.baseline, active=True)
        else:
            row = inventory._systemctl_show(inventory.Runner(), DAEMON)
            require(inventory._resolve_executable(inventory.Runner(), row) == ('lxd_snap', 'snap:lxd'), 'LXD_IDENTITY_DRIFT')
            require(inventory._endpoint(inventory.Runner(), SOCKET_PATH, unit=DAEMON)[1], 'LXD_ENDPOINT_DRIFT')
            inventory._require_full_local_access(SOCKET_PATH, incus=False)
        runner = inventory.Runner()
        row = inventory._validate_instance_config(inventory._detail(
            runner, ['/snap/bin/lxc', '--force-local'], 'instances', (name,), 'default',
            command_id='lxd_instance_config_show', env=ENV | {'LXD_SOCKET': SOCKET_PATH}, safe_args=[name, 'default']), name, 'default')
        uuid = row['config'].get('volatile.uuid')
        require(isinstance(uuid, str) and bool(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', uuid)), 'NODE_UUID_UNAVAILABLE')
        require(row['type'] == 'container' and row['status'] in {'Running', 'Stopped'}, 'NODE_STATE_UNSUPPORTED')
        identity = {'uuid': uuid, 'created_at': row['created_at'], 'configuration': config_projection(row, instance=True),
                    'name': name, 'type': row['type'], 'profiles': row['profiles']}
        return {'status': row['status'], 'identity': digest(canonical(identity))}

    def snapshot(self) -> dict[str, Any]:
        self.budget()
        require(self.deadline - time.monotonic() >= 300, 'INVENTORY_RESERVE_MISSING')
        runner = ConfigRunner()
        artifact = inventory.capture(self.source, runner=runner)
        inventory._validate_artifact(artifact)
        require([row['project'] for row in artifact['lxd_projects']] == ['default'], 'LXD_PROJECT_SET_UNSUPPORTED')
        require({row['name'] for row in artifact['lxd_projects'][0]['instances']} == set(NODES), 'LXD_NODE_SET_DRIFT')
        require(len(artifact['lxd_executables']) == 1 and artifact['lxd_executables'][0]['identity_id'] == 'lxd_snap', 'LXD_IDENTITY_DRIFT')
        require(len(artifact['incus_executables']) == 1, 'INCUS_UNAVAILABLE')
        preserve = {key: artifact[key] for key in ('lxd_projects', 'incus_projects', 'lxd_pools', 'incus_pools',
                                                    'lxd_admission', 'incus_admission', 'sockets')}
        preserve['configuration_digests'] = runner.configs
        preserve['incus_units'] = artifact['incus_units']
        preserve['lxd_units'] = [{key: value for key, value in row.items() if key != 'main_pid'}
                                 for row in artifact['lxd_units']]
        binding = {'installed': self.installed_binding(),
                   'incus_unit': next(row for row in artifact['incus_units'] if row['unit'] == 'incus.service'),
                   'lxd_initial_pid': (self.baseline['binding']['lxd_initial_pid'] if self.baseline is not None
                                       else artifact['lxd_executables'][0]['main_pid'])}
        result = {'nodes': {name: self.node(name) for name in NODES}, 'socket': self.unit(SOCKET),
                  'preserve': preserve, 'binding': binding}
        return validate_snapshot(result)

    def stop_node(self, name: str) -> None:
        require(name in NODES, 'NODE_NOT_ALLOWED')
        require(self.baseline is not None, 'PRESTATE_MISSING')
        self.check_binding(cast(dict[str, Any], self.baseline), active=True)
        self.command(['/snap/bin/lxc', '--force-local', 'stop', name, '--project', 'default', '--timeout', '60'], 75, lxd=True)

    def start_node(self, name: str) -> None:
        require(name in NODES and self.baseline is not None, 'NODE_NOT_ALLOWED')
        self.check_binding(cast(dict[str, Any], self.baseline), active=True)
        # The client has a fixed endpoint even when the caller supplies an ambient override.
        self._lxc_start(name)

    def _lxc_start(self, name: str) -> None:
        require(name in NODES, 'NODE_NOT_ALLOWED')
        self.command(['/snap/bin/lxc', '--force-local', 'start', name, '--project', 'default'], 75, lxd=True)

    def stop_socket(self) -> None:
        require(self.baseline is not None, 'PRESTATE_MISSING')
        self.check_binding(cast(dict[str, Any], self.baseline), active=True)
        self.command(['/usr/bin/systemctl', 'stop', SOCKET], 15)

    def shutdown(self) -> None:
        require(self.baseline is not None, 'PRESTATE_MISSING')
        self.check_binding(cast(dict[str, Any], self.baseline), active=True)
        self.command(['/snap/bin/lxd', 'shutdown', '--timeout', '60'], 75)

    def wait_inactive(self) -> None:
        deadline = min(self.deadline, time.monotonic() + 30)
        while time.monotonic() < deadline:
            if self.unit(DAEMON) == 'inactive':
                return
            time.sleep(.2)
        raise MaintenanceError('SHUTDOWN_OUTCOME_UNCERTAIN')

    def start_daemon(self) -> None:
        require(self.baseline is not None, 'PRESTATE_MISSING')
        self.check_binding(cast(dict[str, Any], self.baseline), active=False)
        self.command(['/usr/bin/systemctl', 'start', DAEMON], 90)

    def restore_socket(self, state: str) -> None:
        require(state in {'active', 'inactive'} and self.baseline is not None, 'SOCKET_STATE_INVALID')
        self.check_binding(cast(dict[str, Any], self.baseline), active=True)
        self.command(['/usr/bin/systemctl', 'start' if state == 'active' else 'stop', SOCKET], 15)

    def run_fixture(self) -> None:
        require(self.unit(DAEMON) == 'inactive' and self.unit(SOCKET) == 'inactive', 'DAEMON_REACTIVATED')
        head, _pins = source_pins()
        require(head == self.source, 'SOURCE_HEAD_DRIFT')
        self.command(['/usr/bin/python3', '-E', '-s', '-B', str(ROOT / FILES[4]),
                 '--target-host', HOST, '--expected-approval-sha256', self.fixture_sha], 900, interrupt_grace=120)
        value = inventory.strict_json(read_private(ROOT / fixture.RESULT_REL))
        require(value.get('status') == 'PASS' and value.get('go_sha256') == self.fixture_sha, 'FIXTURE_NOT_PASS')


@contextmanager
def host_lock() -> Iterator[None]:
    parent = HOST_LOCK_PARENT
    try:
        parent.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = parent.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
            'HOST_LOCK_DIRECTORY_UNSAFE')
    fd = os.open(parent / 'maintenance.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o600
                and info.st_nlink == 1, 'HOST_LOCK_UNSAFE')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise MaintenanceError('MAINTENANCE_BUSY') from exc
        yield
    finally:
        os.close(fd)


def source_pins() -> tuple[str, dict[str, str]]:
    head = bounded(['/usr/bin/git', '--no-optional-locks', 'rev-parse', 'HEAD'], 10).decode('ascii').strip()
    require(bool(inventory.HEX40.fullmatch(head)), 'SOURCE_HEAD_INVALID')
    require(not bounded(['/usr/bin/git', '--no-optional-locks', 'status', '--porcelain', '--untracked-files=all'], 10), 'SOURCE_DIRTY')
    pins = {}
    for relative in FILES:
        path = ROOT / relative
        for parent in path.parents:
            info = parent.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022, 'SOURCE_ANCESTOR_UNSAFE')
            if parent == ROOT:
                break
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022, 'SOURCE_FILE_UNSAFE')
        blob = bounded(['/usr/bin/git', '--no-optional-locks', 'show', head + ':' + relative], 10)
        require(blob == path.read_bytes(), 'SOURCE_BLOB_DRIFT')
        pins[relative] = digest(blob)
    return head, pins


def validate_approval(go: Any, proposal: dict[str, Any], proposal_sha: str, source: str,
                      pins: dict[str, str], now: datetime) -> None:
    keys = {'schema_version', 'decision', 'proposal_sha256', 'source_commit', 'pins', 'host_id_sha256',
            'fixture_go_sha256', 'expires_at_utc', 'reviews'}
    require(isinstance(go, dict) and set(go) == keys and type(go['schema_version']) is int
            and go['schema_version'] == 1 and go['decision'] == 'GO', 'APPROVAL_SCHEMA_INVALID')
    require(go['proposal_sha256'] == proposal_sha and go['source_commit'] == source and go['pins'] == pins
            and proposal['source_commit'] == source and proposal['pins'] == pins
            and go['fixture_go_sha256'] == proposal['fixture_go_sha256']
            and go['host_id_sha256'] == proposal['host_id_sha256'], 'APPROVAL_BINDING_MISMATCH')
    require(isinstance(go['reviews'], dict) and set(go['reviews']) == fixture.REVIEW_KEYS
            and all(value == 'APPROVED' for value in go['reviews'].values()), 'APPROVAL_REVIEWS_MISSING')
    require(isinstance(go['expires_at_utc'], str), 'APPROVAL_EXPIRY_INVALID')
    try:
        expiry = datetime.fromisoformat(go['expires_at_utc'])
        require(expiry.tzinfo is not None and 0 < (expiry - now).total_seconds() <= 1800, 'APPROVAL_EXPIRED')
    except ValueError as exc:
        raise MaintenanceError('APPROVAL_EXPIRY_INVALID') from exc
    require(isinstance(proposal, dict) and set(proposal) == {'source_commit', 'pins', 'host_id_sha256',
            'fixture_go_sha256', 'baseline'}, 'PROPOSAL_SCHEMA_INVALID')
    validate_snapshot(proposal['baseline'])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'execute', 'recover'])
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--expected-go-sha256')
    parser.add_argument('--fixture-go-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        require(os.geteuid() == 0, 'ROOT_REQUIRED')
        def interrupted(_number: int, _frame: Any) -> None:
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, interrupted)
        require(bool(RUN_ID.fullmatch(args.run_id)) and bool(HEX.fullmatch(args.fixture_go_sha256)), 'ARGUMENT_INVALID')
        private_directory(PRIVATE)
        source, pins = source_pins()
        fixture_raw = read_private(ROOT / fixture.GO_REL)
        require(digest(fixture_raw) == args.fixture_go_sha256, 'FIXTURE_APPROVAL_DRIFT')
        fixture.validate_go(inventory.strict_json(fixture_raw), argparse.Namespace(target_host=HOST), source,
                            (ROOT / FILES[6]).read_bytes(), (ROOT / FILES[4]).read_bytes(), (ROOT / FILES[5]).read_bytes())
        fixture._assert_host_identity(HOST)
        host_id = digest(Path('/etc/machine-id').read_bytes())
        directory = PRIVATE / ('native-maintenance-' + args.run_id)
        if args.mode != 'prepare':
            private_directory(directory)
            # Fresh approval precedes even host-lock creation; recheck under lock.
            require(isinstance(args.expected_go_sha256, str) and bool(HEX.fullmatch(args.expected_go_sha256)), 'APPROVAL_REQUIRED')
            approval_raw = read_private(directory / 'approval.json')
            require(digest(approval_raw) == args.expected_go_sha256, 'APPROVAL_HASH_MISMATCH')
            proposal_bytes = read_private(directory / 'proposal.json')
            candidate = inventory.strict_json(proposal_bytes)
            validate_approval(inventory.strict_json(approval_raw), candidate, digest(proposal_bytes),
                              source, pins, datetime.now(timezone.utc))
            require(candidate['host_id_sha256'] == host_id, 'HOST_IDENTITY_DRIFT')
        with (host_lock() if args.mode != 'prepare' else nullcontext()):
            if args.mode == 'prepare':
                require(args.expected_go_sha256 is None, 'ARGUMENT_INVALID')
                directory.mkdir(mode=0o700)
                journal = Journal(directory)
                port = NativePort(source, args.fixture_go_sha256, time.monotonic() + 450)
                baseline = port.snapshot()
                proposal = {'source_commit': source, 'pins': pins, 'host_id_sha256': host_id,
                            'fixture_go_sha256': args.fixture_go_sha256, 'baseline': baseline}
                journal.save('proposal.json', proposal)
                print(json.dumps({'status': 'PREPARED_READ_ONLY', 'proposal_sha256': digest(canonical(proposal))}))
                return 0
            require(isinstance(args.expected_go_sha256, str) and bool(HEX.fullmatch(args.expected_go_sha256)), 'APPROVAL_REQUIRED')
            journal = Journal(directory)
            raw = read_private(directory / 'approval.json')
            require(digest(raw) == args.expected_go_sha256, 'APPROVAL_HASH_MISMATCH')
            proposal_raw = read_private(directory / 'proposal.json')
            proposal = inventory.strict_json(proposal_raw)
            validate_approval(inventory.strict_json(raw), proposal, digest(proposal_raw), source, pins, datetime.now(timezone.utc))
            require(proposal['host_id_sha256'] == host_id, 'HOST_IDENTITY_DRIFT')
            port = NativePort(source, args.fixture_go_sha256, time.monotonic() + 1200)
            port.baseline = proposal['baseline']
            transaction = Transaction(port, journal, proposal['baseline'])
            if args.mode == 'execute':
                require(read_private(ROOT / fixture.RESULT_REL) == fixture.NOT_RUN, 'FIXTURE_RESULT_NOT_RESERVED')
                journal.save('started.json', {'proposal_sha256': digest(proposal_raw), 'approval_sha256': digest(raw)})
                result = transaction.execute()
            else:
                require((directory / 'started.json').exists(), 'NO_STARTED_TRANSACTION')
                transaction.recover()
                result = {'status': 'RECOVERED'}
            journal.save('result-' + uuid4().hex + '.json', result)
            print(json.dumps(result))
            return 0 if result['status'] in {'PASS', 'RECOVERED'} else 2
    except BaseException as exc:
        reason = str(exc) if isinstance(exc, MaintenanceError) else 'MAINTENANCE_FAILED_REDACTED'
        print(json.dumps({'status': reason}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Exact Ubuntu image/alias prerequisite, exclusively before a new live baseline."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import importlib
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import socket
import signal
import stat
import struct
import subprocess
import time
from typing import TYPE_CHECKING, Any, Iterator
from urllib.parse import quote

if TYPE_CHECKING:
    from modules.tsw_native_linux.tools.qualification import native_runtime_inventory as inventory
else:
    inventory = importlib.import_module((__package__ + '.' if __package__ else '') + 'native_runtime_inventory')

ROOT = Path(__file__).resolve().parents[5]
FINGERPRINT = '21c802d47e64cedcf7153503a1b5dbcc8821919b2af993646756868b775a5383'
ALIAS = 'ubuntu-24.04'
FILES = (('incus.tar.xz', 680, '58eb156ee168ce406ec7c0ed6501b79c44d9e6962db373e937b71656cbdad687'),
         ('rootfs.squashfs', 141541376, '7857e5e4edaa70e0c3f7cb7da51e1984ebca79d6314443eba44c34c38b9983a3'))
PROPERTIES = {'architecture': 'amd64', 'description': 'Ubuntu noble amd64 (20261107_07:42)',
              'name': 'ubuntu-noble-amd64-default-20261107_07:42', 'os': 'ubuntu',
              'release': 'noble', 'serial': '20261107_07:42', 'variant': 'default'}
SOURCE_FILES = ('modules/tsw_core/tools/linux/qualification/ubuntu_image_prestage.py',
                'modules/tsw_native_linux/tests/tools/test_ubuntu_image_prestage.py',
                'modules/tsw_core/tools/linux/qualification/native_runtime_inventory.py')
ENV = {'LC_ALL': 'C', 'PATH': '/usr/bin:/bin'}
SOCKETS = {'incus_run': '/run/incus/unix.socket', 'incus_var_lib': '/var/lib/incus/unix.socket'}
HEX = re.compile(r'[0-9a-f]{64}\Z')
SCOPE = 'EXACT_UBUNTU_NOBLE_20261107_0742_BEFORE_BASELINE'


class PrestageError(Exception):
    """Fixed safe reason; no raw host output is included."""


def require(condition: Any, reason: str) -> None:
    if not condition:
        raise PrestageError(reason)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


def _trusted_directory(path: Path, *, private: bool = False) -> None:
    require(path.is_absolute(), 'DIRECTORY_UNTRUSTED')
    for candidate in (path, *path.parents):
        info = candidate.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and not info.st_mode & 0o022,
                'DIRECTORY_UNTRUSTED')
    if private:
        require(stat.S_IMODE(path.lstat().st_mode) == 0o700, 'DIRECTORY_NOT_PRIVATE')


def _file_identity(info: os.stat_result) -> tuple[int, ...]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def stream_file(path: Path, size: int, expected: str, combined: Any) -> None:
    """Bound every read; no rootfs-sized allocation or archive extraction."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.geteuid()
                and stat.S_IMODE(before.st_mode) == 0o600 and before.st_nlink == 1 and before.st_size == size,
                'IMAGE_FILE_UNTRUSTED')
        checksum, total = hashlib.sha256(), 0
        while True:
            chunk = os.read(fd, min(65536, size - total + 1))
            if not chunk:
                break
            total += len(chunk)
            require(total <= size, 'IMAGE_SIZE_CHANGED')
            checksum.update(chunk)
            combined.update(chunk)
        require(total == size and checksum.hexdigest() == expected
                and _file_identity(before) == _file_identity(os.fstat(fd)), 'IMAGE_FILE_CHANGED')
    finally:
        os.close(fd)


def verify_bundle(directory: Path) -> None:
    combined = hashlib.sha256()
    for name, size, checksum in FILES:
        stream_file(directory / name, size, checksum, combined)
    require(combined.hexdigest() == FINGERPRINT, 'IMAGE_FINGERPRINT_CHANGED')


class Journal:
    """Private durable CAS; pending effects cannot be executed a second time."""

    def __init__(self, directory: Path):
        self.directory = directory

    def read(self, name: str) -> bytes | None:
        path = self.directory / name
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        except FileNotFoundError:
            return None
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                    and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1 and info.st_size <= 2 * 1024 * 1024,
                    'JOURNAL_UNTRUSTED')
            raw = bytearray()
            while len(raw) <= info.st_size:
                part = os.read(fd, min(65536, info.st_size - len(raw) + 1))
                if not part:
                    break
                raw.extend(part)
            require(len(raw) == info.st_size and _file_identity(info) == _file_identity(os.fstat(fd)), 'JOURNAL_CHANGED')
            return bytes(raw)
        finally:
            os.close(fd)

    def save(self, name: str, value: Any, expected: bytes | None = None) -> bytes:
        require(self.read(name) == expected, 'JOURNAL_CAS_CONFLICT')
        raw = canonical(value)
        require(len(raw) <= 2 * 1024 * 1024, 'JOURNAL_TOO_LARGE')
        temporary = self.directory / (name + '.pending')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            view = memoryview(raw)
            while view:
                count = os.write(fd, view)
                require(count > 0, 'JOURNAL_WRITE_FAILED')
                view = view[count:]
            os.fsync(fd)
        finally:
            os.close(fd)
        require(self.read(name) == expected, 'JOURNAL_CAS_CONFLICT')
        if expected is None:
            os.link(temporary, self.directory / name, follow_symlinks=False)
            temporary.unlink()
        else:
            os.replace(temporary, self.directory / name)
        directory = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return raw


def _source_digest(path: Path) -> str:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.geteuid()
                and not before.st_mode & 0o022 and before.st_nlink == 1 and before.st_size <= inventory.MAX_STREAM,
                'SOURCE_FILE_UNTRUSTED')
        raw = os.read(fd, inventory.MAX_STREAM + 1)
        require(len(raw) == before.st_size and _file_identity(before) == _file_identity(os.fstat(fd)), 'SOURCE_FILE_CHANGED')
        return digest(raw)
    finally:
        os.close(fd)


class Authority:
    """Reuse the accepted Incus daemon/server proof; bind the actual root peer."""

    def __init__(self, source: str, images: Path, state: Path, runner: inventory.Runner | None = None):
        self.source, self.images, self.state = source, images, state
        self.runner = runner or inventory.Runner()
        self.initial = inventory._systemctl_show(self.runner, 'incus.service')
        self.socket_unit = inventory._systemctl_show(self.runner, 'incus.socket')
        require(self.socket_unit['listen'] in SOCKETS, 'INCUS_SOCKET_UNSUPPORTED')
        self.socket_path = SOCKETS[self.socket_unit['listen']]
        self.env = ENV | {'INCUS_SOCKET': self.socket_path}
        self.source_pins = self.check_source()
        self.guard()
        _, raw, err = self.runner.run(['/usr/bin/incus', '--force-local', 'version'], env=self.env, command_id='prestage_version')
        require(not err and sorted(raw.decode('ascii').splitlines()) == ['Client version: 6.0.5', 'Server version: 6.0.5'],
                'INCUS_VERSION_UNSUPPORTED')

    def source_read(self, args: list[str], expected: set[int] = {0}) -> bytes:
        # Git never runs a configured filter/fsmonitor; all command text is fixed.
        require(self.runner.commands < inventory.MAX_COMMANDS, 'SOURCE_BUDGET_EXCEEDED')
        self.runner.commands += 1
        remaining = inventory.MAX_WALL_SECONDS - (self.runner.clock() - self.runner.started)
        require(remaining > 0, 'SOURCE_BUDGET_EXCEEDED')
        env = ENV | {'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1'}
        process = self.runner.popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    env=env, close_fds=True, start_new_session=True)
        outputs = {'out': bytearray(), 'err': bytearray()}
        selector = selectors.DefaultSelector()
        deadline = self.runner.clock() + min(10, remaining)
        try:
            selector.register(process.stdout, selectors.EVENT_READ, 'out')
            selector.register(process.stderr, selectors.EVENT_READ, 'err')
            while selector.get_map():
                require(self.runner.clock() < deadline, 'SOURCE_BUDGET_EXCEEDED')
                for event, _ in selector.select(.1):
                    stream = outputs[event.data]
                    chunk = os.read(event.fd, min(65536, inventory.MAX_STREAM - len(stream) + 1))
                    if not chunk:
                        selector.unregister(event.fileobj)
                    else:
                        stream.extend(chunk)
                        require(len(stream) <= inventory.MAX_STREAM, 'SOURCE_OUTPUT_TOO_LARGE')
            status = process.wait(timeout=max(.01, deadline - self.runner.clock()))
            self.runner.total_bytes += sum(len(value) for value in outputs.values())
            require(self.runner.total_bytes <= inventory.MAX_TOTAL_BYTES and status in expected and not outputs['err'],
                    'SOURCE_PROOF_FAILED')
            require(self.runner.clock() - self.runner.started <= inventory.MAX_WALL_SECONDS, 'SOURCE_BUDGET_EXCEEDED')
            return bytes(outputs['out'])
        finally:
            selector.close()
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
            process.stdout.close()
            process.stderr.close()

    def check_source(self) -> dict[str, str]:
        _trusted_directory(ROOT)
        _trusted_directory(ROOT / '.git')
        base = ['/usr/bin/git', '--no-optional-locks', '-C', str(ROOT)]
        require(self.source_read([*base, 'rev-parse', 'HEAD']).decode('ascii').strip() == self.source,
                'SOURCE_HEAD_CHANGED')
        keys = self.source_read([*base, 'config', '--name-only', '--get-regexp', r'^filter\..*\.(clean|smudge|process|required)$'], {0, 1}).decode('ascii').splitlines()
        require(len(keys) <= 128 and all(re.fullmatch(r'filter\.([A-Za-z0-9][A-Za-z0-9_.-]{0,127})\.(clean|smudge|process|required)', key) for key in keys), 'SOURCE_FILTER_INVALID')
        drivers = sorted({key[len('filter.'):key.rindex('.')] for key in keys})
        suppression = ['-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false']
        for driver in drivers:
            for field in ('clean', 'smudge', 'process', 'required'):
                suppression += ['-c', f'filter.{driver}.{field}=' + ('false' if field == 'required' else '')]
        require(not self.source_read([*base, *suppression, 'status', '--porcelain', '--untracked-files=all']), 'SOURCE_DIRTY')
        pins = {}
        for relative in SOURCE_FILES:
            path = ROOT / relative
            _trusted_directory(path.parent)
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and not info.st_mode & 0o022, 'SOURCE_FILE_UNTRUSTED')
            pins[relative] = _source_digest(path)
        return pins

    def guard(self) -> None:
        require(self.check_source() == self.source_pins, 'SOURCE_CHANGED')
        current = inventory._systemctl_show(self.runner, 'incus.service')
        require(current == self.initial and current['active_state'] == 'active' and current['sub_state'] == 'running'
                and inventory._systemctl_show(self.runner, 'incus.socket') == self.socket_unit, 'INCUS_RUNTIME_CHANGED')
        require(inventory._resolve_executable(self.runner, current) == ('incus_system', 'system:incus'), 'INCUS_IDENTITY_CHANGED')
        require(inventory._endpoint(self.runner, self.socket_path, unit='incus.service')[1], 'INCUS_ENDPOINT_CHANGED')
        inventory._require_full_local_access(self.socket_path, incus=True)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(2)
            client.connect(self.socket_path)
            pid, uid, _gid = struct.unpack('3i', client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        require(type(current['main_pid']) is int and current['main_pid'] > 1 and uid == 0,
                'INCUS_ROOT_PEER_CHANGED')
        if pid != current['main_pid']:
            require(pid == 1, 'INCUS_ROOT_PEER_CHANGED')
            self._activation_peer()
            self._root_proof()

    def _activation_peer(self) -> None:
        listener = self.socket_unit
        endpoint = listener.get('listen')
        require(listener.get('load_state') == 'loaded' and listener.get('active_state') == 'active'
                and listener.get('sub_state') in {'listening', 'running'}
                and isinstance(endpoint, str) and SOCKETS.get(endpoint) == self.socket_path, 'INCUS_ACTIVATION_UNPROVEN')
        try:
            executable = Path(os.readlink('/proc/1/exe'))
            require(str(executable) in {'/usr/lib/systemd/systemd', '/lib/systemd/systemd'}, 'PID1_EXECUTABLE_UNTRUSTED')
            resolved = executable.resolve(strict=True)
            require(str(resolved) in {'/usr/lib/systemd/systemd', '/lib/systemd/systemd'}, 'PID1_EXECUTABLE_UNTRUSTED')
            _trusted_directory(resolved.parent)
            info = resolved.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022
                    and bool(info.st_mode & 0o111), 'PID1_EXECUTABLE_UNTRUSTED')
            with open('/proc/1/status', 'rb') as stream:
                status = stream.read(65537)
            require(len(status) <= 65536, 'PID1_STATUS_UNTRUSTED')
            require([line.split()[1:] for line in status.splitlines() if line.startswith(b'Uid:')]
                    == [[b'0', b'0', b'0', b'0']], 'PID1_STATUS_UNTRUSTED')
        except OSError as exc:
            raise PrestageError('PID1_PROCESS_UNTRUSTED') from exc

    def _raw_query(self, uri: str) -> Any:
        # The caller fixes/validates URI before this primitive; never recurse into guard.
        _, raw, err = self.runner.run(['/usr/bin/incus', '--force-local', 'query', '--request', 'GET', '--raw', uri],
                                     env=self.env, command_id='prestage_inventory')
        value = inventory.strict_json(raw)
        require(not err and isinstance(value, dict) and set(value) == {'type', 'status', 'status_code', 'operation', 'error_code', 'error', 'metadata'}
                and value['type'] == 'sync' and value['status'] == 'Success' and type(value['status_code']) is int
                and value['status_code'] == 200 and value['operation'] == '' and type(value['error_code']) is int
                and value['error_code'] == 0 and value['error'] == '', 'QUERY_FAILED')
        return value['metadata']

    def _root_proof(self) -> None:
        _validate_root_pid(self._raw_query('/1.0'), self.initial['main_pid'])

    def query(self, uri: str) -> Any:
        require(uri in {'/1.0', '/1.0/projects?recursion=1'} or re.fullmatch(
            r'/1\.0/images(?:/aliases)?\?recursion=1&project=[A-Za-z0-9%_.~-]+', uri), 'QUERY_NOT_FIXED')
        self.guard()
        metadata = self._raw_query(uri)
        if uri == '/1.0':
            _validate_root_pid(metadata, self.initial['main_pid'])
        self.guard()
        return metadata

    def effect(self, kind: str) -> None:
        self.guard()
        verify_bundle(self.images)
        if kind == 'import':
            args = ['image', 'import', str(self.images / FILES[0][0]), str(self.images / FILES[1][0])]
        else:
            require(kind == 'alias', 'EFFECT_NOT_FIXED')
            args = ['image', 'alias', 'create', ALIAS, FINGERPRINT]
        _, _out, err = self.runner.run(['/usr/bin/incus', '--force-local', '--quiet', *args, '--project', 'default'],
                                      env=self.env, command_id='prestage_' + kind)
        require(not err, 'EFFECT_UNCERTAIN')
        self.guard()


def _validate_root_pid(root: Any, main_pid: int) -> dict[str, Any]:
    admission = inventory._validate_server_root(root, incus=True, cli_version='6.0.5')
    require(type(main_pid) is int and main_pid > 1 and root['environment']['server_pid'] == main_pid,
            'INCUS_SERVER_PID_CHANGED')
    return admission


def snapshot(authority: Authority) -> dict[str, Any]:
    root = authority.query('/1.0')
    admission = _validate_root_pid(root, authority.initial['main_pid'])
    projects = authority.query('/1.0/projects?recursion=1')
    require(isinstance(projects, list) and 0 < len(projects) <= 1000, 'PROJECTS_INVALID')
    result: dict[str, Any] = {}
    default_seen = False
    for project in projects:
        require(isinstance(project, dict) and {'name', 'description', 'config', 'used_by'} <= set(project)
                and not set(project) - {'name', 'description', 'config', 'used_by', 'access_entitlements'}, 'PROJECTS_INVALID')
        name = inventory._name(project['name'])
        inventory._string_map(project['config'])
        require(isinstance(project['description'], str), 'PROJECTS_INVALID')
        if 'access_entitlements' in project:
            inventory._strings(project['access_entitlements'])
        feature = project['config'].get('features.images')
        require(feature in {None, 'true', 'false'}, 'IMAGE_PROJECT_SCOPE_UNSUPPORTED')
        inherited = name != 'default' and feature != 'true'
        default_seen = default_seen or name == 'default'
        key = digest(name.encode())
        require(key not in result, 'PROJECT_DUPLICATE')
        images = authority.query('/1.0/images?recursion=1&project=' + quote(name, safe=''))
        aliases = authority.query('/1.0/images/aliases?recursion=1&project=' + quote(name, safe=''))
        require(isinstance(images, list) and len(images) <= 1000 and isinstance(aliases, list) and len(aliases) <= 8192,
                'IMAGE_COLLECTION_INVALID')
        alias_map, wanted = {}, None
        for alias in aliases:
            require(isinstance(alias, dict) and set(alias) == {'name', 'description', 'target', 'type'}
                    and all(type(value) is str for value in alias.values())
                    and alias['name'] and alias['type'] in {'container', 'virtual-machine'}
                    and HEX.fullmatch(alias['target']), 'ALIAS_SCHEMA_INVALID')
            alias_key = digest(alias['name'].encode())
            require(alias_key not in alias_map, 'ALIAS_DUPLICATE')
            alias_map[alias_key] = digest(alias)
            if alias['name'] == ALIAS:
                wanted = alias
        image_map: dict[str, str] = {}
        image_aliases: dict[str, dict[str, str]] = {}
        for image in images:
            require(isinstance(image, dict), 'IMAGE_SCHEMA_INVALID')
            fp = inventory._fingerprint(image.get('fingerprint'))
            require(fp not in image_map, 'IMAGE_DUPLICATE')
            inventory._image_projection(image, fp, 'default' if inherited else name)
            normalized = dict(image)
            entries = [] if image['aliases'] is None else image['aliases']
            for entry in entries:
                require(entry['name'] not in image_aliases, 'IMAGE_ALIAS_DUPLICATE')
                image_aliases[entry['name']] = {'name': entry['name'], 'description': entry['description'],
                                               'target': fp, 'type': image['type']}
            normalized['aliases'] = sorted([entry for entry in entries if not (
                fp == FINGERPRINT and (inherited or name == 'default') and entry['name'] == ALIAS)], key=lambda row: row['name'])
            image_map[fp] = digest(normalized)
            if fp == FINGERPRINT and name == 'default':
                require(image['type'] == 'container' and image['architecture'] == 'x86_64'
                        and image['properties'] == PROPERTIES, 'PINNED_IMAGE_METADATA_MISMATCH')
        require(all(alias['target'] in image_map for alias in aliases), 'ALIAS_TARGET_MISSING')
        require(image_aliases == {alias['name']: alias for alias in aliases}, 'IMAGE_ALIAS_RECIPROCITY_INVALID')
        if name == 'default' and wanted is not None:
            require(wanted['target'] == FINGERPRINT and wanted['type'] == 'container', 'ALIAS_COLLISION')
        project_data = dict(project)
        refs = inventory._consumer_refs(project['used_by'], name)
        image_ref = {'kind': 'images', 'name': FINGERPRINT, 'project': 'default'}
        target_link = name == 'default' and image_ref in refs
        project_data['used_by'] = [ref for ref in refs if not (name == 'default' and ref == image_ref)]
        if name == 'default':
            require(target_link == (FINGERPRINT in image_map), 'IMAGE_PROJECT_MEMBERSHIP_INVALID')
        result[key] = {'default': name == 'default', 'inherited': inherited, 'project_sha256': digest(project_data),
                       'images': image_map, 'aliases': alias_map, 'wanted_alias_sha256': digest(wanted) if wanted is not None else None,
                       'target_link': target_link}
    require(default_seen and authority.query('/1.0') == root, 'SERVER_OR_PROJECT_DRIFT')
    default_views = [row for row in result.values() if row['default']]
    require(len(default_views) == 1, 'DEFAULT_PROJECT_INVALID')
    for row in result.values():
        if row['inherited']:
            require(all(row[field] == default_views[0][field] for field in (
                'images', 'aliases', 'wanted_alias_sha256')), 'INHERITED_IMAGE_VIEW_DRIFT')
    return {'server_sha256': digest(root), 'admission_sha256': digest(admission), 'projects': result}


def _validate_view(value: Any) -> None:
    require(isinstance(value, dict) and set(value) == {'server_sha256', 'admission_sha256', 'projects'}
            and all(isinstance(value[key], str) and HEX.fullmatch(value[key]) for key in ('server_sha256', 'admission_sha256'))
            and isinstance(value['projects'], dict) and 0 < len(value['projects']) <= 1000, 'SNAPSHOT_SCHEMA_INVALID')
    defaults = 0
    for key, row in value['projects'].items():
        require(isinstance(key, str) and HEX.fullmatch(key) and isinstance(row, dict) and set(row) == {
            'default', 'inherited', 'project_sha256', 'images', 'aliases', 'wanted_alias_sha256', 'target_link'}, 'SNAPSHOT_SCHEMA_INVALID')
        require(all(type(row[field]) is bool for field in ('default', 'inherited', 'target_link'))
                and not (row['default'] and row['inherited']) and isinstance(row['project_sha256'], str)
                and HEX.fullmatch(row['project_sha256']), 'SNAPSHOT_SCHEMA_INVALID')
        defaults += int(row['default'])
        for field in ('images', 'aliases'):
            require(isinstance(row[field], dict) and len(row[field]) <= 8192 and all(
                isinstance(name, str) and HEX.fullmatch(name) and isinstance(checksum, str) and HEX.fullmatch(checksum)
                for name, checksum in row[field].items()), 'SNAPSHOT_SCHEMA_INVALID')
        wanted = row['wanted_alias_sha256']
        require(wanted is None or isinstance(wanted, str) and HEX.fullmatch(wanted), 'SNAPSHOT_SCHEMA_INVALID')
        require(wanted == row['aliases'].get(digest(ALIAS.encode())), 'SNAPSHOT_SCHEMA_INVALID')
    require(defaults == 1, 'DEFAULT_PROJECT_INVALID')


def preserved(before: dict[str, Any], after: dict[str, Any], *, alias_added: bool) -> None:
    _validate_view(before)
    _validate_view(after)
    require(set(before) == {'server_sha256', 'admission_sha256', 'projects'} and set(after) == set(before)
            and before['server_sha256'] == after['server_sha256']
            and before['admission_sha256'] == after['admission_sha256']
            and set(before['projects']) == set(after['projects']), 'PRESTATE_DRIFT')
    wanted_key = digest(ALIAS.encode())
    expected_alias = digest({'name': ALIAS, 'target': FINGERPRINT, 'type': 'container', 'description': ''})
    for key, old in before['projects'].items():
        current = after['projects'][key]
        require(set(old) == {'default', 'inherited', 'project_sha256', 'images', 'aliases', 'wanted_alias_sha256', 'target_link'}
                and set(current) == set(old) and all(old[field] == current[field] for field in ('default', 'inherited', 'project_sha256')),
                'PROJECT_METADATA_CHANGED')
        owns_view = old['default'] or old['inherited']
        require(all(current['images'].get(fp) == value for fp, value in old['images'].items()), 'PREEXISTING_IMAGE_CHANGED')
        require(set(current['images']) - set(old['images']) == ({FINGERPRINT} - set(old['images']) if owns_view else set()),
                'UNEXPECTED_IMAGE_ADDITION')
        expected_aliases = dict(old['aliases'])
        if owns_view and alias_added and wanted_key not in expected_aliases:
            expected_aliases[wanted_key] = expected_alias
        require(current['aliases'] == expected_aliases, 'PREEXISTING_ALIAS_CHANGED')
        expected_wanted = expected_aliases.get(wanted_key)
        require(current['wanted_alias_sha256'] == expected_wanted, 'ALIAS_READBACK_INVALID')
        require(current['target_link'] == (True if old['default'] else old['target_link']), 'PROJECT_MEMBERSHIP_CHANGED')


def _default(view: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in view['projects'].values() if row['default']]
    require(len(rows) == 1, 'DEFAULT_PROJECT_INVALID')
    return rows[0]


def _machine_digest() -> str:
    fd = os.open('/etc/machine-id', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022 and info.st_size <= 64,
                'HOST_IDENTITY_INVALID')
        raw = os.read(fd, 65)
        require(re.fullmatch(b'[0-9a-f]{32}\n?', raw) and _file_identity(info) == _file_identity(os.fstat(fd)),
                'HOST_IDENTITY_INVALID')
        return digest(raw)
    finally:
        os.close(fd)


class Prestager:
    def __init__(self, authority: Authority, journal: Journal):
        self.authority, self.journal = authority, journal

    def prepare(self) -> dict[str, Any]:
        verify_bundle(self.authority.images)
        self.authority.guard()
        before = snapshot(self.authority)
        machine_sha256 = _machine_digest()
        plan = {'schema_version': 1, 'scope': SCOPE, 'source_commit': self.authority.source,
                'source_pins': self.authority.source_pins, 'host_sha256': machine_sha256,
                'unit_sha256': digest(self.authority.initial), 'socket_sha256': digest(self.authority.socket_unit),
                'image_fingerprint': FINGERPRINT, 'alias': ALIAS, 'input_files': [list(row) for row in FILES],
                'transport_authentication': 'HTTPS_AND_SHA256_ONLY', 'signature_verified': False,
                'before': before, 'baseline_recapture_required': True}
        self.journal.save('proposal.json', plan)
        return {'status': 'PROPOSAL_ONLY', 'plan_sha256': digest(plan), 'image_fingerprint': FINGERPRINT,
                'alias': ALIAS, 'signature_verified': False, 'baseline_recapture_required': True}

    def _plan(self, expected: str) -> tuple[dict[str, Any], bytes]:
        raw = self.journal.read('proposal.json')
        if raw is None:
            raise PrestageError('PLAN_BINDING_CHANGED')
        require(HEX.fullmatch(expected) and digest(raw) == expected, 'PLAN_BINDING_CHANGED')
        plan = inventory.strict_json(raw)
        require(isinstance(plan, dict) and set(plan) == {'schema_version', 'scope', 'source_commit', 'source_pins',
            'host_sha256', 'unit_sha256', 'socket_sha256', 'image_fingerprint', 'alias', 'input_files',
            'transport_authentication', 'signature_verified', 'before', 'baseline_recapture_required'}
            and type(plan['schema_version']) is int and plan['schema_version'] == 1 and plan['scope'] == SCOPE
            and plan['source_commit'] == self.authority.source and plan['source_pins'] == self.authority.source_pins
            and plan['host_sha256'] == _machine_digest()
            and plan['unit_sha256'] == digest(self.authority.initial) and plan['socket_sha256'] == digest(self.authority.socket_unit)
            and plan['image_fingerprint'] == FINGERPRINT and plan['alias'] == ALIAS
            and plan['input_files'] == [list(row) for row in FILES] and plan['signature_verified'] is False
            and plan['transport_authentication'] == 'HTTPS_AND_SHA256_ONLY' and plan['baseline_recapture_required'] is True,
            'PLAN_SCHEMA_INVALID')
        _validate_view(plan['before'])
        self.authority.guard()
        verify_bundle(self.authority.images)
        return plan, raw

    def execute(self, expected: str) -> dict[str, Any]:
        plan, _ = self._plan(expected)
        require(self.journal.read('intent.json') is None and self.journal.read('result.json') is None, 'REPLAY_REFUSED')
        require(snapshot(self.authority) == plan['before'], 'PRESTATE_DRIFT')
        default = _default(plan['before'])
        present = FINGERPRINT in default['images']
        alias_present = default['wanted_alias_sha256'] is not None
        state: bytes | None = None
        if not present:
            state = self.journal.save('intent.json', {'schema_version': 1, 'plan_sha256': expected, 'stage': 'import_pending'})
            self.authority.effect('import')
            after = snapshot(self.authority)
            preserved(plan['before'], after, alias_added=False)
            state = self.journal.save('intent.json', {'schema_version': 1, 'plan_sha256': expected, 'stage': 'import_verified'}, state)
        if not alias_present:
            current = snapshot(self.authority)
            preserved(plan['before'], current, alias_added=False)
            state = self.journal.save('intent.json', {'schema_version': 1, 'plan_sha256': expected, 'stage': 'alias_pending'}, state)
            self.authority.effect('alias')
        final = snapshot(self.authority)
        preserved(plan['before'], final, alias_added=True)
        if state is not None:
            self.journal.save('intent.json', {'schema_version': 1, 'plan_sha256': expected, 'stage': 'complete'}, state)
        return self._result(expected, 'ALREADY_PRESENT_VERIFIED' if present and alias_present else 'PRESTAGED_VERIFIED')

    def reconcile(self, expected: str) -> dict[str, Any]:
        plan, _ = self._plan(expected)
        raw = self.journal.read('intent.json')
        if raw is None:
            raise PrestageError('RECONCILE_INTENT_MISSING')
        intent = inventory.strict_json(raw)
        require(isinstance(intent, dict) and set(intent) == {'schema_version', 'plan_sha256', 'stage'}
                and type(intent['schema_version']) is int and intent['schema_version'] == 1
                and intent['plan_sha256'] == expected and isinstance(intent['stage'], str) and intent['stage'] in {
                    'import_pending', 'import_verified', 'alias_pending', 'complete'}, 'INTENT_INVALID')
        current = snapshot(self.authority)
        complete = _default(current)['wanted_alias_sha256'] is not None
        if intent['stage'] in {'alias_pending', 'complete'}:
            require(complete, 'EFFECT_STILL_UNCERTAIN')
        preserved(plan['before'], current, alias_added=complete)
        if complete:
            if intent['stage'] != 'complete':
                self.journal.save('intent.json', {'schema_version': 1, 'plan_sha256': expected, 'stage': 'complete'}, raw)
            existing = self.journal.read('result.json')
            if existing is not None:
                result = inventory.strict_json(existing)
                require(result == self._result_value(expected, 'PRESTAGED_VERIFIED') or
                        result == self._result_value(expected, 'RECONCILED_VERIFIED'), 'RESULT_CHANGED')
                return result
            return self._result(expected, 'RECONCILED_VERIFIED')
        require(intent['stage'] in {'import_pending', 'import_verified'}, 'EFFECT_STILL_UNCERTAIN')
        self.journal.save('intent.json', {'schema_version': 1, 'plan_sha256': expected, 'stage': 'import_verified'}, raw)
        return self._result_value(expected, 'IMAGE_ONLY_VERIFIED_ALIAS_NOT_WRITTEN')

    def _result_value(self, plan: str, status: str) -> dict[str, Any]:
        return {'scope': SCOPE, 'status': status, 'plan_sha256': plan, 'image_fingerprint': FINGERPRINT,
                'alias': ALIAS, 'preexisting_images_and_aliases_preserved': True,
                'signature_verified': False, 'services_verified': False, 'baseline_recapture_required': True,
                'allowed_image_cache_addition': FINGERPRINT}

    def _result(self, plan: str, status: str) -> dict[str, Any]:
        value = self._result_value(plan, status)
        self.journal.save('result.json', value)
        return value


@contextmanager
def host_lock() -> Iterator[None]:
    # Same global lock as native maintenance; image writes cannot overlap its pause.
    parent = Path('/run/tsw-epic440-native-maintenance')
    parent.mkdir(mode=0o700, exist_ok=True)
    info = parent.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700, 'LOCK_UNTRUSTED')
    fd = os.open(parent / 'maintenance.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600,
                'LOCK_UNTRUSTED')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PrestageError('MAINTENANCE_BUSY') from exc
        yield
    finally:
        os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'execute', 'reconcile'))
    parser.add_argument('--image-directory', required=True, type=Path)
    parser.add_argument('--state-directory', required=True, type=Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--expected-plan-sha256')
    parser.add_argument('--before-new-baseline', required=True, action='store_true')
    args = parser.parse_args(argv)
    try:
        require(os.geteuid() == 0 and re.fullmatch(r'[0-9a-f]{40}', args.source_commit), 'ROOT_OR_SOURCE_REQUIRED')
        _trusted_directory(args.image_directory, private=True)
        _trusted_directory(args.state_directory, private=True)
        with host_lock():
            authority = Authority(args.source_commit, args.image_directory, args.state_directory)
            for directory in (args.image_directory, args.state_directory):
                require(authority.source_read(['/usr/bin/findmnt', '-T', str(directory), '-n', '-o', 'FSTYPE']) == b'ext4\n',
                        'PRIVATE_EXT4_REQUIRED')
            operation = Prestager(authority, Journal(args.state_directory))
            if args.mode == 'prepare':
                require(args.expected_plan_sha256 is None, 'ARGUMENT_INVALID')
                result = operation.prepare()
            else:
                if args.expected_plan_sha256 is None:
                    raise PrestageError('ARGUMENT_INVALID')
                result = (operation.execute if args.mode == 'execute' else operation.reconcile)(args.expected_plan_sha256)
        print(canonical(result).decode())
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, (PrestageError, inventory.InventoryError)) else 'PRESTAGE_REFUSED_OR_UNCERTAIN'
        print(canonical({'scope': SCOPE, 'status': 'REFUSED_OR_UNCERTAIN', 'code': code,
                         'services_verified': False, 'baseline_recapture_required': True}).decode())
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

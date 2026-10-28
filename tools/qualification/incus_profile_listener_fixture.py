#!/usr/bin/env python3
"""Fail-closed, explicitly authorized Incus listener qualification fixture."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import math
import os
import re
import selectors
import stat
import subprocess
import sys
import time
from urllib.parse import quote, unquote
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TRUSTED_BIN = {'incus': '/usr/bin/incus', 'ip': '/usr/sbin/ip', 'ss': '/usr/bin/ss', 'uname': '/usr/bin/uname', 'free': '/usr/bin/free', 'df': '/usr/bin/df', 'curl': '/usr/bin/curl', 'git': '/usr/bin/git'}
TRUSTED_PATH = '/usr/sbin:/usr/bin:/sbin:/bin'
PRIVATE_EVIDENCE_REL = Path('.tiny-swarm/evidence/issue-449/s449-private-20261027')
GO_REL = PRIVATE_EVIDENCE_REL / 'three-amigos-s02-live-go.json'
RESULT_REL = PRIVATE_EVIDENCE_REL / 'r67-incus-6.0.5-listener-fixture.json'
GO_KEYS = {'decision','source_commit','workflow_sha256','runner_sha256','test_sha256','resource_admission_sha256','issue447_inventory_sha256','target','proxy','cleanup','reviews','windows_rules_unchanged','external_routes_enabled','default_profile_sha256','default_profile_used_by','approved_route_state_sha256','fixture_base_profile_sha256'}
TARGET_KEYS = {'host','endpoint','project','server_version','run_id','profile','base_profile','instance','image_fingerprint'}
PROXY_KEYS = {'listen','connect','bind'}
REVIEW_KEYS = {'requirements','architecture','security','devops','test_evidence'}
HASH64 = re.compile(r'^[0-9a-f]{64}$')
HASH40 = re.compile(r'^[0-9a-f]{40}$')
RUN_ID = re.compile(r'^[0-9a-f]{32}$')
MOUNTINFO_ESCAPE = re.compile(r'\\(040|011|012|134)')
NOT_RUN = b'{"status":"NOT_RUN"}\n'
SUPPORTED_PROXY_PROTOCOL_PAIRS = {
    ('tcp', 'tcp'), ('udp', 'udp'), ('unix', 'unix'),
    ('tcp', 'unix'), ('unix', 'tcp'), ('udp', 'tcp'),
    ('tcp', 'udp'), ('udp', 'unix'), ('unix', 'udp'),
}
_SECRET_CONFIG_KEY = re.compile(r'(?i)(password|passphrase|secret|token|credential|private[_-]?key)')
_INVENTORY_COMMAND_MAX_BYTES = 2 * 1024 * 1024
_INVENTORY_MAX_ENTITIES = 10_000
_INVENTORY_ARTIFACT_MAX_BYTES = 8 * 1024 * 1024
_INVENTORY_MAX_COMMANDS = 256
_INVENTORY_TOTAL_COMMAND_MAX_BYTES = 16 * 1024 * 1024
_INVENTORY_HOST_COMMAND_TIMEOUT_SECONDS = 30
_INVENTORY_TOTAL_TIMEOUT_SECONDS = 300
_INVENTORY_CLEANUP_COMMAND_RESERVE = 32
_INVENTORY_CLEANUP_BYTE_RESERVE = 8 * 1024 * 1024
_INVENTORY_CLEANUP_ENTITY_RESERVE = 5_000
_INVENTORY_CLEANUP_TIMEOUT_RESERVE_SECONDS = 60
_INVENTORY_BYTES_CAPTURED = 0
_INVENTORY_ENTITIES_CAPTURED = 0
_INVENTORY_STARTED_AT: float | None = None
_INVENTORY_RESERVE_CLEANUP = False
_INVENTORY_CLEANUP_MODE = False
_PROJECT_BOOLEAN_KEYS = {
    'features.images', 'features.profiles', 'features.storage.volumes', 'features.networks',
}

_COMMAND_AUDIT: list[dict[str, Any]] = []
_WINDOWS_SNAPSHOT_METADATA: dict[str, Any] = {}


def _inventory_budgets() -> tuple[int, int, int, float]:
    reserve = _INVENTORY_RESERVE_CLEANUP and not _INVENTORY_CLEANUP_MODE
    return (
        _INVENTORY_MAX_COMMANDS - (_INVENTORY_CLEANUP_COMMAND_RESERVE if reserve else 0),
        _INVENTORY_TOTAL_COMMAND_MAX_BYTES - (_INVENTORY_CLEANUP_BYTE_RESERVE if reserve else 0),
        _INVENTORY_MAX_ENTITIES - (_INVENTORY_CLEANUP_ENTITY_RESERVE if reserve else 0),
        _INVENTORY_TOTAL_TIMEOUT_SECONDS - (_INVENTORY_CLEANUP_TIMEOUT_RESERVE_SECONDS if reserve else 0),
    )

class FixtureError(Exception):
    """A safe, reportable failure code."""

class TargetDrift(FixtureError):
    """Post-reservation target state differs from approved state."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise FixtureError('INVALID_GO_DUPLICATE_KEY')
        out[key] = value
    return out


def strict_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(FixtureError('INVALID_GO_CONSTANT')))
    except FixtureError:
        raise
    except (UnicodeError, ValueError, TypeError) as exc:
        raise FixtureError('INVALID_GO_JSON') from exc


def safe_parent(path: Path, create: bool = False) -> None:
    if create:
        _require_private_ext4(ROOT)
    rel = path.parent.relative_to(ROOT)
    current = ROOT
    for part in rel.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if create:
                current.mkdir(mode=0o700)
                mode = current.lstat().st_mode
            else:
                raise FixtureError('UNSAFE_PARENT_PATH')
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise FixtureError('UNSAFE_PARENT_PATH')
    resolved = current.resolve(strict=True)
    if resolved != ROOT and ROOT not in resolved.parents:
        raise FixtureError('UNSAFE_PARENT_PATH')
    if resolved != path.parent.resolve(strict=True):
        raise FixtureError('UNSAFE_PARENT_PATH')


def _decode_mountinfo_field(value: str) -> str:
    escapes = {'040': ' ', '011': '\t', '012': '\n', '134': '\\'}
    return MOUNTINFO_ESCAPE.sub(lambda match: escapes[match.group(1)], value)


def _require_private_ext4(path: Path, mountinfo_path: Path = Path('/proc/self/mountinfo')) -> None:
    """Require private runtime evidence to live on a verifiable local ext4 mount."""
    requested = Path(os.path.abspath(path))
    forbidden_roots = (Path('/mnt/c'), Path('/mnt/d'))
    if any(requested == root or root in requested.parents for root in forbidden_roots):
        raise FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')
    try:
        resolved = requested.resolve(strict=True)
        raw_mountinfo = mountinfo_path.read_text(encoding='utf-8')
    except (OSError, RuntimeError) as exc:
        raise FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNVERIFIABLE') from exc

    matches: list[tuple[int, Path, str]] = []
    try:
        for line in raw_mountinfo.splitlines():
            before, separator, after = line.partition(' - ')
            if not separator:
                raise ValueError('missing mountinfo separator')
            fields = before.split()
            filesystem_fields = after.split()
            if len(fields) < 5 or not filesystem_fields:
                raise ValueError('incomplete mountinfo row')
            mountpoint = Path(_decode_mountinfo_field(fields[4]))
            filesystem_type = filesystem_fields[0]
            if resolved == mountpoint or mountpoint in resolved.parents:
                matches.append((len(mountpoint.parts), mountpoint, filesystem_type))
    except (IndexError, ValueError) as exc:
        raise FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNVERIFIABLE') from exc
    if not matches:
        raise FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNVERIFIABLE')
    deepest_length = max(match[0] for match in matches)
    deepest = [match for match in matches if match[0] == deepest_length]
    if len(deepest) != 1:
        # Multiple rows for the active mountpoint can represent a stacked or
        # otherwise ambiguous overmount. Do not guess which filesystem owns it.
        raise FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNVERIFIABLE')
    _, mountpoint, filesystem_type = deepest[0]
    if filesystem_type != 'ext4':
        raise FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')
    # Explicitly reject DrvFS even if a malformed or synthetic mountinfo row
    # reports an ext4 filesystem type for a Windows drive mountpoint.
    if mountpoint == Path('/mnt/c') or mountpoint == Path('/mnt/d'):
        raise FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')


def _require_private_evidence_dir(path: Path) -> None:
    expected = ROOT / PRIVATE_EVIDENCE_REL
    if path.parent != expected:
        raise FixtureError('UNSAFE_PRIVATE_EVIDENCE_PATH')
    safe_parent(path)
    try:
        info = expected.stat(follow_symlinks=False)
    except OSError as exc:
        raise FixtureError('UNSAFE_PRIVATE_EVIDENCE_DIR') from exc
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise FixtureError('UNSAFE_PRIVATE_EVIDENCE_DIR')
    _require_private_ext4(expected)

def read_once(path: Path) -> bytes:
    safe_parent(path)
    if path == ROOT / GO_REL:
        _require_private_evidence_dir(path)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise FixtureError('GO_UNREADABLE') from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise FixtureError('GO_NOT_REGULAR')
        if path == ROOT / GO_REL and (info.st_uid != os.geteuid()
                                     or stat.S_IMODE(info.st_mode) != 0o600):
            raise FixtureError('GO_FILE_NOT_PRIVATE')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            return stream.read()
    finally:
        os.close(fd)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_profile_sha256(config: dict[str, Any], devices: dict[str, Any]) -> str:
    def validate(value: Any) -> None:
        if value is None or isinstance(value, (bool, str)):
            if isinstance(value, str):
                value.encode('utf-8', errors='strict')
            return
        if isinstance(value, int):
            return
        if isinstance(value, float):
            if not math.isfinite(value):
                raise FixtureError('DEFAULT_PROFILE_CANONICALIZATION_FAILED')
            return
        if isinstance(value, list):
            for item in value:
                validate(item)
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise FixtureError('DEFAULT_PROFILE_CANONICALIZATION_FAILED')
                key.encode('utf-8', errors='strict')
                validate(item)
            return
        raise FixtureError('DEFAULT_PROFILE_CANONICALIZATION_FAILED')
    try:
        validate(config)
        validate(devices)
        raw = json.dumps({'config': config, 'devices': devices}, sort_keys=True,
                         separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (UnicodeError, TypeError, ValueError) as exc:
        raise FixtureError('DEFAULT_PROFILE_CANONICALIZATION_FAILED') from exc
    return digest(raw)


_SAFE_DEVICE_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,62}')


def _derive_fixture_base(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return only the explicitly safe, string-valued source settings."""
    source_config = profile.get('config')
    source_devices = profile.get('devices')
    if not isinstance(source_config, dict) or not isinstance(source_devices, dict):
        raise TargetDrift('DEFAULT_PROFILE_UNREADABLE')
    config: dict[str, str] = {}
    for key, value in source_config.items():
        if key == 'limits.cpu':
            if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]*', value):
                raise TargetDrift('DEFAULT_PROFILE_CONFIG_UNAPPROVED')
            config[key] = value
        elif key == 'limits.memory':
            if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]*(KiB|MiB|GiB)?', value):
                raise TargetDrift('DEFAULT_PROFILE_CONFIG_UNAPPROVED')
            config[key] = value
        elif key == 'boot.autostart':
            if not isinstance(value, str) or value not in {'true', 'false'}:
                raise TargetDrift('DEFAULT_PROFILE_CONFIG_UNAPPROVED')
        else:
            raise TargetDrift('DEFAULT_PROFILE_CONFIG_UNAPPROVED')
    config['boot.autostart'] = 'false'
    devices: dict[str, dict[str, str]] = {}
    for name, device in source_devices.items():
        if name == 'root':
            if (not isinstance(device, dict) or set(device) != {'type', 'path', 'pool'}
                    or device.get('type') != 'disk' or device.get('path') != '/'
                    or not isinstance(device.get('pool'), str)
                    or not _SAFE_DEVICE_ID.fullmatch(device['pool'])):
                raise TargetDrift('DEFAULT_PROFILE_DEVICE_UNAPPROVED')
            devices['root'] = {'type': 'disk', 'path': '/', 'pool': device['pool']}
        elif name == 'eth0':
            if (not isinstance(device, dict) or set(device) != {'type', 'name', 'network'}
                    or device.get('type') != 'nic' or device.get('name') != 'eth0'
                    or not isinstance(device.get('network'), str)
                    or not _SAFE_DEVICE_ID.fullmatch(device['network'])):
                raise TargetDrift('DEFAULT_PROFILE_DEVICE_UNAPPROVED')
            devices['eth0'] = {'type': 'nic', 'name': 'eth0', 'network': device['network']}
        else:
            raise TargetDrift('DEFAULT_PROFILE_DEVICE_UNAPPROVED')
    return {'config': config, 'devices': devices}


def _json_entity_count(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + sum(_json_entity_count(key) + _json_entity_count(item)
                       for key, item in value.items())
    if isinstance(value, list):
        return 1 + sum(_json_entity_count(item) for item in value)
    return 1


def approved_route_state_sha256(listeners_10001: list[bytes],
                                incus_10001_routes: list[dict[str, Any]],
                                windows_snapshot: bytes,
                                incus_projects: list[str] | None = None) -> str:
    tuples = _safe_listener_tuples(listeners_10001)
    payload = {
        'listeners_10001_count': len(tuples),
        'listeners_10001_sha256': digest(json.dumps(
            tuples, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')),
        'incus_projects': sorted(incus_projects or []),
        'incus_10001_routes': sorted(incus_10001_routes,
                                     key=lambda item: (item['project'], item['owner_type'],
                                                       item['owner'], item['device'])),
        'windows_snapshot_sha256': digest(windows_snapshot) if windows_snapshot else '',
    }
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=False).encode('utf-8')
    return digest(raw)


def _pack_windows_snapshot(firewall: bytes, portproxy: bytes) -> bytes:
    """Keep exact Windows state in memory without a text/base64 representation."""
    return len(firewall).to_bytes(8, 'big') + firewall + len(portproxy).to_bytes(8, 'big') + portproxy


def _strict_devices(value: Any, code: str, *, allow_implicit_bind: bool = False) -> dict[str, dict[str, Any]]:
    if (not isinstance(value, dict)
            or any(not isinstance(name, str) or not name or not isinstance(device, dict)
                   for name, device in value.items())):
        raise TargetDrift(code)
    for device in value.values():
        if not isinstance(device.get('type'), str) or not device['type']:
            raise TargetDrift(code)
        if device['type'] == 'proxy':
            try:
                listen_protocol, _ = _parse_proxy_endpoint(device.get('listen'))
                connect_protocol, _ = _parse_proxy_endpoint(device.get('connect'))
            except TargetDrift as exc:
                raise TargetDrift(code) from exc
            if (listen_protocol, connect_protocol) not in SUPPORTED_PROXY_PROTOCOL_PAIRS:
                raise TargetDrift(code)
            nat = device.get('nat', False)
            if nat is True or nat == 'true':
                if (listen_protocol, connect_protocol) not in {('tcp', 'tcp'), ('udp', 'udp')}:
                    raise TargetDrift(code)
            elif nat is not False and nat != 'false':
                raise TargetDrift(code)
            if ('bind' in device and (not isinstance(device['bind'], str)
                                      or device['bind'] not in {'host', 'instance'})):
                raise TargetDrift(code)
            if 'bind' not in device and not allow_implicit_bind:
                raise TargetDrift(code)
    return value


def _parse_proxy_endpoint(value: Any) -> tuple[str, list[tuple[int, int]]]:
    if not isinstance(value, str) or not value:
        raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
    if value.startswith('unix:'):
        path = value.removeprefix('unix:')
        pathname = PurePosixPath(path)
        valid_path = (path.startswith('/') and path != '/' and not path.endswith('/')
                      and pathname.name not in {'.', '..'})
        valid_abstract = path.startswith('@') and len(path) > 1
        if '\x00' in path or not (valid_path or valid_abstract):
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
        return 'unix', []
    try:
        protocol, endpoint = value.split(':', 1)
    except ValueError as exc:
        raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED') from exc
    if protocol not in {'tcp', 'udp'} or ':' not in endpoint:
        raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
    address, port_spec = endpoint.rsplit(':', 1)
    if not address or not port_spec:
        raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
    if address == '0.0.0.0':
        pass
    elif address.startswith('[') and address.endswith(']'):
        literal = address[1:-1]
        try:
            parsed = ipaddress.ip_address(literal)
        except ValueError as exc:
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED') from exc
        if not isinstance(parsed, ipaddress.IPv6Address) or '%' in literal:
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
        if parsed.is_unspecified and address != '[::]':
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
    else:
        if address.startswith('[') or address.endswith(']') or '%' in address:
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as exc:
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED') from exc
        if isinstance(parsed, ipaddress.IPv6Address):
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
    intervals: list[tuple[int, int]] = []
    for index, item in enumerate(port_spec.split(',')):
        match = re.fullmatch(r'([0-9]+)(?:-([0-9]+))?', item)
        if not match:
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
        if index and match.group(2) is not None:
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
        first = int(match.group(1))
        last = int(match.group(2) or match.group(1))
        if not 1 <= first <= last <= 65535:
            raise TargetDrift('INCUS_PROXY_LISTEN_MALFORMED')
        intervals.append((first, last))
    return protocol, intervals


def _is_approved_10001_proxy(listen: str) -> bool:
    """Recognize only the approved singleton TCP/10001 listener tuple."""
    protocol, intervals = _parse_proxy_endpoint(listen)
    if protocol == 'unix':
        return False
    includes_10001 = any(first <= 10001 <= last for first, last in intervals)
    if not includes_10001:
        return False
    if protocol != 'tcp' or intervals != [(10001, 10001)] or listen.rsplit(':', 1)[1] != '10001':
        raise TargetDrift('INCUS_10001_ROUTE_UNAPPROVED')
    return True


def _listener_rows(raw: bytes, port: int) -> list[bytes]:
    matches: list[bytes] = []
    try:
        for row in raw.splitlines():
            columns = row.split()
            if len(columns) < 5:
                raise TargetDrift('LISTENER_INVENTORY_UNREADABLE')
            endpoint = columns[3].decode('ascii', errors='strict')
            match = re.search(r':([0-9]+)$', endpoint)
            if not match:
                raise TargetDrift('LISTENER_INVENTORY_UNREADABLE')
            if int(match.group(1)) == port:
                matches.append(row)
    except (UnicodeError, IndexError) as exc:
        raise TargetDrift('LISTENER_INVENTORY_UNREADABLE') from exc
    return matches


def _safe_listener_tuples(rows: list[bytes]) -> list[dict[str, Any]]:
    """Project raw ss rows onto the allowlisted listener schema."""
    result = []
    for row in rows:
        columns = row.split()
        if len(columns) < 5:
            raise TargetDrift('LISTENER_INVENTORY_UNREADABLE')
        try:
            state = columns[0].decode('ascii', errors='strict').upper()
            protocol = 'tcp'
            endpoint = columns[3].decode('ascii', errors='strict')
            match = re.search(r':([0-9]+)$', endpoint)
            if state != 'LISTEN' or match is None:
                raise ValueError
            address, port = endpoint.rsplit(':', 1)
            address = address.strip('[]')
            ipaddress.ip_address(address)
            port_value = int(port)
            if not 1 <= port_value <= 65535:
                raise ValueError
        except (UnicodeError, ValueError) as exc:
            raise TargetDrift('LISTENER_INVENTORY_UNREADABLE') from exc
        result.append({'protocol': protocol, 'local_address': address, 'local_port': port_value})
    return sorted(result, key=lambda item: (item['protocol'], item['local_address'], item['local_port']))


def _listener_digest(raw: bytes, port: int) -> tuple[list[dict[str, Any]], str]:
    tuples = _safe_listener_tuples(_listener_rows(raw, port))
    canonical = json.dumps(tuples, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False).encode('utf-8')
    return tuples, digest(canonical)


def _assert_approved_route_state(go: dict[str, Any], listeners_10001: list[bytes],
                                 incus_10001_routes: list[dict[str, Any]],
                                 windows_snapshot: bytes, incus_projects: list[str]) -> None:
    observed = approved_route_state_sha256(listeners_10001, incus_10001_routes,
                                           windows_snapshot, incus_projects)
    if observed != go['approved_route_state_sha256']:
        raise TargetDrift('APPROVED_ROUTE_STATE_DRIFT')


def _exact_keys(value: Any, keys: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise FixtureError(code)
    return value


def _hash(value: Any, pattern: re.Pattern[str], code: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise FixtureError(code)
    return value


def validate_go(go: Any, args: argparse.Namespace, head: str, workflow: bytes, runner: bytes, tests: bytes) -> dict[str, Any]:
    go = _exact_keys(go, GO_KEYS, 'INVALID_GO_KEYS')
    if go['decision'] != 'GO':
        raise FixtureError('INVALID_DECISION')
    if not isinstance(go['source_commit'], str) or not HASH40.fullmatch(go['source_commit']) or go['source_commit'] != head:
        raise FixtureError('SOURCE_HEAD_MISMATCH')
    bindings = {'workflow_sha256': workflow, 'runner_sha256': runner, 'test_sha256': tests}
    for key, raw in bindings.items():
        expected = _hash(go[key], HASH64, 'INVALID_GO_HASH')
        if expected != digest(raw):
            raise FixtureError('SOURCE_BINDING_MISMATCH')
    for key in ('resource_admission_sha256', 'issue447_inventory_sha256', 'default_profile_sha256',
                'fixture_base_profile_sha256', 'approved_route_state_sha256'):
        _hash(go[key], HASH64, 'INVALID_GO_HASH')
    target = _exact_keys(go['target'], TARGET_KEYS, 'INVALID_TARGET_KEYS')
    if any(not isinstance(v, str) for v in target.values()):
        raise FixtureError('INVALID_TARGET_TYPES')
    run_id = target['run_id']
    if not RUN_ID.fullmatch(run_id):
        raise FixtureError('INVALID_RUN_ID')
    if target != {
        'host': args.target_host, 'endpoint': 'unix://', 'project': 'default',
        'server_version': '6.0.5', 'run_id': run_id,
        'profile': f'tsw-q449-{run_id}-profile',
        'base_profile': f'tsw-q449-{run_id}-base',
        'instance': f'tsw-q449-{run_id}-fixture',
        'image_fingerprint': target['image_fingerprint'],
    } or args.target_host not in {'192.168.178.33', '192.168.178.58'}:
        raise FixtureError('TARGET_BINDING_MISMATCH')
    _hash(target['image_fingerprint'], HASH64, 'INVALID_IMAGE_FINGERPRINT')
    proxy = _exact_keys(go['proxy'], PROXY_KEYS, 'INVALID_PROXY_KEYS')
    if any(not isinstance(v, str) for v in proxy.values()) or proxy['bind'] != 'host' or proxy['connect'] != 'tcp:127.0.0.1:8080':
        raise FixtureError('INVALID_PROXY')
    match = re.fullmatch(r'tcp:127\.0\.0\.1:(\d+)', proxy['listen'])
    if not match or not 61000 <= int(match.group(1)) <= 65535 or int(match.group(1)) == 10001:
        raise FixtureError('INVALID_LISTEN')
    if go['cleanup'] != [target['instance'], target['profile'], target['base_profile']] or not isinstance(go['cleanup'], list):
        raise FixtureError('INVALID_CLEANUP')
    reviews = _exact_keys(go['reviews'], REVIEW_KEYS, 'INVALID_REVIEW_KEYS')
    if any(v != 'APPROVED' for v in reviews.values()):
        raise FixtureError('REVIEWS_NOT_APPROVED')
    if go['windows_rules_unchanged'] is not True or go['external_routes_enabled'] is not False:
        raise FixtureError('INVALID_ROUTE_FLAGS')
    consumers = go['default_profile_used_by']
    if (not isinstance(consumers, list) or any(not isinstance(v, str) for v in consumers)
            or consumers != sorted(set(consumers))):
        raise FixtureError('INVALID_CONSUMERS')
    return go


def command(argv: list[str]) -> bytes:
    argv = list(argv)
    if argv == ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                '-NoProfile', '-NonInteractive', '-Command', _WINDOWS_ACTIVE_STORE_QUERY]:
        return _snapshot_process(argv, 120, 14 * 1024 * 1024, 2 * 1024 * 1024,
                                 'WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
    if argv == ['/mnt/c/Windows/System32/netsh.exe', 'interface', 'portproxy', 'show', 'all']:
        return _snapshot_process(argv, 30, 2 * 1024 * 1024, 2 * 1024 * 1024,
                                 'WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
    if (argv and argv[0] == 'incus' and len(argv) > 1
            and (argv[1] in {'query', 'list', 'info'}
                 or argv[1:3] in (['project', 'list'], ['profile', 'list'],
                                  ['image', 'list'], ['image', 'info']))):
        raw = _inventory_command(argv)
        parsed = strict_json(raw)
        _account_inventory_entities(_json_entity_count(parsed), 'INCUS_INVENTORY_UNREADABLE')
        return raw
    if argv and argv[0] in TRUSTED_BIN:
        argv[0] = TRUSTED_BIN[argv[0]]
    if not argv or not os.path.isabs(argv[0]):
        raise TargetDrift('UNTRUSTED_EXECUTABLE')
    try:
        result = subprocess.run(argv, cwd=ROOT, env={'PATH': TRUSTED_PATH, 'LANG': 'C.UTF-8'}, check=False, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TargetDrift('JIT_COMMAND_FAILED') from exc
    _COMMAND_AUDIT.append(_safe_command_record(argv, result.returncode, len(result.stdout), 0))
    if result.returncode:
        raise TargetDrift('JIT_COMMAND_FAILED')
    return result.stdout


_WINDOWS_ACTIVE_STORE_QUERY = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$profiles = @(Get-NetFirewallProfile -PolicyStore ActiveStore | Sort-Object Name | Select-Object *)
$settings = @(Get-NetFirewallSetting -PolicyStore ActiveStore | Select-Object *)
$rules = @(Get-NetFirewallRule -PolicyStore ActiveStore | Sort-Object Name | ForEach-Object {
  $rule = $_
  [ordered]@{
    rule = $rule | Select-Object *
    profiles = @(Get-NetFirewallProfile -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
    address = @(Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
    application = @(Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
    interface = @(Get-NetFirewallInterfaceFilter -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
    interface_type = @(Get-NetFirewallInterfaceTypeFilter -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
    port = @(Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
    security = @(Get-NetFirewallSecurityFilter -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
    service = @(Get-NetFirewallServiceFilter -AssociatedNetFirewallRule $rule -PolicyStore ActiveStore | Select-Object *)
  }
})
[ordered]@{profiles=$profiles;settings=$settings;rules=$rules} | ConvertTo-Json -Depth 100 -Compress
'''.strip()


def _snapshot_process(argv: list[str], timeout_seconds: float, stdout_limit: int,
                      stderr_limit: int, failure_code: str) -> bytes:
    """Capture one allowlisted Windows snapshot process under shared budgets."""
    global _INVENTORY_BYTES_CAPTURED, _INVENTORY_STARTED_AT
    command_limit, byte_limit, _, total_timeout = _inventory_budgets()
    if len(_COMMAND_AUDIT) >= command_limit:
        raise TargetDrift('INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED')
    now = time.monotonic()
    if _INVENTORY_STARTED_AT is None:
        _INVENTORY_STARTED_AT = now
    if now - _INVENTORY_STARTED_AT > total_timeout:
        raise TargetDrift('INCUS_INVENTORY_TOTAL_TIMEOUT')
    process = None
    selector = None
    stdout, stderr = bytearray(), bytearray()
    started = time.monotonic()
    try:
        process = subprocess.Popen(argv, cwd=ROOT, env={'PATH': TRUSTED_PATH, 'LANG': 'C.UTF-8'},
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert process.stdout is not None and process.stderr is not None
        selector = selectors.DefaultSelector()
        for stream, target, cap in ((process.stdout, stdout, stdout_limit),
                                    (process.stderr, stderr, stderr_limit)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, (target, cap))
        process_deadline = started + timeout_seconds
        aggregate_deadline = _INVENTORY_STARTED_AT + total_timeout
        deadline = min(process_deadline, aggregate_deadline)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining < 0:
                raise TimeoutError
            for key, _ in selector.select(min(max(remaining, 0.001), 0.25)):
                target, cap = key.data
                aggregate_remaining = byte_limit - _INVENTORY_BYTES_CAPTURED - len(stdout) - len(stderr)
                read_size = min(65536, cap - len(target) + 1, aggregate_remaining + 1)
                chunk = os.read(key.fd, read_size)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                target.extend(chunk)
                if len(target) > cap or len(stdout) + len(stderr) + _INVENTORY_BYTES_CAPTURED > byte_limit:
                    raise OverflowError
        remaining = deadline - time.monotonic()
        if remaining < 0:
            raise TimeoutError
        exit_status = process.wait(timeout=max(0.001, remaining))
    except (TimeoutError, subprocess.TimeoutExpired) as exc:
        total_timeout_exceeded = (aggregate_deadline <= process_deadline
                                  and time.monotonic() > aggregate_deadline)
        if process is not None:
            _kill_and_reap(process, failure_code)
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, len(stdout), len(stderr)))
        if total_timeout_exceeded:
            raise TargetDrift('INCUS_INVENTORY_TOTAL_TIMEOUT') from exc
        raise TargetDrift('WINDOWS_SNAPSHOT_TIMEOUT') from exc
    except OverflowError as exc:
        if process is not None:
            _kill_and_reap(process, failure_code)
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, len(stdout), len(stderr)))
        raise TargetDrift('WINDOWS_SNAPSHOT_OUTPUT_TOO_LARGE') from exc
    except OSError as exc:
        if process is not None:
            _kill_and_reap(process, failure_code)
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, len(stdout), len(stderr)))
        raise TargetDrift('WINDOWS_SNAPSHOT_COMMAND_FAILED') from exc
    except Exception as exc:
        if process is not None:
            _kill_and_reap(process, failure_code)
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, len(stdout), len(stderr)))
        raise TargetDrift('WINDOWS_SNAPSHOT_COMMAND_FAILED') from exc
    except BaseException:
        if process is not None:
            _kill_and_reap(process, failure_code)
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, len(stdout), len(stderr)))
        raise
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()
    duration_ms = int((time.monotonic() - started) * 1000)
    _COMMAND_AUDIT.append(_safe_command_record(argv, exit_status, len(stdout), len(stderr)) |
                          {'duration_ms': duration_ms})
    _INVENTORY_BYTES_CAPTURED += len(stdout) + len(stderr)
    if exit_status:
        raise TargetDrift('WINDOWS_SNAPSHOT_COMMAND_FAILED')
    if time.monotonic() - _INVENTORY_STARTED_AT > total_timeout:
        raise TargetDrift('INCUS_INVENTORY_TOTAL_TIMEOUT')
    return bytes(stdout)


def _safe_command_record(argv: list[str], status: int | None,
                         stdout_bytes: int, stderr_bytes: int) -> dict[str, Any]:
    executable = Path(argv[0]).name if argv else 'unknown'
    operation = argv[1] if len(argv) > 1 and re.fullmatch(r'[a-z][a-z0-9-]{0,31}', argv[1]) else 'other'
    command_id = f'{executable}.{operation}'
    return {'command_id': command_id, 'safe_args': [], 'exit_status': status,
            'stdout_bytes': stdout_bytes, 'stderr_bytes': stderr_bytes}


def _kill_and_reap(process: subprocess.Popen[bytes], error_code: str) -> None:
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=0.5)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise TargetDrift(error_code) from exc


def git_preflight() -> tuple[str, bytes, bytes, bytes]:
    def git(*args: str) -> bytes:
        try:
            r = subprocess.run([TRUSTED_BIN['git'], *args], cwd=ROOT, env={'PATH': TRUSTED_PATH, 'LANG': 'C.UTF-8'}, check=False, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise FixtureError('GIT_INSPECTION_FAILED') from exc
        if r.returncode:
            raise FixtureError('GIT_INSPECTION_FAILED')
        return r.stdout
    head = git('rev-parse', '--verify', 'HEAD').decode('ascii').strip()
    if not HASH40.fullmatch(head) or git('status', '--porcelain', '--untracked-files=all'):
        raise FixtureError('CHECKOUT_NOT_CLEAN')
    wf = git('show', 'HEAD:documentation/workflow/issues/issue-449/workflow.md')
    runner = git('show', 'HEAD:tools/qualification/incus_profile_listener_fixture.py')
    tests = git('show', 'HEAD:tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py')
    return head, wf, runner, tests


def reserve_and_recheck() -> tuple[int, Path]:
    evidence = ROOT / RESULT_REL
    safe_parent(evidence, create=True)
    _require_private_evidence_dir(evidence)
    lock = evidence.with_suffix(evidence.suffix + '.reservation')
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        lock_info = os.fstat(fd)
        if (not stat.S_ISREG(lock_info.st_mode) or lock_info.st_uid != os.geteuid()
                or stat.S_IMODE(lock_info.st_mode) != 0o600):
            os.close(fd)
            raise FixtureError('RESERVATION_NOT_PRIVATE')
        os.write(fd, b'RESERVED\n')
        os.fsync(fd)
    except OSError as exc:
        raise FixtureError('RESERVATION_FAILED') from exc
    flags = os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
    try:
        fd_result = os.open(evidence, flags)
    except FileNotFoundError:
        try:
            fd_result = os.open(evidence, flags | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd_result, NOT_RUN)
            os.fsync(fd_result)
        except OSError as exc:
            raise FixtureError('NOT_RUN_RECHECK_FAILED') from exc
    except OSError as exc:
        raise FixtureError('NOT_RUN_RECHECK_FAILED') from exc
    info = os.fstat(fd_result)
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.geteuid():
        os.close(fd_result)
        raise FixtureError('NOT_RUN_RECHECK_FAILED')
    os.lseek(fd_result, 0, os.SEEK_SET)
    chunks = bytearray()
    while True:
        part = os.read(fd_result, 4096)
        if not part:
            break
        chunks.extend(part)
    if bytes(chunks) != NOT_RUN:
        os.close(fd_result)
        raise FixtureError('NOT_RUN_RECHECK_FAILED')
    os.ftruncate(fd_result, 0)
    os.lseek(fd_result, 0, os.SEEK_SET)
    return fd_result, evidence


def write_result(fd: int, result: dict[str, Any]) -> None:
    try:
        payload = json.dumps(result, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'
    except (TypeError, ValueError, UnicodeError) as exc:
        raise FixtureError('RESULT_SERIALIZATION_FAILED') from exc
    if len(payload) > _INVENTORY_ARTIFACT_MAX_BYTES:
        raise FixtureError('INVENTORY_ARTIFACT_TOO_LARGE')
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        view = view[written:]
    os.fsync(fd)


def _assert_windows_unchanged(before: bytes, after: bytes) -> None:
    if before != after:
        raise TargetDrift('WINDOWS_RULES_CHANGED')


def _windows_snapshot() -> bytes:
    exe = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
    raw_firewall = command([exe, '-NoProfile', '-NonInteractive', '-Command', _WINDOWS_ACTIVE_STORE_QUERY])
    firewall_value = strict_json(raw_firewall)
    if not isinstance(firewall_value, dict) or set(firewall_value) != {'profiles', 'settings', 'rules'}:
        raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
    for key in ('profiles', 'settings', 'rules'):
        if (not isinstance(firewall_value[key], list)
                or any(not isinstance(item, dict) for item in firewall_value[key])):
            raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
    if (any('Name' not in item or not isinstance(item['Name'], str) for item in firewall_value['profiles'])
            or len({item['Name'] for item in firewall_value['profiles']}) != len(firewall_value['profiles'])):
        raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
    active_profiles = {item['Name'] for item in firewall_value['profiles']}
    required_rule_keys = {'rule', 'profiles', 'address', 'application', 'interface',
                          'interface_type', 'port', 'security', 'service'}
    if any(set(rule) != required_rule_keys or not isinstance(rule.get('rule'), dict)
           or not isinstance(rule['rule'].get('Name'), str) for rule in firewall_value['rules']):
        raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
    rule_names = [rule['rule']['Name'] for rule in firewall_value['rules']]
    if len(rule_names) != len(set(rule_names)):
        raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
    firewall_value['profiles'].sort(key=lambda item: str(item.get('Name', '')))
    firewall_value['settings'].sort(key=lambda item: json.dumps(
        item, sort_keys=True, separators=(',', ':'), ensure_ascii=False))
    firewall_value['rules'].sort(key=lambda item: str(item.get('rule', {}).get('Name', '')))
    for rule in firewall_value['rules']:
        for key in ('profiles', 'address', 'application', 'interface', 'interface_type', 'port', 'security', 'service'):
            rows = rule.get(key)
            if (not isinstance(rows, list) or not rows
                    or any(not isinstance(item, dict) or not item for item in rows)):
                raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
            if key == 'profiles' and any(
                    not isinstance(item.get('Name'), str) or item['Name'] not in active_profiles
                    for item in rows):
                raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
            if key != 'profiles' and len(rows) != 1:
                raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
            canonical_rows = [json.dumps(item, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
                              for item in rows]
            if len(canonical_rows) != len(set(canonical_rows)):
                raise TargetDrift('WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')
            rows.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(',', ':'), ensure_ascii=False))
    firewall = json.dumps(firewall_value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False).encode('utf-8')
    portproxy = command(['/mnt/c/Windows/System32/netsh.exe', 'interface', 'portproxy', 'show', 'all'])
    global _WINDOWS_SNAPSHOT_METADATA
    _WINDOWS_SNAPSHOT_METADATA = {
        'schema_version': 'tsw.windows-route-snapshot.v1',
        'firewall_bytes': len(firewall), 'firewall_sha256': digest(firewall),
        'portproxy_bytes': len(portproxy), 'portproxy_sha256': digest(portproxy),
        'profile_count': len(firewall_value['profiles']),
        'setting_count': len(firewall_value['settings']), 'rule_count': len(firewall_value['rules']),
        'captured_at': datetime.now(timezone.utc).isoformat(),
    }
    # Length-prefix each exact component. The byte sequence stays in memory for
    # equality checks; artifacts retain only the metadata above and a digest.
    packed = _pack_windows_snapshot(firewall, portproxy)
    _WINDOWS_SNAPSHOT_METADATA['windows_snapshot_sha256'] = digest(packed)
    return packed


def _assert_host_identity(host: str) -> None:
    if host == '192.168.178.33':
        rows = strict_json(command(['ip', '-j', '-4', 'addr']))
        if not isinstance(rows, list):
            raise TargetDrift('HOST_IDENTITY_DRIFT')
        addresses = {address.get('local') for row in rows if isinstance(row, dict)
                     for address in row.get('addr_info', []) if isinstance(address, dict)}
        if host not in addresses:
            raise TargetDrift('HOST_IDENTITY_DRIFT')
        return
    if b'microsoft' not in command(['uname', '-r']).lower():
        raise TargetDrift('HOST_IDENTITY_DRIFT')
    win = command(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                   '-NoProfile', '-NonInteractive', '-Command',
                   "(Get-NetIPAddress -AddressFamily IPv4).IPAddress"])
    if host not in win.decode('utf-8', errors='strict').split():
        raise TargetDrift('HOST_IDENTITY_DRIFT')


def _bounded_process_output(command_argv: list[str], timeout_seconds: float,
                            max_stream_bytes: int) -> tuple[bytes, bytes, int]:
    """Capture bounded stdout/stderr and kill a process on overflow or timeout."""
    process = None
    selector = None
    stdout = bytearray()
    stderr = bytearray()
    try:
        process = subprocess.Popen(command_argv, cwd=ROOT, env={'PATH': TRUSTED_PATH, 'LANG': 'C.UTF-8'},
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert process.stdout is not None and process.stderr is not None
        selector = selectors.DefaultSelector()
        for stream, target in ((process.stdout, stdout), (process.stderr, stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, target)
        deadline = time.monotonic() + timeout_seconds
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            for key, _ in selector.select(min(remaining, 0.25)):
                remaining_bytes = max_stream_bytes - len(key.data) + 1
                chunk = os.read(key.fd, min(65536, remaining_bytes))
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                key.data.extend(chunk)
                if len(key.data) > max_stream_bytes:
                    raise OverflowError
        exit_status = process.wait(timeout=max(0.1, deadline - time.monotonic()))
    except (TimeoutError, subprocess.TimeoutExpired, OverflowError, OSError) as exc:
        if process is not None:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=0.5)
            except (subprocess.TimeoutExpired, OSError):
                _kill_and_reap(process, 'HOST_IDENTITY_DRIFT')
        raise TargetDrift('HOST_IDENTITY_DRIFT') from exc
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            if process.stdout is not None:
                try:
                    process.stdout.close()
                except OSError:
                    pass
            if process.stderr is not None:
                try:
                    process.stderr.close()
                except OSError:
                    pass
    return bytes(stdout), bytes(stderr), exit_status


def _inventory_host_command(argv: list[str]) -> bytes:
    """Run an exact host identity query without retaining or hashing its output."""
    if argv == ['ip', '-j', '-4', 'addr']:
        command_argv = [TRUSTED_BIN['ip'], '-j', '-4', 'addr']
    elif argv == ['uname', '-r']:
        command_argv = [TRUSTED_BIN['uname'], '-r']
    elif argv == ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                  '-NoProfile', '-NonInteractive', '-Command',
                  '(Get-NetIPAddress -AddressFamily IPv4).IPAddress']:
        command_argv = argv
    else:
        raise FixtureError('INVENTORY_HOST_COMMAND_NOT_ALLOWLISTED')
    stdout, _, exit_status = _bounded_process_output(
        command_argv, _INVENTORY_HOST_COMMAND_TIMEOUT_SECONDS, _INVENTORY_COMMAND_MAX_BYTES)
    if exit_status:
        raise TargetDrift('HOST_IDENTITY_DRIFT')
    return stdout


def _assert_host_identity_inventory(host: str) -> None:
    if host == '192.168.178.33':
        rows = strict_json(_inventory_host_command(['ip', '-j', '-4', 'addr']))
        if not isinstance(rows, list):
            raise TargetDrift('HOST_IDENTITY_DRIFT')
        addresses = {address.get('local') for row in rows if isinstance(row, dict)
                     for address in row.get('addr_info', []) if isinstance(address, dict)}
        if host not in addresses:
            raise TargetDrift('HOST_IDENTITY_DRIFT')
        return
    if b'microsoft' not in _inventory_host_command(['uname', '-r']).lower():
        raise TargetDrift('HOST_IDENTITY_DRIFT')
    win = _inventory_host_command(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                                   '-NoProfile', '-NonInteractive', '-Command',
                                   '(Get-NetIPAddress -AddressFamily IPv4).IPAddress'])
    if host not in win.decode('utf-8', errors='strict').split():
        raise TargetDrift('HOST_IDENTITY_DRIFT')


def _route_state(host: str) -> dict[str, Any]:
    _assert_host_identity(host)
    _assert_local_incus_remote()
    listeners = _listener_rows(command(['ss', '-H', '-ltnp']), 10001)
    projects, routes = _incus_route_inventory()
    windows = _windows_snapshot() if host == '192.168.178.58' else b''
    return {'listeners_10001': listeners, 'incus_10001_routes': routes,
            'incus_projects': projects,
            'windows_snapshot': windows,
            'approved_route_state_sha256': approved_route_state_sha256(listeners, routes, windows, projects)}


def _capture_output_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise FixtureError('UNSAFE_CAPTURE_PATH')
    target = ROOT / path
    if target.parent != ROOT / PRIVATE_EVIDENCE_REL:
        raise FixtureError('UNSAFE_CAPTURE_PATH')
    safe_parent(target, create=True)
    info = target.parent.stat(follow_symlinks=False)
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise FixtureError('EVIDENCE_DIR_NOT_PRIVATE')
    _require_private_ext4(target.parent)
    return target


def _serialize_route_state_artifact(payload: dict[str, Any]) -> bytes:
    try:
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False).encode('utf-8') + b'\n'
    except (TypeError, ValueError) as exc:
        raise FixtureError('RESULT_SERIALIZATION_FAILED') from exc
    if len(raw) > _INVENTORY_ARTIFACT_MAX_BYTES:
        raise FixtureError('INVENTORY_ARTIFACT_TOO_LARGE')
    return raw


def capture_route_state(host: str, output: str) -> None:
    global _INVENTORY_RESERVE_CLEANUP, _INVENTORY_CLEANUP_MODE, _WINDOWS_SNAPSHOT_METADATA
    _COMMAND_AUDIT.clear()
    _INVENTORY_RESERVE_CLEANUP = False
    _INVENTORY_CLEANUP_MODE = False
    _WINDOWS_SNAPSHOT_METADATA = {}
    path = _capture_output_path(output)
    head, _, _, _ = git_preflight()
    state = _route_state(host)
    safe_listeners = _safe_listener_tuples(state['listeners_10001'])
    windows_metadata = dict(globals().get('_WINDOWS_SNAPSHOT_METADATA', {}))
    payload = {'schema_version': 'tsw.route-state.v2', 'source_commit': head,
               'captured_at': datetime.now(timezone.utc).isoformat(),
               'target_host': host, 'target_ip': host,
               'listeners_10001_count': len(safe_listeners),
               'listeners_10001': safe_listeners,
               'listeners_10001_sha256': digest(json.dumps(
                   safe_listeners, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')),
               'incus_projects': state['incus_projects'],
               'incus_10001_routes': state['incus_10001_routes'],
               'windows_snapshot': windows_metadata,
               'approved_route_state_sha256': state['approved_route_state_sha256'],
               'commands': _COMMAND_AUDIT}
    raw = _serialize_route_state_artifact(payload)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise FixtureError('CAPTURE_CREATE_FAILED') from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise FixtureError('CAPTURE_MODE_UNSAFE')
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _canonical_incus_name(encoded: str) -> str | None:
    if not encoded or '/' in encoded or '#' in encoded:
        return None
    try:
        name = unquote(encoded, errors='strict')
    except (UnicodeDecodeError, ValueError):
        return None
    if (not name or '/' in name or chr(92) in name or name in {'.', '..'}
            or quote(name, safe='') != encoded
            or any(ord(char) < 32 or ord(char) == 127 for char in name)):
        return None
    return name


def _is_incus_query_argv(argv: list[str]) -> bool:
    if len(argv) != 3 or argv[:2] != ['incus', 'query']:
        return False
    path = argv[2]
    if '#' in path:
        return False
    endpoint, separator, query = path.partition('?')
    parts = endpoint.split('/')
    if len(parts) != 4 or parts[1] != '1.0':
        return False
    resource = parts[2]
    if _canonical_incus_name(parts[3]) is None:
        return False
    if resource == 'projects':
        return not separator
    if resource not in {'profiles', 'instances'} or not separator:
        return False
    if not query.startswith('project='):
        return False
    encoded_project = query[len('project='):]
    return ('&' not in query and '=' not in encoded_project
            and _canonical_incus_name(encoded_project) is not None)


def _project_api_path(project: str) -> str:
    return '/1.0/projects/' + quote(project, safe='')


def _profile_api_path(profile: str, project: str) -> str:
    return '/1.0/profiles/' + quote(profile, safe='') + '?project=' + quote(project, safe='')


def _instance_api_path(instance: str, project: str) -> str:
    return '/1.0/instances/' + quote(instance, safe='') + '?project=' + quote(project, safe='')


def _inventory_command(argv: list[str]) -> bytes:
    """Run only an allowlisted Incus read and never hash or log its raw output."""
    global _INVENTORY_BYTES_CAPTURED, _INVENTORY_STARTED_AT
    valid = (bool(argv) and argv[0] == 'incus' and (
        argv == ['incus', 'remote', 'list', '--format', 'json'] or
        argv == ['incus', 'remote', 'get-default'] or
        argv == ['incus', 'project', 'list', '--format', 'json'] or
        argv == ['incus', 'image', 'list', '--project', 'default', '--format', 'json'] or
        (len(argv) == 8 and argv[1:3] == ['image', 'info']
         and HASH64.fullmatch(argv[3]) is not None
         and argv[4:] == ['--project', 'default', '--format', 'json']) or
        (len(argv) == 5 and argv[1] == 'info' and _canonical_incus_name(argv[2]) is not None
         and argv[3:] == ['--format', 'json']) or
        _is_incus_query_argv(argv) or
        (len(argv) == 6 and argv[1] == 'list' and argv[2] == '--project'
         and argv[3] and argv[4:] == ['--format', 'json']) or
        (len(argv) == 7 and argv[1:3] == ['profile', 'list'] and argv[3] == '--project' and argv[4] and argv[5:] == ['--format', 'json'])))
    if not valid or any(not isinstance(item, str) or not item or item.startswith('-') and item not in {
            '--project', '--format', '--expanded'} for item in argv):
        raise FixtureError('INVENTORY_COMMAND_NOT_ALLOWLISTED')
    command_limit, byte_limit, _, total_timeout = _inventory_budgets()
    if len(_COMMAND_AUDIT) >= command_limit:
        raise TargetDrift('INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED')
    if _INVENTORY_STARTED_AT is None:
        _INVENTORY_STARTED_AT = time.monotonic()
    if time.monotonic() - _INVENTORY_STARTED_AT > total_timeout:
        raise TargetDrift('INCUS_INVENTORY_TOTAL_TIMEOUT')
    executable = TRUSTED_BIN['incus']
    command_argv = [executable, *argv[1:]]
    process = None
    selector = None
    stdout = bytearray()
    stderr = bytearray()
    try:
        process = subprocess.Popen(command_argv, cwd=ROOT, env={'PATH': TRUSTED_PATH, 'LANG': 'C.UTF-8'},
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert process.stdout is not None and process.stderr is not None
        selector = selectors.DefaultSelector()
        for stream, target in ((process.stdout, stdout), (process.stderr, stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, target)
        deadline = time.monotonic() + _INVENTORY_HOST_COMMAND_TIMEOUT_SECONDS
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            for key, _ in selector.select(min(remaining, 0.25)):
                per_stream_remaining = _INVENTORY_COMMAND_MAX_BYTES - len(key.data) + 1
                aggregate_remaining = (byte_limit - _INVENTORY_BYTES_CAPTURED
                                       - len(stdout) - len(stderr) + 1)
                chunk = os.read(key.fd, min(65536, per_stream_remaining, aggregate_remaining))
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                key.data.extend(chunk)
                if (len(key.data) > _INVENTORY_COMMAND_MAX_BYTES
                        or _INVENTORY_BYTES_CAPTURED + len(stdout) + len(stderr) > byte_limit):
                    raise OverflowError
        exit_status = process.wait(timeout=max(0.1, deadline - time.monotonic()))
    except (TimeoutError, subprocess.TimeoutExpired) as exc:
        if process is not None:
            _kill_and_reap(process, 'INCUS_INVENTORY_COMMAND_FAILED')
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, len(stdout), len(stderr)))
        raise TargetDrift('INCUS_INVENTORY_COMMAND_FAILED') from exc
    except OverflowError as exc:
        if process is not None:
            _kill_and_reap(process, 'INCUS_INVENTORY_OUTPUT_TOO_LARGE')
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, len(stdout), len(stderr)))
        raise TargetDrift('INCUS_INVENTORY_OUTPUT_TOO_LARGE') from exc
    except OSError as exc:
        if process is not None:
            _kill_and_reap(process, 'INCUS_INVENTORY_COMMAND_FAILED')
        _COMMAND_AUDIT.append(_safe_command_record(argv, None, 0, 0))
        raise TargetDrift('INCUS_INVENTORY_COMMAND_FAILED') from exc
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
    _COMMAND_AUDIT.append(_safe_command_record(argv, exit_status, len(stdout), len(stderr)))
    _INVENTORY_BYTES_CAPTURED += len(stdout) + len(stderr)
    if exit_status:
        raise TargetDrift('INCUS_INVENTORY_COMMAND_FAILED')
    if (_INVENTORY_STARTED_AT is not None
            and time.monotonic() - _INVENTORY_STARTED_AT > total_timeout):
        raise TargetDrift('INCUS_INVENTORY_TOTAL_TIMEOUT')
    return bytes(stdout)


def _inventory_config(value: Any, code: str) -> None:
    if not isinstance(value, dict) or len(value) > _INVENTORY_MAX_ENTITIES:
        raise TargetDrift(code)
    for key, val in value.items():
        if not isinstance(key, str) or not isinstance(val, str) or _SECRET_CONFIG_KEY.search(key):
            raise TargetDrift(code)


_INVENTORY_DEVICE_FIELDS = {
    'type', 'name', 'nictype', 'parent', 'network', 'listen', 'connect', 'bind', 'ports',
    'path', 'source', 'pool', 'size', 'readonly', 'required', 'shift', 'limits.cpu',
    'limits.memory', 'boot.priority',
}


def _inventory_devices(value: Any, code: str) -> dict[str, dict[str, str]]:
    _account_inventory_entities(len(value) if isinstance(value, dict) else _INVENTORY_MAX_ENTITIES + 1, code)
    if not isinstance(value, dict) or len(value) > _INVENTORY_MAX_ENTITIES:
        raise TargetDrift(code)
    result: dict[str, dict[str, str]] = {}
    for name, config in value.items():
        if (not isinstance(name, str) or not name or not isinstance(config, dict)
                or set(config) - _INVENTORY_DEVICE_FIELDS
                or any(not isinstance(k, str) or _SECRET_CONFIG_KEY.search(k) for k in config)
                or any(not isinstance(v, str) for v in config.values())):
            raise TargetDrift(code)
        kind = config.get('type')
        if kind not in {'disk', 'nic', 'proxy'}:
            raise TargetDrift(code)
        if kind == 'proxy':
            if not isinstance(config.get('listen'), str) or not isinstance(config.get('connect'), str):
                raise TargetDrift(code)
            try:
                listen_protocol, _ = _parse_proxy_endpoint(config['listen'])
                connect_protocol, _ = _parse_proxy_endpoint(config['connect'])
            except TargetDrift as exc:
                raise TargetDrift(code) from exc
            if (listen_protocol, connect_protocol) not in SUPPORTED_PROXY_PROTOCOL_PAIRS:
                raise TargetDrift(code)
            if 'bind' in config and config['bind'] not in {'host', 'instance'}:
                raise TargetDrift(code)
        result[name] = dict(sorted(config.items()))
    return dict(sorted(result.items()))


def _project_isolation(config: Any) -> dict[str, bool | None]:
    if not isinstance(config, dict):
        raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
    for key, value in config.items():
        if not isinstance(key, str) or _SECRET_CONFIG_KEY.search(key):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        if key in _PROJECT_BOOLEAN_KEYS:
            if not isinstance(value, bool) and (not isinstance(value, str) or value not in {'true', 'false'}):
                raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        elif not isinstance(value, str):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
    result: dict[str, bool | None] = {}
    for key in sorted(_PROJECT_BOOLEAN_KEYS):
        if key not in config:
            result[key] = None
            continue
        value = config[key]
        if isinstance(value, bool):
            result[key] = value
        elif isinstance(value, str) and value in {'true', 'false'}:
            result[key] = value == 'true'
        else:
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
    return result


def _account_inventory_entities(count: int, code: str) -> None:
    global _INVENTORY_ENTITIES_CAPTURED
    _, _, entity_limit, _ = _inventory_budgets()
    if count < 0 or count > entity_limit or _INVENTORY_ENTITIES_CAPTURED + count > entity_limit:
        raise TargetDrift(code)
    _INVENTORY_ENTITIES_CAPTURED += count


def _require_local_incus_admin() -> None:
    """The unix socket is complete only for root or a member of incus-admin."""
    if os.geteuid() == 0:
        return
    try:
        import grp
        admin_gid = grp.getgrnam('incus-admin').gr_gid
    except (ImportError, KeyError) as exc:
        raise FixtureError('INCUS_PROJECT_VISIBILITY_UNVERIFIED') from exc
    if admin_gid not in {*os.getgroups(), os.getegid()}:
        raise FixtureError('INCUS_PROJECT_VISIBILITY_UNVERIFIED')


def _capture_project_inventory(host: str) -> dict[str, Any]:
    global _INVENTORY_BYTES_CAPTURED, _INVENTORY_ENTITIES_CAPTURED, _INVENTORY_STARTED_AT
    _INVENTORY_BYTES_CAPTURED = 0
    _INVENTORY_ENTITIES_CAPTURED = 0
    _INVENTORY_STARTED_AT = None
    commands_start = len(_COMMAND_AUDIT)
    _assert_host_identity_inventory(host)
    _assert_local_incus_remote_inventory()
    _require_local_incus_admin()
    projects_raw = strict_json(_inventory_command(['incus', 'project', 'list', '--format', 'json']))
    if not isinstance(projects_raw, list) or not projects_raw or len(projects_raw) > _INVENTORY_MAX_ENTITIES:
        raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
    _account_inventory_entities(len(projects_raw), 'INCUS_PROJECT_INVENTORY_UNREADABLE')
    names = []
    for row in projects_raw:
        if not isinstance(row, dict) or set(row) - {'name', 'description', 'config', 'used_by'}:
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        if 'description' in row and not isinstance(row['description'], str):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        if 'config' in row:
            _project_isolation(row['config'])
        if 'used_by' in row and (not isinstance(row['used_by'], list) or len(row['used_by']) > _INVENTORY_MAX_ENTITIES
                                 or any(not isinstance(x, str) for x in row['used_by'])
                                 or len(set(row['used_by'])) != len(row['used_by'])):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        name = row.get('name')
        if not isinstance(name, str) or not name or name in names:
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        names.append(name)
    result = []
    for project in sorted(names):
        pdata = strict_json(_inventory_command(['incus', 'query', _project_api_path(project)]))
        if (not isinstance(pdata, dict) or set(pdata) - {'name', 'description', 'config', 'used_by'}
                or pdata.get('name') != project or not isinstance(pdata.get('description'), str)):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        if 'used_by' in pdata and (not isinstance(pdata['used_by'], list) or len(pdata['used_by']) > _INVENTORY_MAX_ENTITIES
                                   or any(not isinstance(x, str) for x in pdata['used_by'])
                                   or len(set(pdata['used_by'])) != len(pdata['used_by'])):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        isolation = _project_isolation(pdata.get('config'))
        profile_project_local = project == 'default' or isolation['features.profiles'] is True
        profiles_raw = (strict_json(_inventory_command(
            ['incus', 'profile', 'list', '--project', project, '--format', 'json']))
            if profile_project_local else [])
        if not isinstance(profiles_raw, list) or len(profiles_raw) > _INVENTORY_MAX_ENTITIES or any(not isinstance(x, dict) or set(x) - {'name', 'description', 'used_by', 'config', 'devices', 'project'} or not isinstance(x.get('name'), str) for x in profiles_raw):
            raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
        _account_inventory_entities(len(profiles_raw), 'INCUS_PROFILE_INVENTORY_UNREADABLE')
        for row in profiles_raw:
            if 'project' in row and row['project'] != project:
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            if 'project' in row and not isinstance(row['project'], str):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            if 'description' in row and not isinstance(row['description'], str):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            if 'used_by' in row and (not isinstance(row['used_by'], list) or len(row['used_by']) > _INVENTORY_MAX_ENTITIES
                                     or any(not isinstance(x, str) for x in row['used_by'])
                                     or len(set(row['used_by'])) != len(row['used_by'])):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            if 'config' in row:
                _inventory_config(row['config'], 'INCUS_PROFILE_INVENTORY_UNREADABLE')
            if 'devices' in row:
                _inventory_devices(row['devices'], 'INCUS_PROFILE_INVENTORY_UNREADABLE')
        profiles: list[dict[str, Any]] = []
        for profile_name in sorted(x['name'] for x in profiles_raw):
            if not profile_name or any(p['name'] == profile_name for p in profiles):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            pdata2 = strict_json(_inventory_command(['incus', 'query', _profile_api_path(profile_name, project)]))
            if (not isinstance(pdata2, dict)
                    or set(pdata2) - {'config', 'description', 'devices', 'name', 'used_by', 'project'}
                    or pdata2.get('name') != profile_name
                    or ('project' in pdata2 and (not isinstance(pdata2['project'], str) or pdata2['project'] != project))):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            _inventory_config(pdata2.get('config'), 'INCUS_PROFILE_INVENTORY_UNREADABLE')
            pused = pdata2.get('used_by')
            if (not isinstance(pused, list) or len(pused) > _INVENTORY_MAX_ENTITIES
                    or any(not isinstance(x, str) for x in pused) or len(set(pused)) != len(pused)):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            profiles.append({'name': profile_name, 'used_by': sorted(pused),
                             'devices': _inventory_devices(pdata2.get('devices'), 'INCUS_PROFILE_INVENTORY_UNREADABLE')})
        instances_raw = strict_json(_inventory_command(['incus', 'list', '--project', project, '--format', 'json']))
        if not isinstance(instances_raw, list) or len(instances_raw) > _INVENTORY_MAX_ENTITIES:
            raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
        _account_inventory_entities(len(instances_raw), 'INCUS_INSTANCE_INVENTORY_UNREADABLE')
        instances = []
        for item in sorted(instances_raw, key=lambda x: x.get('name', '') if isinstance(x, dict) else ''):
            if (not isinstance(item, dict) or set(item) - {'name', 'status', 'status_code', 'type', 'profiles', 'architecture', 'created_at', 'last_used_at', 'location', 'description', 'stateful', 'ephemeral', 'project', 'config', 'devices', 'expanded_config', 'expanded_devices', 'backups', 'snapshots', 'state'}
                    or not isinstance(item.get('name'), str) or not item['name']
                    or not isinstance(item.get('profiles'), list) or len(item['profiles']) > _INVENTORY_MAX_ENTITIES
                    or any(not isinstance(p, str) for p in item['profiles'])
                    or len(set(item['profiles'])) != len(item['profiles'])):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            for key in ('backups', 'snapshots'):
                if key not in item or item[key] is None:
                    continue
                entries = item[key]
                if (not isinstance(entries, list) or len(entries) > _INVENTORY_MAX_ENTITIES
                        or any(not isinstance(entry, dict) or len(entry) > _INVENTORY_MAX_ENTITIES
                               for entry in entries)):
                    raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
                _account_inventory_entities(len(entries), 'INCUS_INSTANCE_INVENTORY_UNREADABLE')
            if 'state' in item and item['state'] is not None:
                state = item['state']
                if not isinstance(state, dict) or len(state) > _INVENTORY_MAX_ENTITIES:
                    raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
                _account_inventory_entities(len(state), 'INCUS_INSTANCE_INVENTORY_UNREADABLE')
            if 'status_code' in item and (not isinstance(item['status_code'], int) or isinstance(item['status_code'], bool)):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            for key in ('architecture', 'created_at', 'last_used_at', 'location', 'description'):
                if key in item and not isinstance(item[key], str):
                    raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            for key in ('stateful', 'ephemeral'):
                if key in item and not isinstance(item[key], bool):
                    raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            if 'project' in item and (not isinstance(item['project'], str) or item['project'] != project):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            for key in ('config', 'expanded_config'):
                if key in item:
                    _inventory_config(item[key], 'INCUS_INSTANCE_INVENTORY_UNREADABLE')
            for key in ('devices', 'expanded_devices'):
                if key in item:
                    _inventory_devices(item[key], 'INCUS_INSTANCE_INVENTORY_UNREADABLE')
            name = item['name']
            api_data = strict_json(_inventory_command(['incus', 'query', _instance_api_path(name, project)]))
            if (not isinstance(api_data, dict) or api_data.get('name') != name
                    or ('project' in api_data and api_data['project'] != project)):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            local = {key: api_data.get(key) for key in ('config', 'devices', 'profiles')}
            effective = {'config': api_data.get('expanded_config'),
                         'devices': api_data.get('expanded_devices'),
                         'profiles': api_data.get('profiles')}
            def instance_config(data: Any) -> tuple[dict[str, dict[str, str]], list[str]]:
                if not isinstance(data, dict) or set(data) - {'config', 'devices', 'profiles'}:
                    raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
                _inventory_config(data.get('config'), 'INCUS_INSTANCE_INVENTORY_UNREADABLE')
                ps = data.get('profiles')
                if not isinstance(ps, list) or len(ps) > _INVENTORY_MAX_ENTITIES or any(not isinstance(p, str) for p in ps):
                    raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
                if len(set(ps)) != len(ps):
                    raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
                return _inventory_devices(data.get('devices'), 'INCUS_INSTANCE_INVENTORY_UNREADABLE'), sorted(ps)
            local_devices, profiles_used = instance_config(local)
            effective_devices, _ = instance_config(effective)
            if profiles_used != sorted(item['profiles']):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            status, typ = item.get('status'), item.get('type')
            if not isinstance(status, str) or not isinstance(typ, str):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            instances.append({'name': name, 'status': status, 'type': typ, 'profiles': profiles_used,
                              'local_devices': local_devices, 'expanded_devices': effective_devices})
        if len({x['name'] for x in instances}) != len(instances):
            raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
        result.append({'name': project, 'isolation': isolation, 'profiles': profiles, 'instances': instances})
    audit = [dict(row) for row in _COMMAND_AUDIT[commands_start:]
             if row.get('command_id', '').startswith('incus.')]
    return {'projects': result, 'command_records': audit}


def capture_project_inventory(host: str, output: str) -> None:
    global _INVENTORY_STARTED_AT, _INVENTORY_BYTES_CAPTURED, _INVENTORY_ENTITIES_CAPTURED
    global _INVENTORY_RESERVE_CLEANUP, _INVENTORY_CLEANUP_MODE
    _COMMAND_AUDIT.clear()
    _INVENTORY_RESERVE_CLEANUP = False
    _INVENTORY_CLEANUP_MODE = False
    _INVENTORY_STARTED_AT = None
    _INVENTORY_BYTES_CAPTURED = 0
    _INVENTORY_ENTITIES_CAPTURED = 0
    # Verify filesystem and path first, but defer directory creation until after source preflight.
    _require_private_ext4(ROOT)
    rel = Path(output)
    if rel.is_absolute() or '..' in rel.parts or ROOT / rel != ROOT / PRIVATE_EVIDENCE_REL / rel.name:
        raise FixtureError('UNSAFE_CAPTURE_PATH')
    _require_private_evidence_dir(ROOT / GO_REL)
    path = _capture_output_path(output)
    try:
        path.lstat()
    except FileNotFoundError:
        pass
    else:
        raise FixtureError('CAPTURE_CREATE_FAILED')
    head, _, _, _ = git_preflight()
    inventory = _capture_project_inventory(host)
    payload = {'schema_version': 'tsw.incus.project-inventory.v1', 'target_host': host,
               'source_commit': head, 'projects': inventory['projects'],
               'command_records': inventory['command_records']}
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode() + b'\n'
    if len(raw) > _INVENTORY_ARTIFACT_MAX_BYTES:
        raise FixtureError('INVENTORY_ARTIFACT_TOO_LARGE')
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0), 0o600)
    except OSError as exc:
        raise FixtureError('CAPTURE_CREATE_FAILED') from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise FixtureError('CAPTURE_MODE_UNSAFE')
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _incus_route_inventory() -> tuple[list[str], list[dict[str, Any]]]:
    project_rows = strict_json(command(['incus', 'project', 'list', '--format', 'json']))
    if not isinstance(project_rows, list):
        raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
    projects: list[str] = []
    for row in project_rows:
        if (not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row['name']
                or ('description' in row and not isinstance(row['description'], str))
                or ('config' in row and (not isinstance(row['config'], dict)
                    or any(not isinstance(key, str) or not isinstance(value, str)
                           for key, value in row['config'].items())))):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        projects.append(row['name'])
    if not projects or len(set(projects)) != len(projects):
        raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
    projects.sort()
    if 'default' not in projects:
        raise TargetDrift('INCUS_PROJECT_DRIFT')
    routes: list[dict[str, Any]] = []
    for project in projects:
        project_data = strict_json(command(['incus', 'query', _project_api_path(project)]))
        if (not isinstance(project_data, dict) or project_data.get('name') != project
                or not {'name', 'description', 'config'} <= set(project_data)
                or set(project_data) - {'name', 'description', 'config', 'used_by'}
                or not isinstance(project_data.get('description'), str)
                or not isinstance(project_data.get('config'), dict)
                or any(not isinstance(key, str) or not isinstance(value, str)
                       for key, value in project_data['config'].items())
                or ('used_by' in project_data and
                    (not isinstance(project_data['used_by'], list)
                     or any(not isinstance(item, str) for item in project_data['used_by'])
                     or project_data['used_by'] != sorted(set(project_data['used_by']))))):
            raise TargetDrift('INCUS_PROJECT_INVENTORY_UNREADABLE')
        profile_project_local = (project == 'default'
                                 or _project_isolation(project_data['config'])['features.profiles'] is True)
        profiles = (strict_json(command(['incus', 'profile', 'list', '--project', project, '--format', 'json']))
                    if profile_project_local else [])
        if (not isinstance(profiles, list)
                or any(not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row['name']
                       for row in profiles)
                or len({row['name'] for row in profiles}) != len(profiles)):
            raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
        for row in profiles:
            name = row['name']
            data = strict_json(command(['incus', 'query', _profile_api_path(name, project)]))
            if (not isinstance(data, dict) or data.get('name') != name
                    or ('project' in data and data['project'] != project)
                    or not isinstance(data.get('config'), dict)):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            devices = _strict_devices(data.get('devices'), 'INCUS_PROFILE_INVENTORY_UNREADABLE',
                                      allow_implicit_bind=True)
            used_by = data.get('used_by')
            if (not isinstance(used_by, list) or any(not isinstance(item, str) for item in used_by)
                    or used_by != sorted(set(used_by))):
                raise TargetDrift('INCUS_PROFILE_INVENTORY_UNREADABLE')
            for device_name, device in devices.items():
                if device.get('type') == 'proxy' and _is_approved_10001_proxy(device['listen']):
                    routes.append(_safe_route_row(project, 'profile', name, device_name,
                                                  device, [name]))
        instances = strict_json(command(['incus', 'list', '--project', project, '--format', 'json']))
        if (not isinstance(instances, list)
                or any(not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row['name']
                       for row in instances)
                or len({row['name'] for row in instances}) != len(instances)):
            raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
        for row in instances:
            name = row['name']
            data = strict_json(command(['incus', 'query', _instance_api_path(name, project)]))
            if (not isinstance(data, dict) or data.get('name') != name
                    or ('project' in data and data['project'] != project)
                    or not isinstance(data.get('config'), dict)
                    or any(not isinstance(key, str) or not isinstance(value, str)
                           for key, value in data['config'].items())):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            devices = _strict_devices(data.get('devices'), 'INCUS_INSTANCE_INVENTORY_UNREADABLE',
                                      allow_implicit_bind=True)
            instance_profiles = data.get('profiles')
            if not isinstance(instance_profiles, list) or any(not isinstance(item, str) for item in instance_profiles):
                raise TargetDrift('INCUS_INSTANCE_INVENTORY_UNREADABLE')
            for device_name, device in devices.items():
                if device.get('type') == 'proxy' and _is_approved_10001_proxy(device['listen']):
                    routes.append(_safe_route_row(project, 'instance', name, device_name,
                                                  device, instance_profiles))
    return projects, sorted(routes, key=lambda item: (item['project'], item['owner_type'], item['owner'], item['device']))


def _safe_route_row(project: str, owner_type: str, owner: str, device_name: str,
                    device: dict[str, Any], profiles: list[str]) -> dict[str, Any]:
    if (owner_type not in {'profile', 'instance'} or not all(
            isinstance(value, str) and value and len(value) <= 128
            and re.fullmatch(r'[A-Za-z0-9_.-]+', value)
            for value in (project, owner, device_name))):
        raise TargetDrift('INCUS_10001_ROUTE_UNAPPROVED')
    if (set(device) - {'type', 'listen', 'connect', 'bind'}
            or not {'type', 'listen', 'connect'} <= set(device)):
        raise TargetDrift('INCUS_10001_ROUTE_UNAPPROVED')
    def endpoint(value: str) -> dict[str, Any]:
        protocol, _ = _parse_proxy_endpoint(value)
        if protocol != 'tcp':
            raise TargetDrift('INCUS_10001_ROUTE_UNAPPROVED')
        address, port = value.split(':', 1)[1].rsplit(':', 1)
        if address.startswith('[') and address.endswith(']'):
            address = address[1:-1]
        return {'protocol': protocol, 'address': address, 'port': int(port)}
    bind = device.get('bind', 'host')
    if bind not in {'host', 'instance'}:
        raise TargetDrift('INCUS_10001_ROUTE_UNAPPROVED')
    if (not isinstance(profiles, list) or any(not isinstance(p, str) or not p for p in profiles)
            or len(profiles) != len(set(profiles))):
        raise TargetDrift('INCUS_10001_ROUTE_UNAPPROVED')
    return {'project': project, 'owner_type': owner_type, 'owner': owner,
            'device': device_name, 'device_type': 'proxy',
            'effective_profiles': sorted(profiles), 'listen': endpoint(device['listen']),
            'connect': endpoint(device['connect']), 'bind': bind}


def _incus_10001_routes() -> list[dict[str, Any]]:
    """Compatibility helper for route-focused tests; production binds names too."""
    return _incus_route_inventory()[1]


def _validate_local_incus_remote(remotes: Any, default: str) -> None:
    if default != 'local':
        raise TargetDrift('INCUS_REMOTE_DRIFT')
    local = remotes.get('local') if isinstance(remotes, dict) else None
    string_fields = {'Addr', 'AuthType', 'Project', 'Protocol', 'CredHelper'}
    boolean_fields = {'Public', 'Global', 'Static'}
    if (not isinstance(local, dict) or set(local) - string_fields - boolean_fields - {'KeepAlive'}
            or local.get('Addr') != 'unix://'
            or any(key in local and not isinstance(local[key], str) for key in string_fields)
            or ('KeepAlive' in local and (not isinstance(local['KeepAlive'], int)
                                          or isinstance(local['KeepAlive'], bool) or local['KeepAlive'] < 0))
            or any(key in local and not isinstance(local[key], bool) for key in boolean_fields)):
        raise TargetDrift('INCUS_ENDPOINT_DRIFT')


def _assert_local_incus_remote() -> None:
    _assert_local_incus_remote_inventory()


def _assert_local_incus_remote_inventory() -> None:
    """Verify the Incus default endpoint without hashing its raw response."""
    remotes = strict_json(_inventory_command(['incus', 'remote', 'list', '--format', 'json']))
    default = _inventory_command(['incus', 'remote', 'get-default'])
    _validate_local_incus_remote(remotes, default.decode('ascii', errors='strict').strip())


def _read_default_profile(go: dict[str, Any], expected_consumers: list[str]) -> dict[str, Any]:
    profile = strict_json(_inventory_command(['incus', 'query', _profile_api_path('default', 'default')]))
    _account_inventory_entities(_json_entity_count(profile), 'DEFAULT_PROFILE_UNREADABLE')
    if (not isinstance(profile, dict) or set(profile) - {'name', 'project', 'description', 'config', 'devices', 'used_by'}
            or profile.get('name') != 'default'
            or ('project' in profile and profile['project'] != 'default')
            or ('description' in profile and not isinstance(profile['description'], str))
            or not isinstance(profile.get('config'), dict)):
        raise TargetDrift('DEFAULT_PROFILE_UNREADABLE')
    devices = _strict_devices(profile.get('devices'), 'DEFAULT_PROFILE_UNREADABLE')
    if canonical_profile_sha256(profile['config'], devices) != go['default_profile_sha256']:
        raise TargetDrift('DEFAULT_PROFILE_DRIFT')
    consumers = profile.get('used_by')
    if (not isinstance(consumers, list) or any(not isinstance(item, str) for item in consumers)
            or consumers != sorted(set(consumers)) or consumers != expected_consumers):
        raise TargetDrift('DEFAULT_PROFILE_CONSUMERS_DRIFT')
    derived = _derive_fixture_base({'config': profile['config'], 'devices': devices})
    if canonical_profile_sha256(derived['config'], derived['devices']) != go['fixture_base_profile_sha256']:
        raise TargetDrift('FIXTURE_BASE_PROFILE_DIGEST_MISMATCH')
    return {'config': profile['config'], 'devices': devices, 'used_by': consumers,
            'derived': derived, 'sha256': go['default_profile_sha256']}


def _assert_fixture_profile(go: dict[str, Any], data: dict[str, Any],
                            expected_consumers: list[str]) -> dict[str, Any]:
    expected_device = {'q449-listener': {
        'type': 'proxy', 'listen': go['proxy']['listen'],
        'connect': go['proxy']['connect'], 'bind': go['proxy']['bind'],
    }}
    if (not isinstance(data, dict)
            or data.get('name') != go['target']['profile']
            or ('project' in data and data['project'] != 'default')
            or data.get('config') != {'user.q449.run_id': go['target']['run_id']}):
        raise TargetDrift('FIXTURE_PROFILE_CONFIG_UNVERIFIED')
    devices = _strict_devices(data.get('devices'), 'FIXTURE_PROFILE_DEVICE_UNVERIFIED')
    if devices != expected_device:
        raise TargetDrift('FIXTURE_PROFILE_DEVICE_UNVERIFIED')
    consumers = data.get('used_by')
    if (not isinstance(consumers, list) or any(not isinstance(item, str) for item in consumers)
            or consumers != sorted(set(consumers)) or consumers != expected_consumers):
        raise TargetDrift('FIXTURE_PROFILE_CONSUMERS_UNVERIFIED')
    return {'config': data['config'], 'devices': devices, 'used_by': consumers}


def _assert_base_profile(go: dict[str, Any], data: dict[str, Any],
                         expected_consumers: list[str],
                         derived: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if (not isinstance(data, dict) or data.get('name') != go['target']['base_profile']
            or ('project' in data and data['project'] != 'default')
            or data.get('config') != derived['config']):
        raise TargetDrift('FIXTURE_BASE_PROFILE_CONFIG_UNVERIFIED')
    devices = _strict_devices(data.get('devices'), 'FIXTURE_BASE_PROFILE_DEVICE_UNVERIFIED')
    if devices != derived['devices']:
        raise TargetDrift('FIXTURE_BASE_PROFILE_DEVICE_UNVERIFIED')
    if canonical_profile_sha256(data['config'], devices) != go['fixture_base_profile_sha256']:
        raise TargetDrift('FIXTURE_BASE_PROFILE_DIGEST_MISMATCH')
    consumers = data.get('used_by')
    if (not isinstance(consumers, list) or any(not isinstance(item, str) for item in consumers)
            or consumers != sorted(set(consumers)) or consumers != expected_consumers):
        raise TargetDrift('FIXTURE_BASE_PROFILE_CONSUMERS_UNVERIFIED')
    return {'config': data['config'], 'devices': devices, 'used_by': consumers}


def _profile_create_readback_owned(data: Any, expected_name: str) -> bool:
    """Recognize only the exact empty, newly-created run-named profile state."""
    return (isinstance(data, dict) and data.get('name') == expected_name
            and data.get('project', 'default') == 'default'
            and data.get('config') == {} and data.get('devices') == {}
            and data.get('used_by') == [])


def _fixture_profile_cleanup_prefix_owned(data: Any, profile: str, project: str,
                                          run_id: str, expected_device: dict[str, Any],
                                          expected_consumers: list[str]) -> bool:
    """Accept only the marker-only or marker-plus-listener profile prefix."""
    if (not isinstance(data, dict) or data.get('name') != profile
            or data.get('project', 'default') != project
            or data.get('config') != {'user.q449.run_id': run_id}
            or data.get('devices') not in ({}, {'q449-listener': expected_device})):
        return False
    consumers = data.get('used_by')
    return (isinstance(consumers, list) and consumers == sorted(set(consumers))
            and consumers == expected_consumers)


def _instance_create_readback_owned(data: Any, instance: str, run_id: str,
                                    base_profile: str, fixture_profile: str) -> bool:
    """Accept an ambiguous init only when exact name/profile binding proves ownership."""
    if (not isinstance(data, dict) or data.get('name') != instance
            or data.get('project', 'default') != 'default'
            or data.get('profiles') != [base_profile, fixture_profile]
            or data.get('devices') not in ({}, None)):
        return False
    config = data.get('config')
    return (isinstance(config, dict) and set(config) <= {'user.q449.run_id'}
            and config.get('user.q449.run_id') in (None, run_id))


def _verify_effective_instance(go: dict[str, Any], default_profile: dict[str, Any],
                               fixture_profile: dict[str, Any]) -> dict[str, Any]:
    target, instance = go['target'], go['target']['instance']
    local = strict_json(_incus('query', _instance_api_path(instance, 'default')))
    if (not isinstance(local, dict) or local.get('name') != instance
            or ('project' in local and local['project'] != 'default')):
        raise TargetDrift('INSTANCE_CONFIG_UNREADABLE')
    expanded = {'config': local.get('expanded_config'),
                'devices': local.get('expanded_devices'),
                'profiles': local.get('profiles')}
    local = {key: local.get(key) for key in ('config', 'devices', 'profiles')}
    if not isinstance(local.get('config'), dict):
        raise TargetDrift('INSTANCE_CONFIG_UNREADABLE')
    local_devices = _strict_devices(local.get('devices'), 'INSTANCE_CONFIG_UNREADABLE')
    if local_devices:
        raise TargetDrift('INSTANCE_DEVICE_OVERRIDE_PRESENT')
    if local['config'].get('user.q449.run_id') != target['run_id']:
        raise TargetDrift('INSTANCE_OWNERSHIP_UNVERIFIED')
    if not isinstance(expanded, dict):
        raise TargetDrift('EXPANDED_INSTANCE_CONFIG_UNREADABLE')
    profiles = expanded.get('profiles')
    if profiles != [target['base_profile'], target['profile']]:
        raise TargetDrift('EFFECTIVE_PROFILES_UNVERIFIED')
    devices = _strict_devices(expanded.get('devices'), 'EXPANDED_INSTANCE_CONFIG_UNREADABLE')
    expected: dict[str, dict[str, Any]] = {}
    for profile_devices in (default_profile['derived']['devices'], fixture_profile['devices']):
        for name, device in profile_devices.items():
            if name in expected:
                raise TargetDrift('EFFECTIVE_DEVICE_COLLISION')
            expected[name] = device
    if devices != expected:
        raise TargetDrift('EFFECTIVE_DEVICES_UNVERIFIED')
    proxy_devices = {name: device for name, device in devices.items() if device.get('type') == 'proxy'}
    expected_proxy = {'q449-listener': fixture_profile['devices']['q449-listener']}
    if proxy_devices != expected_proxy:
        raise TargetDrift('EFFECTIVE_PROXY_ROUTES_UNVERIFIED')
    return {'profiles': profiles, 'devices': devices}


def _parse_incus_version(output: bytes) -> tuple[str, str]:
    """Parse the exact two-line version output supported by Incus 6.0.5."""
    try:
        lines = output.decode('ascii', errors='strict').splitlines()
    except UnicodeDecodeError as exc:
        raise TargetDrift('INCUS_VERSION_UNREADABLE') from exc
    if len(lines) != 2:
        raise TargetDrift('INCUS_VERSION_UNREADABLE')
    prefixes = ('Client version: ', 'Server version: ')
    values: list[str] = []
    for line, prefix in zip(lines, prefixes, strict=True):
        if not line.startswith(prefix):
            raise TargetDrift('INCUS_VERSION_UNREADABLE')
        value = line[len(prefix):]
        if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?', value):
            raise TargetDrift('INCUS_VERSION_UNREADABLE')
        values.append(value)
    return values[0], values[1]


def jit(go: dict[str, Any], host: str) -> dict[str, Any]:
    target = go['target']
    _assert_host_identity(host)
    _assert_local_incus_remote_inventory()
    _, server_version = _parse_incus_version(command(['incus', 'version']))
    if server_version != target['server_version']:
        raise TargetDrift('INCUS_VERSION_DRIFT')
    image = strict_json(command(['incus', 'image', 'list', '--project', 'default', '--format', 'json']))
    if not any(i.get('fingerprint') == target['image_fingerprint'] for i in image):
        raise TargetDrift('INCUS_IMAGE_DRIFT')
    image_info = strict_json(command(['incus', 'image', 'info', target['image_fingerprint'], '--project', 'default', '--format', 'json']))
    properties = image_info.get('properties')
    if not isinstance(properties, dict) or 'alpine' not in str(properties.get('os', '')).lower() or properties.get('release') != '3.20':
        raise TargetDrift('INCUS_IMAGE_NOT_ALPINE_320')
    profile = _read_default_profile(go, go['default_profile_used_by'])
    memory_output = command(['free', '-b'])
    disk_output = command(['df', '-B1', '--output=avail', str(ROOT)])
    memory_row = next((line.split()[1:] for line in memory_output.decode('ascii', errors='strict').splitlines()
                       if line.startswith('Mem:')), [])
    disk_rows = [line.split() for line in disk_output.decode('ascii', errors='strict').splitlines()[1:] if line.split()]
    if len(memory_row) < 6 or not all(value.isdigit() for value in memory_row[:6]) or not disk_rows or not disk_rows[-1][0].isdigit():
        raise TargetDrift('RESOURCE_BASELINE_UNREADABLE')
    resource_baseline = {'memory_total_bytes': int(memory_row[0]),
                         'memory_available_bytes': int(memory_row[5]),
                         'filesystem_available_bytes': int(disk_rows[-1][0])}
    listen_port = go['proxy']['listen'].rsplit(':', 1)[1]
    ss = command(['ss', '-H', '-ltn'])
    if _listener_rows(ss, int(listen_port)):
        raise TargetDrift('LISTEN_PORT_IN_USE')
    listener_rows = _listener_rows(command(['ss', '-H', '-ltnp']), 10001)
    if any(_listener_rows(ss, port) for port in (80, 443, 16080, 16081)):
        raise TargetDrift('FORBIDDEN_LISTENER_PRESENT')
    if go['target']['instance'] in str(strict_json(command(['incus', 'list', '--project', 'default', '--format', 'json']))):
        raise TargetDrift('INSTANCE_NAME_COLLISION')
    profile_rows = strict_json(command(['incus', 'profile', 'list', '--project', 'default', '--format', 'json']))
    if any(row.get('name') in {go['target']['profile'], go['target']['base_profile']}
           for row in profile_rows):
        raise TargetDrift('PROFILE_NAME_COLLISION')
    incus_projects, incus_routes = _incus_route_inventory()
    if 'default' not in incus_projects:
        raise TargetDrift('INCUS_PROJECT_DRIFT')
    windows = b''
    if host == '192.168.178.58':
        windows = _windows_snapshot()
    _assert_approved_route_state(go, listener_rows, incus_routes, windows, incus_projects)
    return {'listeners_10001': listener_rows, 'incus_10001_routes': incus_routes,
            'incus_projects': incus_projects,
            'windows_rules_portproxy': windows, 'resources': resource_baseline,
            'approved_route_state_sha256': go['approved_route_state_sha256'],
            'default_profile_sha256': profile['sha256'],
            'derived_base_profile': profile['derived']}




def _incus(*args: str) -> bytes:
    if args and (args[0] == 'query' or args[:1] == ('info',)):
        return _inventory_command(['incus', *args])
    return command(['incus', *args])


def _instance_state(instance: str) -> str:
    data = strict_json(_incus('info', instance, '--format', 'json'))
    return str(data.get('status', data.get('state', ''))).lower()


def _listeners() -> bytes:
    return command(['ss', '-H', '-ltnp'])


def _assert_no_fixture_listener(port: str) -> None:
    if _listener_rows(_listeners(), int(port)):
        raise TargetDrift('FIXTURE_LISTENER_EARLY')


def _run_fixture(go: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Execute the one-shot, uniquely named loopback fixture after JIT approval."""
    global _INVENTORY_CLEANUP_MODE
    _INVENTORY_CLEANUP_MODE = False
    target, proxy = go['target'], go['proxy']
    instance, profile, base_profile = target['instance'], target['profile'], target['base_profile']
    port = proxy['listen'].rsplit(':', 1)[1]
    created_profile = created_base = created_instance = False
    profile_marker_set = False
    derived = baseline['derived_base_profile']
    evidence: dict[str, Any] = {'status': 'RUNNING', 'source_commit': go['source_commit'],
                                'target_endpoint': target['endpoint'], 'project': target['project'],
                                'server_version': target['server_version'], 'profile': profile, 'instance': instance,
                                'base_profile': base_profile,
                                'default_profile_sha256': go['default_profile_sha256'],
                                'fixture_base_profile_sha256': go['fixture_base_profile_sha256'],
                                'approved_route_state_sha256': baseline['approved_route_state_sha256'],
                                'default_profile_used_by': go['default_profile_used_by'],
                                'run_id': target['run_id'], 'target_host': target['host'],
                                'listener_before_sha256': _listener_digest(_listeners(), 10001)[1],
                                'listener_10001_before_count': len(baseline['listeners_10001']),
                                'listener_10001_before_sha256': approved_route_state_sha256(
                                    baseline['listeners_10001'], [], b'', []) and
                                    digest(json.dumps(_safe_listener_tuples(baseline['listeners_10001']),
                                                      sort_keys=True, separators=(',', ':')).encode()),
                                'incus_projects_before': baseline['incus_projects'],
                                'incus_10001_routes_before_count': len(baseline['incus_10001_routes']),
                                'incus_10001_routes_before_sha256': digest(json.dumps(
                                    baseline['incus_10001_routes'], sort_keys=True, separators=(',', ':')).encode()),
                                'windows_rules_before_sha256': digest(baseline['windows_rules_portproxy']),
                                'resource_baseline': baseline['resources']}

    def checkpoint() -> None:
        _read_default_profile(go, go['default_profile_used_by'])
        listeners = _listener_rows(_listeners(), 10001)
        if listeners != baseline['listeners_10001']:
            raise TargetDrift('AUTHORIZED_LISTENER_CHANGED')
        projects, routes = _incus_route_inventory()
        if projects != baseline['incus_projects'] or routes != baseline['incus_10001_routes']:
            raise TargetDrift('INCUS_10001_ROUTE_CHANGED')
        if target['host'] == '192.168.178.58':
            _assert_windows_unchanged(baseline['windows_rules_portproxy'], _windows_snapshot())
        _assert_approved_route_state(go, listeners, routes,
                                     baseline['windows_rules_portproxy'], projects)

    def prepare_write(*args: str) -> None:
        checkpoint()
        if args[:2] == ('profile', 'create'):
            names = strict_json(_incus('profile', 'list', '--project', 'default', '--format', 'json'))
            if (not isinstance(names, list)
                    or any(not isinstance(row, dict) or not isinstance(row.get('name'), str) for row in names)):
                raise TargetDrift('PROFILE_NAME_INVENTORY_UNREADABLE')
            if any(row['name'] == args[2] for row in names):
                raise TargetDrift('PROFILE_NAME_COLLISION')
        elif args[:1] == ('init',):
            names = strict_json(_incus('list', '--project', 'default', '--format', 'json'))
            if (not isinstance(names, list)
                    or any(not isinstance(row, dict) or not isinstance(row.get('name'), str) for row in names)):
                raise TargetDrift('INSTANCE_NAME_INVENTORY_UNREADABLE')
            if any(row['name'] == args[2] for row in names):
                raise TargetDrift('INSTANCE_NAME_COLLISION')

    def write(*args: str) -> bytes:
        prepare_write(*args)
        return _incus(*args)

    def query_profile(name: str) -> dict[str, Any] | None:
        try:
            response = strict_json(_incus('query', _profile_api_path(name, 'default')))
        except TargetDrift as exc:
            if exc.args and exc.args[0] == 'JIT_COMMAND_FAILED':
                return None
            raise
        if not isinstance(response, dict) or response.get('name') != name:
            raise TargetDrift('TEMP_PROFILE_READBACK_UNVERIFIED')
        return response

    def query_instance() -> dict[str, Any] | None:
        try:
            response = strict_json(_incus('query', _instance_api_path(instance, 'default')))
        except TargetDrift as exc:
            if exc.args and exc.args[0] == 'JIT_COMMAND_FAILED':
                return None
            raise
        if not isinstance(response, dict) or response.get('name') != instance:
            raise TargetDrift('TEMP_INSTANCE_READBACK_UNVERIFIED')
        return response

    def recover_profile_create(name: str, *, is_base: bool) -> None:
        nonlocal created_base, created_profile
        observed = query_profile(name)
        if _profile_create_readback_owned(observed, name):
            if is_base:
                created_base = True
            else:
                created_profile = True

    def recover_instance_create() -> None:
        nonlocal created_instance
        observed = query_instance()
        if _instance_create_readback_owned(observed, instance, target['run_id'], base_profile, profile):
            created_instance = True

    try:
        prepare_write('profile', 'create', base_profile, '--project', 'default')
        try:
            _incus('profile', 'create', base_profile, '--project', 'default')
            created_base = True
        except Exception:
            recover_profile_create(base_profile, is_base=True)
            raise
        for key, value in sorted(derived['config'].items()):
            write('profile', 'set', base_profile, key, value, '--project', 'default')
        if 'root' in derived['devices']:
            device = derived['devices']['root']
            write('profile', 'device', 'add', base_profile, 'root', 'disk',
                  'path=/', f'pool={device["pool"]}', '--project', 'default')
        if 'eth0' in derived['devices']:
            device = derived['devices']['eth0']
            write('profile', 'device', 'add', base_profile, 'eth0', 'nic',
                  'name=eth0', f'network={device["network"]}', '--project', 'default')
        prepare_write('profile', 'create', profile, '--project', 'default')
        try:
            _incus('profile', 'create', profile, '--project', 'default')
            created_profile = True
        except Exception:
            recover_profile_create(profile, is_base=False)
            raise
        try:
            write('profile', 'set', profile, 'user.q449.run_id', target['run_id'], '--project', 'default')
            profile_marker_set = True
        except Exception:
            observed = query_profile(profile)
            if (observed is not None and observed.get('config') == {'user.q449.run_id': target['run_id']}):
                profile_marker_set = True
            raise
        write('profile', 'device', 'add', profile, 'q449-listener', 'proxy',
              f'listen={proxy["listen"]}', f'connect={proxy["connect"]}', f'bind={proxy["bind"]}',
              '--project', 'default')
        _assert_no_fixture_listener(port)
        _read_default_profile(go, go['default_profile_used_by'])
        _assert_fixture_profile(go, strict_json(_incus('query', _profile_api_path(profile, 'default'))), [])
        prepare_write('init', target['image_fingerprint'], instance, '--project', 'default',
                      '--profile', base_profile, '--profile', profile, '--no-start')
        try:
            _incus('init', target['image_fingerprint'], instance, '--project', 'default',
                   '--profile', base_profile, '--profile', profile, '--no-start')
            created_instance = True
        except Exception:
            recover_instance_create()
            raise
        write('config', 'set', instance, 'user.q449.run_id', target['run_id'], '--project', 'default')
        shown = strict_json(write('query', _instance_api_path(instance, 'default')))
        if shown.get('config', {}).get('user.q449.run_id') != target['run_id'] or _instance_state(instance) != 'stopped':
            raise TargetDrift('INSTANCE_NOT_STOPPED')
        fixture_consumers = [f'/1.0/instances/{instance}']
        default_before_start = _read_default_profile(go, go['default_profile_used_by'])
        fixture_before_start = _assert_fixture_profile(
            go, strict_json(_incus('query', _profile_api_path(profile, 'default'))),
            fixture_consumers)
        _assert_base_profile(
            go, strict_json(_incus('query', _profile_api_path(base_profile, 'default'))),
            fixture_consumers, derived)
        default_before_start['derived'] = derived
        _verify_effective_instance(go, default_before_start, fixture_before_start)
        _assert_no_fixture_listener(port)
        write('start', instance, '--project', 'default')
        if _instance_state(instance) != 'running':
            raise TargetDrift('INSTANCE_START_UNVERIFIED')
        listeners = _listeners()
        evidence['listener_after_start'] = _listener_digest(listeners, int(port))[1]
        fixture_rows = _listener_rows(listeners, int(port))
        if len(fixture_rows) != 1 or not re.search(rb'\s127\.0\.0\.1:' + port.encode() + rb'\s', fixture_rows[0]):
            raise TargetDrift('FIXTURE_LISTENER_ATTRIBUTION_UNVERIFIED')
        if not re.search(rb'users:\(\("(?:incusd|incus|forkproxy)",pid=[0-9]+', fixture_rows[0]):
            raise TargetDrift('FIXTURE_INCUS_PROCESS_UNVERIFIED')
        default_after_start = _read_default_profile(go, go['default_profile_used_by'])
        fixture_after_start = _assert_fixture_profile(
            go, strict_json(_incus('query', _profile_api_path(profile, 'default'))),
            fixture_consumers)
        _assert_base_profile(
            go, strict_json(_incus('query', _profile_api_path(base_profile, 'default'))),
            fixture_consumers, derived)
        default_after_start['derived'] = derived
        evidence['effective_devices_after_start'] = _verify_effective_instance(
            go, default_after_start, fixture_after_start)
        write('exec', instance, '--project', 'default', '--', 'sh', '-c',
              'busybox httpd -f -p 127.0.0.1:8080 >/dev/null 2>&1 &')
        response = command(['curl', '--fail', '--silent', '--show-error', '--max-time', '5',
                            f'http://127.0.0.1:{port}/'])
        if not response:
            raise TargetDrift('FIXTURE_HTTP_UNVERIFIED')
        evidence['http_response_sha256'] = digest(response)
        after_10001 = _listener_rows(command(['ss', '-H', '-ltnp']), 10001)
        if after_10001 != baseline['listeners_10001']:
            raise TargetDrift('AUTHORIZED_LISTENER_CHANGED')
        incus_projects_after, incus_routes_after = _incus_route_inventory()
        if incus_projects_after != baseline['incus_projects'] or incus_routes_after != baseline['incus_10001_routes']:
            raise TargetDrift('INCUS_10001_ROUTE_CHANGED')
        after_windows = b''
        if target['host'] == '192.168.178.58':
            after_windows = _windows_snapshot()
            _assert_windows_unchanged(baseline['windows_rules_portproxy'], after_windows)
        after_route_state_sha256 = approved_route_state_sha256(
            after_10001, incus_routes_after, after_windows, incus_projects_after)
        if after_route_state_sha256 != baseline['approved_route_state_sha256']:
            raise TargetDrift('APPROVED_ROUTE_STATE_CHANGED')
        evidence['listener_10001_after_count'] = len(after_10001)
        evidence['listener_10001_after_sha256'] = _listener_digest(
            command(['ss', '-H', '-ltnp']), 10001)[1]
        evidence['incus_10001_routes_after_count'] = len(incus_routes_after)
        evidence['incus_10001_routes_after_sha256'] = digest(json.dumps(
            incus_routes_after, sort_keys=True, separators=(',', ':')).encode())
        evidence['incus_projects_after'] = incus_projects_after
        evidence['windows_rules_after_sha256'] = digest(after_windows)
        evidence['approved_route_state_sha256_after'] = after_route_state_sha256
        evidence['status'] = 'PASS'
        return evidence
    finally:
        # Cleanup is restricted to the exact approved names, in GO order.
        _INVENTORY_CLEANUP_MODE = True
        active_error = sys.exc_info()[1]
        cleanup_route_errors: list[FixtureError] = []

        def cleanup_checkpoint() -> None:
            try:
                checkpoint()
            except FixtureError as exc:
                cleanup_route_errors.append(exc)

        def cleanup_write(*args: str) -> bytes:
            cleanup_checkpoint()
            return _incus(*args)

        def owned_instance() -> dict[str, Any]:
            observed = query_instance()
            config = observed.get('config') if observed is not None else None
            if (observed is None or observed.get('project', 'default') != 'default'
                    or observed.get('profiles') != [base_profile, profile]
                    or observed.get('devices') not in ({}, None)
                    or not isinstance(config, dict)
                    or set(config) - {'user.q449.run_id'}
                    or ('user.q449.run_id' in config
                        and config['user.q449.run_id'] != target['run_id'])):
                raise TargetDrift('INSTANCE_OWNERSHIP_UNVERIFIED')
            return observed

        def owned_fixture_profile(expected_consumers: list[str]) -> dict[str, Any]:
            observed = query_profile(profile)
            if observed is None or observed.get('project', 'default') != 'default':
                raise TargetDrift('PROFILE_OWNERSHIP_UNVERIFIED')
            if profile_marker_set:
                expected_device = {'type': 'proxy', 'listen': proxy['listen'],
                                   'connect': proxy['connect'], 'bind': proxy['bind']}
                if not _fixture_profile_cleanup_prefix_owned(
                        observed, profile, 'default', target['run_id'],
                        expected_device, expected_consumers):
                    raise TargetDrift('PROFILE_OWNERSHIP_UNVERIFIED')
                return {'config': observed['config'], 'devices': observed['devices'],
                        'used_by': observed['used_by']}
            if (observed.get('config') != {} or observed.get('devices') != {}
                    or observed.get('used_by') != []):
                raise TargetDrift('PROFILE_OWNERSHIP_UNVERIFIED')
            return {'config': {}, 'devices': {}, 'used_by': []}

        def owned_base_profile(expected_consumers: list[str]) -> dict[str, Any]:
            observed = query_profile(base_profile)
            if (observed is None or observed.get('project', 'default') != 'default'
                    or not isinstance(observed.get('config'), dict)
                    or not isinstance(observed.get('devices'), dict)):
                raise TargetDrift('FIXTURE_BASE_PROFILE_OWNERSHIP_UNVERIFIED')
            config, devices = observed['config'], observed['devices']
            if (set(config) - set(derived['config'])
                    or any(value != derived['config'][key] for key, value in config.items())
                    or set(devices) - set(derived['devices'])
                    or any(value != derived['devices'][key] for key, value in devices.items())):
                raise TargetDrift('FIXTURE_BASE_PROFILE_OWNERSHIP_UNVERIFIED')
            if (not isinstance(observed.get('used_by'), list)
                    or observed['used_by'] != expected_consumers):
                raise TargetDrift('FIXTURE_BASE_PROFILE_CONSUMERS_UNVERIFIED')
            return observed

        if created_instance:
            state = _instance_state(instance)
            owned_instance()
            fixture_consumers = [f'/1.0/instances/{instance}']
            owned_fixture_profile(fixture_consumers)
            owned_base_profile(fixture_consumers)
            if state == 'running':
                cleanup_write('stop', instance, '--project', 'default', '--timeout', '30')
            if _instance_state(instance) != 'stopped':
                raise TargetDrift('INSTANCE_STOP_UNVERIFIED')
            owned_instance()
            cleanup_write('delete', instance, '--project', 'default')
        if created_profile:
            owned_fixture_profile([])
            cleanup_write('profile', 'delete', profile, '--project', 'default')
        if created_base:
            owned_base_profile([])
            cleanup_write('profile', 'delete', base_profile, '--project', 'default')
        remaining_instances = strict_json(_incus('list', '--project', 'default', '--format', 'json'))
        remaining_profiles = strict_json(_incus('profile', 'list', '--project', 'default', '--format', 'json'))
        if (created_instance and
                (not isinstance(remaining_instances, list)
                 or any(item.get('name') == instance for item in remaining_instances))):
            raise TargetDrift('INSTANCE_REMOVAL_UNVERIFIED')
        if (created_profile and
                (not isinstance(remaining_profiles, list)
                 or any(item.get('name') == profile for item in remaining_profiles))):
            raise TargetDrift('PROFILE_REMOVAL_UNVERIFIED')
        if (created_base and
                (not isinstance(remaining_profiles, list)
                 or any(item.get('name') == base_profile for item in remaining_profiles))):
            raise TargetDrift('FIXTURE_BASE_PROFILE_REMOVAL_UNVERIFIED')
        cleanup_checkpoint()
        if cleanup_route_errors and active_error is None:
            raise cleanup_route_errors[0]
        _INVENTORY_CLEANUP_MODE = False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-approval-sha256')
    parser.add_argument('--target-host', required=True, choices=['192.168.178.33', '192.168.178.58'])
    parser.add_argument('--capture-route-state', action='store_true')
    parser.add_argument('--capture-project-inventory', action='store_true')
    parser.add_argument('--output')
    args = parser.parse_args(argv)
    if args.capture_project_inventory:
        if args.capture_route_state or args.expected_approval_sha256 is not None or not args.output:
            print('INVALID_CAPTURE_ARGUMENTS', file=sys.stderr)
            return 2
        try:
            capture_project_inventory(args.target_host, args.output)
            return 0
        except Exception as exc:
            code = exc.args[0] if isinstance(exc, FixtureError) else 'CAPTURE_FAILED'
            print(str(code), file=sys.stderr)
            return 2
    if args.capture_route_state:
        if args.expected_approval_sha256 is not None or not args.output:
            print('INVALID_CAPTURE_ARGUMENTS', file=sys.stderr)
            return 2
        try:
            capture_route_state(args.target_host, args.output)
            return 0
        except Exception as exc:
            code = exc.args[0] if isinstance(exc, FixtureError) else 'CAPTURE_FAILED'
            print(str(code), file=sys.stderr)
            return 2
    evidence_fd: int | None = None
    try:
        global _INVENTORY_BYTES_CAPTURED, _INVENTORY_ENTITIES_CAPTURED, _INVENTORY_STARTED_AT
        global _INVENTORY_RESERVE_CLEANUP, _INVENTORY_CLEANUP_MODE
        _INVENTORY_BYTES_CAPTURED = 0
        _INVENTORY_ENTITIES_CAPTURED = 0
        _INVENTORY_STARTED_AT = None
        _INVENTORY_RESERVE_CLEANUP = True
        _INVENTORY_CLEANUP_MODE = False
        if not args.expected_approval_sha256 or not HASH64.fullmatch(args.expected_approval_sha256):
            raise FixtureError('INVALID_EXPECTED_SHA256')
        head, workflow, runner, tests = git_preflight()
        raw = read_once(ROOT / GO_REL)
        if digest(raw) != args.expected_approval_sha256:
            raise FixtureError('APPROVAL_SHA256_MISMATCH')
        go = validate_go(strict_json(raw), args, head, workflow, runner, tests)
        evidence_fd, _ = reserve_and_recheck()
        try:
            baseline = jit(go, args.target_host)
        except Exception as exc:
            code = exc.args[0] if isinstance(exc, FixtureError) else 'JIT_UNREADABLE'
            write_result(evidence_fd, {'status': 'BLOCKED_TARGET_DRIFT', 'code': str(code), 'commands': _COMMAND_AUDIT, 'go_sha256': digest(raw), 'source_commit': head})
            return 2
        try:
            result = _run_fixture(go, baseline)
            _INVENTORY_CLEANUP_MODE = True
            port = go['proxy']['listen'].rsplit(':', 1)[1]
            final_listeners = _listeners()
            if any(re.search(rb':' + port.encode() + rb'\s', line) for line in final_listeners.splitlines()):
                raise TargetDrift('FIXTURE_LISTENER_REMAINS_AFTER_CLEANUP')
            final_10001 = [line for line in command(['ss', '-H', '-ltnp']).splitlines() if re.search(rb':10001\s', line)]
            if final_10001 != baseline['listeners_10001']:
                raise TargetDrift('AUTHORIZED_LISTENER_CHANGED')
            final_projects, final_routes = _incus_route_inventory()
            if final_projects != baseline['incus_projects'] or final_routes != baseline['incus_10001_routes']:
                raise TargetDrift('INCUS_10001_ROUTE_CHANGED')
            if args.target_host == '192.168.178.58':
                _assert_windows_unchanged(baseline['windows_rules_portproxy'], _windows_snapshot())
            result['listener_after_cleanup_sha256'] = _listener_digest(
                final_listeners, int(port))[1]
            result['commands'] = _COMMAND_AUDIT
            _INVENTORY_CLEANUP_MODE = False
        except Exception as exc:
            _INVENTORY_CLEANUP_MODE = False
            code = exc.args[0] if isinstance(exc, FixtureError) else 'FIXTURE_FAILED'
            write_result(evidence_fd, {'status': 'BLOCKED_TARGET_DRIFT', 'code': str(code), 'commands': _COMMAND_AUDIT, 'go_sha256': digest(raw), 'source_commit': head})
            return 2
        result.update({'go_sha256': digest(raw), 'workflow_sha256': go['workflow_sha256'], 'runner_sha256': go['runner_sha256'], 'test_sha256': go['test_sha256'], 'source_commit': head, 'issue447_inventory_sha256': go['issue447_inventory_sha256'], 'resource_admission_sha256': go['resource_admission_sha256']})
        write_result(evidence_fd, result)
        return 0
    except FixtureError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        if evidence_fd is not None:
            os.close(evidence_fd)

if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fixed read-only native R449-33 capture; never installs or changes resources."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
import platform
from pathlib import Path
import stat
import sys
from typing import TYPE_CHECKING, Any

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'modules/tsw_core/src'))
if TYPE_CHECKING:
    from tiny_swarm_world.domain.native_preparation import qualification_failures
    from tiny_swarm_world.infrastructure.adapters.host.native_preparation import NativePreparationInspector
else:
    qualification_failures = importlib.import_module('tiny_swarm_world.domain.native_preparation').qualification_failures
    NativePreparationInspector = importlib.import_module(
        'tiny_swarm_world.infrastructure.adapters.host.native_preparation').NativePreparationInspector

GIB = 1024 ** 3
SELECTION = {'manager': {'cpu_threads': 2, 'memory_bytes': 10 * GIB, 'disk_bytes': 20 * GIB},
             'worker1': {'cpu_threads': 2, 'memory_bytes': 6 * GIB, 'disk_bytes': 50 * GIB},
             'worker2': {'cpu_threads': 4, 'memory_bytes': GIB, 'disk_bytes': 10 * GIB}}
CONFIG = ROOT / '.tiny-swarm/evidence/issue-449/s449-private-20261027/native-infra-override/config/node-providers/provider_config.yaml'


def selection(raw: bytes) -> dict[str, dict[str, int]]:
    import yaml
    class UniqueLoader(yaml.SafeLoader):
        pass
    def mapping(loader: Any, node: Any) -> dict[Any, Any]:
        result: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=True)
            if key in result:
                raise ValueError('DUPLICATE_CONFIG_KEY')
            result[key] = loader.construct_object(value_node, deep=True)
        return result
    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    document = yaml.load(raw, Loader=UniqueLoader)
    if not isinstance(document, dict) or not isinstance(document.get('nodes'), list):
        raise ValueError('CONFIG_INVALID')
    names = {'swarm-manager': 'manager', 'swarm-worker-1': 'worker1', 'swarm-worker-2': 'worker2'}
    expected = {'manager': {'cpu': '2', 'memory': '10GiB', 'disk': '20GiB'},
                'worker1': {'cpu': '2', 'memory': '6GiB', 'disk': '50GiB'},
                'worker2': {'cpu': '4', 'memory': '1GiB', 'disk': '10GiB'}}
    seen = set()
    for node in document['nodes']:
        if not isinstance(node, dict) or node.get('name') not in names or node['name'] in seen:
            raise ValueError('CONFIG_SELECTION_INVALID')
        seen.add(node['name'])
        if node.get('resources') != expected[names[node['name']]]:
            raise ValueError('CONFIG_SELECTION_INVALID')
    if seen != set(names):
        raise ValueError('CONFIG_SELECTION_INVALID')
    return SELECTION


def read_config(expected_config: str) -> bytes:
    for parent in CONFIG.parents:
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('CONFIG_PARENT_UNSAFE')
        if parent == ROOT:
            break
    fd = os.open(CONFIG, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
            raise ValueError('CONFIG_UNSAFE')
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024 or hashlib.sha256(raw).hexdigest() != expected_config:
        raise ValueError('CONFIG_HASH_MISMATCH')
    return raw


def capture(source: str, expected_config: str) -> dict[str, Any]:
    selected = selection(read_config(expected_config))
    facts = NativePreparationInspector(ROOT, service_profile='service-access').inspect()
    failures = qualification_failures(facts, needs_network=False, needs_ports=True, needs_privilege=True,
                                      service_profile='service-access')
    mount: tuple[str, str] | None = None
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        before, separator, after = line.partition(' - ')
        fields = before.split()
        if separator and len(fields) >= 5 and (str(CONFIG.parent) == fields[4] or str(CONFIG.parent).startswith(fields[4].rstrip('/') + '/')):
            if mount is None or len(fields[4]) > len(mount[0]):
                mount = (fields[4], after.split()[0])
    checks = {'structured_service_access_preflight': not failures,
              'selection_budget': selected == SELECTION,
              'memory': facts.memory_bytes >= 17 * GIB,
              'cpu': facts.cpu_count >= 8, 'disk': facts.free_disk_bytes >= 150 * GIB,
              'config_source': True, 'native': not facts.is_wsl,
              'private_ext4': mount is not None and mount[1] == 'ext4',
              'incus_version': False}
    return {'schema_version': 'tsw.resource-admission.v1', 'target_host': '192.168.178.33',
            'platform': 'native_linux', 'scenario_id': 'R449-33',
            'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'source_commit': source,
            'candidate': {'provider_config_sha256': expected_config}, 'selection': selected,
            'observed': asdict(facts) | {'kernel': platform.release(), 'filesystem': None if mount is None else mount[1],
                'mount': None if mount is None else mount[0], 'incus_client_version': None, 'incus_server_version': None},
            'thresholds': {'memory_bytes': 17 * GIB, 'cpu_threads': 8, 'free_disk_bytes': 150 * GIB},
            'checks': checks, 'decision': 'PASS' if all(checks.values()) else 'BLOCKED',
            'commands': []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--validate-config-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.validate_config_only:
            selection(read_config(args.config_sha256))
            result = {'status': 'CONFIG_VALIDATED', 'config_sha256': args.config_sha256}
        else:
            result = capture(args.source, args.config_sha256)
        print(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False))
        return 0
    except Exception:
        print(json.dumps({'status': 'RESOURCE_CAPTURE_FAILED'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

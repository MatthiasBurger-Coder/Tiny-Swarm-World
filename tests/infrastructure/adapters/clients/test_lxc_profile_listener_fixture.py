"""Fail-closed tests for the issue 449 opt-in listener fixture runner."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import signal
import subprocess
import threading
from types import SimpleNamespace
from typing import Any
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.linux.qualification import incus_profile_listener_fixture as fixture


def _snapshot_asset_digest():
    return fixture.digest((fixture.ROOT / fixture.WINDOWS_SNAPSHOT_REL).read_bytes())


def _firewall_v2_fixture(legacy):
    """Literal provider protocol fixture with opaque POCO values, not a production converter."""
    kinds = ('address', 'application', 'interface', 'interface_type', 'port', 'security', 'service')
    return {'schema_version': 2, 'store': 'ActiveStore', 'association_model': 'PROVIDER_IDENTITY_ONE_TO_ONE',
            'profiles': [{'identity': item['Name'], 'value': item} for item in legacy['profiles']],
            'settings': [{'identity': json.dumps(item, sort_keys=True), 'value': item} for item in legacy['settings']],
            'rules': [{'identity': item['rule']['Name'], 'value': item['rule']} for item in legacy['rules']],
            'filters': {kind: [{'identity': item['rule']['Name'], 'value': item[kind][0]}
                               for item in legacy['rules']] for kind in kinds},
            'cim_layout': {'provider_identity': ['class_name', 'namespace', 'server', 'path'],
                           'native_property': ['cim_type', 'flags', 'value'],
                           'adapted_override': ['member_type', 'clr_type', 'alias_target', 'value'],
                           'enum_view': ['clr_type', 'name'],
                           'equivalent_rule': 'same-name exact CLR type/value',
                           'alias_rule': 'native referenced-member exact CLR type/value'}}


def _certificate_fixture(legacy):
    full = _firewall_v2_fixture(legacy)
    for kind in ('profiles', 'settings', 'rules'):
        full[kind].sort(key=lambda row: row['identity'])
    for rows in full['filters'].values():
        rows.sort(key=lambda row: row['identity'])
    raw = json.dumps(full, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    counts = {kind: len(full[kind]) for kind in ('rules', 'profiles', 'settings')}
    counts.update({kind: len(rows) for kind, rows in full['filters'].items()})
    return {'schema_version': 'tsw.windows-firewall-certificate.v1', 'query_sha256': _snapshot_asset_digest(),
            'snapshot_sha256': fixture.digest(raw), 'snapshot_bytes': len(raw), 'snapshot_schema_version': 2,
            'store': 'ActiveStore', 'association_model': 'PROVIDER_IDENTITY_ONE_TO_ONE', 'counts': counts}


def _fixture_instance_dto(go, derived, properties, phase='init'):
    maps = json.dumps([{'Isuid': True, 'Isgid': False, 'Hostid': 1000000, 'Nsid': 0, 'Maprange': 65536},
                       {'Isuid': False, 'Isgid': True, 'Hostid': 1000000, 'Nsid': 0, 'Maprange': 65536}], separators=(',', ':'))
    config = {'user.q449.run_id': go['target']['run_id'], 'volatile.base_image': go['target']['image_fingerprint'],
              'volatile.uuid': '11111111-1111-4111-8111-111111111111',
              'volatile.uuid.generation': '11111111-1111-4111-8111-111111111111',
              'volatile.cloud-init.instance-id': '22222222-2222-4222-8222-222222222222',
              'volatile.idmap.base': '1000000', 'volatile.idmap.next': maps,
              'volatile.last_state.idmap': '[]', 'volatile.apply_template': 'create',
              **{'image.' + key: value for key, value in properties.items()}}
    if phase != 'init':
        config.pop('volatile.apply_template')
        config.update({'volatile.idmap.current': maps, 'volatile.last_state.idmap': maps,
                       'volatile.last_state.power': 'RUNNING' if phase == 'running' else 'STOPPED',
                       'volatile.last_state.ready': 'false', 'volatile.cpu.nodes': '0'})
        if 'eth0' in derived['devices']:
            config['volatile.eth0.hwaddr'] = '10:66:6a:00:00:01'
            if phase == 'running':
                config['volatile.eth0.host_name'] = 'vethabc123'
    return {'name': go['target']['instance'], 'project': 'default', 'type': 'container',
            'status': 'Running' if phase == 'running' else 'Stopped',
            'config': config, 'devices': {}, 'profiles': [go['target']['base_profile'], go['target']['profile']],
            'expanded_config': {**derived['config'], **config},
            'expanded_devices': {**derived['devices'], 'q449-listener': {'type': 'proxy', **go['proxy']}}}


class PrivateEvidenceFilesystemTests(unittest.TestCase):
    def _mountinfo(self, directory: Path, filesystem: str) -> Path:
        mountinfo = directory / 'mountinfo'
        mountinfo.write_text(
            f'36 25 0:32 / {directory} rw,relatime - {filesystem} /dev/test rw\n',
            encoding='utf-8')
        return mountinfo

    def test_accepts_evidence_on_ext4_mount(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            fixture._require_private_ext4(path, self._mountinfo(path, 'ext4'))

    def test_rejects_drvfs_and_other_filesystem_types(self):
        for filesystem in ('drvfs', 'ntfs3', 'tmpfs', 'overlay'):
            with self.subTest(filesystem=filesystem), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                with self.assertRaisesRegex(
                        fixture.FixtureError, 'PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE'):
                    fixture._require_private_ext4(path, self._mountinfo(path, filesystem))

    def test_rejects_windows_drive_mount_paths_before_mountinfo_lookup(self):
        missing_mountinfo = Path('/path/that/must/not/be/read')
        for path in (Path('/mnt/c/checkout'), Path('/mnt/d/checkout')):
            with self.subTest(path=path), self.assertRaisesRegex(
                    fixture.FixtureError, 'PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE'):
                fixture._require_private_ext4(path, missing_mountinfo)

    def test_fails_closed_when_filesystem_cannot_be_identified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with self.assertRaisesRegex(
                    fixture.FixtureError, 'PRIVATE_EVIDENCE_FILESYSTEM_UNVERIFIABLE'):
                fixture._require_private_ext4(path, path / 'missing-mountinfo')
            malformed = path / 'malformed-mountinfo'
            malformed.write_text('not a mountinfo row\n', encoding='utf-8')
            with self.assertRaisesRegex(
                    fixture.FixtureError, 'PRIVATE_EVIDENCE_FILESYSTEM_UNVERIFIABLE'):
                fixture._require_private_ext4(path, malformed)

    def test_rejects_duplicate_deepest_mount_rows_in_either_order(self):
        for filesystems in (('ext4', 'drvfs'), ('drvfs', 'ext4'), ('ext4', 'ext4')):
            with self.subTest(filesystems=filesystems), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                mountinfo = path / 'duplicate-mountinfo'
                rows = [
                    f'{index + 36} 25 0:32 / {path} rw,relatime - {filesystem} /dev/test rw'
                    for index, filesystem in enumerate(filesystems)
                ]
                mountinfo.write_text('\n'.join(rows) + '\n', encoding='utf-8')
                with self.assertRaisesRegex(
                        fixture.FixtureError, 'PRIVATE_EVIDENCE_FILESYSTEM_UNVERIFIABLE'):
                    fixture._require_private_ext4(path, mountinfo)


class _FixtureBehaviorTestCase(unittest.TestCase):
    """Keep unrelated behavior tests independent of their temporary mount type."""

    def setUp(self):
        fixture._INVENTORY_TARGET_HOST = '192.168.178.33'
        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_ENTITIES_CAPTURED = 0
        fixture._INVENTORY_ENTITY_SLOTS.clear()
        fixture._INVENTORY_STARTED_AT = None
        fixture._INVENTORY_RESERVE_CLEANUP = False
        fixture._INVENTORY_CLEANUP_MODE = False
        patcher = patch.object(fixture, '_require_private_ext4')
        patcher.start()
        self.addCleanup(patcher.stop)


class PrivateEvidenceEntrypointTests(unittest.TestCase):
    def test_capture_stops_before_commands_or_evidence_directory_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, '_require_private_ext4',
                               side_effect=fixture.FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')) as guard,
                  patch.object(fixture, 'command') as command,
                  patch.object(fixture, 'git_preflight') as git):
                status = fixture.main([
                    '--capture-route-state', '--target-host', '192.168.178.33',
                    '--output', '.tiny-swarm/evidence/issue-449/s449-private-20261027/capture.json'])
            guard.assert_called_once_with(root)
            command.assert_not_called()
            git.assert_not_called()
            self.assertEqual(status, 2)
            self.assertFalse((root / fixture.PRIVATE_EVIDENCE_REL).exists())

    def test_go_entrypoint_stops_before_reservation_or_host_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / fixture.PRIVATE_EVIDENCE_REL
            evidence.mkdir(parents=True, mode=0o700)
            evidence.chmod(0o700)
            go = root / fixture.GO_REL
            go.write_bytes(b'{}\n')
            go.chmod(0o600)
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_require_private_ext4',
                               side_effect=fixture.FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')) as guard,
                  patch.object(fixture, 'reserve_and_recheck') as reserve,
                  patch.object(fixture, 'command') as command):
                status = fixture.main([
                    '--target-host', '192.168.178.33', '--expected-approval-sha256', 'b' * 64])
            guard.assert_called_once_with(evidence)
            reserve.assert_not_called()
            command.assert_not_called()
            self.assertEqual(status, 2)
            self.assertEqual({path.name for path in evidence.iterdir()}, {go.name})

    def test_reservation_entrypoint_checks_filesystem_before_evidence_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = root / fixture.RESULT_REL
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, '_require_private_ext4',
                               side_effect=fixture.FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')) as guard,
                  patch.object(fixture, 'command') as command,
                  self.assertRaisesRegex(
                      fixture.FixtureError, 'PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')):
                fixture.reserve_and_recheck()
            guard.assert_called_once_with(root)
            command.assert_not_called()
            self.assertFalse(result.parent.exists())


class StrictJsonTests(_FixtureBehaviorTestCase):
    def test_rejects_duplicate_keys_at_any_depth(self):
        with self.assertRaises(fixture.FixtureError):
            fixture.strict_json(b'{"outer":{"x":1,"x":2}}')

    def test_rejects_invalid_utf8_and_non_json_constants(self):
        for raw in (b'\xff', b'{"x":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(fixture.FixtureError):
                fixture.strict_json(raw)

    def test_canonical_profile_hash_uses_compact_sorted_utf8(self):
        cfg = {'z': '☃', 'a': 'x'}
        devices = {'eth0': {'nictype': 'bridged'}}
        expected = hashlib.sha256('{"config":{"a":"x","z":"☃"},"devices":{"eth0":{"nictype":"bridged"}}}'.encode()).hexdigest()
        self.assertEqual(fixture.canonical_profile_sha256(cfg, devices), expected)

    def test_profile_hash_known_answers_key_order_and_invalid_values(self):
        self.assertEqual(fixture.canonical_profile_sha256({}, {}),
                         '079aa36c8373b157f411a389cd569d038a5da42dfcb380ba625a366cc95205c3')
        self.assertEqual(fixture.canonical_profile_sha256({'user.note': 'München'}, {}),
                         'cc7a06da6878973e8431910042d01f3ff1a8a7bafb972917a3ee329436fddd2c')
        self.assertEqual(fixture.canonical_profile_sha256({'a': 1, 'b': 2}, {}),
                         fixture.canonical_profile_sha256({'b': 2, 'a': 1}, {}))
        for config in ({'x': float('nan')}, {'x': object()}, {'x': '\ud800'}):
            with self.subTest(config=config), self.assertRaises(fixture.FixtureError):
                fixture.canonical_profile_sha256(config, {})

    def test_fixture_base_allowlists_exact_string_values_and_forces_autostart_off(self):
        for autostart in ('true', 'false', None):
            config = {'limits.cpu': '2', 'limits.memory': '4GiB'}
            if autostart is not None:
                config['boot.autostart'] = autostart
            derived = fixture._derive_fixture_base({'config': config, 'devices': {
                'root': {'type': 'disk', 'path': '/', 'pool': 'default'},
                'eth0': {'type': 'nic', 'name': 'eth0', 'network': 'incusbr0'}}})
            self.assertEqual(derived['config']['boot.autostart'], 'false')
            self.assertEqual(derived['config']['limits.cpu'], '2')
            self.assertEqual(derived['config']['limits.memory'], '4GiB')
        for key, value in (('limits.cpu', 2), ('limits.cpu', '02'), ('limits.cpu', '2\n'),
                           ('limits.memory', True), ('limits.memory', '2TB'),
                           ('boot.autostart', True), ('boot.autostart', 'TRUE'),
                           ('security.privileged', 'true'), ('raw.lxc', 'anything'),
                           ('linux.kernel_modules', 'x'), ('idmap.base', 'x'), ('unknown', 'x')):
            with self.subTest(key=key, value=value), self.assertRaises(fixture.TargetDrift):
                fixture._derive_fixture_base({'config': {key: value}, 'devices': {}})
        for devices in (
                {'root': {'type': 'disk', 'path': '/host', 'pool': 'default'}},
                {'web': {'type': 'proxy', 'listen': 'tcp:0.0.0.0:10001'}},
                {'root': {'type': 'disk', 'path': '/', 'pool': 'default', 'source': '/tmp'}},
                {'root': {'type': 'disk', 'path': '/', 'pool': '../unsafe'}},
                {'eth0': {'type': 'nic', 'name': 'eth0', 'network': 'bad network'}},
                {'unknown': {'type': 'disk', 'path': '/', 'pool': 'default'}}):
            with self.subTest(devices=devices), self.assertRaises(fixture.TargetDrift):
                fixture._derive_fixture_base({'config': {}, 'devices': devices})


class RouteStateDigestTests(_FixtureBehaviorTestCase):
    def test_shared_remote_parser_accepts_incus_605_addr_and_rejects_legacy_url(self):
        remote_json = b'{"local":{"Addr":"unix://","AuthType":"tls","KeepAlive":30,"Project":"","Protocol":"incus","CredHelper":"","Public":false,"Global":false,"Static":true}}'
        with patch.object(fixture, '_inventory_command', side_effect=[remote_json, b'local']) as run:
            fixture._COMMAND_AUDIT.clear()
            fixture._assert_local_incus_remote()
        self.assertEqual(run.call_args_list[0].args[0], ['incus', 'remote', 'list', '--format', 'json'])
        self.assertEqual(run.call_args_list[1].args[0], ['incus', 'remote', 'get-default'])
        self.assertTrue(all('stdout_sha256' not in record for record in fixture._COMMAND_AUDIT))
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_ENDPOINT_DRIFT'):
            fixture._validate_local_incus_remote({'local': {'URL': 'unix://'}}, 'local')
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_ENDPOINT_DRIFT'):
            fixture._validate_local_incus_remote({'local': {'Addr': 'https://remote'}}, 'local')
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_REMOTE_DRIFT'):
            fixture._validate_local_incus_remote({'local': {'Addr': 'unix://'}}, 'remote')

    def test_route_state_digest_uses_safe_listener_projection_and_snapshot_hash(self):
        listeners = [b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))']
        routes = [{'project': 'default', 'owner_type': 'profile', 'owner': 'manager', 'device': 'web',
                   'device_type': 'proxy', 'effective_profiles': ['manager'],
                   'listen': {'protocol': 'tcp', 'address': '127.0.0.1', 'port': 10001},
                   'connect': {'protocol': 'tcp', 'address': '127.0.0.1', 'port': 8080}, 'bind': 'host'}]
        windows = b'firewall\r\n--PORTPROXY--\r\n10001\r\n'
        payload = {
            'listeners_10001_count': 1,
            'listeners_10001_sha256': hashlib.sha256(json.dumps(
                fixture._safe_listener_tuples(listeners), sort_keys=True, separators=(',', ':'),
                ensure_ascii=False).encode('utf-8')).hexdigest(),
            'incus_projects': ['default'],
            'incus_10001_routes': routes,
            'windows_snapshot_sha256': hashlib.sha256(windows).hexdigest(),
        }
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                             ensure_ascii=False).encode('utf-8')).hexdigest()
        self.assertEqual(fixture.approved_route_state_sha256(listeners, routes, windows, ['default']), expected)

    def test_successfully_read_empty_route_state_is_a_valid_bound_baseline(self):
        outputs = [b'',
                   b'[{"name":"default"}]', b'{"name":"default","description":"","config":{}}',
                   b'[]', b'[]']
        with patch.object(fixture, '_assert_host_identity'), patch.object(
                fixture, '_assert_local_incus_remote_inventory'), patch.object(
                fixture, 'command', side_effect=outputs) as command:
            state = fixture._route_state('192.168.178.33')
        self.assertEqual(state['listeners_10001'], [])
        self.assertEqual(state['incus_10001_routes'], [])
        self.assertEqual(state['incus_projects'], ['default'])
        self.assertEqual(state['approved_route_state_sha256'],
                         fixture.approved_route_state_sha256([], [], b'', ['default']))
        self.assertEqual(command.call_count, 5)

    def test_empty_route_inventory_covers_and_binds_every_project(self):
        outputs = [b'[{"name":"default"},{"name":"qa"}]',
                   b'{"name":"default","description":"","config":{}}', b'[]', b'[]',
                   b'{"name":"qa","description":"","config":{"features.images":"true","features.profiles":"true"}}',
                   b'[]', b'[]']
        with patch.object(fixture, 'command', side_effect=outputs) as command:
            projects, routes = fixture._incus_route_inventory()
        self.assertEqual(projects, ['default', 'qa'])
        self.assertEqual(routes, [])
        self.assertEqual(command.call_count, 7)
        self.assertNotEqual(fixture.approved_route_state_sha256([], [], b'', projects),
                            fixture.approved_route_state_sha256([], [], b'', ['default']))

    def test_route_inventory_reads_shared_profiles_only_from_default_project(self):
        calls = []

        def command(argv):
            calls.append(tuple(argv))
            responses = {
                ('incus', 'project', 'list', '--format', 'json'):
                    b'[{"name":"default"},{"name":"issue447"},{"name":"legacy"}]',
                ('incus', 'query', '/1.0/projects/default'):
                    b'{"name":"default","description":"","config":{"features.profiles":"true"}}',
                ('incus', 'query', '/1.0/projects/issue447'):
                    b'{"name":"issue447","description":"","config":{"features.profiles":"false"}}',
                ('incus', 'query', '/1.0/projects/legacy'):
                    b'{"name":"legacy","description":"","config":{}}',
                ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'):
                    b'[{"name":"shared","project":"default","config":{},"devices":{"listener":{"type":"proxy","listen":"tcp:0.0.0.0:10001","connect":"tcp:127.0.0.1:8080"}},"used_by":["/1.0/instances/swarm-manager?project=issue447"]}]',
                ('incus', 'query', '/1.0/profiles/shared?project=default'):
                    b'{"name":"shared","project":"default","config":{},"devices":{"listener":{"type":"proxy","listen":"tcp:0.0.0.0:10001","connect":"tcp:127.0.0.1:8080"}},"used_by":["/1.0/instances/swarm-manager?project=issue447"]}',
                ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
                ('incus', 'list', '--project', 'issue447', '--format', 'json'): b'[]',
                ('incus', 'list', '--project', 'legacy', '--format', 'json'): b'[]',
            }
            return responses[tuple(argv)]

        with patch.object(fixture, 'command', side_effect=command):
            projects, routes = fixture._incus_route_inventory()

        self.assertEqual(projects, ['default', 'issue447', 'legacy'])
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]['project'], 'default')
        self.assertEqual(routes[0]['owner'], 'shared')
        self.assertEqual(routes[0]['effective_profiles'], ['shared'])
        self.assertEqual(calls.count(('incus', 'profile', 'list', '--project', 'default', '--format', 'json')), 1)
        self.assertIn(('incus', 'list', '--project', 'issue447', '--format', 'json'), calls)
        self.assertNotIn(('incus', 'profile', 'list', '--project', 'issue447', '--format', 'json'), calls)
        self.assertNotIn(('incus', 'profile', 'list', '--project', 'legacy', '--format', 'json'), calls)

    def test_instance_inventory_rejects_missing_complete_config(self):
        outputs = [b'[{"name":"default"}]',
                   b'{"name":"default","description":"","config":{}}',
                   b'[]', b'[{"name":"broken-instance"}]',
                   b'{"devices":{},"profiles":["default"]}']
        with patch.object(fixture, 'command', side_effect=outputs):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INSTANCE_INVENTORY_UNREADABLE'):
                fixture._incus_route_inventory()

    def test_capture_fails_closed_when_default_project_is_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / fixture.PRIVATE_EVIDENCE_REL
            evidence.mkdir(parents=True, mode=0o700)
            evidence.chmod(0o700)

            def command(argv):
                responses = {
                    ('incus', 'remote', 'list', '--format', 'json'): b'{"local":{"Addr":"unix://"}}',
                    ('incus', 'remote', 'get-default'): b'local',
                    ('ss', '-H', '-ltnp'): b'',
                    ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"qa"}]',
                }
                return responses[tuple(argv)]

            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_assert_host_identity'),
                  patch.object(fixture, '_assert_local_incus_remote_inventory'),
                  patch.object(fixture, 'command', side_effect=command),
                  self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROJECT_DRIFT')):
                fixture.capture_route_state('192.168.178.33',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/pre-go-route-state.json')
            self.assertEqual(list(evidence.iterdir()), [])
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('b' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_route_state', side_effect=fixture.TargetDrift(
                      'WINDOWS_SNAPSHOT_TIMEOUT')),
                  self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_TIMEOUT')):
                fixture.capture_route_state('192.168.178.58',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/windows-timeout.json')
            self.assertEqual(list(evidence.iterdir()), [])


class RouteStateCaptureTests(_FixtureBehaviorTestCase):
    def _private_evidence_root(self, root: Path) -> Path:
        path = root / fixture.PRIVATE_EVIDENCE_REL
        path.mkdir(parents=True, mode=0o700)
        path.chmod(0o700)
        return path

    def test_capture_writes_private_exclusive_artifact_and_preserves_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self._private_evidence_root(root)
            state = {'listeners_10001': [], 'incus_10001_routes': [], 'incus_projects': ['default'],
                     'windows_snapshot': b'',
                     'approved_route_state_sha256': fixture.approved_route_state_sha256([], [], b'', ['default'])}
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_route_state', return_value=state),
                  patch.object(fixture, 'read_once', side_effect=AssertionError('GO must not be read')),
                  patch.object(fixture, 'reserve_and_recheck', side_effect=AssertionError('must not reserve'))):
                fixture.capture_route_state('192.168.178.33',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/native-pre-go-route-state.json')
            output = evidence / 'native-pre-go-route-state.json'
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            payload = fixture.strict_json(output.read_bytes())
            self.assertEqual(payload['target_host'], '192.168.178.33')
            self.assertEqual(payload['target_ip'], '192.168.178.33')
            self.assertEqual(payload['source_commit'], 'a' * 40)
            self.assertEqual(payload['approved_route_state_sha256'], state['approved_route_state_sha256'])
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_route_state', return_value=state),
                  self.assertRaisesRegex(
                    fixture.FixtureError, 'CAPTURE_CREATE_FAILED')):
                fixture.capture_route_state('192.168.178.33',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/native-pre-go-route-state.json')

    def test_capture_rejects_unsafe_directory_and_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self._private_evidence_root(root)
            evidence.chmod(0o755)
            with patch.object(fixture, 'ROOT', root), self.assertRaisesRegex(
                    fixture.FixtureError, 'EVIDENCE_DIR_NOT_PRIVATE'):
                fixture._capture_output_path(
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/capture.json')
            with patch.object(fixture, 'ROOT', root), self.assertRaisesRegex(
                    fixture.FixtureError, 'UNSAFE_CAPTURE_PATH'):
                fixture._capture_output_path('../escape.json')

    def test_capture_never_follows_symlink_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self._private_evidence_root(root)
            destination = evidence / 'destination.json'
            destination.write_bytes(b'preserve')
            (evidence / 'capture.json').symlink_to(destination)
            state = {'listeners_10001': [], 'incus_10001_routes': [], 'incus_projects': ['default'],
                     'windows_snapshot': b'',
                     'approved_route_state_sha256': fixture.approved_route_state_sha256([], [], b'', ['default'])}
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_route_state', return_value=state),
                  self.assertRaisesRegex(fixture.FixtureError, 'CAPTURE_CREATE_FAILED')):
                fixture.capture_route_state('192.168.178.33',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/capture.json')
            self.assertEqual(destination.read_bytes(), b'preserve')

    def test_capture_cli_does_not_require_approval_digest(self):
        with patch.object(fixture, 'capture_route_state') as capture:
            self.assertEqual(fixture.main(['--capture-route-state', '--target-host', '192.168.178.33',
                                           '--output', '.tiny-swarm/evidence/issue-449/s449-private-20261027/capture.json']), 0)
        capture.assert_called_once_with('192.168.178.33',
            '.tiny-swarm/evidence/issue-449/s449-private-20261027/capture.json')

    def test_route_inventory_rejects_names_only_profile_summary_without_detail_fallback(self):
        def command(argv):
            if argv == ['incus', 'project', 'list', '--format', 'json']:
                return b'[{"name":"default"}]'
            if argv == ['incus', 'query', '/1.0/projects/default']:
                return b'{"name":"default","description":"","config":{}}'
            if argv == ['incus', 'profile', 'list', '--project', 'default', '--format', 'json']:
                return b'[{"name":"expected"}]'
            if argv[:2] == ['incus', 'query']:
                return json.dumps({'name': 'other', 'project': 'default',
                                   'config': {}, 'devices': {}, 'used_by': []}).encode()
            raise AssertionError(argv)
        with patch.object(fixture, 'command', side_effect=command):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROFILE_INVENTORY_UNREADABLE'):
                fixture._incus_route_inventory()

    def test_route_inventory_rejects_names_only_instance_summary_without_detail_fallback(self):
        def command(argv):
            if argv == ['incus', 'project', 'list', '--format', 'json']:
                return b'[{"name":"default"}]'
            if argv == ['incus', 'query', '/1.0/projects/default']:
                return b'{"name":"default","description":"","config":{}}'
            if argv == ['incus', 'profile', 'list', '--project', 'default', '--format', 'json']:
                return b'[]'
            if argv == ['incus', 'list', '--project', 'default', '--format', 'json']:
                return b'[{"name":"expected"}]'
            if argv[:2] == ['incus', 'query']:
                return json.dumps({'name': 'other', 'project': 'default',
                                   'config': {}, 'devices': {}, 'profiles': []}).encode()
            raise AssertionError(argv)
        with patch.object(fixture, 'command', side_effect=command):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INSTANCE_INVENTORY_UNREADABLE'):
                fixture._incus_route_inventory()

    def test_route_inventory_rejects_profile_and_instance_wrong_projects(self):
        for resource in ('profile', 'instance'):
            with self.subTest(resource=resource):
                def command(argv):
                    if argv == ['incus', 'project', 'list', '--format', 'json']:
                        return b'[{"name":"default"}]'
                    if argv == ['incus', 'query', '/1.0/projects/default']:
                        return b'{"name":"default","description":"","config":{}}'
                    if argv == ['incus', 'profile', 'list', '--project', 'default', '--format', 'json']:
                        return json.dumps([{'name': 'expected', 'project': 'other', 'config': {}, 'devices': {}, 'used_by': []}]).encode() if resource == 'profile' else b'[]'
                    if argv == ['incus', 'list', '--project', 'default', '--format', 'json']:
                        return json.dumps([{'name': 'expected', 'project': 'other', 'status': 'Running', 'type': 'container', 'config': {}, 'devices': {}, 'profiles': []}]).encode() if resource == 'instance' else b'[]'
                    if argv[:2] == ['incus', 'query']:
                        identity = {'name': 'expected', 'project': 'other',
                                    'config': {}, 'devices': {}}
                        identity['used_by' if resource == 'profile' else 'profiles'] = []
                        return json.dumps(identity).encode()
                    raise AssertionError(argv)
                code = 'INCUS_PROFILE_INVENTORY_UNREADABLE' if resource == 'profile' else 'INCUS_INSTANCE_INVENTORY_UNREADABLE'
                with patch.object(fixture, 'command', side_effect=command):
                    with self.assertRaisesRegex(fixture.TargetDrift, code):
                        fixture._incus_route_inventory()

    def test_read_default_profile_rejects_wrong_name_or_project(self):
        for field in ('name', 'project'):
            with self.subTest(field=field):
                profile = {'name': 'default', 'project': 'default',
                           'config': {}, 'devices': {}, 'used_by': []}
                profile[field] = 'other'
                with patch.object(fixture, '_inventory_command',
                                  return_value=json.dumps(profile).encode()):
                    with self.assertRaisesRegex(fixture.TargetDrift, 'DEFAULT_PROFILE_UNREADABLE'):
                        fixture._read_default_profile({
                            'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
                            'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256(
                                {'boot.autostart': 'false'}, {})}, [])

    def test_capture_executes_read_only_inventory_allowlist_and_binds_all_projects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self._private_evidence_root(root)
            route_device = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001',
                            'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}
            seen = []

            def command(argv):
                key = tuple(argv)
                seen.append(key)
                responses = {
                    ('ip', '-j', '-4', 'addr'): b'[{"addr_info":[{"local":"192.168.178.33"}]}]',
                    ('incus', 'remote', 'list', '--format', 'json'): b'{"local":{"Addr":"unix://"}}',
                    ('incus', 'remote', 'get-default'): b'local',
                    ('ss', '-H', '-ltnp'): b'',
                    ('incus', 'project', 'list', '--format', 'json'):
                        b'[{"name":"default"},{"name":"qa"}]',
                    ('incus', 'query', '/1.0/projects/default'):
                        b'{"name":"default","description":"","config":{}}',
                    ('incus', 'query', '/1.0/projects/qa'):
                        b'{"name":"qa","description":"","config":{"features.profiles":"true"}}',
                    ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'): b'[]',
                    ('incus', 'profile', 'list', '--project', 'qa', '--format', 'json'):
                        json.dumps([{'name': 'qa-profile', 'project': 'qa', 'config': {}, 'devices': {'web': route_device}, 'used_by': []}]).encode(),
                    ('incus', 'query', fixture._profile_api_path('qa-profile', 'qa')):
                        json.dumps({'name': 'qa-profile', 'project': 'qa', 'config': {}, 'devices': {'web': route_device}, 'used_by': []}).encode(),
                    ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
                    ('incus', 'list', '--project', 'qa', '--format', 'json'):
                        json.dumps([{'name': 'qa-instance', 'project': 'qa', 'status': 'Running', 'type': 'container', 'config': {}, 'devices': {'web': route_device}, 'expanded_config': {}, 'expanded_devices': {'web': route_device}, 'profiles': ['qa-profile']}]).encode(),
                    ('incus', 'query', fixture._instance_api_path('qa-instance', 'qa')):
                        json.dumps({'name': 'qa-instance', 'project': 'qa', 'config': {}, 'devices': {'web': route_device},
                                    'profiles': ['default']}).encode(),
                }
                return responses[key]

            def remote_inventory(_argv=None):
                seen.extend([
                    ('incus', 'remote', 'list', '--format', 'json'),
                    ('incus', 'remote', 'get-default'),
                ])

            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('b' * 40, b'w', b'r', b't')),
                  patch.object(fixture, 'command', side_effect=command),
                  patch.object(fixture, '_assert_local_incus_remote_inventory', side_effect=remote_inventory),
                  patch.object(fixture, 'read_once', side_effect=AssertionError('capture must not read GO')),
                  patch.object(fixture, 'reserve_and_recheck', side_effect=AssertionError('capture must not reserve'))):
                fixture.capture_route_state('192.168.178.33',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/pre-go-route-state.json')

            read_only_incus_verbs = {'remote', 'project', 'profile', 'list', 'config', 'query'}
            allowed_executables = {'ip', 'incus', 'ss', 'uname', 'free', 'df'}
            forbidden_incus_mutations = {
                'add', 'attach', 'create', 'delete', 'detach', 'edit', 'init', 'launch',
                'move', 'publish', 'remove', 'rename', 'restore', 'set', 'start', 'stop',
                'unset',
            }
            for argv in seen:
                self.assertIn(argv[0], allowed_executables)
                if argv[0] == 'incus':
                    self.assertIn(argv[1], read_only_incus_verbs)
                    self.assertNotIn(argv[2] if argv[1] in {'profile', 'project', 'config'} else argv[1],
                                     forbidden_incus_mutations)
                    if argv[1] == 'remote':
                        self.assertIn(tuple(argv), {
                            ('incus', 'remote', 'list', '--format', 'json'),
                            ('incus', 'remote', 'get-default'),
                        })
                    if argv[1] == 'project':
                        self.assertEqual(argv[2], 'list')
                    if argv[1] == 'query':
                        self.assertIn(tuple(argv), {('incus', 'query', '/1.0/projects/default'), ('incus', 'query', '/1.0/projects/qa'), ('incus', 'query', fixture._profile_api_path('qa-profile', 'qa')), ('incus', 'query', fixture._instance_api_path('qa-instance', 'qa'))})
                    if argv[1] == 'profile':
                        self.assertEqual(argv[2], 'list')
                    if argv[1] == 'config':
                        self.assertEqual(argv[2], 'show')
            self.assertEqual(seen[1], ('incus', 'remote', 'list', '--format', 'json'))
            self.assertIn(('incus', 'remote', 'list', '--format', 'json'), seen)
            self.assertIn(('incus', 'project', 'list', '--format', 'json'), seen)
            payload = fixture.strict_json((evidence / 'pre-go-route-state.json').read_bytes())
            self.assertEqual(payload['incus_projects'], ['default', 'qa'])
            expected_routes = [
                fixture._safe_route_row('qa', 'instance', 'qa-instance', 'web', route_device, ['qa-profile']),
                fixture._safe_route_row('qa', 'profile', 'qa-profile', 'web', route_device, ['qa-profile']),
            ]
            self.assertEqual(payload['incus_10001_routes'], expected_routes)
            self.assertEqual(payload['approved_route_state_sha256'],
                             fixture.approved_route_state_sha256([], expected_routes, b'', ['default', 'qa']))
            self.assertEqual({path.name for path in evidence.iterdir()}, {'pre-go-route-state.json'})


class ProjectInventoryCaptureTests(_FixtureBehaviorTestCase):
    def _evidence(self, root: Path) -> Path:
        path = root / fixture.PRIVATE_EVIDENCE_REL
        path.mkdir(parents=True, mode=0o700)
        path.chmod(0o700)
        return path

    def test_inventory_capture_cli_uses_only_read_commands_and_never_go_or_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self._evidence(root)
            calls = []
            responses = {
                ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"default"}]',
                ('incus', 'query', '/1.0/projects/default'): b'{"name":"default","description":"","config":{"features.images":"true","features.networks":true,"features.profiles":"false","features.storage.volumes":false}}',
                ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'): b'[]',
                ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
            }
            def inventory(argv):
                calls.append(tuple(argv))
                self.assertFalse((evidence / 'inventory.json').exists())
                return responses[tuple(argv)]
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'wf', b'runner', b'tests')),
                  patch.object(fixture, '_require_private_ext4'),
                  patch.object(fixture, '_assert_host_identity_inventory'),
                  patch.object(fixture, '_assert_local_incus_remote_inventory'),
                  patch.object(fixture, '_require_local_incus_admin'),
                  patch.object(fixture, '_inventory_command', side_effect=inventory),
                  patch.object(fixture, 'read_once', side_effect=AssertionError('GO read forbidden')),
                  patch.object(fixture, 'reserve_and_recheck', side_effect=AssertionError('reservation forbidden'))):
                status = fixture.main(['--capture-project-inventory', '--target-host', '192.168.178.33',
                    '--output', '.tiny-swarm/evidence/issue-449/s449-private-20261027/inventory.json'])
            self.assertEqual(status, 0)
            self.assertEqual(calls, list(responses))
            payload = fixture.strict_json((evidence / 'inventory.json').read_bytes())
            self.assertEqual(set(payload), {'schema_version', 'target_host', 'source_commit', 'projects', 'command_records'})
            self.assertEqual(payload['schema_version'], 'tsw.incus.project-inventory.v1')
            self.assertEqual(payload['projects'][0]['isolation'], {
                'features.images': True, 'features.networks': True,
                'features.profiles': False, 'features.storage.volumes': False})
            self.assertEqual(payload['source_commit'], 'a' * 40)
            self.assertEqual(set(payload['projects'][0]), {'name', 'isolation', 'profiles', 'instances'})
            self.assertTrue(all(set(record) == {'command_id', 'safe_args', 'exit_status', 'stdout_bytes', 'stderr_bytes'}
                                for record in payload['command_records']))
            self.assertEqual((evidence / 'inventory.json').stat().st_mode & 0o777, 0o600)

    def test_inventory_rejects_secret_and_unknown_device_schema(self):
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROJECT_INVENTORY_UNREADABLE'):
            fixture._inventory_config({'api-token': 'secret-value'}, 'INCUS_PROJECT_INVENTORY_UNREADABLE')
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROFILE_INVENTORY_UNREADABLE'):
            fixture._inventory_devices({'x': {'type': 'mystery', 'foo': 'bar'}}, 'INCUS_PROFILE_INVENTORY_UNREADABLE')
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROFILE_INVENTORY_UNREADABLE'):
            fixture._inventory_devices({'x': {'type': 'disk', 'path': '/', 'source': '/safe', 'password': 'secret'}},
                                       'INCUS_PROFILE_INVENTORY_UNREADABLE')

    def test_project_isolation_keeps_unset_feature_values_null_without_inference(self):
        self.assertEqual(fixture._project_isolation({}), {
            'features.images': None,
            'features.networks': None,
            'features.profiles': None,
            'features.storage.volumes': None,
        })

    def test_inventory_allows_known_incus_proxy_without_explicit_default_bind(self):
        result = fixture._inventory_devices({'web': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:8080',
                                                     'connect': 'tcp:127.0.0.1:80'}},
                                            'INCUS_PROFILE_INVENTORY_UNREADABLE')
        self.assertEqual(result, {'web': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:8080',
                                          'connect': 'tcp:127.0.0.1:80'}})

    def test_inventory_command_templates_allow_only_canonical_get_paths(self):
        class FakeProcess:
            def __init__(self, output=b'[]', errors=b''):
                self.stdout = self._pipe(output)
                self.stderr = self._pipe(errors)
            @staticmethod
            def _pipe(data):
                read_fd, write_fd = os.pipe()
                if data:
                    os.write(write_fd, data)
                os.close(write_fd)
                return os.fdopen(read_fd, 'rb', buffering=0)
            def wait(self, timeout=None):
                return 0
            def kill(self):
                pass
        valid = [
            ['incus', 'list', '--project', 'qa-blue', '--format', 'json'],
            ['incus', 'query', '/1.0/projects/qa%20blue'],
            ['incus', 'query', '/1.0/profiles/web%20blue?project=qa%20blue'],
            ['incus', 'query', '/1.0/instances/vm%20one?project=qa%20blue'],
            ['incus', 'query', '/1.0/images/' + 'e' * 64 + '?project=default'],
        ]
        with patch.object(fixture.subprocess, 'Popen',
                          side_effect=lambda *a, **k: FakeProcess()) as run:
            fixture._COMMAND_AUDIT.clear()
            for argv in valid:
                self.assertEqual(fixture._inventory_command(argv), b'[]')
            self.assertEqual(run.call_count, len(valid))
        record = fixture._COMMAND_AUDIT[-1]
        self.assertEqual(set(record), {'command_id', 'safe_args', 'exit_status', 'stdout_bytes', 'stderr_bytes'})
        self.assertNotIn(valid[-1][-1], json.dumps(record))
        invalid = [
            ['incus', 'image', 'info', 'e' * 64, '--project', 'default', '--format', 'json'],
            ['incus', 'query', '/1.0/images/' + 'e' * 63 + '?project=default'],
            ['incus', 'query', '/1.0/images/' + 'E' * 64 + '?project=default'],
            ['incus', 'query', '/1.0/images/' + 'e' * 64 + '?project=qa'],
            ['incus', 'query', '/1.0/images/' + 'e' * 64 + '?project=default&recursion=1'],
            ['incus', 'query', '/1.0/projects/qa%2fblue'],
            ['incus', 'query', '/1.0/projects/../default'],
            ['incus', 'query', '/1.0/instances/vm'],
            ['incus', 'query', '/1.0/profiles/web?project=qa&project=other'],
            ['incus', 'query', '/1.0/profiles/web?project=qa&recursion=1'],
            ['incus', 'query', '/1.0/projects/default?project=default'],
            ['incus', 'query', '/1.0/instances/vm?project=qa', '-X', 'DELETE'],
        ]
        for argv in invalid:
            with self.subTest(argv=argv), self.assertRaisesRegex(
                    fixture.FixtureError, 'INVENTORY_COMMAND_NOT_ALLOWLISTED'):
                fixture._inventory_command(argv)

    def test_kill_and_reap_uses_bounded_wait_and_fails_closed(self):
        class StuckProcess:
            killed = False
            timeout = None
            def kill(self):
                self.killed = True
            def wait(self, timeout=None):
                self.timeout = timeout
                raise fixture.subprocess.TimeoutExpired('incus', timeout)
        process = StuckProcess()
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_FAILED'):
            fixture._kill_and_reap(process, 'INCUS_INVENTORY_COMMAND_FAILED')
        self.assertTrue(process.killed)
        self.assertEqual(process.timeout, 0.5)

    def test_inventory_remote_verification_uses_real_json_shapes_without_generic_command(self):
        class FakeProcess:
            outputs = [b'{"local":{"Addr":"unix://","AuthType":"tls","KeepAlive":30,"Project":"","Protocol":"incus","CredHelper":"","Public":false,"Global":false,"Static":true}}', b'local\n']
            def __init__(self, *args, **kwargs):
                self.stdout = FakeProcess._pipe(self.outputs.pop(0))
                self.stderr = FakeProcess._pipe(b'')
            @staticmethod
            def _pipe(data):
                read_fd, write_fd = os.pipe()
                if data:
                    os.write(write_fd, data)
                os.close(write_fd)
                return os.fdopen(read_fd, 'rb', buffering=0)
            def wait(self, timeout=None):
                return 0
            def kill(self):
                pass
        fixture._COMMAND_AUDIT.clear()
        with (patch.object(fixture.subprocess, 'Popen', side_effect=FakeProcess) as popen,
              patch.object(fixture, 'command', side_effect=AssertionError('generic command hashes output'))):
            fixture._assert_local_incus_remote_inventory()
        self.assertEqual(popen.call_args_list[0].args[0], [fixture.TRUSTED_BIN['incus'], 'remote', 'list', '--format', 'json'])
        self.assertEqual(popen.call_args_list[1].args[0], [fixture.TRUSTED_BIN['incus'], 'remote', 'get-default'])
        self.assertTrue(all(set(row) == {'command_id', 'safe_args', 'exit_status', 'stdout_bytes', 'stderr_bytes'}
                            for row in fixture._COMMAND_AUDIT))

    def test_inventory_host_identity_uses_no_hash_command_path(self):
        class FakeProcess:
            def __init__(self, *args, **kwargs):
                self.stdout = self._pipe(b'[{"addr_info":[{"local":"192.168.178.33"}]}]')
                self.stderr = self._pipe(b'')
            @staticmethod
            def _pipe(data):
                read_fd, write_fd = os.pipe()
                if data:
                    os.write(write_fd, data)
                os.close(write_fd)
                return os.fdopen(read_fd, 'rb', buffering=0)
            def wait(self, timeout=None):
                return 0
            def terminate(self):
                pass
            def kill(self):
                pass
        with (patch.object(fixture.subprocess, 'Popen', side_effect=FakeProcess) as run,
              patch.object(fixture, 'command', side_effect=AssertionError('generic command hashes IP output'))):
            fixture._assert_host_identity_inventory('192.168.178.33')
        self.assertEqual(run.call_args.args[0], [fixture.TRUSTED_BIN['ip'], '-j', '-4', 'addr'])

    def test_inventory_host_capture_is_bounded_and_kills_on_overflow_or_timeout(self):
        class FakeProcess:
            def __init__(self, payload=b'', hang=False, *args, **kwargs):
                self.stopped = threading.Event()
                self.write_lock = threading.Lock()
                self.write_fds = set()
                self.stdout = self._pipe(payload, hang)
                self.stderr = self._pipe(b'', hang)
            def _pipe(self, payload, hang):
                read_fd, write_fd = os.pipe()
                with self.write_lock:
                    self.write_fds.add(write_fd)
                if not hang:
                    def emit():
                        try:
                            for offset in range(0, len(payload), 1024):
                                with self.write_lock:
                                    if self.stopped.is_set() or write_fd not in self.write_fds:
                                        break
                                    os.write(write_fd, payload[offset:offset + 1024])
                        except OSError:
                            pass
                        finally:
                            self._close_writer(write_fd)
                    threading.Thread(target=emit, daemon=True).start()
                return os.fdopen(read_fd, 'rb', buffering=0)
            def _close_writer(self, fd):
                with self.write_lock:
                    if fd in self.write_fds:
                        self.write_fds.remove(fd)
                        os.close(fd)
            def terminate(self):
                pass
            def wait(self, timeout=None):
                if not self.stopped.is_set():
                    raise fixture.subprocess.TimeoutExpired('fake', timeout)
                return -9
            def kill(self):
                self.stopped.set()
                for fd in tuple(self.write_fds):
                    self._close_writer(fd)
        with patch.object(fixture.subprocess, 'Popen', side_effect=lambda *a, **k: FakeProcess(b'12345')):
            with self.assertRaisesRegex(fixture.TargetDrift, 'HOST_IDENTITY_DRIFT'):
                fixture._bounded_process_output(['/fixed/command'], 1, 4)
        with patch.object(fixture.subprocess, 'Popen', side_effect=lambda *a, **k: FakeProcess(hang=True)):
            with self.assertRaisesRegex(fixture.TargetDrift, 'HOST_IDENTITY_DRIFT'):
                fixture._bounded_process_output(['/fixed/command'], 0.01, 4)

    def test_inventory_enforces_aggregate_command_entity_and_artifact_caps(self):
        class TinyProcess:
            def __init__(self, payload=b'[]', *args, **kwargs):
                self.stdout = self._pipe(payload)
                self.stderr = self._pipe(b'')
            @staticmethod
            def _pipe(data):
                read_fd, write_fd = os.pipe()
                if data:
                    os.write(write_fd, data)
                os.close(write_fd)
                return os.fdopen(read_fd, 'rb', buffering=0)
            def wait(self, timeout=None):
                return 0
            def kill(self):
                pass

        with (patch.object(fixture, '_INVENTORY_BYTES_CAPTURED', fixture._INVENTORY_TOTAL_COMMAND_MAX_BYTES - 1),
              patch.object(fixture.subprocess, 'Popen', side_effect=lambda *a, **k: TinyProcess(b'[]')),
              self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_OUTPUT_TOO_LARGE')):
            fixture._inventory_command(['incus', 'project', 'list', '--format', 'json'])
        with patch.object(fixture, '_INVENTORY_ENTITIES_CAPTURED', fixture._INVENTORY_MAX_ENTITIES):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INSTANCE_INVENTORY_UNREADABLE'):
                fixture._account_inventory_entities(1, 'INCUS_INSTANCE_INVENTORY_UNREADABLE')
        with patch.object(fixture, '_COMMAND_AUDIT', [{}] * fixture._INVENTORY_MAX_COMMANDS), self.assertRaisesRegex(
                fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED'):
            fixture._inventory_command(['incus', 'project', 'list', '--format', 'json'])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self._evidence(root)
            output = '.tiny-swarm/evidence/issue-449/s449-private-20261027/inventory.json'
            with (patch.object(fixture, 'ROOT', root), patch.object(fixture, '_require_private_ext4'),
                  patch.object(fixture, '_INVENTORY_ARTIFACT_MAX_BYTES', 1),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_capture_project_inventory', return_value={'projects': [], 'command_records': []}),
                  self.assertRaisesRegex(fixture.FixtureError, 'INVENTORY_ARTIFACT_TOO_LARGE')):
                fixture.capture_project_inventory('192.168.178.33', output)
            self.assertFalse((evidence / 'inventory.json').exists())

    def test_fixture_inventory_reserves_command_budget_for_cleanup(self):
        full_audit = [{}] * (fixture._INVENTORY_MAX_COMMANDS
                             - fixture._INVENTORY_CLEANUP_COMMAND_RESERVE)
        with (patch.object(fixture, '_COMMAND_AUDIT', full_audit),
              patch.object(fixture, '_INVENTORY_RESERVE_CLEANUP', True),
              patch.object(fixture, '_INVENTORY_CLEANUP_MODE', False),
              patch.object(fixture.subprocess, 'Popen') as process,
              self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED')):
            fixture._inventory_command(['incus', 'project', 'list', '--format', 'json'])
        process.assert_not_called()
        with (patch.object(fixture, '_COMMAND_AUDIT', full_audit),
              patch.object(fixture, '_INVENTORY_RESERVE_CLEANUP', True),
              patch.object(fixture, '_INVENTORY_CLEANUP_MODE', True),
              patch.object(fixture.subprocess, 'Popen', side_effect=OSError('injected')),
              self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_FAILED')):
            fixture._inventory_command(['incus', 'project', 'list', '--format', 'json'])

    def test_fixture_inventory_reserves_byte_entity_and_time_budgets_for_cleanup(self):
        with (patch.object(fixture, '_INVENTORY_RESERVE_CLEANUP', True),
              patch.object(fixture, '_INVENTORY_CLEANUP_MODE', False)):
            self.assertEqual(fixture._inventory_budgets(), (
                fixture._INVENTORY_MAX_COMMANDS - fixture._INVENTORY_CLEANUP_COMMAND_RESERVE,
                fixture._INVENTORY_TOTAL_COMMAND_MAX_BYTES - fixture._INVENTORY_CLEANUP_BYTE_RESERVE,
                fixture._INVENTORY_MAX_ENTITIES - fixture._INVENTORY_CLEANUP_ENTITY_RESERVE,
                fixture._INVENTORY_TOTAL_TIMEOUT_SECONDS - fixture._INVENTORY_CLEANUP_TIMEOUT_RESERVE_SECONDS))
        with (patch.object(fixture, '_INVENTORY_RESERVE_CLEANUP', True),
              patch.object(fixture, '_INVENTORY_CLEANUP_MODE', True)):
            self.assertEqual(fixture._inventory_budgets(), (
                fixture._INVENTORY_MAX_COMMANDS, fixture._INVENTORY_TOTAL_COMMAND_MAX_BYTES,
                fixture._INVENTORY_MAX_ENTITIES, fixture._INVENTORY_TOTAL_TIMEOUT_SECONDS))

    def test_inventory_terminates_when_command_output_exceeds_per_stream_cap(self):
        class FakeProcess:
            oversized_channel = 'stdout'
            def __init__(self, *args, **kwargs):
                self.stopped = threading.Event()
                large = b'x' * (fixture._INVENTORY_COMMAND_MAX_BYTES + 1)
                self.stdout = self._pipe(large if self.oversized_channel == 'stdout' else b'', self.stopped)
                self.stderr = self._pipe(large if self.oversized_channel == 'stderr' else b'', self.stopped)
            @staticmethod
            def _pipe(data, stopped):
                read_fd, write_fd = os.pipe()
                def emit():
                    try:
                        for offset in range(0, len(data), 16384):
                            if stopped.is_set():
                                break
                            os.write(write_fd, data[offset:offset + 16384])
                    except OSError:
                        pass
                    finally:
                        os.close(write_fd)
                threading.Thread(target=emit, daemon=True).start()
                return os.fdopen(read_fd, 'rb', buffering=0)
            def wait(self, timeout=None):
                return 0
            def kill(self):
                self.stopped.set()
        for channel in ('stdout', 'stderr'):
            with self.subTest(channel=channel):
                FakeProcess.oversized_channel = channel
                with patch.object(fixture.subprocess, 'Popen', side_effect=FakeProcess), self.assertRaisesRegex(
                        fixture.TargetDrift, 'INCUS_INVENTORY_OUTPUT_TOO_LARGE'):
                    fixture._inventory_command(['incus', 'project', 'list', '--format', 'json'])

    def test_inventory_projects_and_incus_api_rows_project_exact_local_and_expanded_schema(self):
        features = {'features.images': 'true', 'features.networks': 'false',
                    'features.profiles': 'true', 'features.storage.volumes': 'false'}
        device = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:8080', 'connect': 'tcp:127.0.0.1:80'}
        responses = {
            ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"qa","description":"","config":{}}]',
            ('incus', 'query', '/1.0/projects/qa'):
                json.dumps({'name': 'qa', 'description': '', 'config': features, 'used_by': []}).encode(),
            ('incus', 'profile', 'list', '--project', 'qa', '--format', 'json'):
                b'[{"name":"web","description":"","used_by":[],"project":"qa","config":{},"devices":{}}]',
            ('incus', 'query', fixture._profile_api_path('web', 'qa')):
                json.dumps({'name': 'web', 'project': 'qa', 'description': '', 'config': {'user.note': 'omit'},
                            'devices': {'proxy0': device}, 'used_by': []}).encode(),
            ('incus', 'list', '--project', 'qa', '--format', 'json'):
                json.dumps([{'name': 'vm', 'status': 'Running', 'status_code': 103,
                             'type': 'virtual-machine', 'profiles': ['web'], 'ephemeral': False,
                             'description': '', 'project': 'qa', 'backups': None,
                             'snapshots': [{'name': 'vm/snap0'}],
                             'state': {'status': 'Running', 'status_code': 103,
                                       'memory': {'usage': 42}, 'network': None}}]).encode(),
            ('incus', 'query', fixture._instance_api_path('vm', 'qa')):
                json.dumps({'name': 'vm', 'project': 'qa',
                            'config': {'user.note': 'omit'},
                            'devices': {'local0': device}, 'profiles': ['web'],
                            'expanded_config': {'user.note': 'omit'},
                            'expanded_devices': {'expanded0': device}}).encode(),
        }
        seen = []
        def read(argv):
            key = tuple(argv)
            seen.append(key)
            return responses[key]
        with (patch.object(fixture, '_assert_host_identity_inventory'), patch.object(fixture, '_assert_local_incus_remote_inventory'),
              patch.object(fixture, '_require_local_incus_admin'), patch.object(fixture, '_inventory_command', side_effect=read)):
            inventory = fixture._capture_project_inventory('192.168.178.33')
        project = inventory['projects'][0]
        self.assertEqual(project['name'], 'qa')
        self.assertEqual(project['isolation'], {'features.images': True, 'features.networks': False,
            'features.profiles': True, 'features.storage.volumes': False})
        self.assertEqual(project['profiles'], [{'name': 'web', 'used_by': [], 'devices': {'proxy0': device}}])
        self.assertEqual(project['instances'], [{'name': 'vm', 'status': 'Running', 'type': 'virtual-machine',
            'profiles': ['web'], 'local_devices': {'local0': device}, 'expanded_devices': {'expanded0': device}}])
        self.assertIn(('incus', 'list', '--project', 'qa', '--format', 'json'), seen)
        self.assertIn(('incus', 'query', fixture._instance_api_path('vm', 'qa')), seen)
        self.assertEqual(set(inventory), {'projects', 'command_records'})

    def test_inventory_records_inherited_profiles_once_and_keeps_project_instances(self):
        shared_used_by = ['/1.0/instances/swarm-manager?project=issue447']
        instance = {'name': 'swarm-manager', 'project': 'issue447', 'config': {}, 'devices': {},
                    'profiles': ['default'], 'expanded_config': {}, 'expanded_devices': {}}
        responses = {
            ('incus', 'project', 'list', '--format', 'json'):
                b'[{"name":"default"},{"name":"issue447"},{"name":"legacy"}]',
            ('incus', 'query', '/1.0/projects/default'):
                b'{"name":"default","description":"","config":{"features.profiles":"true"}}',
            ('incus', 'query', '/1.0/projects/issue447'):
                b'{"name":"issue447","description":"","config":{"features.profiles":"false"}}',
            ('incus', 'query', '/1.0/projects/legacy'):
                b'{"name":"legacy","description":"","config":{}}',
            ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'):
                b'[{"name":"shared"}]',
            ('incus', 'query', '/1.0/profiles/shared?project=default'):
                json.dumps({'name': 'shared', 'project': 'default', 'config': {}, 'devices': {},
                            'used_by': shared_used_by}).encode(),
            ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
            ('incus', 'list', '--project', 'issue447', '--format', 'json'):
                b'[{"name":"swarm-manager","status":"Running","type":"container","profiles":["default"],"project":"issue447"}]',
            ('incus', 'query', fixture._instance_api_path('swarm-manager', 'issue447')):
                json.dumps(instance).encode(),
            ('incus', 'list', '--project', 'legacy', '--format', 'json'): b'[]',
        }
        seen = []

        def read(argv):
            key = tuple(argv)
            seen.append(key)
            return responses[key]

        with (patch.object(fixture, '_assert_host_identity_inventory'),
              patch.object(fixture, '_assert_local_incus_remote_inventory'),
              patch.object(fixture, '_require_local_incus_admin'),
              patch.object(fixture, '_inventory_command', side_effect=read)):
            inventory = fixture._capture_project_inventory('192.168.178.33')

        default, inherited, unset = inventory['projects']
        self.assertEqual(default['profiles'], [{'name': 'shared', 'used_by': shared_used_by, 'devices': {}}])
        self.assertEqual(inherited['isolation']['features.profiles'], False)
        self.assertEqual(inherited['profiles'], [])
        self.assertEqual(inherited['instances'][0]['profiles'], ['default'])
        self.assertIsNone(unset['isolation']['features.profiles'])
        self.assertEqual(unset['profiles'], [])
        self.assertEqual(seen.count(('incus', 'profile', 'list', '--project', 'default', '--format', 'json')), 1)
        self.assertNotIn(('incus', 'profile', 'list', '--project', 'issue447', '--format', 'json'), seen)
        self.assertNotIn(('incus', 'profile', 'list', '--project', 'legacy', '--format', 'json'), seen)
        self.assertIn(('incus', 'list', '--project', 'issue447', '--format', 'json'), seen)

    def test_inventory_refuses_to_list_projects_without_completeness_authority(self):
        with (patch.object(fixture, '_assert_host_identity_inventory'), patch.object(fixture, '_assert_local_incus_remote_inventory'),
              patch.object(fixture, '_require_local_incus_admin',
                           side_effect=fixture.FixtureError('INCUS_PROJECT_VISIBILITY_UNVERIFIED')) as authority,
              patch.object(fixture, '_inventory_command') as read):
            with self.assertRaisesRegex(fixture.FixtureError, 'INCUS_PROJECT_VISIBILITY_UNVERIFIED'):
                fixture._capture_project_inventory('192.168.178.33')
        authority.assert_called_once_with()
        read.assert_not_called()

    def test_inventory_rejects_profile_and_instance_project_mismatch_and_malformed_optional_fields(self):
        feature_config = {'features.images': 'true', 'features.networks': 'true',
                          'features.profiles': 'true', 'features.storage.volumes': 'true'}
        scenarios = [
            ('profile-project-mismatch',
             {('incus', 'profile', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"p","project":"other"}]'}, 'INCUS_PROFILE_INVENTORY_UNREADABLE'),
            ('profile-show-project-mismatch',
             {('incus', 'profile', 'list', '--project', 'qa', '--format', 'json'): b'[{"name":"p"}]',
              ('incus', 'query', fixture._profile_api_path('p', 'qa')):
              b'{"name":"p","project":"other","config":{},"devices":{},"used_by":[]}'},
             'INCUS_PROFILE_INVENTORY_UNREADABLE'),
            ('instance-project-mismatch',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"project":"other"}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-architecture',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"architecture":12}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-created-at',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"created_at":12}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-stateful',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"stateful":"false"}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-ephemeral',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"ephemeral":"false"}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-status-code',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"status_code":true}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-backups',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"backups":{}}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-snapshots',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"snapshots":["snap0"]}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('malformed-state',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"state":[]}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('oversized-snapshots',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              json.dumps([{'name': 'i', 'status': 'Running', 'type': 'container', 'profiles': [],
                           'snapshots': [{} for _ in range(fixture._INVENTORY_MAX_ENTITIES + 1)]}]).encode()},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('oversized-state',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              json.dumps([{'name': 'i', 'status': 'Running', 'type': 'container', 'profiles': [],
                           'state': {f'field-{i}': None for i in range(fixture._INVENTORY_MAX_ENTITIES + 1)}}]).encode()},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
            ('unknown-instance-summary-field',
             {('incus', 'list', '--project', 'qa', '--format', 'json'):
              b'[{"name":"i","status":"Running","type":"container","profiles":[],"vendor_extra":true}]'},
             'INCUS_INSTANCE_INVENTORY_UNREADABLE'),
        ]
        for label, overrides, error in scenarios:
            with self.subTest(label=label):
                base = {
                    ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"qa"}]',
                    ('incus', 'query', '/1.0/projects/qa'):
                        json.dumps({'name': 'qa', 'description': '', 'config': feature_config}).encode(),
                    ('incus', 'profile', 'list', '--project', 'qa', '--format', 'json'): b'[]',
                    ('incus', 'list', '--project', 'qa', '--format', 'json'): b'[]',
                }
                base.update(overrides)
                def read(argv):
                    return base[tuple(argv)]
                with (patch.object(fixture, '_assert_host_identity_inventory'), patch.object(fixture, '_assert_local_incus_remote_inventory'),
                      patch.object(fixture, '_require_local_incus_admin'), patch.object(fixture, '_inventory_command', side_effect=read),
                      self.assertRaisesRegex(fixture.TargetDrift, error)):
                    fixture._capture_project_inventory('192.168.178.33')

    def test_admin_gate_accepts_root_or_incus_admin_and_rejects_other_local_identity(self):
        with patch.object(fixture.os, 'geteuid', return_value=0):
            fixture._require_local_incus_admin()
        with (patch.object(fixture.os, 'geteuid', return_value=1200),
              patch.object(fixture.os, 'getgroups', return_value=[2200]),
              patch.object(fixture.os, 'getegid', return_value=2200),
              patch('grp.getgrnam', return_value=SimpleNamespace(gr_gid=2200))):
            fixture._require_local_incus_admin()
        with (patch.object(fixture.os, 'geteuid', return_value=1200),
              patch.object(fixture.os, 'getgroups', return_value=[]),
              patch.object(fixture.os, 'getegid', return_value=1200),
              patch('grp.getgrnam', return_value=SimpleNamespace(gr_gid=2200)),
              self.assertRaisesRegex(fixture.FixtureError, 'INCUS_PROJECT_VISIBILITY_UNVERIFIED')):
            fixture._require_local_incus_admin()

    def test_inventory_refuses_symlink_or_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self._evidence(root)
            target = evidence / 'kept.json'
            target.write_bytes(b'keep')
            (evidence / 'inventory.json').symlink_to(target)
            for name in ('inventory.json', 'kept.json'):
                with (self.subTest(name=name), patch.object(fixture, 'ROOT', root),
                      patch.object(fixture, '_require_private_ext4'),
                      patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                      patch.object(fixture, '_capture_project_inventory', return_value={'projects': [], 'command_records': []})):
                    with self.assertRaisesRegex(fixture.FixtureError, 'CAPTURE_CREATE_FAILED'):
                        fixture.capture_project_inventory('192.168.178.33',
                            f'.tiny-swarm/evidence/issue-449/s449-private-20261027/{name}')
            self.assertEqual(target.read_bytes(), b'keep')

    def test_inventory_ext4_guard_precedes_git_and_host_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, '_require_private_ext4', side_effect=fixture.FixtureError('PRIVATE_EVIDENCE_FILESYSTEM_UNSAFE')) as guard,
                  patch.object(fixture, 'git_preflight') as git,
                  patch.object(fixture, '_assert_host_identity_inventory') as host,
                  patch.object(fixture, '_inventory_command') as incus):
                status = fixture.main(['--capture-project-inventory', '--target-host', '192.168.178.33', '--output',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/inventory.json'])
            self.assertEqual(status, 2)
            guard.assert_called_once_with(root)
            git.assert_not_called()
            host.assert_not_called()
            incus.assert_not_called()
            self.assertFalse((root / fixture.PRIVATE_EVIDENCE_REL).exists())


class ProxyRouteParsingTests(_FixtureBehaviorTestCase):
    def test_only_tcp_singleton_10001_is_an_approved_route(self):
        self.assertTrue(fixture._is_approved_10001_proxy('tcp:127.0.0.1:10001'))
        self.assertTrue(fixture._is_approved_10001_proxy('tcp:[2001:db8::1]:10001'))

    def test_range_or_list_containing_10001_is_rejected(self):
        for listen in ('tcp:127.0.0.1:10000-10002',
                       'tcp:127.0.0.1:8080,10001',
                       'tcp:[::1]:10001-10001'):
            with self.subTest(listen=listen), self.assertRaisesRegex(
                    fixture.TargetDrift, 'INCUS_10001_ROUTE_UNAPPROVED'):
                fixture._is_approved_10001_proxy(listen)

    def test_udp_10001_is_rejected(self):
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_10001_ROUTE_UNAPPROVED'):
            fixture._is_approved_10001_proxy('udp:0.0.0.0:10001')

    def test_valid_non_overlapping_ranges_and_lists_are_outside_inventory(self):
        self.assertFalse(fixture._is_approved_10001_proxy('tcp:127.0.0.1:10002-10010'))
        self.assertFalse(fixture._is_approved_10001_proxy('udp:[::1]:10002,10003'))

    def test_malformed_proxy_fields_are_rejected(self):
        valid = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001',
                 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}
        malformed = (
            {**valid, 'listen': 'tcp:127.0.0.1:bad'},
            {**valid, 'listen': 'tcp:127.0.0.1:8080,9000-9002'},
            {**valid, 'connect': 'tcp:127.0.0.1:70000'},
            {**valid, 'connect': 'tcp:localhost:8080'},
            {**valid, 'connect': None},
            {**valid, 'connect': 'unix:relative.sock'},
            {**valid, 'connect': 'unix:@'},
            {**valid, 'connect': 'unix:/'},
            {**valid, 'connect': 'unix:/run/'},
            {key: value for key, value in valid.items() if key != 'bind'},
            {**valid, 'bind': []},
        )
        for device in malformed:
            with self.subTest(device=device), self.assertRaisesRegex(
                    fixture.TargetDrift, 'PROFILE_DEVICE_INVALID'):
                fixture._strict_devices({'proxy': device}, 'PROFILE_DEVICE_INVALID')

    def test_proxy_addresses_must_be_literal_and_use_documented_wildcards(self):
        valid = {'type': 'proxy', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}
        malformed_addresses = ('localhost', 'example.com', '*', '127.0.0.999', '::1',
                               '::', '[::1', '[127.0.0.1]', 'fe80::1%eth0')
        for address in malformed_addresses:
            with self.subTest(address=address), self.assertRaisesRegex(
                    fixture.TargetDrift, 'PROFILE_DEVICE_INVALID'):
                fixture._strict_devices(
                    {'proxy': {**valid, 'listen': f'tcp:{address}:10001'}}, 'PROFILE_DEVICE_INVALID')
        for address in ('0.0.0.0', '[::]'):
            with self.subTest(address=address):
                fixture._strict_devices(
                    {'proxy': {**valid, 'listen': f'tcp:{address}:10001'}}, 'PROFILE_DEVICE_INVALID')

    def test_documented_cross_protocol_pairs_and_unix_abstract_paths_are_valid(self):
        pairs = (
            ('tcp:127.0.0.1:8080', 'unix:/run/fixture.sock'),
            ('udp:127.0.0.1:8080', 'tcp:127.0.0.1:8080'),
            ('tcp:127.0.0.1:8080', 'udp:127.0.0.1:8080'),
            ('unix:@fixture-service', 'tcp:127.0.0.1:8080'),
            ('udp:127.0.0.1:8080', 'unix:/run/fixture.sock'),
            ('unix:/run/fixture.sock', 'udp:127.0.0.1:8080'),
        )
        for listen, connect in pairs:
            with self.subTest(listen=listen, connect=connect):
                fixture._strict_devices({'proxy': {'type': 'proxy', 'listen': listen,
                                                   'connect': connect, 'bind': 'host'}},
                                        'PROFILE_DEVICE_INVALID')

    def test_nat_mode_rejects_documented_non_nat_cross_protocol_pair(self):
        with self.assertRaisesRegex(fixture.TargetDrift, 'PROFILE_DEVICE_INVALID'):
            fixture._strict_devices({'proxy': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:8080',
                                               'connect': 'unix:/run/fixture.sock', 'bind': 'host',
                                               'nat': 'true'}}, 'PROFILE_DEVICE_INVALID')

    def test_malformed_proxy_records_in_profiles_and_instances_fail_closed(self):
        malformed = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:8080',
                     'connect': 'tcp:127.0.0.1:8080', 'bind': 'invalid'}
        profile_outputs = [b'[{"name":"default"}]', b'{"name":"default","description":"","config":{}}',
                           b'[{"name":"bad-profile"}]',
                           json.dumps({'config': {}, 'devices': {'web': malformed}, 'used_by': []}).encode()]
        with patch.object(fixture, 'command', side_effect=profile_outputs):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROFILE_INVENTORY_UNREADABLE'):
                fixture._incus_10001_routes()

        instance_outputs = [b'[{"name":"default"}]', b'{"name":"default","description":"","config":{}}',
                            b'[]', b'[{"name":"bad-instance"}]',
                            json.dumps({'config': {}, 'devices': {'web': malformed},
                                        'profiles': ['default']}).encode()]
        with patch.object(fixture, 'command', side_effect=instance_outputs):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INSTANCE_INVENTORY_UNREADABLE'):
                fixture._incus_10001_routes()


class GoValidationTests(_FixtureBehaviorTestCase):
    def setUp(self):
        self.args = argparse.Namespace(target_host='192.168.178.58')
        self.workflow, self.runner, self.tests = b'w', b'r', b't'
        run_id = 'a' * 32
        self.go = {
            'decision': 'GO', 'source_commit': 'b' * 40,
            'workflow_sha256': fixture.digest(self.workflow),
            'runner_sha256': fixture.digest(self.runner),
            'test_sha256': fixture.digest(self.tests),
            'resource_admission_sha256': 'c' * 64,
            'issue447_inventory_sha256': 'd' * 64,
            'target': {'host': self.args.target_host, 'endpoint': 'unix://', 'project': 'default',
                       'server_version': '6.0.5', 'run_id': run_id,
                       'profile': f'tsw-q449-{run_id}-profile', 'base_profile': f'tsw-q449-{run_id}-base',
                       'instance': f'tsw-q449-{run_id}-fixture',
                       'image_fingerprint': 'e' * 64},
            'proxy': {'listen': 'tcp:127.0.0.1:61000', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'},
            'cleanup': [f'tsw-q449-{run_id}-fixture', f'tsw-q449-{run_id}-profile', f'tsw-q449-{run_id}-base'],
            'reviews': {k: 'APPROVED' for k in fixture.REVIEW_KEYS},
            'windows_rules_unchanged': True, 'external_routes_enabled': False,
            'default_profile_sha256': fixture.canonical_profile_sha256({}, {}), 'default_profile_used_by': [],
            'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256({'boot.autostart': 'false'}, {}),
            'approved_route_state_sha256': '0' * 64,
        }

    def test_accepts_exact_bound_contract(self):
        self.assertEqual(fixture.validate_go(self.go, self.args, 'b' * 40, self.workflow, self.runner, self.tests), self.go)

    def test_rejects_unknown_and_missing_top_level_keys(self):
        for mutate in (lambda g: g.update(extra=1), lambda g: g.pop('decision')):
            candidate = json.loads(json.dumps(self.go))
            mutate(candidate)
            with self.subTest(candidate=candidate), self.assertRaises(fixture.FixtureError):
                fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)

    def test_rejects_unknown_nested_keys(self):
        for key in ('target', 'proxy', 'reviews'):
            for mutation in ('extra', 'missing'):
                candidate = json.loads(json.dumps(self.go))
                if mutation == 'extra':
                    candidate[key]['extra'] = 'x'
                else:
                    candidate[key].pop(next(iter(candidate[key])))
                with self.subTest(key=key, mutation=mutation), self.assertRaises(fixture.FixtureError):
                    fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)

    def test_rejects_non_allowlisted_target_and_nonlocal_endpoint(self):
        for key, value in (('host', '192.168.178.1'), ('endpoint', 'https://remote')):
            candidate = json.loads(json.dumps(self.go))
            candidate['target'][key] = value
            with self.subTest(key=key), self.assertRaises(fixture.FixtureError):
                fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)

    def test_rejects_bad_names_port_order_reviews_and_hash_bindings(self):
        mutations = (
            lambda g: g['target'].__setitem__('instance', 'wrong'),
            lambda g: g['proxy'].__setitem__('listen', 'tcp:127.0.0.1:65536'),
            lambda g: g.__setitem__('default_profile_used_by', ['/z', '/a']),
            lambda g: g['reviews'].__setitem__('security', 'PENDING'),
            lambda g: g.__setitem__('runner_sha256', '0' * 64),
        )
        for mutate in mutations:
            candidate = json.loads(json.dumps(self.go))
            mutate(candidate)
            with self.subTest(candidate=candidate), self.assertRaises(fixture.FixtureError):
                fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)


class NoMutationTests(_FixtureBehaviorTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch.object(fixture, '_assert_local_incus_remote_inventory')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_pre_start_gate_rejects_fixture_port_listener_on_ipv4_or_ipv6(self):
        rows = (
            b'LISTEN 0 1 127.0.0.1:61000 0.0.0.0:*',
            b'LISTEN 0 1 0.0.0.0:61000 0.0.0.0:*',
            b'LISTEN 0 1 [::1]:61000 [::]:*',
            b'LISTEN 0 1 [::]:61000 [::]:*',
            b'LISTEN 0 1 *:61000 *:*',
        )
        for row in rows:
            with self.subTest(row=row), patch.object(fixture, '_listeners', return_value=row):
                with self.assertRaisesRegex(fixture.TargetDrift, 'FIXTURE_LISTENER_EARLY'):
                    fixture._assert_no_fixture_listener('61000')

    def test_listener_inventory_rejects_malformed_rows(self):
        for row in (b'not an ss row', b'LISTEN 0 1 malformed 0.0.0.0:*'):
            with self.subTest(row=row), self.assertRaisesRegex(
                    fixture.TargetDrift, 'LISTENER_INVENTORY_UNREADABLE'):
                fixture._listener_rows(row, 61000)

    def test_digest_rejection_happens_before_reservation_or_live_command(self):
        raw = b'{"decision":"GO"}\n'
        with (
            patch.object(fixture, 'git_preflight', return_value=('b' * 40, b'w', b'r', b't')),
            patch.object(fixture, 'read_once', return_value=raw) as go_read,
            patch.object(fixture, 'validate_go', side_effect=AssertionError('must not parse wrong digest')),
            patch.object(fixture, 'reserve_and_recheck', side_effect=AssertionError('must not reserve')),
            patch.object(fixture, 'subprocess') as subprocess_mock,
        ):
            status = fixture.main(['--expected-approval-sha256', '0' * 64,
                                   '--target-host', '192.168.178.33'])
        self.assertEqual(status, 2)
        go_read.assert_called_once()
        subprocess_mock.run.assert_not_called()

    def test_invalid_go_stops_before_reservation_or_any_live_command(self):
        raw = b'{"unknown":true}\n'
        with (
            patch.object(fixture, 'git_preflight', return_value=('b' * 40, b'w', b'r', b't')),
            patch.object(fixture, 'read_once', return_value=raw),
            patch.object(fixture, 'reserve_and_recheck', side_effect=AssertionError('must not reserve')),
            patch.object(fixture, 'jit', side_effect=AssertionError('must not inspect target')),
            patch.object(fixture, 'subprocess') as subprocess_mock,
        ):
            status = fixture.main(['--expected-approval-sha256', hashlib.sha256(raw).hexdigest(),
                                   '--target-host', '192.168.178.33'])
        self.assertEqual(status, 2)
        subprocess_mock.run.assert_not_called()

    def test_command_audit_records_only_safe_metadata(self):
        fixture._COMMAND_AUDIT.clear()
        with patch.object(fixture.subprocess, 'Popen', return_value=_BoundedMemoryProcess(b'secret output')) as process:
            self.assertEqual(fixture.command(['/usr/bin/mock-command']), b'secret output')
        self.assertEqual(process.call_args.args[0], ['/usr/bin/mock-command'])
        record = fixture._COMMAND_AUDIT[-1]
        self.assertEqual(set(record), {'command_id', 'safe_args', 'exit_status', 'stdout_bytes', 'stderr_bytes'})
        self.assertEqual(record['stdout_bytes'], len(b'secret output'))
        self.assertEqual(record['exit_status'], 0)
        self.assertNotIn('stdout_base64', record)
        self.assertNotIn('stdout', record)

    def test_command_audit_never_hashes_incus_output(self):
        result = type('Completed', (), {'returncode': 0, 'stdout': b'{"config":{"password":"secret"}}'})()
        fixture._COMMAND_AUDIT.clear()
        with patch.object(fixture, '_inventory_command', return_value=result.stdout) as inventory:
            self.assertEqual(fixture.command(['incus', 'query', fixture._profile_api_path('default', 'default')]),
                             b'{"config":{"password":"secret"}}')
        inventory.assert_called_once_with(['incus', 'query', fixture._profile_api_path('default', 'default')])
        self.assertEqual(fixture._COMMAND_AUDIT, [])

    def test_jit_drift_is_typed_and_stops_before_any_incus_write(self):
        go = {'target': {'host': '192.168.178.33'}}
        with patch.object(fixture, 'command', side_effect=fixture.TargetDrift('INJECTED_DRIFT')) as cmd:
            with self.assertRaises(fixture.TargetDrift):
                fixture.jit(go, '192.168.178.33')
        self.assertEqual(cmd.call_count, 1)
        self.assertEqual(cmd.call_args.args[0][:2], ['ip', '-j'])

    def test_reservation_mismatch_retains_existing_result_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_rel = fixture.PRIVATE_EVIDENCE_REL / 'result.json'
            result = root / result_rel
            result.parent.mkdir(parents=True, mode=0o700)
            result.parent.chmod(0o700)
            result.write_bytes(b'{"status":"PASS"}\n')
            result.chmod(0o600)
            with patch.object(fixture, 'ROOT', root), patch.object(fixture, 'RESULT_REL', result_rel):
                with self.assertRaises(fixture.FixtureError):
                    fixture.reserve_and_recheck()
            self.assertEqual(result.read_bytes(), b'{"status":"PASS"}\n')
            self.assertTrue(result.with_suffix('.json.reservation').exists())

    def test_post_reservation_shape_failure_is_recorded_as_consumed_drift(self):
        raw = b'{"authorized":"fixture"}\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / fixture.PRIVATE_EVIDENCE_REL / 'result.json'
            with (
                patch.object(fixture, 'git_preflight', return_value=('b' * 40, b'w', b'r', b't')),
                patch.object(fixture, 'read_once', return_value=raw),
                patch.object(fixture, 'validate_go', return_value={'source_commit': 'b' * 40}),
                patch.object(fixture, 'ROOT', root),
                patch.object(fixture, 'RESULT_REL', fixture.PRIVATE_EVIDENCE_REL / 'result.json'),
                patch.object(fixture, 'jit', side_effect=TypeError('malformed JIT shape')),
                patch.object(fixture, '_run_fixture') as run_fixture,
                patch.object(fixture, 'command') as command,
            ):
                status = fixture.main(['--expected-approval-sha256', hashlib.sha256(raw).hexdigest(),
                                       '--target-host', '192.168.178.33'])
            persisted = json.loads(evidence.read_text())
        self.assertEqual(status, 2)
        self.assertEqual(persisted['status'], 'BLOCKED_TARGET_DRIFT')
        self.assertEqual(persisted['code'], 'JIT_UNREADABLE')
        self.assertTrue(persisted['go_sha256'])
        run_fixture.assert_not_called()
        command.assert_not_called()



class GoValidationMatrixTests(_FixtureBehaviorTestCase):
    def setUp(self):
        GoValidationTests.setUp(self)
        self.base = self.go

    def test_each_approval_digest_binding_is_required_and_exact(self):
        cases = (('workflow_sha256', '0' * 64), ('runner_sha256', '0' * 64),
                 ('test_sha256', '0' * 64))
        for key, wrong in cases:
            candidate = json.loads(json.dumps(self.base))
            candidate[key] = wrong
            with self.subTest(key=key), self.assertRaises(fixture.FixtureError):
                fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)

    def test_resource_and_inventory_digests_are_syntax_only_and_profile_binding_is_jit(self):
        candidate = json.loads(json.dumps(self.base))
        candidate['resource_admission_sha256'] = '1' * 64
        candidate['issue447_inventory_sha256'] = '2' * 64
        candidate['default_profile_sha256'] = '3' * 64
        self.assertEqual(fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests), candidate)

    def test_every_sha256_and_source_hash_rejects_bad_syntax(self):
        keys = ('workflow_sha256', 'runner_sha256', 'test_sha256', 'resource_admission_sha256',
                'issue447_inventory_sha256', 'default_profile_sha256', 'fixture_base_profile_sha256', 'windows_snapshot_sha256', 'windows_certificate_sha256',
                'approved_route_state_sha256')
        for key in keys:
            candidate = json.loads(json.dumps(self.base))
            candidate[key] = 'G' * 64
            with self.subTest(key=key), self.assertRaises(fixture.FixtureError):
                fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)
        candidate = json.loads(json.dumps(self.base))
        candidate['source_commit'] = 'g' * 40
        with self.assertRaises(fixture.FixtureError):
            fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)
        candidate = json.loads(json.dumps(self.base))
        candidate['target']['image_fingerprint'] = 'G' * 64
        with self.assertRaises(fixture.FixtureError):
            fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)

    def test_cleanup_reviews_flags_and_consumer_order_are_exact(self):
        mutations = (
            lambda g: g.__setitem__('cleanup', list(reversed(g['cleanup']))),
            lambda g: g['reviews'].__setitem__('requirements', 'REJECTED'),
            lambda g: g.__setitem__('windows_rules_unchanged', 1),
            lambda g: g.__setitem__('external_routes_enabled', True),
            lambda g: g.__setitem__('default_profile_used_by', ['/z', '/a']),
            lambda g: g.__setitem__('default_profile_used_by', ['/a', '/a']),
            lambda g: g.__setitem__('cleanup', 'wrong-type'),
        )
        for mutate in mutations:
            candidate = json.loads(json.dumps(self.base))
            mutate(candidate)
            with self.subTest(candidate=candidate), self.assertRaises(fixture.FixtureError):
                fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)

    def test_every_proxy_field_and_run_binding_has_exact_type_and_value(self):
        mutations = (
            lambda g: g['proxy'].__setitem__('listen', 61000),
            lambda g: g['proxy'].__setitem__('connect', 'tcp:0.0.0.0:8080'),
            lambda g: g['proxy'].__setitem__('bind', 'both'),
            lambda g: g['target'].__setitem__('project', 'other'),
            lambda g: g['target'].__setitem__('server_version', 'latest'),
            lambda g: g['target'].__setitem__('run_id', 'A' * 32),
            lambda g: g['target'].__setitem__('profile', 'wrong'),
            lambda g: g['target'].__setitem__('image_fingerprint', 'F' * 64),
        )
        for mutate in mutations:
            candidate = json.loads(json.dumps(self.base))
            mutate(candidate)
            with self.subTest(candidate=candidate), self.assertRaises(fixture.FixtureError):
                fixture.validate_go(candidate, self.args, 'b' * 40, self.workflow, self.runner, self.tests)



class ReadAndReservationTests(_FixtureBehaviorTestCase):
    def test_read_once_rejects_symlink_and_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / 'approval.json'
            regular.write_bytes(b'{}')
            link = root / 'link.json'
            link.symlink_to(regular)
            with patch.object(fixture, 'ROOT', root):
                with self.assertRaises(fixture.FixtureError):
                    fixture.read_once(link)
                directory_path = root / 'directory'
                directory_path.mkdir()
                with self.assertRaises(fixture.FixtureError):
                    fixture.read_once(directory_path)

    def test_go_file_must_be_owned_and_mode_0600_in_private_evidence_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private_dir = root / fixture.PRIVATE_EVIDENCE_REL
            private_dir.mkdir(parents=True, mode=0o700)
            private_dir.chmod(0o700)
            go_path = root / fixture.GO_REL
            go_path.write_bytes(b'{"decision":"GO"}')
            go_path.chmod(0o644)
            with patch.object(fixture, 'ROOT', root), self.assertRaisesRegex(
                    fixture.FixtureError, 'GO_FILE_NOT_PRIVATE'):
                fixture.read_once(go_path)
            go_path.chmod(0o600)
            with patch.object(fixture, 'ROOT', root):
                self.assertEqual(fixture.read_once(go_path), b'{"decision":"GO"}')

    def test_read_once_uses_a_single_regular_file_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'go.json'
            source.write_bytes(b'{"decision":"GO"}')
            real_fdopen = fixture.os.fdopen
            reads = []

            class CountingReader:
                def __init__(self, stream):
                    self.stream = stream
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    self.stream.close()
                def read(self):
                    reads.append(1)
                    return self.stream.read()

            def wrap(fd, mode, closefd=False):
                return CountingReader(real_fdopen(fd, mode, closefd=closefd))

            with patch.object(fixture, 'ROOT', root), patch.object(fixture.os, 'fdopen', side_effect=wrap):
                self.assertEqual(fixture.read_once(source), b'{"decision":"GO"}')
            self.assertEqual(len(reads), 1)

    def test_first_reservation_consumes_exact_not_run_and_retains_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(fixture, 'ROOT', root), patch.object(
                    fixture, 'RESULT_REL', fixture.PRIVATE_EVIDENCE_REL / 'result.json'):
                observed = []
                real_ftruncate = fixture.os.ftruncate
                def capture_sentinel(fd, length):
                    observed.append(fixture.os.pread(fd, len(fixture.NOT_RUN), 0))
                    return real_ftruncate(fd, length)
                with patch.object(fixture.os, 'ftruncate', side_effect=capture_sentinel):
                    fd, path = fixture.reserve_and_recheck()
                self.assertEqual(observed, [fixture.NOT_RUN])
                self.assertEqual(path.read_bytes(), b'')
                fixture.os.close(fd)
                self.assertTrue(path.with_suffix('.json.reservation').is_file())
                with self.assertRaises(fixture.FixtureError):
                    fixture.reserve_and_recheck()


class FixtureLifecycleTests(_FixtureBehaviorTestCase):
    def test_initial_consumer_listener_and_wsl_route_drift_prevent_first_write(self):
        for drift in ('consumer', 'listener', 'wsl'):
            with self.subTest(drift=drift):
                run_id = 'a' * 32
                host = '192.168.178.58' if drift == 'wsl' else '192.168.178.33'
                go = {'source_commit': 'b' * 40,
                      'target': {'host': host, 'endpoint': 'unix://', 'project': 'default',
                                 'server_version': '6.0.5', 'run_id': run_id,
                                 'profile': f'tsw-q449-{run_id}-profile',
                                 'base_profile': f'tsw-q449-{run_id}-base',
                                 'instance': f'tsw-q449-{run_id}-fixture'},
                      'proxy': {'listen': 'tcp:127.0.0.1:61000',
                                'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'},
                      'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
                      'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256(
                          {'boot.autostart': 'false'}, {}),
                      'default_profile_used_by': []}
                windows = b'approved windows state' if drift == 'wsl' else b''
                route_digest = fixture.approved_route_state_sha256([], [], windows, ['default'])
                go['approved_route_state_sha256'] = route_digest
                baseline = {'listeners_10001': [], 'incus_10001_routes': [],
                            'incus_projects': ['default'], 'windows_rules_portproxy': windows,
                            'approved_route_state_sha256': route_digest,
                            'image_properties': {}, 'derived_base_profile': {'config': {'boot.autostart': 'false'}, 'devices': {}},
                            'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3,
                                          'filesystem_available_bytes': 2}}
                writes = []
                listener_reads = {'count': 0}
                profile = {'name': 'default', 'project': 'default', 'config': {},
                           'devices': {}, 'used_by': ['/1.0/instances/foreign']
                           if drift == 'consumer' else []}

                def command(argv):
                    if argv[0] == 'ss':
                        listener_reads['count'] += 1
                        if drift == 'listener' and listener_reads['count'] == 1:
                            return b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:*\n'
                        return b''
                    raise AssertionError(argv)

                def incus(*args, profile_data=None):
                    if args[:1] == ('list',) or args[:2] == ('profile', 'list'):
                        return b'[]'
                    writes.append(args)
                    return b''

                with (
                    patch.object(fixture, '_incus', side_effect=incus),
                    patch.object(fixture, '_inventory_command', return_value=json.dumps(profile).encode()),
                    patch.object(fixture, 'command', side_effect=command),
                    patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
                    patch.object(fixture, '_windows_snapshot', return_value=b'changed windows state'),
                ):
                    code = {'consumer': 'DEFAULT_PROFILE_CONSUMERS_DRIFT',
                            'listener': 'AUTHORIZED_LISTENER_CHANGED',
                            'wsl': 'WINDOWS_RULES_CHANGED'}[drift]
                    with self.assertRaisesRegex(fixture.TargetDrift, code):
                        fixture._run_fixture(go, baseline)
                self.assertEqual(writes, [])

    def test_ambiguous_create_readback_requires_exact_run_owned_identity(self):
        for name in ('tsw-q449-run-base', 'tsw-q449-run-profile'):
            valid_profile = {'name': name, 'project': 'default', 'config': {},
                             'devices': {}, 'used_by': []}
            self.assertTrue(fixture._profile_create_readback_owned(valid_profile, name))
            for altered in ({**valid_profile, 'name': 'other'},
                            {**valid_profile, 'project': 'other'},
                            {**valid_profile, 'devices': {'foreign': {'type': 'disk'}}},
                            {**valid_profile, 'used_by': ['/1.0/instances/foreign']}):
                with self.subTest(name=name, altered=altered):
                    self.assertFalse(fixture._profile_create_readback_owned(altered, name))
        transport = _FullGraphFixtureTransport(self)
        derived = fixture._derive_fixture_base(transport.profiles['default'])
        properties = {'os': 'Alpine', 'release': '3.21'}
        baseline = {'derived_base_profile': derived, 'image_properties': properties}
        valid_instance = _fixture_instance_dto(transport.go, derived, properties)
        fixture._FixtureInstanceReceipt(transport.go, baseline, valid_instance)
        for altered in ({**valid_instance, 'name': 'foreign'},
                        {**valid_instance, 'profiles': ['default', transport.profile]},
                        {**valid_instance, 'config': {'user.q449.run_id': 'b' * 32}},
                        {**valid_instance, 'devices': {'foreign': {'type': 'disk'}}}):
            with self.subTest(altered_keys=sorted(altered)), self.assertRaises(fixture.TargetDrift):
                fixture._FixtureInstanceReceipt(transport.go, baseline, altered)

    def test_cleanup_accepts_only_exact_fixture_profile_prefixes(self):
        device = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:61000',
                  'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}
        marker_only = {'name': 'tsw-q449-run-profile', 'project': 'default',
                       'config': {'user.q449.run_id': 'a' * 32},
                       'devices': {}, 'used_by': []}
        marker_and_listener = {**marker_only,
                               'devices': {'q449-listener': device}}
        for profile_data in (marker_only, marker_and_listener):
            self.assertTrue(fixture._fixture_profile_cleanup_prefix_owned(
                profile_data, 'tsw-q449-run-profile', 'default', 'a' * 32, device, []))
        for altered in ({**marker_only, 'name': 'foreign'},
                        {**marker_only, 'config': {'user.q449.run_id': 'b' * 32}},
                        {**marker_and_listener, 'devices': {'q449-listener': {**device, 'listen': 'tcp:0.0.0.0:61000'}}},
                        {**marker_only, 'devices': {'foreign': device}},
                        {**marker_only, 'used_by': ['/1.0/instances/foreign']}):
            self.assertFalse(fixture._fixture_profile_cleanup_prefix_owned(
                altered, 'tsw-q449-run-profile', 'default', 'a' * 32, device, []))

    def test_success_creates_verifies_and_cleans_instance_then_profile(self):
        run_id = 'a' * 32
        go = {
            'source_commit': 'b' * 40,
            'target': {'host': '192.168.178.33', 'endpoint': 'unix://', 'project': 'default',
                       'server_version': '6.0.5', 'image_fingerprint': 'e' * 64, 'run_id': run_id,
                       'profile': f'tsw-q449-{run_id}-profile',
                       'base_profile': f'tsw-q449-{run_id}-base',
                       'instance': f'tsw-q449-{run_id}-fixture'},
            'proxy': {'listen': 'tcp:127.0.0.1:61000', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'},
            'default_profile_sha256': fixture.canonical_profile_sha256({}, {}), 'default_profile_used_by': [],
            'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256({'boot.autostart': 'false'}, {}),
        }
        state = {'instance': False, 'profile_marker': False, 'instance_marker': False,
                 'status': 'stopped', 'foreign_consumer': False, 'base_exists': False,
                 'base_config': {}, 'profile_exists': False, 'profile_device': False,
                 'ambiguous_create': None, 'foreign_profile': None,
                 'foreign_instance': False, 'route_drift': False,
                 'inject_route_drift_after_delete': False}
        calls = []
        instance, profile = go['target']['instance'], go['target']['profile']
        base_profile = go['target']['base_profile']
        route = f'/1.0/instances/{instance}'
        device = {'type': 'proxy', **go['proxy']}
        listener = (b'LISTEN 0 4096 127.0.0.1:61000 0.0.0.0:* users:(("incusd",pid=123,fd=4))\n'
                    b'LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=44,fd=5))\n')
        approved_route_state = fixture.approved_route_state_sha256(
            [listener.splitlines()[1]], [], b'', ['default'])
        go['approved_route_state_sha256'] = approved_route_state

        def incus(*args, profile_data=None):
            calls.append(args)
            if args[:2] == ('profile', 'create') and args[2] == base_profile:
                state['base_exists'] = True
                state['base_config'] = dict(profile_data['config'])
                if state['ambiguous_create'] == 'base':
                    state['ambiguous_create'] = None
                    raise fixture.TargetDrift('JIT_COMMAND_FAILED')
            if args[:2] == ('profile', 'create') and args[2] == profile:
                state['profile_exists'] = True
                state['profile_marker'] = profile_data['config'] == {'user.q449.run_id': run_id}
                state['profile_device'] = profile_data['devices'] == {'q449-listener': device}
                if state['ambiguous_create'] == 'profile':
                    state['ambiguous_create'] = None
                    raise fixture.TargetDrift('JIT_COMMAND_FAILED')
            if args[:2] == ('profile', 'set') and args[2] == profile:
                state['profile_marker'] = True
                if state['ambiguous_create'] == 'marker':
                    state['ambiguous_create'] = None
                    raise fixture.TargetDrift('JIT_COMMAND_FAILED')
            if args[:2] == ('profile', 'set') and args[2] == base_profile:
                state['base_config'][args[3]] = args[4]
            if args[:3] == ('profile', 'device', 'add') and args[3] == profile:
                state['profile_device'] = True
                if state['ambiguous_create'] == 'listener':
                    state['ambiguous_create'] = None
                    raise fixture.TargetDrift('JIT_COMMAND_FAILED')
            if args[:1] == ('init',):
                # Qualified Incus 6.0.5 init creates stopped instances and has no --no-start flag.
                if '--no-start' in args:
                    raise fixture.TargetDrift('INCUS_INIT_UNSUPPORTED_FLAG')
                state['instance'] = True
                state['ever_started'] = False
                state['instance_marker'] = '-c' in args and args[args.index('-c') + 1] == 'user.q449.run_id=' + run_id
                if state['ambiguous_create'] == 'instance':
                    state['ambiguous_create'] = None
                    raise fixture.TargetDrift('JIT_COMMAND_FAILED')
            if args[:2] == ('config', 'set'):
                state['instance_marker'] = True
            if args[:1] == ('start',):
                state['status'] = 'running'
                state['ever_started'] = True
            if args[:1] == ('stop',):
                state['status'] = 'stopped'
            if args[:1] == ('delete',):
                state['instance'] = False
                if state['inject_route_drift_after_delete']:
                    state['route_drift'] = True
            if args[:2] == ('profile', 'delete') and args[2] == profile:
                state['profile_exists'] = False
            if args[:2] == ('profile', 'delete') and args[2] == base_profile:
                state['base_exists'] = False
            if args[:1] == ('list',):
                names = ([{'name': instance}] if state['foreign_instance'] else [])
                return json.dumps(names).encode()
            if args[:2] == ('profile', 'list'):
                names = ([{'name': base_profile}] if state['base_exists'] else [])
                if state['profile_exists']:
                    names.append({'name': profile})
                if state['foreign_profile']:
                    names.append({'name': state['foreign_profile']})
                return json.dumps(names).encode()
            if args[:1] == ('query',) and args[1] == fixture._profile_api_path('default', 'default'):
                return json.dumps({'name': 'default', 'project': 'default',
                                   'config': {}, 'devices': {}, 'used_by': []}).encode()
            if args[:1] == ('query',) and args[1] == fixture._profile_api_path(profile, 'default'):
                if not state['profile_exists']:
                    raise fixture.TargetDrift('JIT_COMMAND_FAILED')
                return json.dumps({'name': profile, 'project': 'default',
                                   'config': {'user.q449.run_id': run_id} if state['profile_marker'] else {},
                                   'devices': {'q449-listener': device} if state['profile_device'] else {},
                                   'used_by': ['/1.0/instances/foreign'] if state['instance'] and state['foreign_consumer'] else ([route] if state['instance'] else [])}).encode()
            if args[:1] == ('query',) and args[1] == fixture._profile_api_path(base_profile, 'default'):
                return json.dumps({'name': base_profile, 'project': 'default',
                                   'config': dict(state['base_config']), 'devices': {},
                                   'used_by': [route] if state['instance'] else []}).encode()
            if args[:1] == ('query',) and args[1] == fixture._instance_api_path(instance, 'default'):
                data = _fixture_instance_dto(go, {'config': dict(state['base_config']), 'devices': {}}, {},
                    'running' if state['status'] == 'running' else ('stopped' if state.get('ever_started') else 'init'))
                if not state['instance_marker']:
                    data['config'].pop('user.q449.run_id')
                return json.dumps(data).encode()
            if args[:1] == ('info',):
                return json.dumps({'status': state['status']}).encode()
            return b''

        def command(argv):
            if argv[0] == 'curl':
                self.assertIn('--disable', argv)
                self.assertEqual(argv[argv.index('--noproxy') + 1], '*')
                return state.get('http_body', run_id.encode('ascii'))
            if argv[0] == 'incus':
                if argv[1:2] == ['query'] and argv[2] == fixture._profile_api_path('default', 'default'):
                    return json.dumps({'name': 'default', 'project': 'default',
                                   'config': {}, 'devices': {}, 'used_by': []}).encode()
                return b'[]'
            if argv[0] == 'ss':
                return listener if state['status'] == 'running' else listener.splitlines()[1] + b'\n'
            raise AssertionError(f'unexpected command {argv!r}')

        def inventory_command(argv):
            if argv == ['incus', 'query', fixture._profile_api_path('default', 'default')]:
                return json.dumps({'name': 'default', 'project': 'default',
                                   'config': {}, 'devices': {}, 'used_by': []}).encode()
            return incus(*argv[1:])

        baseline = {'listeners_10001': [listener.splitlines()[1]], 'incus_projects': ['default'],
                    'incus_10001_routes': [], 'windows_rules_portproxy': b'',
                    'approved_route_state_sha256': approved_route_state,
                    'image_properties': {}, 'derived_base_profile': {'config': {'boot.autostart': 'false'}, 'devices': {}},
                    'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3, 'filesystem_available_bytes': 2}}
        with (
            patch.object(fixture, '_incus', side_effect=incus),
            patch.object(fixture, '_inventory_command', side_effect=inventory_command),
            patch.object(fixture, 'command', side_effect=command),
            patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
        ):
            result = fixture._run_fixture(go, baseline)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['http_response_sha256'], fixture.digest(run_id.encode('ascii')))
        execute = next(args for args in calls if args[:1] == ('exec',))
        self.assertEqual(execute[-1], fixture._fixture_responder_script(run_id))
        self.assertLess(calls.index(('delete', instance, '--project', 'default')),
                        calls.index(('profile', 'delete', profile, '--project', 'default')))
        self.assertLess(calls.index(('profile', 'delete', profile, '--project', 'default')),
                        calls.index(('profile', 'delete', base_profile, '--project', 'default')))
        self.assertFalse(state['instance'])
        state.update({'base_config': {}, 'profile_marker': False, 'instance_marker': False, 'profile_device': False,
                      'status': 'stopped', 'http_body': b'foreign response'})
        calls.clear()
        with (
            patch.object(fixture, '_incus', side_effect=incus),
            patch.object(fixture, '_inventory_command', side_effect=inventory_command),
            patch.object(fixture, 'command', side_effect=command),
            patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
        ):
            with self.assertRaisesRegex(fixture.TargetDrift, 'FIXTURE_HTTP_UNVERIFIED'):
                fixture._run_fixture(go, baseline)
        self.assertFalse(state['instance'])
        self.assertFalse(state['profile_exists'])
        self.assertFalse(state['base_exists'])
        self.assertIn(('delete', instance, '--project', 'default'), calls)
        state.pop('http_body')
        state.update({'instance': False, 'profile_marker': False, 'instance_marker': False,
                      'status': 'stopped', 'foreign_consumer': True,
                      'base_exists': False, 'base_config': {}, 'profile_exists': False,
                      'profile_device': False, 'ambiguous_create': None,
                      'foreign_profile': None, 'foreign_instance': False})
        calls.clear()
        with (
            patch.object(fixture, '_incus', side_effect=incus),
            patch.object(fixture, '_inventory_command', side_effect=inventory_command),
            patch.object(fixture, 'command', side_effect=command),
            patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
        ):
            with self.assertRaises(fixture.TargetDrift):
                fixture._run_fixture(go, {'listeners_10001': [listener.splitlines()[1]],
                                          'incus_projects': ['default'],
                                          'incus_10001_routes': [], 'windows_rules_portproxy': b'',
                                          'approved_route_state_sha256': approved_route_state,
                                          'image_properties': {}, 'derived_base_profile': {'config': {'boot.autostart': 'false'}, 'devices': {}},
                                          'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3,
                                                        'filesystem_available_bytes': 2}})
        self.assertNotIn(('profile', 'delete', profile, '--project', 'default'), calls)
        self.assertTrue(state['instance'])

        state.update({'instance': False, 'profile_marker': False, 'instance_marker': False,
                      'status': 'stopped', 'foreign_consumer': False,
                      'base_exists': False, 'base_config': {}, 'profile_exists': False,
                      'profile_device': False, 'route_drift': False,
                      'inject_route_drift_after_delete': True})
        calls.clear()
        checkpoints = {'count': 0}
        drift_route = {'project': 'default', 'owner_type': 'profile', 'owner': 'unrelated',
                       'device': 'web', 'config': {'type': 'proxy',
                       'listen': 'tcp:0.0.0.0:10001'}, 'used_by': []}

        def route_drift_after_owned_instance():
            checkpoints['count'] += 1
            if state['route_drift']:
                return ['default'], [drift_route]
            return ['default'], []

        with (
            patch.object(fixture, '_incus', side_effect=incus),
            patch.object(fixture, '_inventory_command', side_effect=inventory_command),
            patch.object(fixture, 'command', side_effect=command),
            patch.object(fixture, '_incus_route_inventory', side_effect=route_drift_after_owned_instance),
        ):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_10001_ROUTE_CHANGED'):
                fixture._run_fixture(go, {
                    'listeners_10001': [listener.splitlines()[1]], 'incus_projects': ['default'],
                    'incus_10001_routes': [], 'windows_rules_portproxy': b'',
                    'approved_route_state_sha256': approved_route_state,
                    'image_properties': {}, 'derived_base_profile': {'config': {'boot.autostart': 'false'}, 'devices': {}},
                    'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3,
                                  'filesystem_available_bytes': 2}})
        self.assertTrue(state['instance'] is False)
        self.assertIn(('start', instance, '--project', 'default'), calls)
        self.assertIn(('delete', instance, '--project', 'default'), calls)
        self.assertIn(('profile', 'delete', profile, '--project', 'default'), calls)
        self.assertIn(('profile', 'delete', base_profile, '--project', 'default'), calls)
        self.assertGreaterEqual(checkpoints['count'], 2)

        for resource in ('base', 'profile', 'instance'):
            with self.subTest(ambiguous_resource=resource):
                state.update({'instance': False, 'profile_marker': False,
                              'instance_marker': False, 'status': 'stopped',
                              'foreign_consumer': False, 'base_exists': False,
                              'base_config': {}, 'profile_exists': False,
                              'profile_device': False, 'route_drift': False,
                              'inject_route_drift_after_delete': False,
                              'ambiguous_create': resource,
                              'foreign_profile': None, 'foreign_instance': False})
                calls.clear()
                with (
                    patch.object(fixture, '_incus', side_effect=incus),
                    patch.object(fixture, '_inventory_command', side_effect=inventory_command),
                    patch.object(fixture, 'command', side_effect=command),
                    patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
                ):
                    with self.assertRaisesRegex(fixture.TargetDrift, 'JIT_COMMAND_FAILED'):
                        fixture._run_fixture(go, {
                            'listeners_10001': [listener.splitlines()[1]], 'incus_projects': ['default'],
                            'incus_10001_routes': [], 'windows_rules_portproxy': b'',
                            'approved_route_state_sha256': approved_route_state,
                            'image_properties': {}, 'derived_base_profile': {'config': {'boot.autostart': 'false'}, 'devices': {}},
                            'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3,
                                          'filesystem_available_bytes': 2}})
                if resource == 'base':
                    self.assertIn(('profile', 'delete', base_profile, '--project', 'default'), calls)
                    self.assertFalse(state['profile_exists'])
                else:
                    self.assertIn(('profile', 'delete', profile, '--project', 'default'), calls)
                    self.assertIn(('profile', 'delete', base_profile, '--project', 'default'), calls)
                    if resource == 'instance':
                        self.assertIn(('delete', instance, '--project', 'default'), calls)
                self.assertFalse(state['instance'])

        for foreign in ('base_profile', 'fixture_profile', 'instance'):
            state.update({'instance': False, 'profile_marker': False,
                          'instance_marker': False, 'status': 'stopped',
                          'foreign_consumer': False, 'base_exists': False,
                          'base_config': {}, 'profile_exists': False,
                          'profile_device': False, 'ambiguous_create': None,
                          'foreign_profile': None, 'foreign_instance': False})
            if foreign == 'base_profile':
                state['foreign_profile'] = base_profile
                error_code = 'PROFILE_NAME_COLLISION'
            elif foreign == 'fixture_profile':
                state['foreign_profile'] = profile
                error_code = 'PROFILE_NAME_COLLISION'
            else:
                state['foreign_instance'] = True
                error_code = 'INSTANCE_NAME_COLLISION'
            calls.clear()
            with (
                patch.object(fixture, '_incus', side_effect=incus),
                patch.object(fixture, '_inventory_command', side_effect=inventory_command),
                patch.object(fixture, 'command', side_effect=command),
                patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
            ):
                with self.assertRaisesRegex(fixture.TargetDrift, error_code):
                    fixture._run_fixture(go, {
                        'listeners_10001': [listener.splitlines()[1]], 'incus_projects': ['default'],
                        'incus_10001_routes': [], 'windows_rules_portproxy': b'',
                        'approved_route_state_sha256': approved_route_state,
                        'image_properties': {}, 'derived_base_profile': {'config': {'boot.autostart': 'false'}, 'devices': {}},
                        'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3,
                                      'filesystem_available_bytes': 2}})
            self.assertNotIn(('delete', instance, '--project', 'default'), calls)
            if foreign == 'base_profile':
                self.assertNotIn(('profile', 'delete', base_profile, '--project', 'default'), calls)
            elif foreign == 'fixture_profile':
                self.assertNotIn(('profile', 'delete', profile, '--project', 'default'), calls)
            else:
                self.assertIn(('profile', 'delete', profile, '--project', 'default'), calls)
                self.assertIn(('profile', 'delete', base_profile, '--project', 'default'), calls)


class ResponderShellTests(unittest.TestCase):
    def test_responder_uses_fixed_nonce_http_and_nonconnecting_listener_readiness(self):
        fake = r"""#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
args=sys.argv[1:]
root=Path(os.environ['RESPONDER_FIXTURE'])
with (root/'calls.jsonl').open('a') as stream:stream.write(json.dumps(args)+'\n')
mode=os.environ['RESPONDER_MODE']
if args==['nc','-l','-s','127.0.0.1','-p','8080','-w','15']:
 data=sys.stdin.buffer.read()
 (root/'response.bin').write_bytes(data)
 (root/'ready').write_text('listener')
 deadline=time.monotonic()+3
 while not (root/'finished').exists() and time.monotonic()<deadline:time.sleep(0.01)
 sys.exit(0)
if args==['netstat','-ltn']:
 if (root/'ready').exists():
  address='0.0.0.0:8080' if mode=='foreign' else '127.0.0.1:8080'
  print('tcp 0 0 '+address+' 0.0.0.0:* LISTEN')
  if mode=='ready':(root/'finished').write_text('readiness observed without connecting')
 sys.exit(0)
if args[0]=='awk':
 assert args[1]=='$1 == "tcp" && $4 == "127.0.0.1:8080" && $6 == "LISTEN" { ready=1 } END { exit !ready }'
 rows=[line.split() for line in sys.stdin]
 sys.exit(0 if any(len(row)>=6 and row[0]=='tcp' and row[3]=='127.0.0.1:8080' and row[5]=='LISTEN' for row in rows) else 1)
if args==['sleep','0.2']:sys.exit(0)
sys.exit(2)
"""
        nonce = '0123456789abcdef' * 2
        script = fixture._fixture_responder_script(nonce)
        for mode in ('ready', 'foreign'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                busybox = root / 'busybox'
                busybox.write_text(fake)
                busybox.chmod(0o700)
                process = subprocess.Popen(['/bin/sh', '-c', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env={'PATH': str(root) + ':/usr/bin:/bin', 'RESPONDER_FIXTURE': str(root), 'RESPONDER_MODE': mode},
                    start_new_session=True)
                try:
                    stdout, stderr = process.communicate(timeout=8)
                finally:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    if process.poll() is None:
                        process.wait(timeout=3)
                self.assertEqual((stdout, stderr), (b'', b''))
                if mode == 'ready':
                    self.assertEqual(process.returncode, 0)
                else:
                    self.assertNotEqual(process.returncode, 0)
                response = (root / 'response.bin').read_bytes()
                headers, body = response.split(b'\r\n\r\n', 1)
                self.assertEqual(headers, b'HTTP/1.1 200 OK\r\nContent-Length: 32\r\nConnection: close\r\nContent-Type: text/plain')
                self.assertEqual(body, nonce.encode('ascii'))
                calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
                self.assertEqual(sum(call[0] == 'nc' for call in calls), 1)
                self.assertTrue(any(call == ['netstat', '-ltn'] for call in calls))
                self.assertTrue(all(call[0] in {'nc', 'netstat', 'awk', 'sleep'} for call in calls))
        for invalid in ('', 'A' * 32, 'a' * 31, 'a' * 33, 'a' * 31 + "'", 'a' * 32 + '\n'):
            with self.subTest(invalid=invalid), self.assertRaises(fixture.FixtureError):
                fixture._fixture_responder_script(invalid)


class JitNoMutationTests(_FixtureBehaviorTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch.object(fixture, '_assert_local_incus_remote_inventory')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_incus_plain_text_version_output_is_parsed_strictly(self):
        self.assertEqual(fixture._parse_incus_version(
            b'Client version: 6.0.5\nServer version: 6.0.5\n'), ('6.0.5', '6.0.5'))
        for output in (
                b'Server version: 6.0.5\nClient version: 6.0.5\n',
                b'Client version: 6.0.5\n',
                b'Client version: 6.0.5\nServer version: 6.0.5\nextra\n',
                b'Client version: 6.0.5\nServer version: unknown\n',
                b'Client version: 6.0.5\nServer version: 6.0.5\nServer version: 6.0.5\n',
                b'Client version: 6.0.5\nServer version: 6.0.5\xff\n'):
            with self.subTest(output=output), self.assertRaisesRegex(
                    fixture.TargetDrift, 'INCUS_VERSION_UNREADABLE'):
                fixture._parse_incus_version(output)

    def test_fixture_image_rejects_retired_or_unapproved_release_before_profile_read(self):
        fingerprint = 'e' * 64
        go = {'target': {'server_version': '6.0.5', 'image_fingerprint': fingerprint}}
        for properties in ({'os': 'Alpine Linux', 'release': '3.20'},
                           {'os': 'Alpine Linux', 'release': '3.22'},
                           {'os': 'Ubuntu', 'release': '3.21'},
                           {'os': 'Alpine Linux', 'release': '3.21\n'},
                           {'os': 'Alpine Linux', 'release': True}):
            outputs = [b'Client version: 6.0.5\nServer version: 6.0.5\n',
                       json.dumps([{'fingerprint': fingerprint}]).encode(),
                       json.dumps({'properties': properties}).encode()]
            with (self.subTest(properties=properties),
                  patch.object(fixture, '_assert_host_identity'),
                  patch.object(fixture, '_assert_local_incus_remote_inventory'),
                  patch.object(fixture, 'command', side_effect=outputs) as called,
                  patch.object(fixture, '_read_default_profile') as profile):
                with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_IMAGE_NOT_ALPINE_321'):
                    fixture.jit(go, '192.168.178.33')
                profile.assert_not_called()
                self.assertEqual(called.call_count, 3)
                self.assertEqual(called.call_args.args[0], ['incus', 'query', '/1.0/images/' + fingerprint + '?project=default'])

    def test_default_profile_digest_mismatch_is_a_jit_drift(self):
        run_id = 'a' * 32
        fingerprint = 'e' * 64
        profile = {'name': 'default', 'project': 'default', 'config': {}, 'devices': {}, 'used_by': []}
        go = {'target': {'host': '192.168.178.33', 'server_version': '6.0.5',
                         'instance': f'tsw-q449-{run_id}-fixture',
                         'profile': f'tsw-q449-{run_id}-profile',
                         'base_profile': f'tsw-q449-{run_id}-base',
                         'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': '0' * 64, 'default_profile_used_by': [],
              'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256({'boot.autostart': 'false'}, {})}
        outputs = [b'[{"addr_info":[{"local":"192.168.178.33"}]}]',
                   b'Client version: 6.0.5\nServer version: 6.0.5\n',
                   json.dumps([{'fingerprint': fingerprint}]).encode(),
                   b'{"properties":{"os":"Alpine Linux","release":"3.21"}}',
                   json.dumps(profile).encode()]
        seen = []
        def command(argv):
            seen.append(argv)
            return outputs[len(seen) - 1]
        with (patch.object(fixture, 'command', side_effect=command),
              patch.object(fixture, '_inventory_command', return_value=json.dumps(profile).encode())):
            with self.assertRaisesRegex(fixture.TargetDrift, 'DEFAULT_PROFILE_DRIFT'):
                fixture.jit(go, '192.168.178.33')
        self.assertEqual(len(seen), 4)
        self.assertFalse(any(argv[0] == 'incus' and argv[1] in {'create', 'init', 'start', 'delete'} for argv in seen))

    def test_default_profile_proxy_route_is_rejected_before_fixture_mutation(self):
        fingerprint = 'e' * 64
        run_id = 'a' * 32
        profile = {'name': 'default', 'project': 'default', 'config': {}, 'devices': {'web': {
            'type': 'proxy', 'listen': 'tcp:0.0.0.0:80', 'connect': 'tcp:127.0.0.1:8080',
            'bind': 'host'}},
            'used_by': []}
        def command(argv):
            if argv[:4] == ['ip', '-j', '-4', 'addr']:
                return b'[{"addr_info":[{"local":"192.168.178.33"}]}]'
            if argv[1:3] == ['remote', 'list']:
                return b'{"local":{"Addr":"unix://"}}'
            if argv[1:3] == ['remote', 'get-default']:
                return b'local'
            if argv == ['incus', 'version']:
                return b'Client version: 6.0.5\nServer version: 6.0.5\n'
            if argv[1:3] == ['project', 'list']:
                return b'[{"name":"default"}]'
            if argv[1:3] == ['image', 'list']:
                return json.dumps([{'fingerprint': fingerprint}]).encode()
            if argv == ['incus', 'query', '/1.0/images/' + fingerprint + '?project=default']:
                return b'{"properties":{"os":"Alpine Linux","release":"3.21"}}'
            if argv[:2] == ['incus', 'query'] and argv[2] == fixture._profile_api_path('default', 'default'):
                return json.dumps(profile).encode()
            raise AssertionError(f'unexpected command {argv!r}')
        go = {'target': {'host': '192.168.178.33', 'server_version': '6.0.5',
                         'instance': f'tsw-q449-{run_id}-fixture',
                         'profile': f'tsw-q449-{run_id}-profile',
                         'base_profile': f'tsw-q449-{run_id}-base', 'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256(profile['config'], profile['devices']),
              'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256({'boot.autostart': 'false'}, {}),
              'default_profile_used_by': []}
        with (patch.object(fixture, '_incus_10001_routes', return_value=[]),
              patch.object(fixture, 'command', side_effect=command) as command_mock,
              patch.object(fixture, '_inventory_command', return_value=json.dumps(profile).encode())):
            with self.assertRaisesRegex(fixture.TargetDrift, 'DEFAULT_PROFILE_DEVICE_UNAPPROVED'):
                fixture.jit(go, '192.168.178.33')
        self.assertFalse(any(call.args[0][0] == 'incus' and call.args[0][1] in {'create', 'init', 'start', 'delete'}
                             for call in command_mock.call_args_list))

    def test_malformed_device_rows_are_rejected_instead_of_skipped(self):
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROFILE_INVENTORY_UNREADABLE'):
            fixture._strict_devices({'broken': 'proxy'}, 'INCUS_PROFILE_INVENTORY_UNREADABLE')

    def test_proxy_device_allows_default_bind_to_be_omitted(self):
        device = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:8080',
                  'connect': 'tcp:127.0.0.1:80'}
        self.assertEqual(fixture._strict_devices({'web': device}, 'INCUS_PROFILE_INVENTORY_UNREADABLE',
                                                 allow_implicit_bind=True), {'web': device})
        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROFILE_INVENTORY_UNREADABLE'):
            fixture._strict_devices({'web': device}, 'INCUS_PROFILE_INVENTORY_UNREADABLE')

    def test_proxy_device_rejects_invalid_explicit_bind(self):
        for bind in ('invalid', []):
            with self.subTest(bind=bind):
                device = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:8080',
                          'connect': 'tcp:127.0.0.1:80', 'bind': bind}
                with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_PROFILE_INVENTORY_UNREADABLE'):
                    fixture._strict_devices({'web': device}, 'INCUS_PROFILE_INVENTORY_UNREADABLE',
                                            allow_implicit_bind=True)

    def test_fixture_profile_response_rejects_wrong_name_or_project(self):
        run_id = 'a' * 32
        profile_name = 'q449-profile'
        go = {'target': {'profile': profile_name, 'run_id': run_id},
              'proxy': {'listen': 'tcp:127.0.0.1:61000',
                        'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}}
        valid = {'name': profile_name, 'project': 'default',
                 'config': {'user.q449.run_id': run_id},
                 'devices': {'q449-listener': {'type': 'proxy', **go['proxy']}},
                 'used_by': []}
        self.assertEqual(fixture._assert_fixture_profile(go, valid, [] )['config'],
                         valid['config'])
        for field in ('name', 'project'):
            with self.subTest(field=field):
                mismatch = {**valid, field: 'other'}
                with self.assertRaises(fixture.TargetDrift):
                    fixture._assert_fixture_profile(go, mismatch, [])

    def test_effective_profile_and_device_set_is_exact_and_has_no_instance_overrides(self):
        run_id = 'a' * 32
        go = {'target': {'instance': 'fixture', 'profile': 'q449-profile',
                         'base_profile': 'q449-base', 'run_id': run_id},
              'proxy': {'listen': 'tcp:127.0.0.1:61000',
                        'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}}
        default_profile = {'derived': {'devices': {
            'root': {'type': 'disk', 'path': '/', 'pool': 'default'}}}}
        fixture_device = {'type': 'proxy', **go['proxy']}
        fixture_profile = {'devices': {'q449-listener': fixture_device}}
        local = {'name': 'fixture', 'project': 'default',
                 'config': {'user.q449.run_id': run_id}, 'devices': {},
                 'profiles': ['q449-base', 'q449-profile'],
                 'expanded_config': {'user.q449.run_id': run_id},
                 'expanded_devices': {'root': default_profile['derived']['devices']['root'],
                                      'q449-listener': fixture_device}}
        expanded_devices = local['expanded_devices']
        with patch.object(fixture, '_incus', return_value=json.dumps(local).encode()):
            self.assertEqual(fixture._verify_effective_instance(go, default_profile, fixture_profile)['devices'],
                             expanded_devices)
        candidates = (
            {'profiles': ['q449-base', 'q449-profile'], 'devices': {
                **expanded_devices, 'extra': {'type': 'proxy', 'listen': 'tcp:0.0.0.0:80'}}},
            {'profiles': ['q449-base', 'foreign', 'q449-profile'], 'devices': expanded_devices},
            {'profiles': ['q449-base', 'q449-profile'], 'devices': {**expanded_devices, 'bad': 'proxy'}},
        )
        for candidate in candidates:
            api_instance = {**local, 'expanded_devices': candidate['devices'],
                            'profiles': candidate['profiles']}
            with self.subTest(candidate=candidate), patch.object(
                    fixture, '_incus', return_value=json.dumps(api_instance).encode()):
                with self.assertRaises(fixture.TargetDrift):
                    fixture._verify_effective_instance(go, default_profile, fixture_profile)

    def test_approved_route_state_mismatch_is_rejected(self):
        listeners = [b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:*']
        routes = [{'project': 'default', 'owner_type': 'profile', 'owner': 'manager', 'device': 'web',
                   'config': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001'}, 'used_by': []}]
        go = {'approved_route_state_sha256': fixture.approved_route_state_sha256(
            listeners, routes, b'approved windows state', ['default'])}
        with self.assertRaisesRegex(fixture.TargetDrift, 'APPROVED_ROUTE_STATE_DRIFT'):
            fixture._assert_approved_route_state(go, listeners, routes, b'changed windows state', ['default'])

    def test_every_jit_command_failure_prefix_contains_no_incus_write(self):
        run_id = 'a' * 32
        fingerprint = 'e' * 64
        profile = {'name': 'default', 'project': 'default', 'config': {}, 'devices': {}, 'used_by': []}
        route = {'name': 'legacy', 'project': 'default', 'config': {}, 'devices': {'web': {'type': 'proxy',
                 'listen': 'tcp:127.0.0.1:10001', 'connect': 'tcp:127.0.0.1:8080',
                 'bind': 'host'}}, 'used_by': []}
        responses = {
            ('ip', '-j', '-4', 'addr'): b'[{"addr_info":[{"local":"192.168.178.33"}]}]',
            ('incus', 'version'): b'Client version: 6.0.5\nServer version: 6.0.5\n',
            ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"default"}]',
            ('incus', 'query', '/1.0/projects/default'): b'{"name":"default","description":"","config":{}}',
            ('incus', 'image', 'list', '--project', 'default', '--format', 'json'): json.dumps([{'fingerprint': fingerprint}]).encode(),
            ('incus', 'query', '/1.0/images/' + fingerprint + '?project=default'): b'{"properties":{"os":"Alpine Linux","release":"3.21"}}',
            ('free', '-b'): b'header\nMem: 40000000000 1000000 2000000 0 3000000 35000000000',
            ('df', '-B1', '--output=avail', str(fixture.ROOT)): b'Avail\n100000000000',
            ('ss', '-H', '-ltn'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:*',
            ('ss', '-H', '-ltnp'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))',
            ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
            ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'): json.dumps([route]).encode(),
        }
        go = {'target': {'host': '192.168.178.33', 'server_version': '6.0.5',
                         'instance': f'tsw-q449-{run_id}-fixture',
                         'profile': f'tsw-q449-{run_id}-profile', 'base_profile': f'tsw-q449-{run_id}-base',
                         'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
              'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256({'boot.autostart': 'false'}, {}),
              'default_profile_used_by': []}
        go['approved_route_state_sha256'] = fixture.approved_route_state_sha256(
            [b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))'],
            [{'project': 'default', 'owner_type': 'profile', 'owner': 'legacy', 'device': 'web',
              'config': route['devices']['web'], 'used_by': []}], b'', ['default'])
        command_order = [
            ('ip', '-j', '-4', 'addr'), ('incus', 'version'),
            ('incus', 'image', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'query', '/1.0/images/' + fingerprint + '?project=default'),
            ('free', '-b'), ('df', '-B1', '--output=avail', str(fixture.ROOT)),
            ('ss', '-H', '-ltn'), ('ss', '-H', '-ltnp'),
            ('incus', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'project', 'list', '--format', 'json'),
            ('incus', 'query', '/1.0/projects/default'),
            ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'list', '--project', 'default', '--format', 'json'),
        ]
        self.assertEqual(set(command_order), set(responses))
        for failure_index in range(1, len(command_order) + 1):
            seen = []

            def command(argv):
                key = tuple(argv)
                seen.append(key)
                if len(seen) == failure_index:
                    raise fixture.TargetDrift('injected read-only drift')
                return responses[key]

            with (self.subTest(failure_index=failure_index),
                  patch.object(fixture, 'command', side_effect=command),
                  patch.object(fixture, '_inventory_command', return_value=json.dumps(profile).encode())):
                with self.assertRaises(fixture.TargetDrift):
                    fixture.jit(go, '192.168.178.33')
            self.assertTrue(all(not (cmd[0] == 'incus' and cmd[1] in {
                'create', 'init', 'start', 'stop', 'delete',
                'config', 'launch', 'copy', 'move',
            }) for cmd in seen))


class WslJitTests(_FixtureBehaviorTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch.object(fixture, '_assert_local_incus_remote_inventory')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_source_commit_must_equal_current_head(self):
        case = GoValidationTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        candidate = json.loads(json.dumps(case.go))
        candidate['source_commit'] = 'c' * 40
        with self.assertRaises(fixture.FixtureError):
            fixture.validate_go(candidate, case.args, 'b' * 40, case.workflow, case.runner, case.tests)

    def test_default_profile_consumer_drift_is_detected_by_jit(self):
        case = GoValidationTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        go = {'target': {'host': '192.168.178.33', 'server_version': '6.0.5',
                         'instance': case.go['target']['instance'], 'profile': case.go['target']['profile'],
                         'base_profile': case.go['target']['base_profile'],
                         'image_fingerprint': case.go['target']['image_fingerprint']},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
              'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256({'boot.autostart': 'false'}, {}),
              'default_profile_used_by': []}
        outputs = [b'[{"addr_info":[{"local":"192.168.178.33"}]}]',
                   b'Client version: 6.0.5\nServer version: 6.0.5\n',
                   json.dumps([{'fingerprint': case.go['target']['image_fingerprint']}]).encode(),
                   b'{"properties":{"os":"Alpine Linux","release":"3.21"}}',
                   b'{"name":"default","project":"default","config":{},"devices":{},"used_by":["/1.0/instances/other"]}']
        with (patch.object(fixture, 'command', side_effect=outputs),
              patch.object(fixture, '_inventory_command', return_value=outputs[-1])):
            with self.assertRaisesRegex(fixture.TargetDrift, 'DEFAULT_PROFILE_CONSUMERS_DRIFT'):
                fixture.jit(go, '192.168.178.33')

    def test_wsl_identity_and_windows_rules_portproxy_snapshot(self):
        fingerprint = 'e' * 64
        profile = {'name': 'default', 'project': 'default', 'config': {}, 'devices': {}, 'used_by': []}
        route = {'name': 'legacy', 'project': 'default', 'config': {}, 'devices': {'web': {'type': 'proxy',
                 'listen': 'tcp:127.0.0.1:10001', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}},
                 'used_by': []}
        seen = []

        def command(argv):
            seen.append(argv)
            if argv[0] == 'uname':
                return b'6.6.87.2-microsoft-standard-WSL2'
            if argv[0].endswith('powershell.exe'):
                script = argv[-1]
                if 'Get-NetIPAddress' in script:
                    return b'192.168.178.58\n'
                if 'tsw.windows-firewall-certificate.v1' in script:
                    return json.dumps(_certificate_fixture({'profiles': [], 'settings': [], 'rules': []})).encode()
            if argv[0].endswith('/netsh.exe'):
                return b'listen 0.0.0.0:10001 connect 127.0.0.1:10001\r\n'
            mapping = {
                ('incus', 'remote', 'list', '--format', 'json'): b'{"local":{"Addr":"unix://"}}',
                ('incus', 'remote', 'get-default'): b'local',
                ('incus', 'version'): b'Client version: 6.0.5\nServer version: 6.0.5\n',
                ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"default"}]',
                ('incus', 'query', '/1.0/projects/default'): b'{"name":"default","description":"","config":{}}',
                ('incus', 'image', 'list', '--project', 'default', '--format', 'json'): json.dumps([{'fingerprint': fingerprint}]).encode(),
                ('incus', 'query', '/1.0/images/' + fingerprint + '?project=default'): b'{"properties":{"os":"Alpine Linux","release":"3.21"}}',
                ('incus', 'query', fixture._profile_api_path('default', 'default')): json.dumps(profile).encode(),
                ('free', '-b'): b'header\nMem: 40000000000 1000000 2000000 0 3000000 35000000000',
                ('df', '-B1', '--output=avail', str(fixture.ROOT)): b'Avail\n100000000000',
                ('ss', '-H', '-ltn'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:*',
                ('ss', '-H', '-ltnp'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))',
                ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
                ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'): json.dumps([route]).encode(),
                }
            return mapping[tuple(argv)]

        go = {'target': {'host': '192.168.178.58', 'server_version': '6.0.5',
                         'instance': 'tsw-q449-' + 'a' * 32 + '-fixture',
                         'profile': 'tsw-q449-' + 'a' * 32 + '-profile',
                         'base_profile': 'tsw-q449-' + 'a' * 32 + '-base',
                         'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
              'windows_snapshot_sha256': _snapshot_asset_digest(), 'windows_certificate_sha256': fixture.WINDOWS_CERTIFICATE_SHA256, 'fixture_base_profile_sha256': fixture.canonical_profile_sha256({'boot.autostart': 'false'}, {}),
              'default_profile_used_by': []}
        firewall_bytes = json.dumps(_certificate_fixture({'profiles': [], 'settings': [], 'rules': []}),
                                    sort_keys=True, separators=(',', ':')).encode()
        portproxy_bytes = b'listen 0.0.0.0:10001 connect 127.0.0.1:10001\r\n'
        windows_snapshot = fixture._pack_windows_snapshot(firewall_bytes, portproxy_bytes)
        go['approved_route_state_sha256'] = fixture.approved_route_state_sha256(
            [b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))'],
            [fixture._safe_route_row('default', 'profile', 'legacy', 'web',
                                     route['devices']['web'], ['legacy'])], windows_snapshot, ['default'])
        with (patch.object(fixture, 'command', side_effect=command),
              patch.object(fixture, '_inventory_command', return_value=json.dumps(profile).encode())):
            baseline = fixture.jit(go, '192.168.178.58')
        self.assertEqual(baseline['windows_rules_portproxy'], windows_snapshot)
        self.assertTrue(any(argv[0].endswith('powershell.exe') and 'Get-NetIPAddress' in argv[-1] for argv in seen))
        firewall_command = next(argv[-1] for argv in seen if argv[0].endswith('powershell.exe')
                                and 'tsw.windows-firewall-certificate.v1' in argv[-1])
        self.assertEqual(firewall_command, fixture._windows_snapshot_wrapper(go['windows_snapshot_sha256']))
        query_source = fixture._windows_snapshot_query(go['windows_snapshot_sha256'])
        for cmdlet in ('Get-NetFirewallProfile',
                       'Get-NetFirewallSetting',
                       'Get-NetFirewallAddressFilter', 'Get-NetFirewallApplicationFilter',
                       'Get-NetFirewallInterfaceFilter', 'Get-NetFirewallInterfaceTypeFilter',
                       'Get-NetFirewallPortFilter', 'Get-NetFirewallSecurityFilter',
                       'Get-NetFirewallServiceFilter'):
            self.assertIn(cmdlet, query_source)
        self.assertTrue(any(argv[0].endswith('/netsh.exe') and argv[1:] == [
            'interface', 'portproxy', 'show', 'all'] for argv in seen))
        self.assertEqual(baseline['incus_10001_routes'][0]['owner'], 'legacy')

        seen.clear()
        def fail_firewall_snapshot(argv):
            if argv[0].endswith('powershell.exe') and 'tsw.windows-firewall-certificate.v1' in argv[-1]:
                seen.append(argv)
                raise fixture.TargetDrift('WINDOWS_SNAPSHOT_TIMEOUT')
            return command(argv)
        with (patch.object(fixture, 'command', side_effect=fail_firewall_snapshot),
              patch.object(fixture, '_inventory_command', return_value=json.dumps(profile).encode())):
            with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_TIMEOUT'):
                fixture.jit(go, '192.168.178.58')
        self.assertFalse(any(argv[0] == 'incus' and len(argv) > 1 and argv[1] in {
            'create', 'init', 'launch', 'start', 'stop', 'delete', 'copy', 'move',
        } for argv in seen))

        go['approved_route_state_sha256'] = '0' * 64
        seen.clear()
        with (patch.object(fixture, 'command', side_effect=command),
              patch.object(fixture, '_inventory_command', return_value=json.dumps(profile).encode())):
            with self.assertRaisesRegex(fixture.TargetDrift, 'APPROVED_ROUTE_STATE_DRIFT'):
                fixture.jit(go, '192.168.178.58')
        self.assertFalse(any(argv[0] == 'incus' and argv[1] in {
            'create', 'init', 'start', 'stop', 'delete', 'launch', 'copy', 'move',
        } for argv in seen))

    def test_windows_snapshot_comparison_accepts_equal_and_rejects_changed(self):
        fixture._assert_windows_unchanged(b'approved state', b'approved state')
        with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_RULES_CHANGED'):
            fixture._assert_windows_unchanged(b'approved state', b'changed state')

    def test_windows_snapshot_digest_is_stable_across_provider_order(self):
        base = {'profiles': [{'Name': 'Public'}, {'Name': 'Private'}],
                'settings': [{'Setting': 'z'}, {'Setting': 'a'}],
                'rules': [{'rule': {'Name': 'rule-b'},
                           'profiles': [{'Name': 'Public'}, {'Name': 'Private'}],
                           'address': [{'RemoteAddress': 'Any'}], 'application': [{'Program': 'Any'}],
                           'interface': [{'InterfaceAlias': 'Any'}],
                           'interface_type': [{'InterfaceType': 'Any'}], 'port': [{'LocalPort': 'Any'}],
                           'security': [{'Authentication': 'NotRequired'}], 'service': [{'Service': 'Any'}]},
                          {'rule': {'Name': 'rule-a'},
                           'profiles': [{'Name': 'Private'}, {'Name': 'Public'}],
                           'address': [{'RemoteAddress': 'LocalSubnet'}], 'application': [{'Program': 'Any'}],
                           'interface': [{'InterfaceAlias': 'Any'}],
                           'interface_type': [{'InterfaceType': 'Any'}], 'port': [{'LocalPort': 'Any'}],
                           'security': [{'Authentication': 'NotRequired'}], 'service': [{'Service': 'Any'}]}]}
        reordered = json.loads(json.dumps(base))
        reordered['profiles'].reverse()
        reordered['settings'].reverse()
        reordered['rules'].reverse()
        for rule in reordered['rules']:
            rule['profiles'].reverse()
        portproxy = b'raw exact portproxy bytes\r\n'
        outputs = [json.dumps(_certificate_fixture(base)).encode(), portproxy,
                   json.dumps(_certificate_fixture(reordered)).encode(), portproxy]
        with patch.object(fixture, 'command', side_effect=outputs):
            first = fixture._windows_snapshot()
            first_digest = fixture._WINDOWS_SNAPSHOT_METADATA['windows_snapshot_sha256']
            second = fixture._windows_snapshot()
        self.assertEqual(first, second)
        self.assertEqual(first_digest, fixture._WINDOWS_SNAPSHOT_METADATA['windows_snapshot_sha256'])
        self.assertEqual(first[-len(portproxy):], portproxy)
        self.assertNotIn(b'base64', first)

    def test_wsl_route_capture_binds_identity_and_canonical_active_store_plus_exact_portproxy(self):
        firewall_value = {
            'profiles': [{'Name': 'Public', 'Enabled': True}, {'Name': 'Domain', 'Enabled': False}],
            'settings': [{'PolicyStoreSource': 'ActiveStore'}],
            'rules': [{'rule': {'Name': 'z-rule', 'Enabled': True},
                       'profiles': [{'Name': 'Public'}], 'address': [{'RemoteAddress': 'Any'}],
                       'application': [{'Program': 'Any'}], 'interface': [{'InterfaceAlias': 'Any'}],
                       'interface_type': [{'InterfaceType': 'Any'}], 'port': [{'LocalPort': 'Any'}],
                       'security': [{'Authentication': 'NotRequired'}], 'service': [{'Service': 'Any'}]},
                      {'rule': {'Name': 'a-rule', 'Enabled': False},
                       'profiles': [{'Name': 'Public'}], 'address': [{'RemoteAddress': 'Any'}],
                       'application': [{'Program': 'Any'}], 'interface': [{'InterfaceAlias': 'Any'}],
                       'interface_type': [{'InterfaceType': 'Any'}], 'port': [{'LocalPort': 'Any'}],
                       'security': [{'Authentication': 'NotRequired'}], 'service': [{'Service': 'Any'}]}],
        }
        raw_portproxy = b'listen 0.0.0.0:10001 connect 127.0.0.1:10001\r\n'
        seen = []

        def command(argv):
            seen.append(argv)
            if argv[0] == 'uname':
                return b'6.6.87.2-microsoft-standard-WSL2'
            if argv[0].endswith('powershell.exe'):
                if 'Get-NetIPAddress' in argv[-1]:
                    return b'192.168.178.58\n'
                if 'tsw.windows-firewall-certificate.v1' in argv[-1]:
                    return json.dumps(_certificate_fixture(firewall_value)).encode('utf-8')
            if argv[0].endswith('/netsh.exe'):
                return raw_portproxy
            if argv[0] == 'ss':
                return b''
            if argv == ['incus', 'remote', 'list', '--format', 'json']:
                return b'{"local":{"Addr":"unix://"}}'
            if argv == ['incus', 'remote', 'get-default']:
                return b'local'
            if argv == ['incus', 'project', 'list', '--format', 'json']:
                return b'[{"name":"default"},{"name":"qa"}]'
            if argv == ['incus', 'query', '/1.0/projects/default']:
                return b'{"name":"default","description":"","config":{}}'
            if argv == ['incus', 'query', '/1.0/projects/qa']:
                return b'{"name":"qa","description":"","config":{}}'
            if argv[:3] == ['incus', 'profile', 'list']:
                return b'[]'
            if argv[:2] == ['incus', 'list']:
                return b'[]'
            self.fail(f'unexpected capture command: {argv}')

        def remote_inventory():
            seen.extend([
                ['incus', 'remote', 'list', '--format', 'json'],
                ['incus', 'remote', 'get-default'],
            ])

        with (patch.object(fixture, 'command', side_effect=command),
              patch.object(fixture, '_assert_local_incus_remote_inventory', side_effect=remote_inventory)):
            state = fixture._route_state('192.168.178.58')

        expected_value = _certificate_fixture(firewall_value)
        expected_firewall = json.dumps(expected_value, sort_keys=True, separators=(',', ':'),
                                       ensure_ascii=False).encode('utf-8')
        expected_snapshot = fixture._pack_windows_snapshot(expected_firewall, raw_portproxy)
        self.assertEqual(state['windows_snapshot'], expected_snapshot)
        self.assertEqual(state['approved_route_state_sha256'],
                         fixture.approved_route_state_sha256([], [], expected_snapshot, ['default', 'qa']))
        self.assertEqual(seen[0], ['uname', '-r'])
        self.assertIn(['incus', 'remote', 'list', '--format', 'json'], seen)
        self.assertIn(['incus', 'remote', 'get-default'], seen)
        self.assertIn(['incus', 'project', 'list', '--format', 'json'], seen)
        self.assertTrue(any(argv[0].endswith('powershell.exe') and 'Get-NetIPAddress' in argv[-1]
                            for argv in seen))
        self.assertTrue(any(argv[0].endswith('/netsh.exe') and argv[1:] == [
            'interface', 'portproxy', 'show', 'all'] for argv in seen))

    def test_windows_snapshot_rejects_malformed_provider_rows(self):
        complete_rule = {'rule': {'Name': 'r'},
                         'profiles': [{'Name': 'Public'}], 'address': [{'RemoteAddress': 'Any'}],
                         'application': [{'Program': 'Any'}], 'interface': [{'InterfaceAlias': 'Any'}],
                         'interface_type': [{'InterfaceType': 'Any'}], 'port': [{'LocalPort': 'Any'}],
                         'security': [{'Authentication': 'NotRequired'}], 'service': [{'Service': 'Any'}]}
        collections = ('profiles', 'address', 'application', 'interface', 'interface_type',
                       'port', 'security', 'service')
        missing_filters = [{**complete_rule, key: []} for key in collections]
        duplicate_filters = [{**complete_rule, key: [complete_rule[key][0],
                               dict(complete_rule[key][0])]} for key in collections]
        empty_associated_filter = {**complete_rule, 'port': [{}]}
        orphan_profile_association = {**complete_rule, 'profiles': [{'Name': 'MissingProfile'}]}
        orphan_collection = {**complete_rule, 'orphan': [{'Address': '192.0.2.1'}]}
        malformed_outputs = (
            b'{"profiles":[null],"settings":[],"rules":[]}',
            b'{"profiles":[],"settings":[],"rules":[{"rule":null}]}',
            b'{"profiles":[],"settings":[],"rules":[{"rule":{"Name":"r"},"profiles":[null],"address":[],"application":[],"interface":[],"interface_type":[],"port":[],"security":[],"service":[]}]}',
            *(json.dumps({'profiles': [{'Name': 'Public'}], 'settings': [], 'rules': [rule]}).encode()
              for rule in missing_filters),
            *(json.dumps({'profiles': [{'Name': 'Public'}], 'settings': [], 'rules': [rule]}).encode()
              for rule in duplicate_filters),
            json.dumps({'profiles': [{'Name': 'Public'}], 'settings': [], 'rules': [empty_associated_filter]}).encode(),
            json.dumps({'profiles': [{'Name': 'Public'}], 'settings': [], 'rules': [orphan_profile_association]}).encode(),
            json.dumps({'profiles': [{'Name': 'Public'}], 'settings': [], 'rules': [orphan_collection]}).encode(),
        )
        for raw in malformed_outputs:
            with self.subTest(raw=raw), patch.object(fixture, 'command', return_value=raw):
                with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE'):
                    fixture._windows_snapshot()


    def test_wsl_identity_mismatch_stops_before_incus(self):
        cases = (
            (b'Linux-native-kernel',),
            (b'6.6.87.2-microsoft-standard-WSL2', b'192.168.178.33\n'),
        )
        for outputs in cases:
            seen = []
            def command(argv):
                seen.append(argv)
                return outputs[len(seen) - 1]
            with self.subTest(outputs=outputs), patch.object(fixture, 'command', side_effect=command):
                with self.assertRaises(fixture.TargetDrift):
                    fixture.jit({'target': {'host': '192.168.178.58'}}, '192.168.178.58')
            self.assertFalse(any(argv[0] == 'incus' for argv in seen))



class BoundedWindowsSnapshotProcessTests(_FixtureBehaviorTestCase):
    def setUp(self):
        super().setUp()
        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None

    def _run(self, program, timeout=5, stdout_cap=128, stderr_cap=64, total_cap=512):
        with patch.object(fixture, '_inventory_budgets', return_value=(256, total_cap, 10_000, 300)):
            return fixture._snapshot_process(
                [fixture.sys.executable, '-c', program], timeout, stdout_cap, stderr_cap,
                'WINDOWS_SNAPSHOT_COMMAND_FAILED')

    def test_per_command_exact_stream_cap_is_accepted_and_cap_plus_one_rejected(self):
        self.assertEqual(self._run("import sys; sys.stdout.buffer.write(b'x'*128)"), b'x' * 128)
        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None
        with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_OUTPUT_TOO_LARGE'):
            self._run("import sys; sys.stdout.buffer.write(b'x'*129)")

    def test_exact_production_stream_and_aggregate_caps_are_accepted(self):
        mib = 1024 * 1024
        budgets = (256, 16 * mib, 10_000, 300)
        with patch.object(fixture, '_inventory_budgets', return_value=budgets):
            powershell = [fixture.sys.executable, '-c',
                          f"import sys; sys.stdout.buffer.write(b'o'*{14*mib}); "
                          f"sys.stderr.buffer.write(b'e'*{2*mib})"]
            output = fixture._snapshot_process(powershell, 120, 14*mib, 2*mib, 'FAILED')
            self.assertEqual(len(output), 14*mib)
            self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 16*mib)

        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None
        with patch.object(fixture, '_inventory_budgets', return_value=budgets):
            netsh = [fixture.sys.executable, '-c',
                     f"import sys; sys.stdout.buffer.write(b'o'*{2*mib}); "
                     f"sys.stderr.buffer.write(b'e'*{2*mib})"]
            self.assertEqual(len(fixture._snapshot_process(netsh, 30, 2*mib, 2*mib, 'FAILED')), 2*mib)
            self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 4*mib)

        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None
        with patch.object(fixture, '_inventory_budgets', return_value=budgets):
            first = [fixture.sys.executable, '-c', f"import sys; sys.stdout.buffer.write(b'x'*{14*mib})"]
            second = [fixture.sys.executable, '-c', f"import sys; sys.stderr.buffer.write(b'y'*{2*mib})"]
            self.assertEqual(len(fixture._snapshot_process(first, 120, 14*mib, 2*mib, 'FAILED')), 14*mib)
            self.assertEqual(fixture._snapshot_process(second, 30, 2*mib, 2*mib, 'FAILED'), b'')
            self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 16*mib)

    def test_per_command_and_aggregate_cap_plus_one_are_rejected(self):
        mib = 1024 * 1024
        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None
        with patch.object(fixture, '_inventory_budgets', return_value=(256, 16*mib, 10_000, 300)):
            oversized_firewall = [fixture.sys.executable, '-c',
                                  f"import sys; sys.stdout.buffer.write(b'x'*{14*mib+1})"]
            with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_OUTPUT_TOO_LARGE'):
                fixture._snapshot_process(oversized_firewall, 120, 14*mib, 2*mib, 'FAILED')

        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None
        with patch.object(fixture, '_inventory_budgets', return_value=(256, 16*mib, 10_000, 300)):
            oversized_netsh = [fixture.sys.executable, '-c',
                               f"import sys; sys.stderr.buffer.write(b'x'*{2*mib+1})"]
            with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_OUTPUT_TOO_LARGE'):
                fixture._snapshot_process(oversized_netsh, 30, 2*mib, 2*mib, 'FAILED')

        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None
        with patch.object(fixture, '_inventory_budgets', return_value=(256, 16*mib, 10_000, 300)):
            first = [fixture.sys.executable, '-c', f"import sys; sys.stdout.buffer.write(b'x'*{14*mib})"]
            oversized_second = [fixture.sys.executable, '-c', f"import sys; sys.stderr.buffer.write(b'y'*{2*mib+1})"]
            fixture._snapshot_process(first, 120, 14*mib, 2*mib, 'FAILED')
            with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_OUTPUT_TOO_LARGE'):
                fixture._snapshot_process(oversized_second, 30, 2*mib, 2*mib+1, 'FAILED')

    def test_aggregate_byte_cap_is_shared_between_commands(self):
        with patch.object(fixture, '_inventory_budgets', return_value=(256, 199, 10_000, 300)):
            command = [fixture.sys.executable, '-c', "import sys; sys.stdout.buffer.write(b'x'*100)"]
            self.assertEqual(fixture._snapshot_process(command, 5, 128, 64, 'FAILED'), b'x' * 100)
            with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_OUTPUT_TOO_LARGE'):
                fixture._snapshot_process(command, 5, 128, 64, 'FAILED')

    def test_timeout_is_distinct_from_nonzero_exit_and_child_is_reaped(self):
        processes = []
        popen = fixture.subprocess.Popen
        def track(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process
        with patch.object(fixture.subprocess, 'Popen', side_effect=track):
            with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_TIMEOUT'):
                self._run('import time; time.sleep(2)', timeout=0.05)
        self.assertTrue(processes)
        self.assertIsNotNone(processes[0].poll())
        fixture._COMMAND_AUDIT.clear()
        fixture._INVENTORY_BYTES_CAPTURED = 0
        fixture._INVENTORY_STARTED_AT = None
        with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_COMMAND_FAILED'):
            self._run('raise SystemExit(7)')

    def test_aggregate_command_limit_rejects_overrun(self):
        command = [fixture.sys.executable, '-c', 'pass']
        with patch.object(fixture, '_inventory_budgets', return_value=(1, 512, 10_000, 300)):
            fixture._snapshot_process(command, 5, 128, 64, 'FAILED')
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED'):
                fixture._snapshot_process(command, 5, 128, 64, 'FAILED')

    def test_production_256_command_limit_accepts_exact_count_then_rejects_plus_one(self):
        command = [fixture.sys.executable, '-c', 'pass']
        with patch.object(fixture, '_inventory_budgets', return_value=(256, 16*1024*1024, 10_000, 300)):
            for _ in range(256):
                self.assertEqual(fixture._snapshot_process(command, 5, 128, 64, 'FAILED'), b'')
            self.assertEqual(len(fixture._COMMAND_AUDIT), 256)
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED'):
                fixture._snapshot_process(command, 5, 128, 64, 'FAILED')

    def test_windows_command_dispatch_uses_required_timeout_and_caps(self):
        powershell = ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                      '-NoProfile', '-NonInteractive', '-Command', fixture._windows_snapshot_wrapper()]
        netsh = ['/mnt/c/Windows/System32/netsh.exe', 'interface', 'portproxy', 'show', 'all']
        with patch.object(fixture, '_snapshot_process', return_value=b'ok') as snapshot:
            self.assertEqual(fixture.command(powershell), b'ok')
            snapshot.assert_called_with(powershell, 120, 2 * 1024 * 1024,
                                        2 * 1024 * 1024, 'WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE', require_empty_stderr=True)
            self.assertEqual(fixture.command(netsh), b'ok')
            snapshot.assert_called_with(netsh, 30, 2 * 1024 * 1024,
                                        2 * 1024 * 1024, 'WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE')

    def test_production_timeout_limit_accepts_exact_deadline_and_rejects_plus_one(self):
        class FakePipe:
            def __init__(self, number):
                self.number = number
            def fileno(self):
                return self.number
            def close(self):
                pass

        class FakeProcess:
            def __init__(self, *args, **kwargs):
                self.stdout, self.stderr = FakePipe(11), FakePipe(12)
                self.killed = False
            def wait(self, timeout=None):
                return 0
            def kill(self):
                self.killed = True

        class FakeSelector:
            def __init__(self, elapsed, clock):
                self.elapsed, self.clock = elapsed, clock
                self.rows = {}
                self.advanced = False
            def register(self, stream, event, data):
                self.rows[stream.number] = SimpleNamespace(fileobj=stream, fd=stream.number, data=data)
            def get_map(self):
                return self.rows
            def select(self, timeout=None):
                if not self.advanced:
                    self.clock[0] += self.elapsed
                    self.advanced = True
                return [(row, 1) for row in list(self.rows.values())]
            def unregister(self, stream):
                self.rows.pop(stream.number)
            def close(self):
                pass

        for timeout, elapsed in ((120, 120), (30, 30)):
            with self.subTest(timeout=timeout, elapsed=elapsed):
                clock = [0.0]
                process = FakeProcess()
                with (patch.object(fixture, '_inventory_budgets', return_value=(256, 16*1024*1024, 10_000, 300)),
                      patch.object(fixture.subprocess, 'Popen', return_value=process),
                      patch.object(fixture.selectors, 'DefaultSelector', side_effect=lambda: FakeSelector(elapsed, clock)),
                      patch.object(fixture.os, 'set_blocking'), patch.object(fixture.os, 'read', return_value=b''),
                      patch.object(fixture.time, 'monotonic', side_effect=lambda: clock[0])):
                    fixture._INVENTORY_STARTED_AT = None
                    fixture._INVENTORY_BYTES_CAPTURED = 0
                    fixture._COMMAND_AUDIT.clear()
                    self.assertEqual(fixture._snapshot_process(['bounded.exe'], timeout, 8, 8, 'FAILED'), b'')

        for timeout, elapsed in ((120, 121), (30, 31)):
            with self.subTest(timeout=timeout, elapsed=elapsed):
                clock = [0.0]
                process = FakeProcess()
                with (patch.object(fixture, '_inventory_budgets', return_value=(256, 16*1024*1024, 10_000, 300)),
                      patch.object(fixture.subprocess, 'Popen', return_value=process),
                      patch.object(fixture.selectors, 'DefaultSelector', side_effect=lambda: FakeSelector(elapsed, clock)),
                      patch.object(fixture.os, 'set_blocking'), patch.object(fixture.os, 'read', return_value=b''),
                      patch.object(fixture.time, 'monotonic', side_effect=lambda: clock[0])):
                    fixture._INVENTORY_STARTED_AT = None
                    fixture._INVENTORY_BYTES_CAPTURED = 0
                    fixture._COMMAND_AUDIT.clear()
                    with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_SNAPSHOT_TIMEOUT'):
                        fixture._snapshot_process(['bounded.exe'], timeout, 8, 8, 'FAILED')
                    self.assertTrue(process.killed)

    def test_aggregate_300_second_limit_accepts_exact_deadline_and_rejects_plus_one(self):
        class Pipe:
            def __init__(self, number): self.number = number
            def fileno(self): return self.number
            def close(self): pass
        class Process:
            def __init__(self, *args, **kwargs):
                self.stdout, self.stderr, self.killed = Pipe(21), Pipe(22), False
            def wait(self, timeout=None): return 0
            def kill(self): self.killed = True
        class Selector:
            def __init__(self, elapsed, clock): self.elapsed, self.clock, self.rows = elapsed, clock, {}
            def register(self, stream, event, data):
                self.rows[stream.number] = SimpleNamespace(fileobj=stream, fd=stream.number, data=data)
            def get_map(self): return self.rows
            def select(self, timeout=None):
                self.clock[0] += self.elapsed
                return [(row, 1) for row in list(self.rows.values())]
            def unregister(self, stream): self.rows.pop(stream.number)
            def close(self): pass

        for elapsed, expected_error in ((300, None), (301, 'INCUS_INVENTORY_TOTAL_TIMEOUT')):
            with self.subTest(elapsed=elapsed):
                clock, process = [0.0], Process()
                with (patch.object(fixture, '_inventory_budgets', return_value=(256, 16*1024*1024, 10_000, 300)),
                      patch.object(fixture.subprocess, 'Popen', return_value=process),
                      patch.object(fixture.selectors, 'DefaultSelector', side_effect=lambda: Selector(elapsed, clock)),
                      patch.object(fixture.os, 'set_blocking'), patch.object(fixture.os, 'read', return_value=b''),
                      patch.object(fixture.time, 'monotonic', side_effect=lambda: clock[0])):
                    fixture._INVENTORY_STARTED_AT = None
                    fixture._INVENTORY_BYTES_CAPTURED = 0
                    fixture._COMMAND_AUDIT.clear()
                    if expected_error is None:
                        self.assertEqual(fixture._snapshot_process(['aggregate.exe'], 400, 8, 8, 'FAILED'), b'')
                    else:
                        with self.assertRaisesRegex(fixture.TargetDrift, expected_error):
                            fixture._snapshot_process(['aggregate.exe'], 400, 8, 8, 'FAILED')

    def test_powershell_and_netsh_share_aggregate_duration_budget(self):
        class Pipe:
            def __init__(self, number): self.number = number
            def fileno(self): return self.number
            def close(self): pass
        class Process:
            def __init__(self, *args, **kwargs): self.stdout, self.stderr = Pipe(31), Pipe(32)
            def wait(self, timeout=None): return 0
            def kill(self): pass
        class Selector:
            def __init__(self, elapsed, clock): self.elapsed, self.clock, self.rows = elapsed, clock, {}
            def register(self, stream, event, data):
                self.rows[stream.number] = SimpleNamespace(fileobj=stream, fd=stream.number, data=data)
            def get_map(self): return self.rows
            def select(self, timeout=None):
                self.clock[0] += self.elapsed
                return [(row, 1) for row in list(self.rows.values())]
            def unregister(self, stream): self.rows.pop(stream.number)
            def close(self): pass

        for starting_elapsed, should_pass in ((150, True), (151, False)):
            with self.subTest(starting_elapsed=starting_elapsed):
                clock = [float(starting_elapsed)]
                elapsed = [120, 30]
                with (patch.object(fixture, '_inventory_budgets', return_value=(256, 16*1024*1024, 10_000, 300)),
                      patch.object(fixture.subprocess, 'Popen', side_effect=Process),
                      patch.object(fixture.selectors, 'DefaultSelector',
                                   side_effect=lambda: Selector(elapsed.pop(0), clock)),
                      patch.object(fixture.os, 'set_blocking'), patch.object(fixture.os, 'read', return_value=b''),
                      patch.object(fixture.time, 'monotonic', side_effect=lambda: clock[0])):
                    fixture._INVENTORY_STARTED_AT = 0.0
                    fixture._INVENTORY_BYTES_CAPTURED = 0
                    fixture._COMMAND_AUDIT.clear()
                    fixture._snapshot_process(['powershell-snapshot'], 120, 14, 2, 'FAILED')
                    if should_pass:
                        fixture._snapshot_process(['netsh-portproxy'], 30, 2, 2, 'FAILED')
                        self.assertEqual(len(fixture._COMMAND_AUDIT), 2)
                    else:
                        with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_TOTAL_TIMEOUT'):
                            fixture._snapshot_process(['netsh-portproxy'], 30, 2, 2, 'FAILED')

    def test_keyboard_interrupt_kills_and_reaps_running_snapshot_process(self):
        class Pipe:
            def __init__(self, number): self.number = number
            def fileno(self): return self.number
            def close(self): pass
        class Process:
            def __init__(self, *args, **kwargs): self.stdout, self.stderr, self.killed = Pipe(41), Pipe(42), False
            def wait(self, timeout=None): return 0
            def kill(self): self.killed = True
        class InterruptingSelector:
            def register(self, *args): pass
            def get_map(self): return {1: True}
            def select(self, *args): raise KeyboardInterrupt
            def close(self): pass
        process = Process()
        with (patch.object(fixture, '_inventory_budgets', return_value=(256, 1024, 100, 300)),
              patch.object(fixture.subprocess, 'Popen', return_value=process),
              patch.object(fixture.selectors, 'DefaultSelector', return_value=InterruptingSelector()),
              patch.object(fixture.os, 'set_blocking')):
            with self.assertRaises(KeyboardInterrupt):
                fixture._snapshot_process(['interruptible.exe'], 120, 8, 8, 'FAILED')
        self.assertTrue(process.killed)

    def test_exact_eight_mib_route_artifact_limit_is_accepted_and_plus_one_rejected(self):
        cap = fixture._INVENTORY_ARTIFACT_MAX_BYTES
        empty = fixture._serialize_route_state_artifact({'padding': ''})
        exact_payload = {'padding': 'x' * (cap - len(empty))}
        exact = fixture._serialize_route_state_artifact(exact_payload)
        self.assertEqual(len(exact), cap)
        with self.assertRaisesRegex(fixture.FixtureError, 'INVENTORY_ARTIFACT_TOO_LARGE'):
            fixture._serialize_route_state_artifact({'padding': 'x' * (cap - len(empty) + 1)})


class SafeRouteProjectionTests(_FixtureBehaviorTestCase):
    def test_source_proxy_keys_are_strictly_allowlisted(self):
        device = {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001',
                  'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}
        row = fixture._safe_route_row('default', 'profile', 'manager', 'web', device, ['manager'])
        self.assertEqual(set(row), {'project', 'owner_type', 'owner', 'device', 'device_type',
                                    'effective_profiles', 'listen', 'connect', 'bind'})
        for extra in ({'nat': 'true'}, {'path': '/etc/passwd'}, {'uid': '1000'}):
            with self.subTest(extra=extra), self.assertRaisesRegex(
                    fixture.TargetDrift, 'INCUS_10001_ROUTE_UNAPPROVED'):
                fixture._safe_route_row('default', 'profile', 'manager', 'web', device | extra, ['manager'])

    def test_route_projection_rejects_malformed_endpoints_and_host_paths(self):
        for listen, connect in (("tcp:example.invalid:10001", 'tcp:127.0.0.1:8080'),
                                ('unix:/tmp/host.sock', 'tcp:127.0.0.1:8080'),
                                ('tcp:127.0.0.1:10001', 'unix:/tmp/host.sock')):
            device = {'type': 'proxy', 'listen': listen, 'connect': connect, 'bind': 'host'}
            with self.subTest(device=device), self.assertRaises(fixture.TargetDrift):
                fixture._safe_route_row('default', 'profile', 'manager', 'web', device, ['manager'])

    def test_route_artifact_schema_has_exact_types_and_failure_creates_no_file(self):
        row = fixture._safe_route_row('default', 'profile', 'manager', 'web', {
            'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001',
            'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}, ['manager'])
        self.assertEqual(row['owner_type'], 'profile')
        self.assertEqual(row['device_type'], 'proxy')
        self.assertIsInstance(row['effective_profiles'], list)
        for endpoint in (row['listen'], row['connect']):
            self.assertEqual(set(endpoint), {'protocol', 'address', 'port'})
            self.assertEqual(endpoint['protocol'], 'tcp')
            self.assertIsInstance(endpoint['address'], str)
            self.assertIsInstance(endpoint['port'], int)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / fixture.PRIVATE_EVIDENCE_REL
            evidence.mkdir(parents=True, mode=0o700)
            evidence.chmod(0o700)
            state = {'listeners_10001': [], 'incus_10001_routes': [row], 'incus_projects': ['default'],
                     'windows_snapshot': b'', 'approved_route_state_sha256': 'a' * 64}
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, '_INVENTORY_ARTIFACT_MAX_BYTES', 1),
                  patch.object(fixture, 'git_preflight', return_value=('b' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_route_state', return_value=state),
                  self.assertRaisesRegex(fixture.FixtureError, 'INVENTORY_ARTIFACT_TOO_LARGE')):
                fixture.capture_route_state('192.168.178.33',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/overflow.json')
            self.assertEqual(list(evidence.iterdir()), [])

    def test_route_artifact_redacts_raw_listener_details(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / fixture.PRIVATE_EVIDENCE_REL
            evidence.mkdir(parents=True, mode=0o700)
            evidence.chmod(0o700)
            raw = b'LISTEN 0 128 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=4312,fd=9))'
            routes = [fixture._safe_route_row(
                'default', 'profile', 'manager', 'web',
                {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001',
                 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}, ['manager'])]
            state = {'listeners_10001': [raw], 'incus_10001_routes': routes, 'incus_projects': ['default'],
                     'windows_snapshot': b'', 'approved_route_state_sha256': fixture.approved_route_state_sha256(
                         [raw], routes, b'', ['default'])}
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('a' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_route_state', return_value=state)):
                fixture.capture_route_state('192.168.178.33',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/safe-route-state.json')
            encoded = (evidence / 'safe-route-state.json').read_bytes()
            payload = fixture.strict_json(encoded)
            self.assertEqual(payload['listeners_10001'], fixture._safe_listener_tuples([raw]))
            self.assertEqual(payload['listeners_10001_count'], 1)
            for forbidden in (b'4312', b'incusd', b'fd=9', b'users:', b'_b64', b'windows_snapshot_b64'):
                self.assertNotIn(forbidden, encoded)

    def test_artifact_and_command_audit_do_not_persist_raw_windows_snapshot_content(self):
        raw_firewall = b'SID=S-1-5-21-123456; ACL=secret-firewall-provider-data'
        raw_portproxy = b'listen 0.0.0.0:10001 connect 127.0.0.1:10001\r\n'
        record = fixture._safe_command_record(
            ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
             '-Command', raw_firewall.decode()], 0, len(raw_firewall), 0)
        self.assertEqual(record['safe_args'], [])
        record_bytes = json.dumps(record).encode()
        self.assertNotIn(b'S-1-5-21', record_bytes)
        self.assertNotIn(b'secret-firewall-provider-data', record_bytes)
        self.assertNotIn(raw_portproxy, record_bytes)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / fixture.PRIVATE_EVIDENCE_REL
            evidence.mkdir(parents=True, mode=0o700)
            evidence.chmod(0o700)
            state = {'listeners_10001': [], 'incus_10001_routes': [], 'incus_projects': ['default'],
                     'windows_snapshot': fixture._pack_windows_snapshot(raw_firewall, raw_portproxy),
                     'approved_route_state_sha256': 'a' * 64}
            def route_state(_host):
                fixture._WINDOWS_SNAPSHOT_METADATA = {
                    'schema_version': 'tsw.windows-route-snapshot.v2',
                    'firewall_bytes': len(raw_firewall), 'firewall_sha256': fixture.digest(raw_firewall),
                    'portproxy_bytes': len(raw_portproxy), 'portproxy_sha256': fixture.digest(raw_portproxy),
                    'windows_snapshot_sha256': fixture.digest(state['windows_snapshot']),
                    'profile_count': 1, 'setting_count': 1, 'rule_count': 1,
                    'captured_at': '2026-01-01T00:00:00+00:00'}
                return state
            with (patch.object(fixture, 'ROOT', root),
                  patch.object(fixture, 'git_preflight', return_value=('c' * 40, b'w', b'r', b't')),
                  patch.object(fixture, '_route_state', side_effect=route_state)):
                fixture.capture_route_state('192.168.178.58',
                    '.tiny-swarm/evidence/issue-449/s449-private-20261027/windows-safe.json')
            encoded = (evidence / 'windows-safe.json').read_bytes()
            for forbidden in (b'S-1-5-21', b'secret-firewall-provider-data', raw_portproxy,
                              b'firewall_active_store_b64', b'portproxy_raw_b64'):
                self.assertNotIn(forbidden, encoded)
            payload = fixture.strict_json(encoded)
            self.assertEqual(payload['windows_snapshot']['windows_snapshot_sha256'],
                             fixture.digest(state['windows_snapshot']))



class _BoundedMemoryProcess:
    """Native transport substitute; real pipe reads/selectors/accounting stay active."""

    def __init__(self, payload=b'', status=0):
        self.status = status
        self.threads: list[threading.Thread] = []
        self.stdout = self._pipe(payload)
        self.stderr = self._pipe(b'')

    def _pipe(self, payload):
        read_fd, write_fd = os.pipe()

        def emit():
            try:
                view = memoryview(payload)
                while view:
                    view = view[os.write(write_fd, view):]
            except OSError:
                pass
            finally:
                os.close(write_fd)

        worker = threading.Thread(target=emit, daemon=True)
        self.threads.append(worker)
        worker.start()
        return os.fdopen(read_fd, 'rb', buffering=0)

    def wait(self, timeout=None):
        for worker in self.threads:
            worker.join(timeout)
        return self.status

    def terminate(self):
        self.status = -15

    def kill(self):
        self.status = -9


class _FullGraphFixtureTransport:
    """Three projects, inherited profiles and full foreign metadata; no kernel/Incus calls."""

    def __init__(self, testcase, *, wsl=False):
        self.is_wsl = wsl
        self.testcase = testcase
        self.run_id = 'a' * 32
        self.base = 'tsw-q449-' + self.run_id + '-base'
        self.profile = 'tsw-q449-' + self.run_id + '-profile'
        self.instance = 'tsw-q449-' + self.run_id + '-fixture'
        self.projects = ['default', 'issue447'] if wsl else ['default', 'foreign', 'inherited']
        self.profiles: dict[str, dict[str, Any]] = {name: {'name': name, 'project': 'default', 'config': {}, 'devices': {}, 'used_by': []}
                         for name in ('default', 'legacy-base', 'legacy-route')}
        self.profiles['default']['devices'] = {'root': {'type': 'disk', 'path': '/', 'pool': 'default'},
                                               'eth0': {'type': 'nic', 'name': 'eth0', 'network': 'incusbr0'}}
        self.profiles['legacy-route']['devices'] = {'web': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001',
                                                          'connect': 'tcp:127.0.0.1:80', 'bind': 'host'}}
        # A realistic full foreign list DTO exceeds the pipe capacity. Every checkpoint rereads it.
        self.foreign: dict[str, Any] = {'name': 'foreign-manager', 'project': 'foreign', 'status': 'Running',
                        'type': 'container', 'architecture': 'x86_64', 'description': '',
                        'config': {f'user.metadata.{i}': 'x' * 95 for i in range(80)},
                        'devices': {}, 'expanded_config': {}, 'expanded_devices': {},
                        'profiles': ['legacy-route'], 'backups': [], 'snapshots': [], 'state': {},
                        'created_at': '2026-11-08T00:00:00Z', 'ephemeral': False,
                        'stateful': False, 'status_code': 103, 'location': 'none'}
        self.foreign['expanded_config'] = dict(self.foreign['config'])
        self.foreign['expanded_devices'] = json.loads(json.dumps(self.profiles['legacy-route']['devices']))
        self.profiles['legacy-route']['used_by'] = ['/1.0/instances/foreign-manager?project=foreign']
        self.foreign_before = json.dumps(self.foreign, sort_keys=True)
        self.foreign_rows: dict[str, list[dict[str, Any]]] = {project: [] for project in self.projects}
        if wsl:
            for index in range(4):
                row = json.loads(self.foreign_before)
                project = 'default' if index < 3 else 'issue447'
                row.update(name='existing-' + str(index), project=project,
                           status='Stopped' if index in (1, 2) else 'Running',
                           status_code=102 if index in (1, 2) else 103)
                if index != 0:
                    row['profiles'] = ['legacy-base']
                    row['expanded_devices'] = {}
                self.foreign_rows[project].append(row)
            self.profiles['legacy-route']['used_by'] = sorted(
                fixture._instance_api_path(row['name'], project) for project, rows in self.foreign_rows.items()
                for row in rows if 'legacy-route' in row['profiles'])
        else:
            self.foreign_rows['foreign'] = [self.foreign]
        self.foreign_rows_before = json.dumps(self.foreign_rows, sort_keys=True)
        self.firewall = {'schema_version': 'tsw.windows-firewall-certificate.v1',
                         'query_sha256': _snapshot_asset_digest(), 'snapshot_sha256': 'c' * 64,
                         'snapshot_bytes': 9000000, 'snapshot_schema_version': 2, 'store': 'ActiveStore',
                         'association_model': 'PROVIDER_IDENTITY_ONE_TO_ONE',
                         'counts': {'rules': 500, 'profiles': 3, 'settings': 1,
                                    **dict.fromkeys(('address', 'application', 'interface', 'interface_type',
                                                    'port', 'security', 'service'), 500)}}
        self.portproxy = b'existing exact portproxy rows\r\n'
        self.windows_snapshot = fixture._pack_windows_snapshot(
            json.dumps(self.firewall, sort_keys=True, separators=(',', ':')).encode(), self.portproxy) if wsl else b''
        self.current: dict[str, Any] | None = None
        self.running = False
        self.events: list[tuple[str, ...]] = []
        self.effects: list[tuple[tuple[str, ...], int]] = []
        self.active_peak = 0
        self.windows_phases: list[bool] = []
        self.foreign_lists = 0
        self.fail_effect: tuple[str, ...] | None = None
        self.lost_create: str | None = None
        self.exhaust_after_base = False
        self.lost_init = False
        self.corrupt_after_exec = False
        self.listener = b'LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=44,fd=5))\n'
        self.go: dict[str, Any] = {'source_commit': 'f' * 40,
                   'target': {'host': '192.168.178.58' if wsl else '192.168.178.33', 'endpoint': 'unix://', 'project': 'default',
                              'server_version': '6.0.5', 'run_id': self.run_id, 'base_profile': self.base,
                              'profile': self.profile, 'instance': self.instance, 'image_fingerprint': 'b' * 64},
                   'proxy': {'listen': 'tcp:127.0.0.1:61000', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'},
                   'default_profile_used_by': []}
        default = self.profiles['default']
        self.go['windows_snapshot_sha256'] = _snapshot_asset_digest()
        self.go['windows_certificate_sha256'] = fixture.WINDOWS_CERTIFICATE_SHA256
        self.go['default_profile_sha256'] = fixture.canonical_profile_sha256(default['config'], default['devices'])
        self.go['fixture_base_profile_sha256'] = fixture.canonical_profile_sha256(
            {'boot.autostart': 'false'}, default['devices'])
        route = fixture._safe_route_row('default', 'profile', 'legacy-route', 'web',
                                        self.profiles['legacy-route']['devices']['web'], ['legacy-route'])
        self.go['approved_route_state_sha256'] = fixture.approved_route_state_sha256(
            [self.listener.rstrip(b'\n')], [route], self.windows_snapshot, self.projects)

    def _observe(self, args):
        self.events.append(tuple(args))
        if not fixture._INVENTORY_CLEANUP_MODE:
            self.active_peak = max(self.active_peak, len(fixture._COMMAND_AUDIT) + 1)

    def _before_effect(self, args):
        # Every effect requires a newly completed full graph since the preceding effect.
        since = self.events[self.effects[-1][1] + 1:] if self.effects else self.events
        required = [('project', 'list', '--format', 'json')]
        required += [('query', fixture._project_api_path(project)) for project in self.projects]
        required += [('list', '--project', project, '--format', 'json') for project in self.projects]
        required += [('profile', 'list', '--project', 'default', '--format', 'json')]
        for read in required:
            self.testcase.assertIn(read, since)
        self.effects.append((tuple(args), len(self.events) - 1))
        if self.fail_effect == tuple(args):
            raise OSError('simulated transport loss before effect')

    def _instance(self):
        if self.current is None:
            return None
        data = dict(self.current)
        data['status'] = 'Running' if self.running else 'Stopped'
        return data

    def _json(self, value):
        return json.dumps(value, sort_keys=True).encode()

    def read(self, args):
        if args == ['remote', 'list', '--format', 'json']:
            return self._json({'local': {'Addr': 'unix://', 'Public': False, 'Protocol': 'incus', 'Static': True}})
        if args == ['remote', 'get-default']:
            return b'local\n'
        if args == ['project', 'list', '--format', 'json']:
            return self._json([{'name': project} for project in self.projects])
        if args[:2] == ['profile', 'list']:
            return self._json(list(self.profiles.values()))
        if args[:1] == ['list']:
            project = args[args.index('--project') + 1]
            rows = list(self.foreign_rows[project])
            if rows:
                self.foreign_lists += 1
            if project == 'default' and self.current is not None:
                rows.append(self._instance())
            return self._json(rows)
        if args[:1] == ['info']:
            return self._json({'status': 'running' if self.running else 'stopped'})
        if args[:2] == ['image', 'list']:
            return self._json([{'fingerprint': 'b' * 64}])
        if args[:1] == ['query']:
            path = args[1]
            if path.startswith('/1.0/projects/'):
                project = path.rsplit('/', 1)[-1]
                return self._json({'name': project, 'description': '', 'config':
                                   {'features.profiles': 'true' if project == 'default' else 'false'}})
            if path.startswith('/1.0/images/'):
                return self._json({'properties': {'os': 'Alpine', 'release': '3.21'}})
            for name, profile in self.profiles.items():
                if path == fixture._profile_api_path(name, 'default'):
                    return self._json(profile)
            if path == fixture._instance_api_path('foreign-manager', 'foreign'):
                return self._json(self.foreign)
            if self.current is not None and path == fixture._instance_api_path(self.instance, 'default'):
                return self._json(self._instance())
        raise AssertionError(f'unexpected Incus read: {args!r}')

    def popen(self, argv, **kwargs):
        args = argv[1:]
        if (argv[0] != fixture.TRUSTED_BIN['incus']
                or args[:1] in (['version'], ['init'], ['start'], ['stop'], ['delete'], ['exec'])
                or args[:2] == ['profile', 'delete']):
            response = self.run(argv, **kwargs)
            return _BoundedMemoryProcess(response.stdout, response.returncode)
        self._observe(args)
        if args[:2] == ['profile', 'create']:
            self._before_effect(args)
            self.testcase.assertIsInstance(kwargs['stdin'], int)
            self.testcase.assertNotEqual(kwargs['stdin'], subprocess.DEVNULL)
            body = json.loads(os.read(kwargs['stdin'], 65537))
            self.testcase.assertEqual(set(body), {'config', 'devices'})
            self.profiles[args[2]] = {'name': args[2], 'project': 'default', 'used_by': [], **body}
            if self.exhaust_after_base and args[2] == self.base:
                # Keep the actual total cap; spend only active capacity, preserving cleanup reserve.
                fixture._COMMAND_AUDIT.extend({} for _ in range(145 - len(fixture._COMMAND_AUDIT)))
            return _BoundedMemoryProcess(status=1 if self.lost_create == args[2] else 0)
        self.testcase.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
        return _BoundedMemoryProcess(self.read(args))

    def run(self, argv, **kwargs):
        command_name, args = Path(argv[0]).name, argv[1:]
        self.testcase.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
        self._observe(args if command_name == 'incus' else [command_name, *args])
        if command_name == 'incus':
            if args == ['version']:
                output = b'Client version: 6.0.5\nServer version: 6.0.5\n'
            else:
                self._before_effect(args)
                if args[:1] == ['init']:
                    self.testcase.assertEqual(args[-2:], ['-c', 'user.q449.run_id=' + self.run_id])
                    self.current = _fixture_instance_dto(self.go, self.profiles[self.base], {'os': 'Alpine', 'release': '3.21'})
                    for name in (self.base, self.profile):
                        self.profiles[name]['used_by'] = ['/1.0/instances/' + self.instance]
                elif args[:1] == ['start']:
                    self.running = True
                    self.current = _fixture_instance_dto(self.go, self.profiles[self.base], {'os': 'Alpine', 'release': '3.21'}, 'running')
                elif args[:1] == ['stop']:
                    self.running = False
                    self.current = _fixture_instance_dto(self.go, self.profiles[self.base], {'os': 'Alpine', 'release': '3.21'}, 'stopped')
                elif args[:1] == ['delete']:
                    self.current = None
                    for name in (self.base, self.profile):
                        self.profiles[name]['used_by'] = []
                elif args[:2] == ['profile', 'delete']:
                    del self.profiles[args[2]]
                else:
                    self.testcase.assertEqual(args[0], 'exec')
                    if self.corrupt_after_exec:
                        assert self.current is not None
                        for field in ('volatile.uuid', 'volatile.uuid.generation'):
                            self.current['config'][field] = '33333333-3333-4333-8333-333333333333'
                            self.current['expanded_config'][field] = '33333333-3333-4333-8333-333333333333'
                output = b''
        elif command_name == 'powershell.exe':
            if 'tsw.windows-firewall-certificate.v1' in args[-1]:
                self.windows_phases.append(fixture._INVENTORY_CLEANUP_MODE)
            output = (b'192.168.178.58\n' if 'Get-NetIPAddress' in args[-1]
                      else self._json(self.firewall))
        elif command_name == 'netsh.exe':
            output = self.portproxy
        elif command_name == 'uname':
            output = b'6.6.87.2-microsoft-standard-WSL2'
        elif command_name == 'ip':
            output = b'[{"addr_info":[{"local":"192.168.178.33"}]}]'
        elif command_name == 'free':
            output = b'              total used free shared buff/cache available\nMem: 4000000000 1 2 0 1 3000000000\n'
        elif command_name == 'df':
            output = b'Avail\n10000000000\n'
        elif command_name == 'ss':
            output = self.listener
            if self.running:
                output += b'LISTEN 0 4096 127.0.0.1:61000 0.0.0.0:* users:(("incusd",pid=123,fd=4))\n'
        elif command_name == 'curl':
            output = self.run_id.encode()
        else:
            raise AssertionError(f'unexpected native command: {argv!r}')
        return SimpleNamespace(returncode=1 if self.lost_init and command_name == 'incus' and args[:1] == ['init'] else 0, stdout=output)


class HostScopedInventoryBudgetTests(_FixtureBehaviorTestCase):
    def test_native_and_wsl_profiles_reset_every_quota_without_cleanup_reclaim(self):
        for host, active, total in (('192.168.178.58', 350, 650), ('192.168.178.33', 240, 300)):
            fixture._COMMAND_AUDIT.append({'old': True})
            fixture._INVENTORY_BYTES_CAPTURED = 100
            fixture._INVENTORY_ENTITIES_CAPTURED = 100
            fixture._INVENTORY_ENTITY_SLOTS.add((('old',), ()))
            fixture._INVENTORY_STARTED_AT = 12.0
            fixture._WINDOWS_SNAPSHOT_METADATA = {'old': True}
            fixture._begin_inventory(host, reserve_cleanup=True)
            self.assertEqual(fixture._inventory_budgets(), (146, 8 * 1024 * 1024, 5000, active))
            self.assertEqual(fixture._COMMAND_AUDIT, [])
            self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 0)
            self.assertEqual(fixture._INVENTORY_ENTITIES_CAPTURED, 0)
            self.assertEqual(fixture._INVENTORY_ENTITY_SLOTS, set())
            self.assertIsNone(fixture._INVENTORY_STARTED_AT)
            self.assertEqual(fixture._WINDOWS_SNAPSHOT_METADATA, {})
            fixture._COMMAND_AUDIT.append({'consumed': True})
            fixture._INVENTORY_BYTES_CAPTURED = 123
            fixture._INVENTORY_STARTED_AT = 99.0
            fixture._INVENTORY_CLEANUP_MODE = True
            self.assertEqual(fixture._inventory_budgets(), (256, 16 * 1024 * 1024, 10000, total))
            self.assertEqual(fixture._COMMAND_AUDIT, [{'consumed': True}])
            self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 123)
            self.assertEqual(fixture._INVENTORY_STARTED_AT, 99.0)

    def test_invalid_host_never_grants_wsl_time_or_resets_consumed_quota(self):
        fixture._begin_inventory('192.168.178.33', reserve_cleanup=True)
        fixture._INVENTORY_BYTES_CAPTURED = 37
        with self.assertRaisesRegex(fixture.FixtureError, 'HOST_IDENTITY_DRIFT'):
            fixture._begin_inventory('unbound', reserve_cleanup=True)
        self.assertEqual(fixture._inventory_budgets()[-1], 240)
        self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 37)

    def test_all_capture_entrypoints_reset_stale_host_and_time_before_queries(self):
        for capture in (fixture.capture_route_state, fixture.capture_project_inventory):
            for host, total in (('192.168.178.58', 650), ('192.168.178.33', 300)):
                fixture._INVENTORY_STARTED_AT = -999.0
                fixture._INVENTORY_BYTES_CAPTURED = 999
                fixture._COMMAND_AUDIT.append({'stale': True})
                with (patch.object(fixture, '_capture_output_path', side_effect=fixture.FixtureError('STOP_BEFORE_QUERY')),
                      patch.object(fixture, '_require_private_evidence_dir'),
                      patch.object(fixture, 'command') as query,
                      self.assertRaisesRegex(fixture.FixtureError, 'STOP_BEFORE_QUERY')):
                    capture(host, str(fixture.PRIVATE_EVIDENCE_REL / 'capture.json'))
                self.assertEqual(fixture._inventory_budgets()[-1], total)
                self.assertIsNone(fixture._INVENTORY_STARTED_AT)
                self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 0)
                self.assertEqual(fixture._COMMAND_AUDIT, [])
                query.assert_not_called()

    def test_main_resets_host_scope_before_approval_or_effect(self):
        import contextlib
        import io
        for host, active in (('192.168.178.58', 350), ('192.168.178.33', 240)):
            fixture._INVENTORY_STARTED_AT = -999.0
            fixture._INVENTORY_BYTES_CAPTURED = 999
            with (contextlib.redirect_stderr(io.StringIO()), patch.object(fixture, 'git_preflight') as source):
                status = fixture.main(['--target-host', host, '--expected-approval-sha256', 'invalid'])
            self.assertEqual(status, 2)
            self.assertEqual(fixture._inventory_budgets()[-1], active)
            self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 0)
            self.assertIsNone(fixture._INVENTORY_STARTED_AT)
            source.assert_not_called()

    def test_shared_producer_asset_is_mandatory_and_not_an_inline_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / fixture.WINDOWS_CERTIFICATE_REL
            path.parent.mkdir(parents=True)
            good = (Path(__file__).resolve().parents[4] / fixture.WINDOWS_CERTIFICATE_REL).read_bytes()
            for raw in (b'', b'\xff', b'\xef\xbb\xbf' + good, good + b'\n', b'x' * 65537):
                path.write_bytes(raw)
                with patch.object(fixture, 'ROOT', root), self.assertRaises(fixture.FixtureError):
                    fixture._windows_certificate_source()
            path.unlink()
            target = root / 'other.ps1'
            target.write_bytes(good)
            path.symlink_to(target)
            with patch.object(fixture, 'ROOT', root), self.assertRaises(fixture.FixtureError):
                fixture._windows_certificate_source()
            path.unlink()
            with patch.object(fixture, 'ROOT', root), self.assertRaises(fixture.FixtureError):
                fixture._windows_certificate_source()
        with self.assertRaises(fixture.FixtureError):
            fixture._windows_certificate_source('0' * 64)
        with (patch.object(fixture, '_windows_certificate_source', return_value='missing placeholders'),
              patch.object(fixture.subprocess, 'Popen') as spawn,
              self.assertRaisesRegex(fixture.FixtureError, 'WINDOWS_SNAPSHOT_TEMPLATE_INVALID')):
            fixture._windows_snapshot_wrapper()
        spawn.assert_not_called()

class R3BudgetAndAtomicTransportTests(_FixtureBehaviorTestCase):
    def test_incus_read_cannot_spend_active_or_cleanup_time_reserve(self):
        for host, cleanup, total in (('192.168.178.33', False, 240), ('192.168.178.33', True, 300),
                                     ('192.168.178.58', False, 350), ('192.168.178.58', True, 650)):
            with self.subTest(host=host, cleanup=cleanup):
                self.setUp()
                fixture._INVENTORY_TARGET_HOST = host
                fixture._INVENTORY_STARTED_AT = 0.0
                fixture._INVENTORY_RESERVE_CLEANUP = True
                fixture._INVENTORY_CLEANUP_MODE = cleanup
                clock = [total - 0.1]
                process = Mock()
                process.stdout.fileno.return_value = 101
                process.stderr.fileno.return_value = 102
                selector = Mock()
                selector.get_map.return_value = {101: object()}
                def advance(timeout):
                    self.assertLessEqual(timeout, 0.101)
                    clock[0] += timeout
                    return []
                selector.select.side_effect = advance
                with (patch.object(fixture.subprocess, 'Popen', return_value=process) as spawn,
                      patch.object(fixture.selectors, 'DefaultSelector', return_value=selector),
                      patch.object(fixture.os, 'set_blocking'),
                      patch.object(fixture.time, 'monotonic', side_effect=lambda: clock[0]),
                      patch.object(fixture, '_kill_and_reap') as reap):
                    with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_FAILED'):
                        fixture._inventory_command(['incus', 'project', 'list', '--format', 'json'])
                    reap.assert_called_once_with(process, 'INCUS_INVENTORY_COMMAND_FAILED')
                    self.assertEqual(spawn.call_count, 1)
                    self.assertLessEqual(clock[0], total)
                    self.assertEqual(len(fixture._COMMAND_AUDIT), 1)
                    with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_TOTAL_TIMEOUT'):
                        fixture._inventory_command(['incus', 'project', 'list', '--format', 'json'])
                    self.assertEqual(spawn.call_count, 1)

    def test_real_full_fresh_graph_success_fits_qualification_and_cleanup_budgets(self):
        transport = _FullGraphFixtureTransport(self)
        fixture._INVENTORY_RESERVE_CLEANUP = True
        with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
              patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
            baseline = fixture.jit(transport.go, '192.168.178.33')
            result = fixture._run_fixture(transport.go, baseline)
            fixture._INVENTORY_CLEANUP_MODE = True
            # Exact main() post-cleanup proof reads, including both listener observations.
            self.assertFalse(fixture._listener_rows(fixture._listeners(), 61000))
            self.assertEqual(fixture._listener_rows(fixture.command(['ss', '-H', '-ltnp']), 10001),
                             baseline['listeners_10001'])
            self.assertEqual(fixture._incus_route_inventory(),
                             (baseline['incus_projects'], baseline['incus_10001_routes']))
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(transport.active_peak, 106)
        self.assertEqual(len(fixture._COMMAND_AUDIT), 180)
        self.assertLessEqual(transport.active_peak, fixture._INVENTORY_MAX_COMMANDS - fixture._INVENTORY_CLEANUP_COMMAND_RESERVE)
        self.assertLessEqual(len(fixture._COMMAND_AUDIT), fixture._INVENTORY_MAX_COMMANDS)
        self.assertLess(fixture._INVENTORY_BYTES_CAPTURED, fixture._INVENTORY_TOTAL_COMMAND_MAX_BYTES)
        self.assertGreaterEqual(transport.foreign_lists, 12)
        self.assertGreater(len(json.dumps(transport.foreign)), 9461)
        self.assertEqual(json.dumps(transport.foreign, sort_keys=True), transport.foreign_before)
        self.assertIsNone(transport.current)
        self.assertEqual(set(transport.profiles), {'default', 'legacy-base', 'legacy-route'})
        self.assertEqual(len(transport.effects), 9)
        self.assertNotIn('xxxxxxxx', json.dumps(fixture._COMMAND_AUDIT))

    def test_cleanup_transport_failures_retain_exact_owned_remainders_without_force_or_retry(self):
        for stage in ('stop', 'delete-instance', 'delete-profile', 'delete-base'):
            with self.subTest(stage=stage):
                self.setUp()
                transport = _FullGraphFixtureTransport(self)
                failures = {
                    'stop': ('stop', transport.instance, '--project', 'default', '--timeout', '30'),
                    'delete-instance': ('delete', transport.instance, '--project', 'default'),
                    'delete-profile': ('profile', 'delete', transport.profile, '--project', 'default'),
                    'delete-base': ('profile', 'delete', transport.base, '--project', 'default'),
                }
                transport.fail_effect = failures[stage]
                fixture._INVENTORY_RESERVE_CLEANUP = True
                with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
                      patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
                    baseline = fixture.jit(transport.go, '192.168.178.33')
                    with self.assertRaisesRegex(fixture.TargetDrift, 'JIT_COMMAND_FAILED'):
                        fixture._run_fixture(transport.go, baseline)
                self.assertEqual(sum(args == failures[stage] for args, _ in transport.effects), 1)
                self.assertEqual(transport.current is not None, stage in {'stop', 'delete-instance'})
                self.assertEqual(transport.profile in transport.profiles, stage != 'delete-base')
                self.assertIn(transport.base, transport.profiles)
                self.assertEqual(json.dumps(transport.foreign, sort_keys=True), transport.foreign_before)
                self.assertFalse(any('--force' in args for args, _ in transport.effects))
                self.assertLessEqual(len(fixture._COMMAND_AUDIT), fixture._INVENTORY_MAX_COMMANDS)

    def test_qualification_budget_denial_prevents_create_without_spending_cleanup_reserve(self):
        transport = _FullGraphFixtureTransport(self)
        fixture._INVENTORY_RESERVE_CLEANUP = True
        with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
              patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
            baseline = fixture.jit(transport.go, '192.168.178.33')
            fixture._COMMAND_AUDIT.extend({} for _ in range(146 - len(fixture._COMMAND_AUDIT)))
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED'):
                fixture._run_fixture(transport.go, baseline)
        self.assertFalse(transport.effects)
        self.assertIsNone(transport.current)
        self.assertEqual(set(transport.profiles), {'default', 'legacy-base', 'legacy-route'})
        self.assertEqual(json.dumps(transport.foreign, sort_keys=True), transport.foreign_before)

    def test_repeated_foreign_full_reads_charge_bytes_and_commands_but_not_repeated_structural_slots(self):
        transport = _FullGraphFixtureTransport(self)
        argv = ['incus', 'list', '--project', 'foreign', '--format', 'json']
        with patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen):
            first = fixture.command(argv)
            initial_slots = fixture._INVENTORY_ENTITIES_CAPTURED
            for _ in range(21):
                self.assertEqual(fixture.command(argv), first)
            self.assertEqual(fixture._INVENTORY_ENTITIES_CAPTURED, initial_slots)
            self.assertEqual(len(fixture._COMMAND_AUDIT), 22)
            self.assertEqual(fixture._INVENTORY_BYTES_CAPTURED, 22 * len(first))
            transport.foreign['config']['user.new-observed-field'] = 'changed current observation'
            latest = json.loads(fixture.command(argv))
            self.assertIn('user.new-observed-field', latest[0]['config'])
            self.assertGreater(fixture._INVENTORY_ENTITIES_CAPTURED, initial_slots)
            self.assertEqual(transport.foreign_lists, 23)
        self.assertNotIn('changed current observation', json.dumps(fixture._COMMAND_AUDIT))

    def test_slots_are_project_object_field_and_array_position_specific_and_failed_debit_is_atomic(self):
        code = 'INCUS_INVENTORY_UNREADABLE'
        first = ['incus', 'list', '--project', 'foreign', '--format', 'json']
        fixture._account_inventory_json(first, [{'name': 'one'}], code)
        count = fixture._INVENTORY_ENTITIES_CAPTURED
        fixture._account_inventory_json(first, [{'name': 'different scalar'}], code)
        self.assertEqual(fixture._INVENTORY_ENTITIES_CAPTURED, count)
        fixture._account_inventory_json(first, [{'name': 'one'}, {'name': 'two'}], code)
        self.assertGreater(fixture._INVENTORY_ENTITIES_CAPTURED, count)
        for scope in (['incus', 'list', '--project', 'other', '--format', 'json'],
                      ['incus', 'query', fixture._instance_api_path('one', 'foreign')],
                      ['incus', 'query', fixture._instance_api_path('two', 'foreign')]):
            before = fixture._INVENTORY_ENTITIES_CAPTURED
            fixture._account_inventory_json(scope, [{'name': 'one'}], code)
            self.assertGreater(fixture._INVENTORY_ENTITIES_CAPTURED, before)
        fixture._INVENTORY_RESERVE_CLEANUP = True
        fixture._INVENTORY_ENTITIES_CAPTURED = 4999
        saved = set(fixture._INVENTORY_ENTITY_SLOTS)
        with self.assertRaisesRegex(fixture.TargetDrift, code):
            fixture._account_inventory_json(first, [{'new': 'value'}], code)
        self.assertEqual(fixture._INVENTORY_ENTITIES_CAPTURED, 4999)
        self.assertEqual(fixture._INVENTORY_ENTITY_SLOTS, saved)
        fixture._INVENTORY_CLEANUP_MODE = True
        fixture._account_inventory_json(first, [{'new': 'value'}], code)
        self.assertGreater(fixture._INVENTORY_ENTITIES_CAPTURED, 4999)

    def test_every_response_rechecks_depth_node_and_transport_limits_even_for_an_existing_scope(self):
        code = 'INCUS_INVENTORY_UNREADABLE'
        scope = ['incus', 'query', fixture._instance_api_path('one', 'foreign')]
        fixture._account_inventory_json(scope, {}, code)
        nested: object = None
        for _ in range(33):
            nested = [nested]
        for malformed in (nested, list(range(10001)), {str(i): i for i in range(5001)}):
            with self.subTest(shape=type(malformed).__name__), self.assertRaisesRegex(fixture.TargetDrift, code):
                fixture._account_inventory_json(scope, malformed, code)
        transport = _FullGraphFixtureTransport(self)
        with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
              patch.object(fixture, '_INVENTORY_COMMAND_MAX_BYTES', 10)):
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_OUTPUT_TOO_LARGE'):
                fixture.command(['incus', 'list', '--project', 'foreign', '--format', 'json'])
        with (patch.object(fixture.subprocess, 'Popen') as spawn,
              patch.object(fixture.time, 'monotonic', return_value=301)):
            fixture._INVENTORY_STARTED_AT = 0
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_TOTAL_TIMEOUT'):
                fixture.command(scope)
        spawn.assert_not_called()

    def test_atomic_profile_body_is_bounded_canonical_ram_input_and_never_audit_payload(self):
        name = 'tsw-q449-' + 'a' * 32 + '-profile'
        data = {'config': {'user.q449.run_id': 'a' * 32}, 'devices': {
            'q449-listener': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:61000',
                              'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}}}
        observed: list[bytes] = []

        def spawn(argv, **kwargs):
            observed.append(os.read(kwargs['stdin'], 65537))
            self.assertEqual(argv, [fixture.TRUSTED_BIN['incus'], 'profile', 'create', name, '--project', 'default'])
            return _BoundedMemoryProcess()

        with patch.object(fixture.subprocess, 'Popen', side_effect=spawn):
            fixture._incus('profile', 'create', name, '--project', 'default', profile_data=data)
        self.assertEqual(observed, [json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()])
        self.assertNotIn('q449-listener', json.dumps(fixture._COMMAND_AUDIT))
        invalid_bodies: tuple[object, ...] = ({}, {'config': {}, 'devices': {}, 'extra': True},
                                             {'config': {'user.large': 'x' * 65537}, 'devices': {}})
        for body in invalid_bodies:
            with (self.subTest(body_type=type(body).__name__), patch.object(fixture.subprocess, 'Popen') as process,
                  self.assertRaisesRegex(fixture.FixtureError, 'PROFILE_CREATE_BODY_INVALID')):
                fixture._create_profile_command(['profile', 'create', name, '--project', 'default'], body)
            process.assert_not_called()
        with (patch.object(fixture.subprocess, 'Popen') as process,
              self.assertRaisesRegex(fixture.FixtureError, 'PROFILE_CREATE_BODY_INVALID')):
            fixture._create_profile_command(['profile', 'create', name, '--project', 'other'], data)
        process.assert_not_called()



    def test_lost_atomic_create_ack_requires_exact_full_body_readback_before_cleanup(self):
        for resource in ('base', 'profile'):
            with self.subTest(resource=resource):
                fixture._COMMAND_AUDIT.clear()
                fixture._INVENTORY_BYTES_CAPTURED = fixture._INVENTORY_ENTITIES_CAPTURED = 0
                fixture._INVENTORY_ENTITY_SLOTS.clear()
                fixture._INVENTORY_STARTED_AT = None
                fixture._INVENTORY_CLEANUP_MODE = False
                fixture._INVENTORY_RESERVE_CLEANUP = True
                transport = _FullGraphFixtureTransport(self)
                transport.lost_create = transport.base if resource == 'base' else transport.profile
                with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
                      patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
                    baseline = fixture.jit(transport.go, '192.168.178.33')
                    with self.assertRaisesRegex(fixture.TargetDrift, 'PROFILE_CREATE_UNCERTAIN'):
                        fixture._run_fixture(transport.go, baseline)
                self.assertEqual(set(transport.profiles), {'default', 'legacy-base', 'legacy-route'})
                self.assertIsNone(transport.current)
                self.assertEqual(json.dumps(transport.foreign, sort_keys=True), transport.foreign_before)

    def test_active_budget_exhaustion_after_owned_create_still_uses_reserved_verified_cleanup(self):
        transport = _FullGraphFixtureTransport(self)
        transport.exhaust_after_base = True
        fixture._INVENTORY_RESERVE_CLEANUP = True
        with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
              patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
            baseline = fixture.jit(transport.go, '192.168.178.33')
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INVENTORY_COMMAND_LIMIT_EXCEEDED'):
                fixture._run_fixture(transport.go, baseline)
        self.assertEqual(set(transport.profiles), {'default', 'legacy-base', 'legacy-route'})
        self.assertIsNone(transport.current)
        self.assertLessEqual(len(fixture._COMMAND_AUDIT), 256)
        self.assertEqual(json.dumps(transport.foreign, sort_keys=True), transport.foreign_before)



class SharedWindowsSnapshotAssetTests(_FixtureBehaviorTestCase):
    def _asset(self, root, raw=b"$ErrorActionPreference = 'Stop'\n'fixed readonly snapshot'\n"):
        certificate = root / fixture.WINDOWS_CERTIFICATE_REL
        certificate.parent.mkdir(parents=True, exist_ok=True)
        certificate.write_bytes((Path(__file__).resolve().parents[4] / fixture.WINDOWS_CERTIFICATE_REL).read_bytes())
        asset = root / fixture.WINDOWS_SNAPSHOT_REL
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(raw)
        return asset, raw

    def test_exact_go_asset_binding_is_required_for_both_hosts_before_effects(self):
        template = GoValidationTests()
        template.setUp()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, raw = self._asset(root)
            with patch.object(fixture, 'ROOT', root):
                for host in ('192.168.178.33', '192.168.178.58'):
                    candidate = json.loads(json.dumps(template.go))
                    candidate['target']['host'] = host
                    candidate['windows_snapshot_sha256'] = fixture.digest(raw)
                    args = argparse.Namespace(target_host=host)
                    self.assertEqual(fixture.validate_go(candidate, args, 'b' * 40,
                        template.workflow, template.runner, template.tests), candidate)
                    for field in ('windows_snapshot_sha256', 'windows_certificate_sha256'):
                        for change in ('missing', 'wrong-hash', 'malformed-hash'):
                            bad = dict(candidate)
                            if change == 'missing':
                                bad.pop(field)
                            else:
                                bad[field] = '0' * 64 if change == 'wrong-hash' else True
                            with self.subTest(host=host, field=field, change=change), self.assertRaises(fixture.FixtureError):
                                fixture.validate_go(bad, args, 'b' * 40, template.workflow, template.runner, template.tests)

    def test_fixed_asset_loader_refuses_missing_symlink_directory_nonutf8_bom_nul_oversize_and_drift(self):
        invalid: tuple[bytes, ...] = (b'', b'\xff', b'\xef\xbb\xbfread', b'read\x00', b'x' * 65537)
        for raw in invalid:
            with self.subTest(length=len(raw)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._asset(root, raw)
                with patch.object(fixture, 'ROOT', root), self.assertRaises(fixture.FixtureError):
                    fixture._windows_snapshot_query(fixture.digest(raw))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset, raw = self._asset(root)
            with patch.object(fixture, 'ROOT', root):
                self.assertEqual(fixture._windows_snapshot_query(fixture.digest(raw)), raw.decode())
                with self.assertRaisesRegex(fixture.FixtureError, 'WINDOWS_SNAPSHOT_ASSET_MISMATCH'):
                    fixture._windows_snapshot_query('0' * 64)
                asset.unlink()
                target = root / 'other.ps1'
                target.write_bytes(raw)
                asset.symlink_to(target)
                with self.assertRaisesRegex(fixture.FixtureError, 'WINDOWS_SNAPSHOT_ASSET_UNSAFE'):
                    fixture._windows_snapshot_query(fixture.digest(raw))
                asset.unlink()
                asset.mkdir()
                with self.assertRaisesRegex(fixture.FixtureError, 'WINDOWS_SNAPSHOT_ASSET_UNSAFE'):
                    fixture._windows_snapshot_query(fixture.digest(raw))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'outside').mkdir()
            (root / 'tools').symlink_to(root / 'outside')
            with patch.object(fixture, 'ROOT', root), self.assertRaisesRegex(fixture.FixtureError, 'WINDOWS_SNAPSHOT_ASSET_UNSAFE'):
                fixture._windows_snapshot_query()

    def test_only_exact_loaded_asset_text_can_use_powershell_snapshot_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, raw = self._asset(root)
            prefix = ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                      '-NoProfile', '-NonInteractive', '-Command']
            with (patch.object(fixture, 'ROOT', root), patch.object(fixture, '_snapshot_process', return_value=b'{}') as run):
                fixture.command([*prefix, fixture._windows_snapshot_wrapper(fixture.digest(raw))])
                run.assert_called_once()
                run.reset_mock()
                for command in ([*prefix, raw.decode() + '; extra'], [*prefix[:-1], '-File', str(root / fixture.WINDOWS_SNAPSHOT_REL)]):
                    with self.assertRaisesRegex(fixture.FixtureError, 'WINDOWS_SNAPSHOT_COMMAND_NOT_ALLOWLISTED'):
                        fixture.command(command)
                run.assert_not_called()



class FirewallCertificateReaderTests(_FixtureBehaviorTestCase):
    def test_reader_binds_query_entire_digest_exact_types_and_all_counts(self):
        good = _certificate_fixture({'rules': [], 'profiles': [], 'settings': []})
        expected = _snapshot_asset_digest()
        self.assertEqual(fixture._windows_firewall_certificate(good, expected), good)
        mutations: tuple[dict[str, object], ...] = (
            {'query_sha256': '0' * 64}, {'snapshot_sha256': 'X' * 64}, {'snapshot_bytes': True},
            {'snapshot_bytes': -1}, {'snapshot_bytes': 14680065}, {'snapshot_schema_version': True},
            {'snapshot_schema_version': 1}, {'schema_version': 'legacy'}, {'store': 'PersistentStore'},
            {'association_model': 'unknown'}, {'extra': True},
            {'counts': {**good['counts'], 'rules': 8193}},
            {'counts': {**good['counts'], 'profiles': 17}},
            {'counts': {**good['counts'], 'settings': 129}},
            {'counts': {**good['counts'], 'address': 1}},
            {'counts': {**good['counts'], 'port': False}},
            {'counts': {key: value for key, value in good['counts'].items() if key != 'port'}},
        )
        for change in mutations:
            with self.subTest(change=change), self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_FIREWALL_SNAPSHOT_UNREADABLE'):
                fixture._windows_firewall_certificate({**good, **change}, expected)
        for field in good:
            incomplete = {key: value for key, value in good.items() if key != field}
            with self.subTest(missing=field), self.assertRaises(fixture.TargetDrift):
                fixture._windows_firewall_certificate(incomplete, expected)

    def test_wrapper_is_exact_source_bound_and_rejects_encoded_commandline_overflow_before_spawn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            certificate = root / fixture.WINDOWS_CERTIFICATE_REL
            certificate.parent.mkdir(parents=True, exist_ok=True)
            certificate.write_bytes((Path(__file__).resolve().parents[4] / fixture.WINDOWS_CERTIFICATE_REL).read_bytes())
            asset = root / fixture.WINDOWS_SNAPSHOT_REL
            asset.parent.mkdir(parents=True, exist_ok=True)
            raw = b"'fixed test query'\n"
            asset.write_bytes(raw)
            with patch.object(fixture, 'ROOT', root):
                wrapper = fixture._windows_snapshot_wrapper(fixture.digest(raw))
                self.assertIn(base64.b64encode(raw).decode(), wrapper)
                self.assertIn(fixture.digest(raw), wrapper)
                self.assertIn('$outputs.Count -ne 1', wrapper)
                self.assertIn('Hash-Bytes $bytes', wrapper)
                self.assertNotIn('Get-NetFirewallRule', wrapper)
                asset.write_bytes(b'x' * 24000)
                with patch.object(fixture.subprocess, 'Popen') as spawn, self.assertRaisesRegex(
                        fixture.FixtureError, 'WINDOWS_SNAPSHOT_COMMAND_TOO_LARGE'):
                    fixture._windows_snapshot_wrapper(fixture.digest(asset.read_bytes()))
                spawn.assert_not_called()


@unittest.skipUnless(Path('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe').is_file(),
                     'Windows PowerShell transport unavailable; no fallback to another host')
class FirewallCertificatePowerShellContractTests(_FixtureBehaviorTestCase):
    """Execute only synthetic query expressions, never real firewall cmdlets."""

    def _run_query(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            certificate = root / fixture.WINDOWS_CERTIFICATE_REL
            certificate.parent.mkdir(parents=True, exist_ok=True)
            certificate.write_bytes((Path(__file__).resolve().parents[4] / fixture.WINDOWS_CERTIFICATE_REL).read_bytes())
            asset = root / fixture.WINDOWS_SNAPSHOT_REL
            asset.parent.mkdir(parents=True, exist_ok=True)
            raw = source.encode('utf-8')
            asset.write_bytes(raw)
            with patch.object(fixture, 'ROOT', root):
                wrapper = fixture._windows_snapshot_wrapper(fixture.digest(raw))
                result = subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                    '-NoProfile', '-NonInteractive', '-Command', wrapper], stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False)
            return result, fixture.digest(raw)

    def _source(self, value):
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        return "[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + base64.b64encode(raw).decode() + "'))", raw

    def test_actual_wrapper_hashes_entire_current_json_and_exports_only_closed_certificate(self):
        value = _firewall_v2_fixture({'rules': [], 'profiles': [{'Name': 'Private', 'opaque': 'SID_CANARY'}], 'settings': []})
        for suffix in ('first', 'second'):
            value['profiles'][0]['value']['opaque'] = 'SID_CANARY_' + suffix
            source, raw = self._source(value)
            result, query_sha = self._run_query(source)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            self.assertFalse(result.stderr)
            certificate = fixture.strict_json(result.stdout)
            self.assertEqual(fixture._windows_firewall_certificate(certificate, query_sha), certificate)
            self.assertEqual(certificate['snapshot_sha256'], fixture.digest(raw))
            self.assertEqual(certificate['snapshot_bytes'], len(raw))
            self.assertEqual(certificate['counts']['profiles'], 1)
            self.assertNotIn(b'SID_CANARY', result.stdout)

    def test_actual_wrapper_rejects_incomplete_ambiguous_wrong_schema_and_unknown_layout_without_raw_errors(self):
        full = _firewall_v2_fixture({'rules': [], 'profiles': [], 'settings': []})
        wrong_layout = json.loads(json.dumps(full))
        wrong_layout['cim_layout']['adapted_override'] = ['missing']
        mutations = [dict(full, schema_version=True), dict(full, store=['ActiveStore']),
                     dict(full, extra=True), wrong_layout,
                     dict(full, profiles=[{'identity': 'x', 'value': {}}, {'identity': 'x', 'value': {}}]),
                     dict(full, filters={**full['filters'], 'port': [{'identity': 'orphan', 'value': {}}]})]
        sources = [self._source(value)[0] for value in mutations]
        sources += ["'SID_CANARY_incomplete{'", "'SID_CANARY_first'; 'SID_CANARY_second'", "throw 'SID_CANARY_exception'"]
        for source in sources:
            with self.subTest(source_digest=fixture.digest(source.encode())):
                result, _ = self._run_query(source)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn(b'SID_CANARY', result.stdout + result.stderr)
                self.assertIn(b'WINDOWS_FIREWALL_CERTIFICATE_FAILED', result.stderr)



class FullListObservationTests(_FixtureBehaviorTestCase):
    def test_wsl_two_project_four_full_foreign_rows_fit_real_counters_and_keep_all_fresh_checks(self):
        fixture._begin_inventory('192.168.178.58', reserve_cleanup=True)
        transport = _FullGraphFixtureTransport(self, wsl=True)
        fixture._INVENTORY_RESERVE_CLEANUP = True
        with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
              patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
            baseline = fixture.jit(transport.go, '192.168.178.58')
            self.assertEqual(sum(len(rows) for rows in transport.foreign_rows.values()), 4)
            result = fixture._run_fixture(transport.go, baseline)
            fixture._INVENTORY_CLEANUP_MODE = True
            self.assertFalse(fixture._listener_rows(fixture._listeners(), 61000))
            self.assertEqual(fixture._listener_rows(fixture.command(['ss', '-H', '-ltnp']), 10001), baseline['listeners_10001'])
            self.assertEqual(fixture._incus_route_inventory(), (baseline['incus_projects'], baseline['incus_10001_routes']))
            fixture._assert_windows_unchanged(baseline['windows_rules_portproxy'],
                                              fixture._windows_snapshot(transport.go['windows_snapshot_sha256']))
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(transport.active_peak, 107)
        self.assertEqual(len(fixture._COMMAND_AUDIT), 181)
        self.assertLessEqual(fixture._INVENTORY_ENTITIES_CAPTURED, 5000)
        self.assertLess(fixture._INVENTORY_BYTES_CAPTURED, 8 * 1024 * 1024)
        self.assertEqual(json.dumps(transport.foreign_rows, sort_keys=True), transport.foreign_rows_before)
        self.assertIsNone(transport.current)
        self.assertEqual(set(transport.profiles), {'default', 'legacy-base', 'legacy-route'})
        self.assertEqual(len(transport.effects), 9)
        windows_observations = [args for args in transport.events if args[:1] == ('powershell.exe',)
                                and 'tsw.windows-firewall-certificate.v1' in args[-1]]
        self.assertEqual(len(windows_observations), 13)
        self.assertEqual(transport.windows_phases.count(False), 7)
        self.assertEqual(transport.windows_phases.count(True), 6)
        self.assertGreaterEqual(transport.foreign_lists, 20)
        self.assertNotIn('xxxxxxxx', json.dumps(fixture._COMMAND_AUDIT))

    def test_missing_expanded_maps_require_observed_empty_local_and_every_actual_profile_map(self):
        row: dict[str, Any] = {'name': 'empty', 'status': 'Stopped', 'type': 'container', 'config': {}, 'devices': {}, 'profiles': ['p']}
        profile: dict[str, Any] = {'name': 'p', 'config': {}, 'devices': {}, 'used_by': []}
        self.assertEqual(fixture._route_instance(row, 'default', {'p': profile}), row)
        cases = [dict(row, config={'user.value': 'present'}),
                 dict(row, devices={'root': {'type': 'disk', 'path': '/', 'pool': 'default'}}),
                 dict(row, expanded_config=None), dict(row, expanded_devices=None),
                 dict(row, profiles=['missing']), dict(row, profiles=['p', 'p']), dict(row, unknown=True)]
        for malformed in cases:
            with self.subTest(fields=sorted(malformed)), self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INSTANCE_INVENTORY_UNREADABLE'):
                fixture._route_instance(malformed, 'default', {'p': profile})
        for field, value in (('config', {'user.value': 'present'}),
                             ('devices', {'web': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001',
                                                 'connect': 'tcp:127.0.0.1:80', 'bind': 'host'}})):
            with self.subTest(inherited_field=field), self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INSTANCE_INVENTORY_UNREADABLE'):
                fixture._route_instance(row, 'default', {'p': {**profile, field: value}})
        complete = {**row, 'expanded_config': {'user.value': 'present'},
                    'expanded_devices': {'root': {'type': 'disk', 'path': '/', 'pool': 'default'}}}
        self.assertEqual(fixture._route_instance(complete, 'default', {'p': profile}), complete)

    def test_current_foreign_list_metadata_is_revalidated_before_next_effect_not_cached_or_repaired(self):
        transport = _FullGraphFixtureTransport(self)
        # Place the malformed observation in the last project: cleanup still attempts every scope.
        transport.foreign_rows['foreign'] = []
        transport.foreign['project'] = 'inherited'
        transport.foreign_rows['inherited'] = [transport.foreign]
        fixture._INVENTORY_RESERVE_CLEANUP = True
        original_create = transport.popen

        def corrupt_after_base(argv, **kwargs):
            process = original_create(argv, **kwargs)
            if argv[1:3] == ['profile', 'create'] and argv[3] == transport.base:
                transport.foreign['expanded_config'] = None
            return process

        with (patch.object(fixture.subprocess, 'Popen', side_effect=corrupt_after_base),
              patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
            baseline = fixture.jit(transport.go, '192.168.178.33')
            with self.assertRaisesRegex(fixture.TargetDrift, 'INCUS_INSTANCE_INVENTORY_UNREADABLE'):
                fixture._run_fixture(transport.go, baseline)
        self.assertFalse(any(args[:2] == ('profile', 'create') and args[2] == transport.profile
                             for args, _ in transport.effects))
        self.assertNotIn(transport.base, transport.profiles)
        self.assertIsNone(transport.current)
        self.assertIsNone(transport.foreign['expanded_config'])
        self.assertFalse(any(args[0] in {'delete', 'stop'} and 'foreign-manager' in args for args, _ in transport.effects))



class FixtureInstanceReceiptTests(_FixtureBehaviorTestCase):
    def inputs(self):
        transport = _FullGraphFixtureTransport(self)
        derived = fixture._derive_fixture_base(transport.profiles['default'])
        properties = {'os': 'Alpine', 'release': '3.21', 'architecture': 'x86_64', 'variant': 'default'}
        baseline = {'derived_base_profile': derived, 'image_properties': properties}
        return transport, baseline, _fixture_instance_dto(transport.go, derived, properties)

    def test_actual_created_uuid_image_and_full_spec_bind_once_before_start_and_only_hashes_export(self):
        transport, baseline, initial = self.inputs()
        receipt = fixture._FixtureInstanceReceipt(transport.go, baseline, initial)
        self.assertRegex(receipt.binding_sha256, r'^[0-9a-f]{64}$')
        running = _fixture_instance_dto(transport.go, baseline['derived_base_profile'], baseline['image_properties'], 'running')
        receipt.observe(running, 'running')
        receipt.observe(running, 'running')
        stopped = _fixture_instance_dto(transport.go, baseline['derived_base_profile'], baseline['image_properties'], 'stopped')
        receipt.observe(stopped, 'stopped')
        for mutation in ({'volatile.uuid': '33333333-3333-4333-8333-333333333333',
                          'volatile.uuid.generation': '33333333-3333-4333-8333-333333333333'},
                         {'volatile.cloud-init.instance-id': '44444444-4444-4444-8444-444444444444'},
                         {'volatile.base_image': '0' * 64}, {'image.os': 'foreign'}, {'image.foreign': 'unexpected'},
                         {'volatile.unknown': 'unexpected'}, {'volatile.eth0.hwaddr': '10:66:6a:00:00:02'},
                         {'volatile.idmap.base': '2000000'}, {'volatile.last_state.power': 'FROZEN'}):
            altered = json.loads(json.dumps(stopped))
            altered['config'].update(mutation)
            altered['expanded_config'].update(mutation)
            with self.subTest(keys=sorted(mutation)), self.assertRaises(fixture.TargetDrift):
                receipt.observe(altered, 'stopped')
        without_marker = json.loads(json.dumps(initial))
        without_marker['config'].pop('user.q449.run_id')
        without_marker['expanded_config'].pop('user.q449.run_id')
        with self.assertRaisesRegex(fixture.TargetDrift, 'INSTANCE_OWNERSHIP_UNVERIFIED'):
            fixture._FixtureInstanceReceipt(transport.go, baseline, without_marker)

    def test_metadata_formats_idmap_regression_and_unmodeled_phase_changes_refuse(self):
        transport, baseline, initial = self.inputs()
        receipt = fixture._FixtureInstanceReceipt(transport.go, baseline, initial)
        running = _fixture_instance_dto(transport.go, baseline['derived_base_profile'], baseline['image_properties'], 'running')
        receipt.observe(running, 'running')
        invalid: tuple[dict[str, object], ...] = (
            {'volatile.idmap.current': '[]'}, {'volatile.last_state.idmap': '[]'},
            {'volatile.idmap.next': '[{"Isuid":true}]'}, {'volatile.idmap.base': '9223372036854775808'},
            {'volatile.uuid': 'not-a-uuid'}, {'volatile.uuid': '00000000-0000-0000-0000-000000000000'},
            {'volatile.eth0.host_name': 'foreign-veth'}, {'volatile.eth0.hwaddr': '00:11:22:33:44:55'},
            {'volatile.cpu.nodes': '0,0'}, {'volatile.apply_template': 'create'}, {'volatile.last_state.ready': 'unknown'})
        for change in invalid:
            altered = json.loads(json.dumps(running))
            altered['config'].update(change)
            altered['expanded_config'].update(change)
            with self.subTest(keys=sorted(change)), self.assertRaises(fixture.TargetDrift):
                receipt.observe(altered, 'running')
        bad_entries: tuple[object, ...] = (None, {}, [{'Isuid': True, 'Isgid': False, 'Hostid': True, 'Nsid': 0, 'Maprange': 1}],
            [{'Isuid': True, 'Isgid': False, 'Hostid': 0, 'Nsid': 0, 'Maprange': 0}],
            [{'Isuid': False, 'Isgid': False, 'Hostid': 0, 'Nsid': 0, 'Maprange': 1}])
        for entry in bad_entries:
            with self.assertRaises(fixture.FixtureError):
                fixture._fixture_idmap(json.dumps(entry))

    def test_real_transport_lost_init_ack_requires_full_uuid_receipt_and_cleans_only_its_bound_instance(self):
        transport = _FullGraphFixtureTransport(self)
        transport.lost_init = True
        fixture._INVENTORY_RESERVE_CLEANUP = True
        with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
              patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
            baseline = fixture.jit(transport.go, '192.168.178.33')
            with self.assertRaisesRegex(fixture.TargetDrift, 'JIT_COMMAND_FAILED'):
                fixture._run_fixture(transport.go, baseline)
        self.assertIsNone(transport.current)
        self.assertEqual(set(transport.profiles), {'default', 'legacy-base', 'legacy-route'})
        self.assertEqual(json.dumps(transport.foreign_rows, sort_keys=True), transport.foreign_rows_before)
        self.assertFalse(any(args[0] == 'start' for args, _ in transport.effects))

    def test_real_cleanup_uuid_drift_blocks_stop_delete_and_keeps_unknown_resources_intact(self):
        transport = _FullGraphFixtureTransport(self)
        transport.corrupt_after_exec = True
        fixture._INVENTORY_RESERVE_CLEANUP = True
        with (patch.object(fixture.subprocess, 'Popen', side_effect=transport.popen),
              patch.object(fixture.subprocess, 'run', side_effect=transport.run)):
            baseline = fixture.jit(transport.go, '192.168.178.33')
            with self.assertRaisesRegex(fixture.TargetDrift, 'INSTANCE_METADATA_DRIFT'):
                fixture._run_fixture(transport.go, baseline)
        self.assertIsNotNone(transport.current)
        self.assertTrue(transport.running)
        self.assertIn(transport.base, transport.profiles)
        self.assertIn(transport.profile, transport.profiles)
        self.assertFalse(any(args[0] in {'stop', 'delete'} or args[:2] == ('profile', 'delete') for args, _ in transport.effects))
        self.assertEqual(json.dumps(transport.foreign_rows, sort_keys=True), transport.foreign_rows_before)


if __name__ == '__main__':
    unittest.main()

"""Fail-closed tests for the issue 449 opt-in listener fixture runner."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import threading
from types import SimpleNamespace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.qualification import incus_profile_listener_fixture as fixture


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

    def test_route_state_digest_uses_exact_base64_bytes_and_sorted_json(self):
        listeners = [b'LISTEN 127.0.0.1:10001']
        routes = [{'owner_type': 'profile', 'owner': 'manager', 'device': 'web',
                   'project': 'default',
                   'config': {'type': 'proxy', 'listen': 'tcp:127.0.0.1:10001'},
                   'used_by': []}]
        windows = b'firewall\r\n--PORTPROXY--\r\n10001\r\n'
        payload = {
            'listeners_10001_b64': [base64.b64encode(listeners[0]).decode('ascii')],
            'incus_projects': [],
            'incus_10001_routes': routes,
            'windows_snapshot_b64': base64.b64encode(windows).decode('ascii'),
        }
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                             ensure_ascii=False).encode('utf-8')).hexdigest()
        self.assertEqual(fixture.approved_route_state_sha256(listeners, routes, windows), expected)

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
                    b'[{"name":"shared"}]',
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
        self.assertEqual(routes[0]['used_by'], ['/1.0/instances/swarm-manager?project=issue447'])
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

    def test_route_inventory_rejects_profile_identity_mismatch(self):
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

    def test_route_inventory_rejects_instance_identity_mismatch(self):
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
                        return b'[{"name":"expected"}]' if resource == 'profile' else b'[]'
                    if argv == ['incus', 'list', '--project', 'default', '--format', 'json']:
                        return b'[{"name":"expected"}]' if resource == 'instance' else b'[]'
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
                with patch.object(fixture, 'command',
                                  return_value=json.dumps(profile).encode()):
                    with self.assertRaisesRegex(fixture.TargetDrift, 'DEFAULT_PROFILE_UNREADABLE'):
                        fixture._read_default_profile({}, [])

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
                        b'[{"name":"qa-profile"}]',
                    ('incus', 'query', fixture._profile_api_path('qa-profile', 'qa')):
                        json.dumps({'name': 'qa-profile', 'project': 'qa', 'config': {}, 'devices': {'web': route_device}, 'used_by': []}).encode(),
                    ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
                    ('incus', 'list', '--project', 'qa', '--format', 'json'):
                        b'[{"name":"qa-instance"}]',
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
                {'project': 'qa', 'owner_type': 'instance', 'owner': 'qa-instance', 'device': 'web',
                 'config': route_device, 'profiles': ['default']},
                {'project': 'qa', 'owner_type': 'profile', 'owner': 'qa-profile', 'device': 'web',
                 'config': route_device, 'used_by': []},
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
            self.assertTrue(all(set(record) == {'argv', 'exit_status', 'stdout_bytes', 'stderr_bytes'}
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
        ]
        with patch.object(fixture.subprocess, 'Popen',
                          side_effect=lambda *a, **k: FakeProcess()) as run:
            fixture._COMMAND_AUDIT.clear()
            for argv in valid:
                self.assertEqual(fixture._inventory_command(argv), b'[]')
            self.assertEqual(run.call_count, len(valid))
        self.assertEqual(fixture._COMMAND_AUDIT[-1]['argv'], valid[-1])
        invalid = [
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
        self.assertTrue(all(set(row) == {'argv', 'exit_status', 'stdout_bytes', 'stderr_bytes'}
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
                b'[{"name":"vm","status":"Running","status_code":103,"type":"virtual-machine","profiles":["web"],"ephemeral":false,"description":"","project":"qa"}]',
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
                       'profile': f'tsw-q449-{run_id}-profile', 'instance': f'tsw-q449-{run_id}-fixture',
                       'image_fingerprint': 'e' * 64},
            'proxy': {'listen': 'tcp:127.0.0.1:61000', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'},
            'cleanup': [f'tsw-q449-{run_id}-fixture', f'tsw-q449-{run_id}-profile'],
            'reviews': {k: 'APPROVED' for k in fixture.REVIEW_KEYS},
            'windows_rules_unchanged': True, 'external_routes_enabled': False,
            'default_profile_sha256': fixture.canonical_profile_sha256({}, {}), 'default_profile_used_by': [],
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

    def test_command_audit_hashes_stdout_without_retaining_raw_bytes(self):
        result = type('Completed', (), {'returncode': 0, 'stdout': b'secret output'})()
        fixture._COMMAND_AUDIT.clear()
        with patch.object(fixture.subprocess, 'run', return_value=result):
            self.assertEqual(fixture.command(['/usr/bin/mock-command']), b'secret output')
        record = fixture._COMMAND_AUDIT[-1]
        self.assertEqual(record['stdout_sha256'], hashlib.sha256(b'secret output').hexdigest())
        self.assertEqual(record['stdout_bytes'], len(b'secret output'))
        self.assertNotIn('stdout_base64', record)
        self.assertNotIn('stdout', record)

    def test_command_audit_never_hashes_incus_output(self):
        result = type('Completed', (), {'returncode': 0, 'stdout': b'{"config":{"password":"secret"}}'})()
        fixture._COMMAND_AUDIT.clear()
        with patch.object(fixture.subprocess, 'run', return_value=result):
            self.assertEqual(fixture.command(['incus', 'query', fixture._profile_api_path('default', 'default')]),
                             b'{"config":{"password":"secret"}}')
        record = fixture._COMMAND_AUDIT[-1]
        self.assertEqual(record['stdout_bytes'], len(result.stdout))
        self.assertNotIn('stdout_sha256', record)
        self.assertNotIn('stdout', record)

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
                'issue447_inventory_sha256', 'default_profile_sha256', 'approved_route_state_sha256')
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
    def test_success_creates_verifies_and_cleans_instance_then_profile(self):
        run_id = 'a' * 32
        go = {
            'source_commit': 'b' * 40,
            'target': {'host': '192.168.178.33', 'endpoint': 'unix://', 'project': 'default',
                       'server_version': '6.0.5', 'image_fingerprint': 'e' * 64, 'run_id': run_id,
                       'profile': f'tsw-q449-{run_id}-profile',
                       'instance': f'tsw-q449-{run_id}-fixture'},
            'proxy': {'listen': 'tcp:127.0.0.1:61000', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'},
            'default_profile_sha256': fixture.canonical_profile_sha256({}, {}), 'default_profile_used_by': [],
        }
        state = {'instance': False, 'profile_marker': False, 'instance_marker': False, 'status': 'stopped', 'foreign_consumer': False}
        calls = []
        instance, profile = go['target']['instance'], go['target']['profile']
        route = f'/1.0/instances/{instance}'
        device = {'type': 'proxy', **go['proxy']}
        listener = (b'LISTEN 0 4096 127.0.0.1:61000 0.0.0.0:* users:(("incusd",pid=123,fd=4))\n'
                    b'LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=44,fd=5))\n')
        approved_route_state = fixture.approved_route_state_sha256(
            [listener.splitlines()[1]], [], b'', ['default'])

        def incus(*args):
            calls.append(args)
            if args[:2] == ('profile', 'set'):
                state['profile_marker'] = True
            if args[:1] == ('init',):
                state['instance'] = True
            if args[:2] == ('config', 'set'):
                state['instance_marker'] = True
            if args[:1] == ('start',):
                state['status'] = 'running'
            if args[:1] == ('stop',):
                state['status'] = 'stopped'
            if args[:1] == ('delete',):
                state['instance'] = False
            if args[:1] == ('list',) or args[:2] == ('profile', 'list'):
                return b'[]'
            if args[:1] == ('query',) and args[1] == fixture._profile_api_path('default', 'default'):
                return json.dumps({'name': 'default', 'project': 'default',
                                   'config': {}, 'devices': {},
                                   'used_by': [route] if state['instance'] else []}).encode()
            if args[:1] == ('query',) and args[1] == fixture._profile_api_path(profile, 'default'):
                return json.dumps({'name': profile, 'project': 'default',
                                   'config': {'user.q449.run_id': run_id} if state['profile_marker'] else {},
                                   'devices': {'q449-listener': device},
                                   'used_by': ['/1.0/instances/foreign'] if state['instance'] and state['foreign_consumer'] else ([route] if state['instance'] else [])}).encode()
            if args[:1] == ('query',) and args[1] == fixture._instance_api_path(instance, 'default'):
                return json.dumps({'name': instance, 'project': 'default',
                                   'config': {'user.q449.run_id': run_id} if state['instance_marker'] else {},
                                   'devices': {}, 'profiles': ['default', profile],
                                   'expanded_config': {'user.q449.run_id': run_id},
                                   'expanded_devices': {'q449-listener': device}}).encode()
            if args[:1] == ('info',):
                return json.dumps({'status': state['status']}).encode()
            return b''

        def command(argv):
            if argv[0] == 'curl':
                return b'fixture response'
            if argv[0] == 'incus':
                if argv[1:2] == ['query'] and argv[2] == fixture._profile_api_path('default', 'default'):
                    return json.dumps({'name': 'default', 'project': 'default',
                                   'config': {}, 'devices': {},
                                       'used_by': [route] if state['instance'] else []}).encode()
                return b'[]'
            if argv[0] == 'ss':
                return listener if state['status'] == 'running' else listener.splitlines()[1] + b'\n'
            raise AssertionError(f'unexpected command {argv!r}')

        with (
            patch.object(fixture, '_incus', side_effect=incus),
            patch.object(fixture, 'command', side_effect=command),
            patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
        ):
            result = fixture._run_fixture(go, {'listeners_10001': [listener.splitlines()[1]],
                                               'incus_projects': ['default'],
                                               'incus_10001_routes': [], 'windows_rules_portproxy': b'',
                                               'approved_route_state_sha256': approved_route_state,
                                               'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3, 'filesystem_available_bytes': 2}})
        self.assertEqual(result['status'], 'PASS')
        self.assertLess(calls.index(('delete', instance, '--project', 'default')),
                        calls.index(('profile', 'delete', profile, '--project', 'default')))
        self.assertFalse(state['instance'])
        state.update({'instance': False, 'profile_marker': False, 'instance_marker': False,
                      'status': 'stopped', 'foreign_consumer': True})
        calls.clear()
        with (
            patch.object(fixture, '_incus', side_effect=incus),
            patch.object(fixture, 'command', side_effect=command),
            patch.object(fixture, '_incus_route_inventory', return_value=(['default'], [])),
        ):
            with self.assertRaises(fixture.TargetDrift):
                fixture._run_fixture(go, {'listeners_10001': [listener.splitlines()[1]],
                                          'incus_projects': ['default'],
                                          'incus_10001_routes': [], 'windows_rules_portproxy': b'',
                                          'approved_route_state_sha256': approved_route_state,
                                          'resources': {'memory_total_bytes': 4, 'memory_available_bytes': 3,
                                                        'filesystem_available_bytes': 2}})
        self.assertNotIn(('profile', 'delete', profile, '--project', 'default'), calls)
        self.assertTrue(state['instance'])


class JitNoMutationTests(_FixtureBehaviorTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch.object(fixture, '_assert_local_incus_remote_inventory')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_default_profile_digest_mismatch_is_a_jit_drift(self):
        run_id = 'a' * 32
        fingerprint = 'e' * 64
        profile = {'name': 'default', 'project': 'default', 'config': {}, 'devices': {}, 'used_by': []}
        go = {'target': {'host': '192.168.178.33', 'server_version': '6.0.5',
                         'instance': f'tsw-q449-{run_id}-fixture',
                         'profile': f'tsw-q449-{run_id}-profile',
                         'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': '0' * 64, 'default_profile_used_by': []}
        outputs = [b'[{"addr_info":[{"local":"192.168.178.33"}]}]',
                   b'{"server":{"version":"6.0.5"}}',
                   json.dumps([{'fingerprint': fingerprint}]).encode(),
                   b'{"properties":{"os":"Alpine Linux","release":"3.20"}}',
                   json.dumps(profile).encode()]
        seen = []
        def command(argv):
            seen.append(argv)
            return outputs[len(seen) - 1]
        with patch.object(fixture, 'command', side_effect=command):
            with self.assertRaisesRegex(fixture.TargetDrift, 'DEFAULT_PROFILE_DRIFT'):
                fixture.jit(go, '192.168.178.33')
        self.assertEqual(len(seen), 5)
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
            if argv[1:3] == ['version', '--format']:
                return b'{"server":{"version":"6.0.5"}}'
            if argv[1:3] == ['project', 'list']:
                return b'[{"name":"default"}]'
            if argv[1:3] == ['image', 'list']:
                return json.dumps([{'fingerprint': fingerprint}]).encode()
            if argv[1:3] == ['image', 'info']:
                return b'{"properties":{"os":"Alpine Linux","release":"3.20"}}'
            if argv[:2] == ['incus', 'query'] and argv[2] == fixture._profile_api_path('default', 'default'):
                return json.dumps(profile).encode()
            raise AssertionError(f'unexpected command {argv!r}')
        go = {'target': {'host': '192.168.178.33', 'server_version': '6.0.5',
                         'instance': f'tsw-q449-{run_id}-fixture',
                         'profile': f'tsw-q449-{run_id}-profile', 'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256(profile['config'], profile['devices']),
              'default_profile_used_by': []}
        with (patch.object(fixture, '_incus_10001_routes', return_value=[]),
              patch.object(fixture, 'command', side_effect=command) as command_mock):
            with self.assertRaisesRegex(fixture.TargetDrift, 'DEFAULT_PROFILE_UNAPPROVED_PROXY'):
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
        go = {'target': {'instance': 'fixture', 'profile': 'q449-profile', 'run_id': run_id},
              'proxy': {'listen': 'tcp:127.0.0.1:61000',
                        'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'}}
        default_profile = {'devices': {'eth0': {'type': 'nic', 'nictype': 'bridged'}}}
        fixture_device = {'type': 'proxy', **go['proxy']}
        fixture_profile = {'devices': {'q449-listener': fixture_device}}
        local = {'name': 'fixture', 'project': 'default',
                 'config': {'user.q449.run_id': run_id}, 'devices': {},
                 'profiles': ['default', 'q449-profile'],
                 'expanded_config': {'user.q449.run_id': run_id},
                 'expanded_devices': {'eth0': default_profile['devices']['eth0'],
                                      'q449-listener': fixture_device}}
        expanded_devices = local['expanded_devices']
        with patch.object(fixture, '_incus', return_value=json.dumps(local).encode()):
            self.assertEqual(fixture._verify_effective_instance(go, default_profile, fixture_profile)['devices'],
                             expanded_devices)
        candidates = (
            {'profiles': ['default', 'q449-profile'], 'devices': {
                **expanded_devices, 'extra': {'type': 'proxy', 'listen': 'tcp:0.0.0.0:80'}}},
            {'profiles': ['default', 'foreign', 'q449-profile'], 'devices': expanded_devices},
            {'profiles': ['default', 'q449-profile'], 'devices': {**expanded_devices, 'bad': 'proxy'}},
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
            ('incus', 'version', '--format', 'json'): b'{"server":{"version":"6.0.5"}}',
            ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"default"}]',
            ('incus', 'query', '/1.0/projects/default'): b'{"name":"default","description":"","config":{}}',
            ('incus', 'image', 'list', '--project', 'default', '--format', 'json'): json.dumps([{'fingerprint': fingerprint}]).encode(),
            ('incus', 'image', 'info', fingerprint, '--project', 'default', '--format', 'json'): b'{"properties":{"os":"Alpine Linux","release":"3.20"}}',
            ('incus', 'query', fixture._profile_api_path('default', 'default')): json.dumps(profile).encode(),
            ('free', '-b'): b'header\nMem: 40000000000 1000000 2000000 0 3000000 35000000000',
            ('df', '-B1', '--output=avail', str(fixture.ROOT)): b'Avail\n100000000000',
            ('ss', '-H', '-ltn'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:*',
            ('ss', '-H', '-ltnp'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))',
            ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
            ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'): b'[{"name":"legacy"}]',
            ('incus', 'query', fixture._profile_api_path('legacy', 'default')): json.dumps(route).encode(),
        }
        go = {'target': {'host': '192.168.178.33', 'server_version': '6.0.5',
                         'instance': f'tsw-q449-{run_id}-fixture',
                         'profile': f'tsw-q449-{run_id}-profile',
                         'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
              'default_profile_used_by': []}
        go['approved_route_state_sha256'] = fixture.approved_route_state_sha256(
            [b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))'],
            [{'project': 'default', 'owner_type': 'profile', 'owner': 'legacy', 'device': 'web',
              'config': route['devices']['web'], 'used_by': []}], b'', ['default'])
        command_order = [
            ('ip', '-j', '-4', 'addr'), ('incus', 'version', '--format', 'json'),
            ('incus', 'image', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'image', 'info', fingerprint, '--project', 'default', '--format', 'json'),
            ('incus', 'query', fixture._profile_api_path('default', 'default')),
            ('free', '-b'), ('df', '-B1', '--output=avail', str(fixture.ROOT)),
            ('ss', '-H', '-ltn'), ('ss', '-H', '-ltnp'),
            ('incus', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'project', 'list', '--format', 'json'),
            ('incus', 'query', '/1.0/projects/default'),
            ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'),
            ('incus', 'query', fixture._profile_api_path('legacy', 'default')),
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

            with self.subTest(failure_index=failure_index), patch.object(fixture, 'command', side_effect=command):
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
                         'image_fingerprint': case.go['target']['image_fingerprint']},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
              'default_profile_used_by': []}
        outputs = [b'[{"addr_info":[{"local":"192.168.178.33"}]}]',
                   b'{"server":{"version":"6.0.5"}}',
                   json.dumps([{'fingerprint': case.go['target']['image_fingerprint']}]).encode(),
                   b'{"properties":{"os":"Alpine Linux","release":"3.20"}}',
                   b'{"name":"default","project":"default","config":{},"devices":{},"used_by":["/1.0/instances/other"]}']
        with patch.object(fixture, 'command', side_effect=outputs):
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
                if 'Get-NetFirewallRule' in script:
                    return b'{"profiles":[],"settings":[],"rules":[]}'
            if argv[0].endswith('/netsh.exe'):
                return b'listen 0.0.0.0:10001 connect 127.0.0.1:10001\r\n'
            mapping = {
                ('incus', 'remote', 'list', '--format', 'json'): b'{"local":{"Addr":"unix://"}}',
                ('incus', 'remote', 'get-default'): b'local',
                ('incus', 'version', '--format', 'json'): b'{"server":{"version":"6.0.5"}}',
                ('incus', 'project', 'list', '--format', 'json'): b'[{"name":"default"}]',
                ('incus', 'query', '/1.0/projects/default'): b'{"name":"default","description":"","config":{}}',
                ('incus', 'image', 'list', '--project', 'default', '--format', 'json'): json.dumps([{'fingerprint': fingerprint}]).encode(),
                ('incus', 'image', 'info', fingerprint, '--project', 'default', '--format', 'json'): b'{"properties":{"os":"Alpine Linux","release":"3.20"}}',
                ('incus', 'query', fixture._profile_api_path('default', 'default')): json.dumps(profile).encode(),
                ('free', '-b'): b'header\nMem: 40000000000 1000000 2000000 0 3000000 35000000000',
                ('df', '-B1', '--output=avail', str(fixture.ROOT)): b'Avail\n100000000000',
                ('ss', '-H', '-ltn'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:*',
                ('ss', '-H', '-ltnp'): b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))',
                ('incus', 'list', '--project', 'default', '--format', 'json'): b'[]',
                ('incus', 'profile', 'list', '--project', 'default', '--format', 'json'): b'[{"name":"legacy"}]',
                ('incus', 'query', fixture._profile_api_path('legacy', 'default')): json.dumps(route).encode(),
            }
            return mapping[tuple(argv)]

        go = {'target': {'host': '192.168.178.58', 'server_version': '6.0.5',
                         'instance': 'tsw-q449-' + 'a' * 32 + '-fixture',
                         'profile': 'tsw-q449-' + 'a' * 32 + '-profile',
                         'image_fingerprint': fingerprint},
              'proxy': {'listen': 'tcp:127.0.0.1:61000'},
              'default_profile_sha256': fixture.canonical_profile_sha256({}, {}),
              'default_profile_used_by': []}
        firewall_bytes = b'{"profiles":[],"rules":[],"settings":[]}'
        portproxy_bytes = b'listen 0.0.0.0:10001 connect 127.0.0.1:10001\r\n'
        windows_snapshot = json.dumps({
            'firewall_active_store_b64': base64.b64encode(firewall_bytes).decode('ascii'),
            'portproxy_raw_b64': base64.b64encode(portproxy_bytes).decode('ascii')},
            sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        go['approved_route_state_sha256'] = fixture.approved_route_state_sha256(
            [b'LISTEN 0 1 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=77,fd=3))'],
            [{'project': 'default', 'owner_type': 'profile', 'owner': 'legacy', 'device': 'web',
              'config': route['devices']['web'], 'used_by': []}], windows_snapshot, ['default'])
        with patch.object(fixture, 'command', side_effect=command):
            baseline = fixture.jit(go, '192.168.178.58')
        self.assertIn(base64.b64encode(portproxy_bytes), baseline['windows_rules_portproxy'])
        self.assertTrue(any(argv[0].endswith('powershell.exe') and 'Get-NetIPAddress' in argv[-1] for argv in seen))
        firewall_command = next(argv[-1] for argv in seen if argv[0].endswith('powershell.exe')
                                and 'Get-NetFirewallRule' in argv[-1])
        for cmdlet in ('Get-NetFirewallProfile -PolicyStore ActiveStore',
                       'Get-NetFirewallSetting -PolicyStore ActiveStore',
                       'Get-NetFirewallAddressFilter', 'Get-NetFirewallApplicationFilter',
                       'Get-NetFirewallInterfaceFilter', 'Get-NetFirewallInterfaceTypeFilter',
                       'Get-NetFirewallPortFilter', 'Get-NetFirewallSecurityFilter',
                       'Get-NetFirewallServiceFilter', 'Select-Object *'):
            self.assertIn(cmdlet, firewall_command)
        self.assertTrue(any(argv[0].endswith('/netsh.exe') and argv[1:] == [
            'interface', 'portproxy', 'show', 'all'] for argv in seen))
        self.assertEqual(baseline['incus_10001_routes'][0]['owner'], 'legacy')
        go['approved_route_state_sha256'] = '0' * 64
        seen.clear()
        with patch.object(fixture, 'command', side_effect=command):
            with self.assertRaisesRegex(fixture.TargetDrift, 'APPROVED_ROUTE_STATE_DRIFT'):
                fixture.jit(go, '192.168.178.58')
        self.assertFalse(any(argv[0] == 'incus' and argv[1] in {
            'create', 'init', 'start', 'stop', 'delete', 'launch', 'copy', 'move',
        } for argv in seen))

    def test_windows_snapshot_comparison_accepts_equal_and_rejects_changed(self):
        fixture._assert_windows_unchanged(b'approved state', b'approved state')
        with self.assertRaisesRegex(fixture.TargetDrift, 'WINDOWS_RULES_CHANGED'):
            fixture._assert_windows_unchanged(b'approved state', b'changed state')

    def test_wsl_route_capture_binds_identity_and_canonical_active_store_plus_exact_portproxy(self):
        firewall_value = {
            'profiles': [{'Name': 'Public', 'Enabled': True}, {'Name': 'Domain', 'Enabled': False}],
            'settings': [{'PolicyStoreSource': 'ActiveStore'}],
            'rules': [{'rule': {'Name': 'z-rule', 'Enabled': True},
                       'profiles': [{'Name': 'Public'}], 'address': [{'RemoteAddress': 'Any'}],
                       'application': [], 'interface': [], 'interface_type': [], 'port': [],
                       'security': [], 'service': []},
                      {'rule': {'Name': 'a-rule', 'Enabled': False},
                       'profiles': [], 'address': [], 'application': [], 'interface': [],
                       'interface_type': [], 'port': [], 'security': [], 'service': []}],
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
                if 'Get-NetFirewallRule' in argv[-1]:
                    return json.dumps(firewall_value).encode('utf-8')
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

        expected_firewall = json.dumps({
            'profiles': sorted(firewall_value['profiles'], key=lambda item: item['Name']),
            'settings': firewall_value['settings'],
            'rules': sorted(firewall_value['rules'], key=lambda item: item['rule']['Name'])},
            sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        expected_snapshot = json.dumps({
            'firewall_active_store_b64': base64.b64encode(expected_firewall).decode('ascii'),
            'portproxy_raw_b64': base64.b64encode(raw_portproxy).decode('ascii')},
            sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
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
        malformed_outputs = (
            b'{"profiles":[null],"settings":[],"rules":[]}',
            b'{"profiles":[],"settings":[],"rules":[{"rule":null}]}',
            b'{"profiles":[],"settings":[],"rules":[{"rule":{"Name":"r"},"profiles":[null],"address":[],"application":[],"interface":[],"interface_type":[],"port":[],"security":[],"service":[]}]}',
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



if __name__ == '__main__':
    unittest.main()

"""Exact-input and preserving-effect contracts; runtime transports are synthetic."""
from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import struct
import tempfile
from typing import Any
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from tools.linux.qualification import ubuntu_image_prestage as stage


def image(fp: str, project: str) -> dict[str, Any]:
    return {'auto_update': False, 'properties': dict(stage.PROPERTIES) if fp == stage.FINGERPRINT else {'user.note': 'CANARY_PRESERVED'},
            'public': False, 'expires_at': '', 'profiles': ['default'], 'aliases': [], 'architecture': 'x86_64',
            'cached': False, 'filename': 'incus.tar.xz', 'fingerprint': fp, 'size': 141542056,
            'update_source': None, 'type': 'container', 'created_at': '2026-11-07T07:42:19Z',
            'last_used_at': '', 'uploaded_at': '', 'project': project}


class FakeAuthority:
    def __init__(self, directory: Path, journal: stage.Journal):
        self.images = directory
        self.source = 'a' * 40
        self.source_pins = {'controller': 'b' * 64}
        self.initial = {'main_pid': 17}
        self.socket_unit = {'listen': 'incus_var_lib'}
        self.journal = journal
        self.effects: list[str] = []
        self.lose: str | None = None
        self.guards = 0
        self.rows = {'default': {'f' * 64: image('f' * 64, 'default')},
                     'isolated': {'e' * 64: image('e' * 64, 'isolated')}}
        self.aliases: dict[str, dict[str, dict[str, str]]] = {'default': {}, 'isolated': {
            stage.ALIAS: {'name': stage.ALIAS, 'target': 'e' * 64, 'description': 'foreign CANARY', 'type': 'container'}}}
        self.root: dict[str, Any] = {key: '' for key in stage.inventory.ROOT_STRINGS}
        environment: dict[str, Any] = {key: '' for key in stage.inventory.ROOT_ENV_STRINGS}
        environment.update(server='incus', project='default', server_version='6.0.5', server_clustered=False,
                           server_pid=17, addresses=[], architectures=[], kernel_features={}, lxc_features={}, storage_supported_drivers=[])
        self.root.update(api_version='1.0', api_status='stable', auth='trusted', public=False,
                         api_extensions=[], auth_methods=[], config={'private': 'SERVER_CANARY'}, environment=environment)

    def guard(self) -> None:
        self.guards += 1

    def query(self, uri: str) -> Any:
        if uri == '/1.0':
            return copy.deepcopy(self.root)
        if uri == '/1.0/projects?recursion=1':
            return [{'name': project, 'description': 'PROJECT_CANARY', 'config': {'features.images': flag},
                     'used_by': ['/1.0/images/' + fp + ('?project=isolated' if project == 'isolated' else '')
                                 for fp in self.rows.get(project, {})]}
                    for project, flag in (('default', 'true'), ('inherited', 'false'), ('isolated', 'true'))]
        parsed = urlsplit(uri)
        project = parse_qs(parsed.query)['project'][0]
        owner = 'default' if project == 'inherited' else project
        aliases = self.aliases[owner]
        if parsed.path == '/1.0/images/aliases':
            return list(copy.deepcopy(aliases).values())
        result = list(copy.deepcopy(self.rows[owner]).values())
        for row in result:
            row['aliases'] = [{'name': alias['name'], 'description': alias['description']}
                              for alias in aliases.values() if alias['target'] == row['fingerprint']]
        return result

    def effect(self, kind: str) -> None:
        raw = self.journal.read('intent.json')
        assert raw is not None
        intent = stage.inventory.strict_json(raw)
        assert intent['stage'] == kind + '_pending'
        self.effects.append(kind)
        if kind == 'import':
            self.rows['default'][stage.FINGERPRINT] = image(stage.FINGERPRINT, 'default')
        elif kind == 'alias':
            self.aliases['default'][stage.ALIAS] = {'name': stage.ALIAS, 'target': stage.FINGERPRINT,
                                                  'description': '', 'type': 'container'}
        else:
            raise AssertionError(kind)
        if kind == self.lose:
            raise stage.PrestageError('EFFECT_UNCERTAIN')


class StreamingBundleTests(unittest.TestCase):
    def test_exact_public_input_contract_is_not_a_gpg_claim(self):
        self.assertEqual(stage.FILES[1][1], 141541376)
        self.assertEqual(stage.FILES[0][2], '58eb156ee168ce406ec7c0ed6501b79c44d9e6962db373e937b71656cbdad687')
        self.assertEqual(stage.FILES[1][2], '7857e5e4edaa70e0c3f7cb7da51e1984ebca79d6314443eba44c34c38b9983a3')
        self.assertEqual(stage.FINGERPRINT, '21c802d47e64cedcf7153503a1b5dbcc8821919b2af993646756868b775a5383')
        self.assertEqual(stage.ALIAS, 'ubuntu-24.04')

    def test_real_141541376_byte_file_is_streamed_without_old_32mib_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rootfs.squashfs'
            size = 141541376
            with path.open('wb') as stream:
                stream.truncate(size)
            path.chmod(0o600)
            expected = hashlib.sha256()
            block = b'\0' * 65536
            for _ in range(size // len(block)):
                expected.update(block)
            expected.update(block[:size % len(block)])
            combined = hashlib.sha256()
            original = os.read
            calls: list[int] = []
            def read(fd: int, count: int) -> bytes:
                calls.append(count)
                return original(fd, count)
            with patch.object(stage.os, 'read', side_effect=read):
                stage.stream_file(path, size, expected.hexdigest(), combined)
            self.assertEqual(combined.hexdigest(), expected.hexdigest())
            self.assertGreater(len(calls), 2048)
            self.assertLessEqual(max(calls), 65536)
            for expected_size, checksum in ((size - 1, expected.hexdigest()), (size, '0' * 64)):
                with self.assertRaises(stage.PrestageError):
                    stage.stream_file(path, expected_size, checksum, hashlib.sha256())
            alias = Path(directory) / 'link'
            alias.symlink_to(path)
            with self.assertRaises(OSError):
                stage.stream_file(alias, size, expected.hexdigest(), hashlib.sha256())


class PreservingWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.directory.chmod(0o700)
        self.journal = stage.Journal(self.directory)
        self.authority = FakeAuthority(self.directory, self.journal)
        self.operation = stage.Prestager(self.authority, self.journal)
        bundle = patch.object(stage, 'verify_bundle')
        bundle.start()
        self.addCleanup(bundle.stop)
        host = patch.object(stage, '_machine_digest', return_value='c' * 64)
        host.start()
        self.addCleanup(host.stop)

    def prepare(self) -> str:
        return self.operation.prepare()['plan_sha256']

    def test_full_real_parser_flow_preserves_foreign_images_aliases_and_inherited_views(self):
        before = copy.deepcopy(self.authority.rows['isolated'])
        aliases = copy.deepcopy(self.authority.aliases['isolated'])
        result = self.operation.execute(self.prepare())
        self.assertEqual(self.authority.effects, ['import', 'alias'])
        self.assertEqual(self.authority.rows['isolated'], before)
        self.assertEqual(self.authority.aliases['isolated'], aliases)
        self.assertEqual(result['status'], 'PRESTAGED_VERIFIED')
        self.assertTrue(result['baseline_recapture_required'])
        self.assertFalse(result['signature_verified'])
        self.assertFalse(result['services_verified'])
        for path in self.directory.iterdir():
            self.assertNotIn(b'CANARY', path.read_bytes())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_identical_image_alias_is_reused_without_runtime_writes(self):
        self.authority.rows['default'][stage.FINGERPRINT] = image(stage.FINGERPRINT, 'default')
        self.authority.aliases['default'][stage.ALIAS] = {'name': stage.ALIAS, 'target': stage.FINGERPRINT,
                                                       'description': 'existing private description', 'type': 'container'}
        result = self.operation.execute(self.prepare())
        self.assertEqual(result['status'], 'ALREADY_PRESENT_VERIFIED')
        self.assertFalse(self.authority.effects)

    def test_alias_collision_and_changed_prestate_refuse_before_effects(self):
        self.authority.aliases['default'][stage.ALIAS] = {'name': stage.ALIAS, 'target': 'f' * 64,
                                                       'description': '', 'type': 'container'}
        with self.assertRaisesRegex(stage.PrestageError, 'ALIAS_COLLISION'):
            self.prepare()
        self.assertIsNone(self.journal.read('proposal.json'))
        self.authority.aliases['default'].clear()
        expected = self.prepare()
        self.authority.rows['default']['f' * 64]['properties']['new'] = 'changed'
        with self.assertRaisesRegex(stage.PrestageError, 'PRESTATE_DRIFT'):
            self.operation.execute(expected)
        self.assertFalse(self.authority.effects)

    def test_import_lost_response_never_replays_or_writes_alias_during_reconcile(self):
        expected = self.prepare()
        self.authority.lose = 'import'
        with self.assertRaisesRegex(stage.PrestageError, 'EFFECT_UNCERTAIN'):
            self.operation.execute(expected)
        with self.assertRaisesRegex(stage.PrestageError, 'REPLAY_REFUSED'):
            self.operation.execute(expected)
        result = self.operation.reconcile(expected)
        self.assertEqual(result['status'], 'IMAGE_ONLY_VERIFIED_ALIAS_NOT_WRITTEN')
        self.assertEqual(self.authority.effects, ['import'])
        self.assertNotIn(stage.ALIAS, self.authority.aliases['default'])

    def test_alias_lost_response_reconciles_exact_readback_without_another_write(self):
        expected = self.prepare()
        self.authority.lose = 'alias'
        with self.assertRaisesRegex(stage.PrestageError, 'EFFECT_UNCERTAIN'):
            self.operation.execute(expected)
        result = self.operation.reconcile(expected)
        self.assertEqual(result['status'], 'RECONCILED_VERIFIED')
        self.assertEqual(self.authority.effects, ['import', 'alias'])
        self.assertEqual(self.operation.reconcile(expected), result)

    def test_unknown_image_or_alias_fields_and_inherited_drift_refuse(self):
        self.authority.rows['default']['f' * 64]['unknown'] = 'forged'
        with self.assertRaises(stage.inventory.InventoryError):
            stage.snapshot(self.authority)
        self.authority.rows['default']['f' * 64].pop('unknown')
        self.authority.aliases['isolated'][stage.ALIAS]['extra'] = 'forged'
        with self.assertRaises(stage.PrestageError):
            stage.snapshot(self.authority)

    def test_private_journal_cas_and_pending_collision_never_overwrite(self):
        first = self.journal.save('owned.json', {'one': 1})
        with self.assertRaisesRegex(stage.PrestageError, 'JOURNAL_CAS_CONFLICT'):
            self.journal.save('owned.json', {'two': 2})
        self.assertEqual(self.journal.read('owned.json'), first)
        self.journal.save('owned.json', {'two': 2}, first)
        (self.directory / 'unsafe.json').symlink_to(self.directory / 'owned.json')
        with self.assertRaises(OSError):
            self.journal.read('unsafe.json')


class AuthorityBoundaryTests(unittest.TestCase):
    def test_unprivileged_entry_refuses_before_constructing_runtime(self):
        with (patch.object(stage.os, 'geteuid', return_value=1000), patch.object(stage, 'Authority') as authority,
              patch('builtins.print')):
            status = stage.main(['prepare', '--image-directory', '/root/images', '--state-directory', '/root/state',
                                 '--source-commit', 'a' * 40, '--before-new-baseline'])
        self.assertEqual(status, 2)
        authority.assert_not_called()

    def test_actual_peer_guard_refuses_nonroot_even_when_unit_and_socket_match(self):
        authority = stage.Authority.__new__(stage.Authority)
        authority.source_pins = {}
        authority.initial = {'main_pid': 17, 'active_state': 'active', 'sub_state': 'running'}
        authority.socket_unit = {'listen': 'incus_var_lib'}
        authority.socket_path = '/var/lib/incus/unix.socket'
        authority.runner = Mock()
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.getsockopt.return_value = struct.pack('3i', 17, 1000, 1000)
        with patch.object(authority, 'check_source', return_value={}), \
                patch.object(stage.inventory, '_systemctl_show', side_effect=[authority.initial, authority.socket_unit]), \
                patch.object(stage.inventory, '_resolve_executable', return_value=('incus_system', 'system:incus')), \
                patch.object(stage.inventory, '_endpoint', return_value=('incus_var_lib', True)), \
                patch.object(stage.inventory, '_require_full_local_access'), patch.object(stage.socket, 'socket', return_value=client):
            with self.assertRaisesRegex(stage.PrestageError, 'INCUS_ROOT_PEER_CHANGED'):
                authority.guard()


if __name__ == '__main__':
    unittest.main()

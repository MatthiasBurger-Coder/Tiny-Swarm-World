"""Closed WSL case execution; real disposal, mocked host/product transports."""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import Mock, PropertyMock, patch

from tools.linux.qualification import wsl_product_acceptance as suite
from tests.tools.test_owned_case_disposal import Port, case
from tests.tools.test_preserving_product_acceptance import altered_capability


def intent() -> suite.Intent:
    return suite.Intent('a' * 32, 'minimal', 'b' * 40, 'c' * 64, 'd' * 64,
        '{11111111-1111-1111-1111-111111111111}', 'e' * 64, 'PC', 'F' * 64,
        '1' * 64, '2' * 64, '3' * 64, '4' * 64, '5' * 64)


def go(proposal: dict[str, Any], *, recover: bool = False) -> dict[str, Any]:
    return {'schema_version': 1, 'decision': 'GO', 'phase': 'wsl-case-recover' if recover else 'wsl-case-run',
        'intent_sha256': suite.sha(suite.canonical(asdict(intent()))), 'proposal_sha256': '6' * 64,
        'source_commit': intent().source_commit, 'pins': proposal['pins'], 'budgets': dict(suite.BUDGETS),
        'expires_at_utc': (datetime.now(timezone.utc) + timedelta(seconds=930 if recover else 6930)).isoformat(),
        'reviews': {key: 'APPROVED' for key in suite.REVIEWS}}


class CasePort:
    def __init__(self, *, failed: bool = False, unsettled: bool = False):
        self.calls: list[str] = []
        self.intent, graph = case()
        self.disposal = Port(graph)
        self.failed, self.unsettled = failed, unsettled
        self.records: list[tuple[str, dict[str, Any]]] = []

    def phase(self, name: str) -> None:
        self.calls.append('phase:' + name)

    def admit(self, proposal: dict[str, Any]) -> None:
        self.calls.append('admit')

    def run(self) -> None:
        self.calls.append('public')
        if self.failed:
            raise suite.CaseError('CASE_REAL_CLI_FAILED')

    def settled(self) -> bool:
        self.calls.append('settled')
        return not self.unsettled

    def dispose(self) -> None:
        self.calls.append('dispose')
        suite.disposal.dispose(self.disposal, self.intent)

    def final(self, baseline: dict[str, Any]) -> None:
        self.calls.append('final')
        assert not self.disposal.graph['instances'] and self.disposal.graph['profile'] is None

    def event(self, stage: str, value: dict[str, Any]) -> None:
        self.calls.append('event:' + stage)
        self.records.append((stage, value))


class WslProductAcceptanceTests(unittest.TestCase):
    def test_closed_root_prepare_keeps_real_admission_and_preview_not_bootstrap_facade(self) -> None:
        for fault in ('valid', 'capability', 'alias', 'preview'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                port = suite.WslCasePort(intent(), Mock())
                port.artifact = {'incus_projects': [{'instances': [], 'profiles': [], 'pools': [],
                    'images': [{'fingerprint': intent().ubuntu_fingerprint, 'type': 'container'}]}]}
                port.details = {('incus_image_show', (intent().ubuntu_fingerprint, 'default')):
                    {'architecture': 'x86_64', 'properties': {'os': 'Ubuntu', 'release': '24.04'}}}
                alias = {'type': 'sync', 'status': 'Success', 'status_code': 200, 'operation': '',
                    'error_code': 0, 'error': '', 'metadata': {'name': 'ubuntu-24.04', 'type': 'container',
                        'description': 'fixed', 'target': 'wrong' if fault == 'alias' else intent().ubuntu_fingerprint}}
                prerequisites = Mock(side_effect=suite.CaseError('ACTUAL_ADMISSION_REFUSED') if fault == 'capability' else None)
                public = Mock(return_value=b'actual-preview-transport')
                preview = Mock(return_value={'validated': 'preview'},
                    side_effect=suite.CaseError('ACTUAL_PREVIEW_REFUSED') if fault == 'preview' else None)
                with (
                    patch.object(suite, 'ROOT', root),
                    patch.object(suite.Intent, 'home', new_callable=PropertyMock, return_value=root / 'campaign'),
                    patch.multiple(port, phase=Mock(), command=Mock(return_value=b'ext4\n'), source=Mock(return_value={'pin': 'fixed'}),
                        prerequisites=prerequisites, identity=Mock(return_value={'identity': 'actual'}), operations=Mock(),
                        capture=Mock(), incus_env=Mock(return_value={'INCUS_SOCKET': '/var/lib/incus/unix.socket'}), public=public),
                    patch.object(suite.inventory, '_parse_json_command', return_value=alias),
                    patch.object(suite, 'projection', return_value={'preserved': 'baseline'}),
                    patch.object(suite, 'validate_preview', preview),
                    patch.object(suite, 'Journal'),
                ):
                    if fault == 'valid':
                        result = port.prepare()
                        self.assertEqual(result['baseline'], {'preserved': 'baseline'})
                    else:
                        with self.assertRaises(suite.CaseError):
                            port.prepare()
                    prerequisites.assert_called_once()
                    if fault in {'capability', 'alias'}:
                        public.assert_not_called()
                    else:
                        public.assert_called_once_with(suite.CASE_RECIPES['minimal'].args(preview=True), timeout=120)
                        preview.assert_called_once_with(b'actual-preview-transport', suite.CASE_RECIPES['minimal'])

    def test_qualification_receipt_allows_only_one_matrix_only_child(self) -> None:
        port = suite.WslCasePort(intent(), Mock())
        qualification, product = 'a' * 40, intent().source_commit
        command = Mock()
        with patch.object(port, 'command', command):
            self.assertEqual(port.qualification_revision(product), product)
            command.assert_not_called()
            variants: tuple[tuple[bytes, bytes, bool], ...] = (
                (f'{product} {qualification}\n'.encode(), (suite.CAPABILITY + '\n').encode(), True),
                (f'{product} {qualification} {"c" * 40}\n'.encode(), (suite.CAPABILITY + '\n').encode(), False),
                (f'{product} {"c" * 40}\n'.encode(), (suite.CAPABILITY + '\n').encode(), False),
                (f'{product} {qualification}\n'.encode(), b'', False),
                (f'{product} {qualification}\n'.encode(), (suite.CAPABILITY + '\ntools/code.py\n').encode(), False),
                (f'{product} {qualification}\n'.encode(), b'infra/config/other.json\n', False),
            )
            for parents, changes, allowed in variants:
                with self.subTest(parents=parents, changes=changes):
                    command.reset_mock(side_effect=True)
                    command.side_effect = [parents, changes]
                    if allowed:
                        self.assertEqual(port.qualification_revision(qualification), qualification)
                    else:
                        with self.assertRaisesRegex(suite.CaseError, 'CASE_QUALIFICATION_PROMOTION'):
                            port.qualification_revision(qualification)
                    self.assertEqual(command.call_args_list[0].args[0][-5:], ['rev-list', '--parents', '-n', '1', product])
                    self.assertEqual(command.call_args_list[1].args[0][-6:], ['diff', '--name-only', '--no-renames', qualification, product, '--'])
            for invalid in (None, True, '', 'main', 'a' * 39):
                with self.subTest(invalid=invalid), self.assertRaisesRegex(suite.CaseError, 'CASE_QUALIFICATION_SOURCE'):
                    port.qualification_revision(invalid)

    def test_upgrade_and_engine_recovery_have_distinct_fixed_go_phases(self) -> None:
        current = replace(intent(), case='upgrade-batch-service-access-portainer-published')
        proposal = {'pins': {'actual': 'c' * 64}}
        for engine, total in ((False, 10500), (True, 4800)):
            budgets = suite.upgrades.budgets(current.case, 'wsl', engine_recovery=engine)
            value = go(proposal) | {'intent_sha256': suite.sha(suite.canonical(asdict(current))),
                'budgets': budgets, 'phase': 'wsl-engine-recovery' if engine else 'wsl-case-run',
                'expires_at_utc': (datetime.now(timezone.utc) + timedelta(seconds=total + 30)).isoformat()}
            if engine:
                value['engine_binding'] = {'actual': 'pending'}
            suite.approval(value, current, proposal, '6' * 64, engine_recovery=engine)
            with self.assertRaises(suite.CaseError):
                suite.approval(value | {'budgets': dict(suite.BUDGETS)}, current, proposal, '6' * 64, engine_recovery=engine)
            with self.assertRaises(suite.CaseError):
                suite.approval(value, current, proposal, '6' * 64, recover=True)

    def test_unexercised_upgrade_is_disposed_but_never_pass(self) -> None:
        port = CasePort()
        def missed():
            raise suite.upgrades.UpgradeError('UPGRADE_NOT_EXERCISED')
        with patch.object(port, 'run', side_effect=missed):
            result = suite.execute(port, {'baseline': {}})
        self.assertEqual(result['status'], 'CASE_NOT_EXERCISED')
        self.assertFalse(result['epic_complete'])
        self.assertFalse(port.disposal.graph['instances'])
        self.assertNotIn('public', port.calls)

    def test_public_dispatch_rehashes_complete_config_and_parses_checked_operator_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(suite, 'BASE', Path(directory)):
            home = Path(directory) / intent().run_id
            infra = home / 'infra'
            infra.mkdir(parents=True)
            operator = infra / 'operator.env'
            operator.write_bytes(b'TSW_PORTAINER_ADMIN_PASSWORD=only-for-test')
            operator.chmod(0o600)
            config = infra / 'config.yaml'
            config.write_bytes(b'fixed: configuration')
            rows = [(p.name, suite.sha(p.read_bytes())) for p in sorted(infra.iterdir())]
            current = replace(intent(), configuration_sha256=suite.sha(suite.canonical(rows)))
            journal = Mock()
            port = suite.WslCasePort(current, journal)
            with patch.object(suite, 'trusted'), patch.object(suite, 'private', side_effect=lambda p: p.read_bytes()) as read:
                values = port.operator_values()
            self.assertEqual(values, {'TSW_PORTAINER_ADMIN_PASSWORD': 'only-for-test'})
            read.assert_called_once_with(operator)
            for changed in (operator, config):
                previous = changed.read_bytes()
                changed.write_bytes(previous + b'changed')
                with patch.object(suite, 'trusted'), patch.object(suite, 'private', side_effect=lambda p: p.read_bytes()), patch.object(suite.subprocess, 'Popen') as popen, patch.object(suite, 'operator_credentials') as parse:
                    with self.assertRaisesRegex(suite.CaseError, 'CASE_CONFIGURATION_DRIFT'):
                        port.command([sys.executable, '-c', 'pass'], 10, public=True)
                popen.assert_not_called()
                parse.assert_not_called()
                journal.save.assert_not_called()
                changed.write_bytes(previous)
            operator.write_bytes(b'TSW_LOCAL_TLS_STATE_ROOT=/root/.local/state/original')
            rows = [(p.name, suite.sha(p.read_bytes())) for p in sorted(infra.iterdir())]
            port = suite.WslCasePort(replace(current, configuration_sha256=suite.sha(suite.canonical(rows))), journal)
            with patch.object(suite, 'trusted'), patch.object(suite, 'private', side_effect=lambda p: p.read_bytes()), patch.object(suite.subprocess, 'Popen') as popen:
                with self.assertRaisesRegex(suite.CaseError, 'CASE_OPERATOR_ENV'):
                    port.command([sys.executable, '-c', 'pass'], 10, public=True)
            popen.assert_not_called()

    def test_fixed_scope_and_tls_are_last_even_if_a_credential_loader_regresses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            with patch.object(suite, 'trusted'):
                journal = suite.Journal(root)
            port = suite.WslCasePort(intent(), journal)
            keys = ('TSW_REPOSITORY_ROOT', 'TSW_INFRA_ROOT', 'TSW_INSTALL_ENV_FILE', 'TSW_LIVE_EVIDENCE_ROOT', 'TSW_LOCAL_TLS_STATE_ROOT')
            injected = dict.fromkeys(keys, '/original/do-not-use') | {'TSW_PORTAINER_ADMIN_PASSWORD': 'only-for-test'}
            with patch.object(port, 'operator_values', return_value=injected), patch.object(port, 'tls_root', return_value=str(root / 'tls')), patch.object(port, 'interpreter', return_value=sys.executable), patch.object(suite.subprocess, 'Popen', side_effect=OSError('fixture launch refusal')) as popen:
                with self.assertRaises(OSError):
                    port.command([sys.executable, '-c', 'pass'], 10, public=True)
            env = popen.call_args.kwargs['env']
            self.assertEqual(env['TSW_REPOSITORY_ROOT'], str(suite.ROOT))
            self.assertEqual(env['TSW_INFRA_ROOT'], str(intent().home / 'infra'))
            self.assertEqual(env['TSW_INSTALL_ENV_FILE'], str(intent().home / 'infra/operator.env'))
            self.assertEqual(env['TSW_LIVE_EVIDENCE_ROOT'], str(root))
            self.assertEqual(env['TSW_LOCAL_TLS_STATE_ROOT'], str(root / 'tls'))
            self.assertEqual(env['TSW_PORTAINER_ADMIN_PASSWORD'], 'only-for-test')

    def test_owned_tls_root_rejects_symlink_and_never_resolves_home_default(self) -> None:
        from tiny_swarm_world.infrastructure.adapters.ingress.tls_state import canonical_tls_state_root
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            journal = Mock(directory=root)
            port = suite.WslCasePort(intent(), journal)
            with patch.object(suite, 'trusted') as guard:
                tls = port.tls_root()
            guard.assert_called_once_with(root, directory=True)
            with patch.object(Path, 'home', side_effect=AssertionError('outside original state')):
                self.assertEqual(canonical_tls_state_root({'TSW_LOCAL_TLS_STATE_ROOT': tls}), root / 'tls')
            outside = root / 'outside'
            outside.mkdir(mode=0o700)
            (root / 'tls').symlink_to(outside, target_is_directory=True)
            with patch.object(suite, 'trusted'), self.assertRaisesRegex(suite.CaseError, 'CASE_TLS_ROOT_UNSAFE'):
                port.tls_root()

    def test_actual_wsl_prerequisite_path_requires_two_literal_hosts_and_all_source_blobs(self) -> None:
        for kind in ('valid', 'copied-native', 'wrong-host', 'missing-host', 'source', 'fixture', 'entry-code', 'artifact-code'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                cap = root / suite.CAPABILITY
                cap.parent.mkdir(parents=True)
                cap.write_bytes(b'cap')
                current = replace(intent(), capability_sha256=suite.sha(b'cap'))
                proof, artifacts, code = altered_capability(kind, current.capability_sha256)
                entry = SimpleNamespace(client_version='6.0.5', server_version='6.0.5', fixture_sha256=suite.sha(code), fixture_source_revision='e' * 40)
                admission = SimpleNamespace(admits=lambda *_: True, admitted_versions=(entry,))
                repository = SimpleNamespace(IncusProfileCapabilityRepository=lambda _: SimpleNamespace(load=lambda: admission))
                resources = SimpleNamespace(selection=Mock())
                configuration = SimpleNamespace(load_requirements=lambda _: SimpleNamespace(storage='default'))
                def read(path: Path) -> bytes:
                    if path.name == 'both-host-profile-capability.json':
                        return suite.canonical(proof)
                    return artifacts[path.name.removeprefix('profile-capability-').removesuffix('.json')] if path.name.startswith('profile-capability-') else b'config'
                def blob(argv: list[str], timeout: int) -> bytes:
                    revision = argv[-1].split(':')[0]
                    return b'wrong' if kind == 'entry-code' and revision == 'e' * 40 or kind == 'artifact-code' and revision == 'b' * 40 else code
                port = suite.WslCasePort(current, Mock())
                modules = {'tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository': repository,
                    (suite.__package__ + '.native_resource_admission'): resources,
                    'tiny_swarm_world.infrastructure.adapters.incus_preparation.configuration': configuration}
                with patch.object(suite, 'ROOT', root), patch.object(suite, 'trusted'), patch.object(suite, 'private', side_effect=read), patch.object(suite.importlib, 'import_module', side_effect=lambda name: modules[name]), patch.object(port, 'command', side_effect=blob) as command, patch.object(port, 'operator_values', return_value={}):
                    if kind == 'valid':
                        port.prerequisites()
                        self.assertEqual(command.call_count, 3)
                        resources.selection.assert_called_once()
                    else:
                        with self.assertRaises(suite.CaseError):
                            port.prerequisites()

    def test_strict_identity_and_closed_eight_actual_public_recipes(self) -> None:
        self.assertEqual(suite.Intent.parse(asdict(intent())), intent())
        self.assertEqual(len(suite.RECIPES), 8)
        self.assertEqual(suite.RECIPES['minimal'].args()[0:3], ['setup', 'run', '--minimal'])
        self.assertIn('--approve-live', suite.RECIPES['swagger-internal'].args())
        self.assertIn('internal', suite.RECIPES['swagger-internal'].args())
        self.assertEqual(set(suite.RECIPES['swagger-published'].services), {'swagger'})
        self.assertEqual(set(suite.RECIPES['swagger-traefik-swarm'].services), {'swagger', 'traefik'})
        self.assertEqual(suite.RECIPES['swagger-add-traefik'].args(add=True)[:4], ['services', 'add', '--services', 'traefik'])
        changes: tuple[tuple[str, Any], ...] = (('case', 'arbitrary-callback'), ('run_id', '../original'),
            ('source_commit', 'main'), ('new_guid', 'Ubuntu'), ('new_vhd_sha256', 'wrong'), ('windows_host', "PC';evil"))
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(suite.CaseError):
                suite.Intent.parse(asdict(intent()) | {key: value})
        with self.assertRaises(suite.CaseError):
            suite.Intent.parse(asdict(intent()) | {'callback': 'any'})

    def test_exact_run_recovery_budgets_and_go_binding_fail_closed(self) -> None:
        proposal = {'pins': {'source': '7' * 64}}
        for recovery in (False, True):
            suite.approval(go(proposal, recover=recovery), intent(), proposal, '6' * 64, recover=recovery)
        changes: tuple[tuple[str, Any], ...] = (('proposal_sha256', '0' * 64), ('source_commit', 'a' * 40),
            ('intent_sha256', '0' * 64), ('pins', {}), ('reviews', {}), ('budgets', {'case': 900}),
            ('expires_at_utc', (datetime.now(timezone.utc) + timedelta(seconds=900)).isoformat()),
            ('schema_version', True), ('phase', 'native-product-maintenance'))
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(suite.CaseError):
                suite.approval(go(proposal) | {key: value}, intent(), proposal, '6' * 64)

    def test_real_disposal_after_pass_and_public_failure_with_honest_scope(self) -> None:
        for failed in (False, True):
            port = CasePort(failed=failed)
            result = suite.execute(port, {'baseline': {}})
            self.assertEqual(result['status'], 'CASE_FAILED_DISPOSED' if failed else 'CASE_PASS_DISPOSED')
            self.assertFalse(result['epic_complete'])
            self.assertFalse(port.disposal.graph['instances'])
            self.assertIsNone(port.disposal.graph['profile'])
            self.assertLess(port.calls.index('event:execution-intent'), port.calls.index('public'))
            self.assertLess(port.calls.index('settled'), port.calls.index('dispose'))
            self.assertLess(port.calls.index('dispose'), port.calls.index('final'))

    def test_unknown_live_worker_prevents_cleanup_and_no_runtime_replay_in_recovery(self) -> None:
        port = CasePort(unsettled=True)
        with self.assertRaisesRegex(suite.CaseError, 'CASE_WORKER_UNSETTLED'):
            suite.execute(port, {'baseline': {}}, recover=True)
        self.assertNotIn('public', port.calls)
        self.assertNotIn('dispose', port.calls)
        port = CasePort()
        result = suite.execute(port, {'baseline': {}}, recover=True)
        self.assertEqual(result['status'], 'CASE_RECOVERED')
        self.assertNotIn('admit', port.calls)
        self.assertNotIn('public', port.calls)
        self.assertEqual([c for c in port.calls if c.startswith('phase:')], ['phase:recover'])

    def test_foreign_uuid_consumer_or_snapshot_blocks_actual_owned_disposal(self) -> None:
        mutations = ('uuid', 'consumer', 'snapshot')
        for mutation in mutations:
            port = CasePort()
            graph = port.disposal.graph
            if mutation == 'uuid':
                graph['instances']['swarm-manager']['config']['volatile.uuid'] = '00000000-0000-0000-0000-000000000000'
            elif mutation == 'consumer':
                graph['profile']['used_by'].append('/1.0/instances/foreign')
            else:
                graph['snapshots'].append({'parent': 'swarm-manager'})
            with self.subTest(mutation=mutation), self.assertRaises(suite.disposal.native.MaintenanceError):
                suite.execute(port, {'baseline': {}})
            self.assertTrue(graph['instances'])
            self.assertNotIn('final', port.calls)

    def test_preservation_subtracts_only_authenticated_case_refs_and_bounded_exact_cache(self) -> None:
        owned, graph = case()
        fp = '1' * 64
        pool = {'name': 'default', 'used_by': [], 'volumes': [], 'snapshots': [], 'image_cache': []}
        project = {'project': 'default', 'used_by': [], 'instances': [], 'profiles': [{'name': 'default', 'used_by': []}],
                   'networks': [{'name': 'incusbr0', 'used_by': []}], 'pools': [pool], 'images': [{'fingerprint': fp}]}
        artifact: dict[str, Any] = {'incus_projects': [project], 'incus_pools': [{'name': 'default', 'used_by': []}],
            'incus_admission': {}, 'incus_units': [], 'lxd_projects': [], 'lxd_pools': [], 'lxd_units': [], 'lxd_admission': None, 'sockets': []}
        base = suite.projection(artifact, {}, None, fp)
        after = copy.deepcopy(artifact)
        row = after['incus_projects'][0]
        row['instances'] = [{'name': n.name} for n in owned.nodes]
        row['profiles'].append({'name': owned.profile_name, 'used_by': []})
        row['pools'][0]['volumes'] = copy.deepcopy(graph['volumes'])
        refs = [{'kind': 'instances', 'name': n.name, 'project': 'default'} for n in owned.nodes]
        row['used_by'] = list(refs)
        row['profiles'][0]['used_by'] = list(refs)
        row['networks'][0]['used_by'] = list(refs)
        row['pools'][0]['used_by'] = list(refs)
        after['incus_pools'][0]['used_by'] = list(refs)
        details: dict[Any, Any] = {('incus_instance_config_show', (n.name, 'default')): graph['instances'][n.name] for n in owned.nodes}
        details[('incus_profile_show', (owned.profile_name, 'default'))] = graph['profile']
        self.assertEqual(suite.projection(after, details, owned, fp, base), base)
        for mutation in ('foreign-node', 'snapshot', 'network', 'foreign-cache'):
            changed = copy.deepcopy(after)
            if mutation == 'foreign-node':
                changed['incus_projects'][0]['instances'].append({'name': 'foreign'})
            elif mutation == 'snapshot':
                changed['incus_projects'][0]['pools'][0]['snapshots'].append({'parent': 'swarm-manager', 'name': 'valuable'})
            elif mutation == 'network':
                changed['incus_projects'][0]['networks'][0]['changed'] = True
            else:
                changed['incus_projects'][0]['pools'][0]['image_cache'].append({'fingerprint': '0' * 64})
            self.assertNotEqual(suite.projection(changed, details, owned, fp, base), base)
        image_ref = {'kind': 'images', 'name': fp, 'project': 'default'}
        after['incus_projects'][0]['pools'][0]['image_cache'] = [{'fingerprint': fp, 'owner_project': 'default', 'content_type': 'filesystem'}]
        after['incus_projects'][0]['pools'][0]['used_by'].append(image_ref)
        after['incus_pools'][0]['used_by'].append(image_ref)
        details[('incus_image_cache_show', ('default', fp, 'default'))] = {'config': {}, 'name': fp}
        self.assertEqual(suite.projection(after, details, owned, fp, base), base)
        foreign_reference = copy.deepcopy(after)
        foreign_reference['incus_projects'][0]['networks'][0]['used_by'].append(image_ref)
        self.assertNotEqual(suite.projection(foreign_reference, details, owned, fp, base), base)
        after['incus_projects'][0]['pools'][0]['image_cache'][0]['content_type'] = 'block'
        with self.assertRaisesRegex(suite.CaseError, 'CASE_CACHE_ADDITION_INVALID'):
            suite.projection(after, details, owned, fp, base)

    def test_operations_require_strict_envelope_known_states_and_uuid_links(self) -> None:
        envelope = {'type': 'sync', 'status': 'Success', 'status_code': 200, 'operation': '',
                    'error_code': 0, 'error': '', 'metadata': {}}
        self.assertTrue(suite.operations_empty(envelope))
        self.assertFalse(suite.operations_empty(envelope | {'metadata': {'success': ['/1.0/operations/' +
            '11111111-1111-1111-1111-111111111111']}}))
        invalid_metadata: tuple[Any, ...] = ({'unknown': []}, {'running': None}, {'running': ['/1.0/instances/foreign']}, [])
        for metadata in invalid_metadata:
            with self.subTest(metadata=metadata), self.assertRaises(suite.CaseError):
                suite.operations_empty(envelope | {'metadata': metadata})
        for changes in ({'status_code': True}, {'extra': 'ignored'}, {'error': 'denied'}):
            with self.assertRaises(suite.CaseError):
                suite.operations_empty(envelope | changes)

    def test_journal_fsync_readback_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            path.chmod(0o700)
            with patch.object(suite, 'trusted') as guard:
                journal = suite.Journal(path)
            guard.assert_called_once_with(path, directory=True)
            journal.save('intent.json', {'fixed': 'value'})
            self.assertEqual(json.loads((path / 'intent.json').read_bytes()), {'fixed': 'value'})
            self.assertEqual((path / 'intent.json').stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                journal.save('intent.json', {'changed': True})
            with self.assertRaises(suite.CaseError):
                journal.save('../original.json', {})

    def test_actual_gated_child_first_output_has_durable_pid_and_settled_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            with patch.object(suite, 'trusted') as guard:
                journal = suite.Journal(root)
            guard.assert_called_once_with(root, directory=True)
            port = suite.WslCasePort(intent(), journal)
            with patch.object(journal, 'save', wraps=journal.save) as save, patch.object(suite, 'ROOT', root), patch.object(port, 'interpreter', return_value=sys.executable), patch.object(port, 'tls_root', return_value=str(root / 'tls')), patch.dict(suite.os.environ, {}, clear=True):
                raw = port.command([sys.executable, '-c', "print('first-output')"], 3)
            self.assertEqual(raw, b'first-output\n')
            self.assertTrue(port.worker_settled)
            names = [call.args[0] for call in save.call_args_list]
            self.assertEqual([name.rsplit('-', 1)[1] for name in names], ['intent.json', 'pid.json', 'outcome.json', 'settled.json'])
            keys = {name.rsplit('-', 1)[0] for name in names}
            self.assertEqual(len(keys), 1)
            pid = json.loads((root / names[1]).read_bytes())
            self.assertGreater(pid['pid'], 1)
            self.assertGreater(pid['start_time'], 0)
            self.assertTrue(json.loads((root / names[3]).read_bytes())['group_absent'])

    def test_identity_refuses_missing_real_receipts_before_windows_interop(self) -> None:
        journal = Mock()
        port = suite.WslCasePort(intent(), journal)
        with patch.object(suite.Path, 'read_text', return_value='microsoft'), patch.dict(suite.os.environ, {'WSL_DISTRO_NAME': 'Ubuntu'}):
            with self.assertRaisesRegex(suite.CaseError, 'CASE_WSL_IDENTITY'):
                port.identity()
        journal.save.assert_not_called()

    def test_windows_scope_is_read_only_exact_registration_and_bound_bundle(self) -> None:
        command = suite.windows_scope(intent())
        self.assertIn(intent().new_guid, command)
        self.assertIn('TSW-Q440-' + intent().run_id, command)
        self.assertIn(intent().bridge_bundle_id, command)
        self.assertIn('GetFileInformationByHandle', command)
        self.assertIn('--list --running --quiet', command)
        self.assertNotIn('--shutdown', command)
        self.assertNotIn('--terminate', command)
        self.assertNotIn('Set-Item', command)
        self.assertNotIn('Start-Service', command)
        self.assertNotIn('Remove-', command)

    def test_real_phase_authorization_reserves_cleanup_and_never_resets_recovery(self) -> None:
        port = suite.WslCasePort(intent(), Mock())
        with patch.object(suite.time, 'monotonic', return_value=100):
            port.authorized_until = 6999
            with self.assertRaisesRegex(suite.CaseError, 'CASE_AUTHORIZATION_RESERVE'):
                port.phase('admit')
            port.authorized_until = 7000
            port.phase('admit')
            self.assertEqual(port.deadline, 400)
        with patch.object(suite.time, 'monotonic', return_value=200):
            port.authorized_until = 6500
            with self.assertRaisesRegex(suite.CaseError, 'CASE_AUTHORIZATION_RESERVE'):
                port.phase('case')
        recovery = suite.WslCasePort(intent(), Mock())
        with patch.object(suite.time, 'monotonic', return_value=100):
            recovery.phase('recover')
        with patch.object(suite.time, 'monotonic', return_value=200):
            recovery.phase('recover')
        self.assertEqual(recovery.deadline, 1000)

    def test_cache_addition_without_actual_creation_authority_is_not_adopted(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(suite, 'BASE', Path(directory)):
            journal = Mock()
            port = suite.WslCasePort(intent(), journal)
            baseline = {'incus_projects': [{'pools': [{'name': 'default', 'image_cache': []}]}]}
            port.artifact = {'incus_projects': [{'pools': [{'name': 'default', 'image_cache': [{
                'fingerprint': intent().ubuntu_fingerprint, 'owner_project': 'default', 'content_type': 'filesystem'}]}]}]}
            with self.assertRaisesRegex(suite.CaseError, 'CASE_IMAGE_CACHE_UNPROVEN'):
                port.cache_receipt(baseline, record=True)
            journal.save.assert_not_called()

    def test_explicit_phases_have_no_native_maintenance_or_network_disposal(self) -> None:
        port = suite.WslCasePort(intent(), Mock())
        with patch.object(suite.time, 'monotonic', return_value=100):
            port.phase('recover')
        self.assertEqual(port.deadline, 1000)
        with self.assertRaises(suite.CaseError):
            port.phase('shutdown')
        self.assertNotIsInstance(port, suite.disposal.native.NativePort)


if __name__ == '__main__':
    unittest.main()

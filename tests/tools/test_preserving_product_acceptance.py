"""Closed native case budgets, child ownership and preserving transaction tests."""
from __future__ import annotations

import copy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tools.linux.qualification import native_lxd_maintenance as native
from tools.linux.qualification import preserving_product_acceptance as suite
from tests.tools.test_native_lxd_maintenance import FakePort, Events, baseline
from tests.tools.test_owned_case_disposal import case, Port


def intent() -> suite.SuiteIntent:
    return suite.SuiteIntent('a' * 32, 'b' * 40, 'minimal', 'c' * 64, 'd' * 64, 'e' * 64, 'f' * 64, '1' * 64)


def proposal() -> dict[str, Any]:
    return {'source_commit': 'b' * 40, 'intent_sha256': '2' * 64, 'host_id_sha256': '3' * 64,
            'pins': {'source': '4' * 64}, 'baseline': baseline()}


def approval(now: datetime, paused: bool = False) -> dict[str, Any]:
    go = {key: proposal()[key] for key in ('source_commit', 'intent_sha256', 'host_id_sha256', 'pins')}
    go.update(schema_version=1, decision='GO', phase='paused-product-case' if paused else 'native-product-maintenance',
        proposal_sha256='5' * 64, budgets=dict(suite.BUDGETS), reviews={key: 'APPROVED' for key in native.fixture.REVIEW_KEYS},
        expires_at_utc=(now + timedelta(seconds=(suite.ACTIVATION_COVERAGE if paused else suite.START_COVERAGE) + 30)).isoformat())
    if paused:
        go.update(resource_sha256='6' * 64, route_sha256='7' * 64, preview_sha256='8' * 64)
    return go


class SuiteTransactionPort(FakePort):
    """Actual unchanged Transaction and actual disposal, only transport faked."""
    def __init__(self, fail: bool = False):
        super().__init__(baseline())
        self.owned_intent, graph = case()
        self.case_port = Port(graph)
        self.fail_case = fail

    def run_fixture(self) -> None:
        try:
            if self.fail_case:
                raise native.MaintenanceError('CASE_CLI_FAILED')
        finally:
            suite.disposal.dispose(self.case_port, self.owned_intent)


class PreservingProductAcceptanceTests(unittest.TestCase):
    def test_actual_maintenance_transaction_recovers_originals_after_pass_and_failed_case(self) -> None:
        for failure in (False, True):
            with self.subTest(failure=failure):
                port = SuiteTransactionPort(failure)
                journal = Events(port)
                result = native.Transaction(port, journal, baseline()).execute()
                self.assertEqual(result['status'], 'QUALIFICATION_FAILED_RECOVERED' if failure else 'PASS')
                self.assertEqual(baseline(), port.state)
                self.assertEqual('active', port.daemon)
                self.assertFalse(port.case_port.graph['instances'])
                self.assertIsNone(port.case_port.graph['profile'])
                self.assertTrue(port.reserve)

    def test_late_fourth_node_or_foreign_project_stops_global_shutdown_and_still_restores(self) -> None:
        for drift in ('foreign-node', 'new-project', 'issue447-data'):
            port = SuiteTransactionPort()
            port.late_drift = drift
            with self.assertRaisesRegex(native.MaintenanceError, 'RECOVERY_REQUIRED'):
                native.Transaction(port, Events(port), baseline()).execute()
            self.assertNotIn(('shutdown', ''), port.calls)
            self.assertTrue(all(row['status'] == 'Running' for row in port.state['nodes'].values()))

    def test_strict_intent_rejects_arbitrary_callback_project_names_and_schema_types(self) -> None:
        raw = asdict(intent())
        self.assertEqual(intent(), suite.SuiteIntent.parse(raw, intent().source_commit))
        variants: tuple[dict[str, Any], ...] = (raw | {'callback': '/bin/sh'}, raw | {'project': 'issue447'},
            raw | {'case': 'arbitrary'}, raw | {'ubuntu_fingerprint': False}, raw | {'run_id': '../foreign'},
            raw | {'source_commit': '0' * 40})
        for value in variants:
            with self.subTest(value=value), self.assertRaises(native.MaintenanceError):
                suite.SuiteIntent.parse(value, intent().source_commit)

    def test_long_suite_go_and_paused_go_have_exact_separate_phase_coverage(self) -> None:
        now = datetime.now(timezone.utc)
        for paused in (False, True):
            go = approval(now, paused)
            suite.validate_go(go, proposal(), '5' * 64, now, paused=paused)
            minimum = suite.ACTIVATION_COVERAGE if paused else suite.START_COVERAGE
            for seconds in (minimum - 1, minimum + 301, 1795):
                bad = go | {'expires_at_utc': (now + timedelta(seconds=seconds)).isoformat()}
                with self.assertRaisesRegex(native.MaintenanceError, 'SUITE_GO_EXPIRED'):
                    suite.validate_go(bad, proposal(), '5' * 64, now, paused=paused)
        self.assertEqual(suite.BUDGETS, {'prepare': 1200, 'pause': 600, 'approval': 180,
            'case': 5400, 'teardown': 900, 'restore': 600})

    def test_go_cannot_change_source_capture_host_budgets_or_role_set(self) -> None:
        now = datetime.now(timezone.utc)
        go = approval(now, True)
        changes: tuple[dict[str, Any], ...] = ({'schema_version': True}, {'phase': 'native-product-maintenance'},
            {'host_id_sha256': '0' * 64}, {'source_commit': '0' * 40}, {'pins': {}}, {'budgets': {}},
            {'resource_sha256': False}, {'reviews': {'architecture': 'APPROVED'}}, {'callback': 'sh'})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(native.MaintenanceError):
                suite.validate_go(go | change, proposal(), '5' * 64, now, paused=True)

    def test_explicit_recovery_has_its_own_narrow_phase_and_1500_second_coverage(self) -> None:
        now = datetime.now(timezone.utc)
        go = approval(now) | {'phase': 'native-product-recovery',
            'expires_at_utc': (now + timedelta(seconds=1530)).isoformat()}
        suite.validate_go(go, proposal(), '5' * 64, now, paused=False, recovery=True)
        with self.assertRaisesRegex(native.MaintenanceError, 'SUITE_GO_SCHEMA_INVALID'):
            suite.validate_go(go, proposal(), '5' * 64, now, paused=False)
        with self.assertRaisesRegex(native.MaintenanceError, 'SUITE_GO_EXPIRED'):
            suite.validate_go(go | {'expires_at_utc': (now + timedelta(seconds=1499)).isoformat()},
                proposal(), '5' * 64, now, paused=False, recovery=True)

    def test_recipe_table_has_real_different_optional_service_sets_and_fixed_public_entrypoints(self) -> None:
        one, two = suite.RECIPES['swagger-published'], suite.RECIPES['swagger-traefik-swarm']
        self.assertEqual(('swagger',), one.services)
        self.assertEqual(('swagger', 'traefik'), two.services)
        self.assertNotEqual(set(one.services), set(two.services))
        self.assertEqual(suite.RECIPES['minimal'].args()[:3], ['setup', 'run', '--minimal'])
        self.assertNotIn('--stack-owner', suite.RECIPES['minimal'].args())
        for recipe in suite.RECIPES.values():
            args = recipe.args()
            self.assertEqual(args[:2], ['setup', 'run'])
            self.assertIn('--approve-live', args)
            self.assertNotIn('--force', args)
            self.assertNotIn('--live', recipe.args(preview=True))
        self.assertEqual(suite.RECIPES['swagger-add-traefik'].args(add=True)[:4], ['services', 'add', '--services', 'traefik'])

    def test_native_listener_controller_is_not_given_an_arbitrary_callback(self) -> None:
        port = suite.SuiteNativePort(intent(), Mock())
        with self.assertRaisesRegex(native.MaintenanceError, 'SUITE_PROPOSAL_MISSING'):
            port.run_fixture()
        self.assertFalse(port.pause_started)
        self.assertFalse(port.in_case_window)

    def test_separate_recovery_budget_and_unsafe_listener_gate_survive_case_expiry(self) -> None:
        port = suite.SuiteNativePort(intent(), Mock())
        port.phase('case')
        port.deadline = time.monotonic() - 1
        port.restore_safe = False
        port.begin_recovery()
        self.assertTrue(port.recovering)
        self.assertGreater(port.deadline - time.monotonic(), 599)
        with self.assertRaisesRegex(native.MaintenanceError, 'CASE_LISTENER_RECOVERY_UNSAFE'):
            port.check_binding(baseline(), active=False)

    def test_owned_group_settlement_does_not_assume_reaped_leader_means_no_descendant(self) -> None:
        probe = Mock(side_effect=[None, None, ProcessLookupError(), ProcessLookupError()])
        with patch.object(suite.os, 'killpg', probe), patch.object(suite.time, 'sleep'):
            self.assertTrue(suite.settle_group(4242))
        self.assertIn(((4242, signal.SIGTERM),), tuple((call.args,) for call in probe.call_args_list))

    def test_operations_tombstones_are_observed_until_empty_without_effect_retry(self) -> None:
        envelope = {'type': 'sync', 'status': 'Success', 'status_code': 200, 'operation': '', 'error_code': 0, 'error': '',
            'metadata': {'success': ['/1.0/operations/11111111-1111-4111-8111-111111111111']}}
        self.assertFalse(suite.operations_empty(envelope))
        self.assertTrue(suite.operations_empty(envelope | {'metadata': {}}))
        port = suite.SuiteNativePort(intent(), Mock())
        port.baseline = baseline()
        clock = [0.0]
        port.deadline = 100
        def sleep(_seconds: float) -> None:
            clock[0] += 5
        with patch.object(suite.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(suite.time, 'sleep', side_effect=sleep), \
                patch.object(native.NativePort, 'check_binding'), patch.object(port, 'incus_env', return_value={}), \
                patch.object(native.inventory, '_parse_json_command', side_effect=[envelope, envelope | {'metadata': {}}]) as query:
            port.wait_operations()
        self.assertEqual(2, query.call_count)
        self.assertEqual(5, clock[0])
        self.assertTrue(all(call.args[1][-1] == '/1.0/operations?all-projects=true' for call in query.call_args_list))
        invalid_metadata: tuple[Any, ...] = ({'unknown': []}, {'success': [False]}, {'success': ['foreign']}, [], False)
        for metadata in invalid_metadata:
            with self.assertRaises(native.MaintenanceError):
                suite.operations_empty(envelope | {'metadata': metadata})

    def test_shared_preparation_helper_reads_real_plan_interface_without_apply(self) -> None:
        for ready in (False, True):
            incus = Mock()
            network = Mock()
            incus.plan = AsyncMock(return_value=SimpleNamespace(verified=ready, actions=(), blockers=()))
            network.plan = AsyncMock(return_value=SimpleNamespace(verified=True, actions=(), blockers=()))
            module = SimpleNamespace(build_incus_preparation_service=Mock(return_value=incus),
                build_network_preparation_service=Mock(return_value=network))
            with patch('builtins.print'), patch.object(suite.importlib, 'import_module', return_value=module):
                if ready:
                    suite.observe_prerequisites()
                else:
                    with self.assertRaisesRegex(native.MaintenanceError, 'SUITE_SHARED_PREPARATION_REQUIRED'):
                        suite.observe_prerequisites()
            incus.apply.assert_not_called()
            network.apply.assert_not_called()

    def test_listener_identity_ignores_row_order_only_not_owner_or_binding(self) -> None:
        self.assertEqual(suite.listener_digest(b'one\ntwo\n'), suite.listener_digest(b'two\none\n'))
        self.assertNotEqual(suite.listener_digest(b'one\ntwo\n'), suite.listener_digest(b'foreign\ntwo\n'))

    def test_real_child_gate_journal_precedes_payload_and_settles_actual_harmless_child(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.chmod(0o700)
            with patch.object(native, 'private_directory') as check:
                journal = native.Journal(root)
            check.assert_called_once_with(root)
            port = suite.SuiteNativePort(intent(), journal)
            with patch.object(port, 'interpreter', return_value=sys.executable), patch.object(suite, 'operator_values', return_value={}):
                code = ('from pathlib import Path;import sys;'
                    'assert len(list(Path(sys.argv[1]).glob("child-*-pid.json")))==1;'
                    'sys.stderr.write("private-not-exported");print("safe-child")')
                output = port.child([sys.executable, '-c', code, str(root)], 10)
            self.assertEqual(b'safe-child\n', output)
            self.assertTrue(port.worker_settled)
            intents = list(root.glob('child-*-intent.json'))
            receipts = list(root.glob('child-*-pid.json'))
            outcomes = list(root.glob('child-*-outcome.json'))
            settled = list(root.glob('child-*-settled.json'))
            self.assertEqual((1, 1, 1, 1), (len(intents), len(receipts), len(outcomes), len(settled)))
            child_key = intents[0].name.removesuffix('-intent.json')
            self.assertEqual(outcomes[0].name, child_key + '-outcome.json')
            self.assertEqual(settled[0].name, child_key + '-settled.json')
            outcome = native.inventory.strict_json(native.read_private(outcomes[0]))
            self.assertEqual(outcome['return_code'], 0)
            self.assertEqual(outcome['stderr_sha256'], native.digest(b'private-not-exported'))
            self.assertNotIn(b'private-not-exported', native.read_private(outcomes[0]))
            self.assertLessEqual(intents[0].stat().st_mtime_ns, receipts[0].stat().st_mtime_ns)
            self.assertTrue(suite.previous_children_settled(journal))
            for path in (*intents, *receipts, *settled):
                self.assertEqual(0o600, path.stat().st_mode & 0o777)

    def test_lost_pid_receipt_or_still_live_group_blocks_disposal_without_signalling(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.chmod(0o700)
            with patch.object(native, 'private_directory'):
                journal = native.Journal(root)
            key = 'child-' + 'a' * 32
            journal.save(key + '-intent.json', {'argv_sha256': 'b' * 64, 'timeout': 10})
            self.assertFalse(suite.previous_children_settled(journal))
            journal.save(key + '-pid.json', {'pid': 4242, 'start_time': 1234})
            with patch.object(suite.os, 'killpg') as probe:
                self.assertFalse(suite.previous_children_settled(journal))
                probe.assert_called_once_with(4242, 0)

    def test_disposal_intent_json_cannot_inject_names_or_change_checkpoint_schema(self) -> None:
        original, _graph = case()
        raw = json.loads(native.canonical(asdict(original)))
        self.assertEqual(original, suite.decode_disposal(raw))
        for value in (raw | {'callback': 'sh'}, raw | {'nodes': [{'name': 'foreign'}]}, raw | {'nodes': False}):
            with self.assertRaises(native.MaintenanceError):
                suite.decode_disposal(value)

    def test_actual_mutation_adapter_requires_private_active_lease_and_closed_arguments(self) -> None:
        port = suite.SuiteNativePort(intent(), Mock())
        port.baseline = baseline()
        port.owned = case()[0]
        args = ['--project', 'default', 'stop', 'swarm-worker-2', '--timeout', '60']
        with self.assertRaisesRegex(native.MaintenanceError, 'CASE_DISPOSAL_LEASE_REQUIRED'):
            port.incus_effect(args, 75)
        port.disposal_lease = Mock()
        with patch.object(port, 'check_binding'), patch.object(port, 'fresh_source'), \
                patch.object(port, 'incus_env', return_value={'LC_ALL': 'C', 'INCUS_SOCKET': '/var/lib/incus/unix.socket'}), \
                patch.object(port, 'command', return_value=b'') as command:
            port.incus_effect(args, 75)
            port.disposal_lease.require_active.assert_called_once()
            actual = command.call_args.args[0]
            self.assertEqual(['/usr/bin/env', '-i'], actual[:2])
            self.assertIn('/usr/bin/incus', actual)
            self.assertEqual(args, actual[-6:])
            command.reset_mock()
            for denied in (['--project', 'issue447', 'delete', 'swarm-manager'],
                ['--project', 'default', 'delete', 'foreign'],
                ['--project', 'default', 'delete', 'swarm-manager', '--force'],
                ['--project', 'default', 'profile', 'delete', 'default']):
                with self.assertRaisesRegex(native.MaintenanceError, 'CASE_COMMAND_NOT_ALLOWED'):
                    port.incus_effect(denied, 30)
            command.assert_not_called()

    def test_exact_cached_ubuntu_transition_reuses_existing_preservation_proof(self) -> None:
        before = baseline()
        before['binding']['fixture_image'] = intent().ubuntu_fingerprint
        project: dict[str, Any] = {'project': 'default', 'images': [{'fingerprint': intent().ubuntu_fingerprint}],
            'profiles': [{'name': 'default', 'owner_project': 'default',
                          'api_storage_devices': [{'selector': 'root', 'pool': 'default'}]}],
            'instances': [], 'used_by': [],
            'pools': [{'name': 'default', 'volumes': [], 'snapshots': [], 'image_cache': [], 'used_by': []}]}
        before['preserve'].update(incus_projects=[project], incus_pools=[{'name': 'default', 'used_by': []}],
            configuration_digests={}, incus_admission=None, incus_units=[])
        artifact: dict[str, Any] = {key: copy.deepcopy(before['preserve'][key]) for key in
                    ('incus_projects', 'incus_pools', 'incus_admission', 'incus_units')}
        raw_cache: dict[str, Any] = {'name': intent().ubuntu_fingerprint, 'config': {}, 'type': 'image'}
        metadata_digest = native.digest(native.canonical(native.config_projection(raw_cache)))
        cache = {'fingerprint': intent().ubuntu_fingerprint, 'owner_project': 'default', 'content_type': 'filesystem',
            'metadata_digest': metadata_digest, 'storage_location': 'none', 'used_by': []}
        artifact['incus_projects'][0]['pools'][0]['image_cache'] = [cache]
        links = [{'kind': 'images', 'name': intent().ubuntu_fingerprint, 'project': 'default'}]
        artifact['incus_projects'][0]['pools'][0]['used_by'] = links
        artifact['incus_pools'][0]['used_by'] = links
        details: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {
            ('incus_image_cache_show', ('default', intent().ubuntu_fingerprint, 'default')): raw_cache}
        self.assertTrue(suite.preserved_case(before, artifact, details, case()[0]))
        for change in ('foreign-cache', 'changed-image', 'foreign-project', 'extra-custom-volume', 'cache-config'):
            bad = copy.deepcopy(artifact)
            bad_details = copy.deepcopy(details)
            if change == 'foreign-cache':
                bad['incus_projects'][0]['pools'][0]['image_cache'][0]['fingerprint'] = '9' * 64
            elif change == 'changed-image':
                bad['incus_projects'][0]['images'][0]['fingerprint'] = '9' * 64
            elif change == 'foreign-project':
                bad['incus_projects'].append(project | {'project': 'foreign'})
            elif change == 'extra-custom-volume':
                bad['incus_projects'][0]['pools'][0]['volumes'].append({'name': 'foreign', 'type': 'custom', 'owner_project': 'default'})
            else:
                bad_details[next(iter(bad_details))]['config']['foreign'] = 'changed'
            with self.subTest(change=change):
                self.assertFalse(suite.preserved_case(before, bad, bad_details, case()[0]))
        self.assertFalse(before['preserve']['incus_projects'][0]['pools'][0]['image_cache'])


if __name__ == '__main__':
    unittest.main()

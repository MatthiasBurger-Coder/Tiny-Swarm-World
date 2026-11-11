"""Closed native case budgets, child ownership and preserving transaction tests."""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import signal
import shlex
import stat
import sys
import tempfile
import time
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import AsyncMock, Mock, patch

from modules.tsw_native_linux.tools.qualification import native_lxd_maintenance as native
from modules.tsw_native_linux.tools.qualification import preserving_product_acceptance as suite
from modules.tsw_native_linux.tests.tools.test_native_lxd_maintenance import FakePort, Events, baseline
from modules.tsw_native_linux.tests.tools.test_owned_case_disposal import case, Port


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


def capability_pair(capability_sha: str = '1' * 64) -> tuple[dict[str, Any], dict[str, bytes], bytes]:
    code = b'fixed-real-fixture-source-for-unit-test'
    artifacts: dict[str, bytes] = {}
    receipts: dict[str, Any] = {}
    for host, target in suite.CAPABILITY_HOSTS.items():
        row = {'status': 'PASS', 'target_host': target, 'source_commit': 'b' * 40,
               'runner_sha256': native.digest(code), 'server_version': '6.0.5', 'go_sha256': 'c' * 64}
        artifacts[host] = native.canonical(row)
        receipts[host] = {'decision': 'PASS', 'artifact_sha256': native.digest(artifacts[host]), 'source_commit': 'b' * 40}
    return {'capability_sha256': capability_sha, 'client': '6.0.5', 'server': '6.0.5', 'hosts': receipts}, artifacts, code


def altered_capability(kind: str, capability_sha: str) -> tuple[dict[str, Any], dict[str, bytes], bytes]:
    proof, artifacts, code = capability_pair(capability_sha)
    if kind == 'copied-native':
        artifacts['wsl2'] = artifacts['native_linux']
    elif kind in {'wrong-host', 'missing-host', 'source', 'fixture'}:
        row = json.loads(artifacts['wsl2'])
        if kind == 'wrong-host':
            row['target_host'] = '192.168.178.33'
        elif kind == 'missing-host':
            del row['target_host']
        elif kind == 'source':
            row['source_commit'] = 'd' * 40
        else:
            row['runner_sha256'] = '0' * 64
        artifacts['wsl2'] = native.canonical(row)
    for host in artifacts:
        proof['hosts'][host]['artifact_sha256'] = native.digest(artifacts[host])
    return proof, artifacts, code


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
    def test_upgrade_go_binds_distinct_complete_purpose_before_dispatch(self) -> None:
        case_name = 'upgrade-batch-service-access-portainer-internal'
        now = datetime.now(timezone.utc)
        budgets = suite.upgrades.budgets(case_name, 'native')
        go = approval(now) | {'budgets': budgets,
            'expires_at_utc': (now + timedelta(seconds=sum(budgets.values()) + 30)).isoformat()}
        suite.validate_go(go, proposal(), '5' * 64, now, paused=False, case=case_name)
        for wrong in (dict(suite.BUDGETS), budgets | {'case': 18000}):
            with self.assertRaisesRegex(native.MaintenanceError, 'BINDING_DRIFT'):
                suite.validate_go(go | {'budgets': wrong}, proposal(), '5' * 64, now, paused=False, case=case_name)
        recovery = suite.upgrades.budgets(case_name, 'native', engine_recovery=True)
        engine = go | {'phase': 'native-product-engine-recovery', 'engine_binding': {'actual': 'pending'},
            'budgets': recovery, 'expires_at_utc': (now + timedelta(seconds=sum(recovery.values()) + 30)).isoformat()}
        suite.validate_go(engine, proposal(), '5' * 64, now, paused=False, case=case_name, engine_recovery=True)
        with self.assertRaises(native.MaintenanceError):
            suite.validate_go(engine, proposal(), '5' * 64, now, paused=False, case=case_name, recovery=True)

    def test_upgrade_baseline_cannot_override_scope_or_tls_even_on_helper_regression(self) -> None:
        selected = replace(intent(), case='upgrade-swagger-swarm')
        journal = Mock(directory=Path('/private/fixture'))
        port = suite.SuiteNativePort(selected, journal)
        port.upgrade_baseline = True
        port.deadline = time.monotonic() + 120
        injected = {'TSW_REPOSITORY_ROOT': '/original', 'TSW_LOCAL_TLS_STATE_ROOT': '/original/tls',
                    'TSW_SWAGGER_UI_IMAGE': 'fixed-source@sha256:' + 'a' * 64}
        with patch.object(suite, 'operator_values', return_value={}), patch.object(suite, 'tree_digest', return_value=selected.infra_sha256), patch.object(suite, 'case_tls_root', return_value='/private/fixture/tls'), \
                patch.object(suite.upgrades, 'baseline_environment', return_value=injected), \
                patch.object(port, 'interpreter', return_value=sys.executable), \
                patch.object(suite.subprocess, 'Popen', side_effect=OSError('launch refused')) as launched:
            with self.assertRaises(OSError):
                port.child([sys.executable, '-c', 'pass'], 10)
        env = launched.call_args.kwargs['env']
        self.assertEqual(env['TSW_REPOSITORY_ROOT'], str(suite.ROOT))
        self.assertEqual(env['TSW_LOCAL_TLS_STATE_ROOT'], '/private/fixture/tls')
        self.assertEqual(env['TSW_SWAGGER_UI_IMAGE'], injected['TSW_SWAGGER_UI_IMAGE'])

    def test_closed_credentials_equal_actual_active_catalog_and_contract_material(self) -> None:
        from tiny_swarm_world.domain.configuration.internal_test_credentials import internal_test_catalog
        from tiny_swarm_world.domain.configuration.configuration_contract import default_configuration_contract
        active = {d.key for d in internal_test_catalog().definitions if d.active}
        material = {r.key for r in default_configuration_contract().requirements
                    if r.value_kind.value == 'secret_value'} | {'TSW_INFISICAL_LOGIN_EMAIL'}
        self.assertEqual(suite.CREDENTIAL_KEYS, active)
        self.assertEqual(suite.CREDENTIAL_KEYS, material)
        values = {d.key: d.value for d in internal_test_catalog().definitions if d.active}
        raw = '\n'.join(k + '=' + shlex.quote(v) for k, v in values.items()).encode()
        with patch.object(Path, 'read_text', side_effect=AssertionError('second path read')):
            self.assertEqual(suite.operator_credentials(raw), values)
        self.assertEqual(suite.operator_credentials(b'TSW_PORTAINER_ADMIN_PASSWORD=only-for-test'),
                         {'TSW_PORTAINER_ADMIN_PASSWORD': 'only-for-test'})

    def test_reserved_operator_keys_and_invalid_htpasswd_refuse_without_secret_echo(self) -> None:
        forbidden = ('TSW_REPOSITORY_ROOT', 'TSW_INFRA_ROOT', 'TSW_INSTALL_ENV_FILE', 'TSW_LIVE_EVIDENCE_ROOT',
            'TSW_LOCAL_TLS_STATE_ROOT', 'TSW_INFISICAL_URL', 'TSW_INFISICAL_PROVIDER_MODE', 'TSW_SEED_INFISICAL_ITEMS',
            'TSW_TRAEFIK_TLS_CERT_PATH', 'TSW_TRAEFIK_TLS_CA_KEY_PATH', 'TSW_TRAEFIK_TLS_CERT_SECRET_NAME',
            'TSW_TRAEFIK_IMAGE', 'TSW_APPROVE_LIVE', 'TSW_SERVICE_PROFILE', 'TSW_SELECTION', 'TSW_UNKNOWN',
            'TSW_REDIS_PASSWORD')
        for key in forbidden:
            with self.subTest(key=key), self.assertRaises(ValueError) as caught:
                suite.operator_credentials((key + '=do-not-echo-this-value').encode())
            self.assertNotIn('do-not-echo-this-value', str(caught.exception))
        with self.assertRaises(ValueError):
            suite.operator_credentials(b'TSW_TRAEFIK_GUI_USERS_HTPASSWD=admin:plaintext')

    def test_native_operator_checksum_parses_same_verified_bytes_once(self) -> None:
        raw = b'TSW_PORTAINER_ADMIN_PASSWORD=only-for-test'
        current = replace(intent(), operator_config_sha256=native.digest(raw))
        with patch.object(native, 'read_private', return_value=raw) as read:
            self.assertEqual(suite.operator_values(current), {'TSW_PORTAINER_ADMIN_PASSWORD': 'only-for-test'})
        read.assert_called_once_with(suite.OPERATOR)
        with patch.object(native, 'read_private', return_value=raw + b'changed'), patch.object(suite, 'operator_credentials') as parse:
            with self.assertRaisesRegex(native.MaintenanceError, 'SUITE_CONFIGURATION_DRIFT'):
                suite.operator_values(current)
        parse.assert_not_called()

    def test_native_bad_operator_blocks_popen_and_fixed_tls_never_falls_back_to_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            with patch.object(native, 'private_directory'):
                journal = native.Journal(root)
            port = suite.SuiteNativePort(intent(), journal)
            with patch.object(suite, 'operator_values', side_effect=native.MaintenanceError('SUITE_OPERATOR_VALUES_INVALID')), patch.object(suite.subprocess, 'Popen') as popen:
                with self.assertRaisesRegex(native.MaintenanceError, 'SUITE_OPERATOR_VALUES_INVALID'):
                    port.child([sys.executable, '-c', 'pass'], 10)
            popen.assert_not_called()
            with patch.object(native, 'private_directory') as guard:
                tls = suite.case_tls_root(journal)
            guard.assert_called_once_with(root)
            from tiny_swarm_world.infrastructure.adapters.ingress.tls_state import canonical_tls_state_root
            with patch.object(Path, 'home', side_effect=AssertionError('original TLS fallback')):
                self.assertEqual(canonical_tls_state_root({'TSW_LOCAL_TLS_STATE_ROOT': tls}), root / 'tls')
            outside = root / 'outside'
            outside.mkdir()
            (root / 'tls').symlink_to(outside, target_is_directory=True)
            with patch.object(native, 'private_directory'), self.assertRaisesRegex(native.MaintenanceError, 'SUITE_TLS_ROOT_UNSAFE'):
                suite.case_tls_root(journal)

    def test_paired_actual_target_hosts_not_just_platform_labels_and_distinct_artifacts(self) -> None:
        proof, artifacts, code = capability_pair()
        self.assertEqual(suite.validate_host_artifacts(proof, '1' * 64, native.digest(code), artifacts),
                         {'native_linux': 'b' * 40, 'wsl2': 'b' * 40})
        for kind in ('copied-native', 'wrong-host', 'missing-host', 'source', 'fixture'):
            proof, artifacts, code = altered_capability(kind, '1' * 64)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                suite.validate_host_artifacts(proof, '1' * 64, native.digest(code), artifacts)

    def test_actual_native_prerequisite_path_rejects_host_and_admission_source_mismatch(self) -> None:
        for kind in ('valid', 'copied-native', 'wrong-host', 'missing-host', 'source', 'fixture', 'entry-code', 'artifact-code'):
            current = replace(intent(), capability_sha256=native.digest(b'cap'), operator_config_sha256=native.digest(b'op'))
            proof, artifacts, code = altered_capability(kind, current.capability_sha256)
            entry = SimpleNamespace(fixture_sha256=native.digest(code), fixture_source_revision='e' * 40,
                                    client_version='6.0.5', server_version='6.0.5')
            admission = SimpleNamespace(admits=lambda *_: True, admitted_versions=(entry,))
            repository = SimpleNamespace(IncusProfileCapabilityRepository=lambda _: SimpleNamespace(load=lambda: admission))
            resources = SimpleNamespace(selection=Mock(), read_config=Mock(return_value=b'config'))
            cap = Mock()
            cap.lstat.return_value = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o600, st_size=3)
            cap.is_file.return_value = True
            cap.is_symlink.return_value = False
            cap.read_bytes.return_value = b'cap'
            def read(path: Path) -> bytes:
                if path.name == 'both-host-profile-capability.json':
                    return native.canonical(proof)
                if path.name.startswith('profile-capability-'):
                    return artifacts[path.name.removeprefix('profile-capability-').removesuffix('.json')]
                return b'op'
            def blob(argv: list[str], _timeout: int) -> bytes:
                revision = argv[-1].split(':')[0]
                return b'wrong' if kind == 'entry-code' and revision == 'e' * 40 or kind == 'artifact-code' and revision == 'b' * 40 else code
            with self.subTest(kind=kind), patch.object(suite, 'CAPABILITY', cap), patch.object(native, 'read_private', side_effect=read), patch.object(suite.importlib, 'import_module', side_effect=lambda name: repository if name.endswith('incus_profile_capability_repository') else resources), patch.object(native, 'bounded', side_effect=blob), patch.object(suite, 'tree_digest', return_value=current.infra_sha256), patch.object(suite, 'operator_values', return_value={}):
                if kind == 'valid':
                    suite.check_prerequisites(current)
                    resources.selection.assert_called_once()
                else:
                    with self.assertRaises(native.MaintenanceError):
                        suite.check_prerequisites(current)

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

    def test_real_native_case_path_keeps_resource_version_preview_and_consent_before_live(self) -> None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
        from tiny_swarm_world.domain.lifecycle.selection import plan_selection
        from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest
        from tiny_swarm_world.application.services.profile_setup import proxy_routes_from_setup_manifest

        root = Path(__file__).resolve().parents[4]
        plan = plan_selection(NativeComponentCatalog(root).load(), minimal=True)
        manifest = default_setup_manifest(service_profile=plan.service_preset,
            resolved_services=plan.resolved_services, service_exposure=plan.service_exposure)
        preview = native.canonical({'status': 'selection_preview', 'plan': plan.model_dump(mode='json'),
            'routes': {'before': [], 'runtime_observed': False, 'listen_address': '127.0.0.1',
                       'after': [row.model_dump(mode='json') for row in proxy_routes_from_setup_manifest(manifest, '127.0.0.1')]},
            'execution': 'not-started', 'data_policy': 'preserve'})
        for mode in ('ready', 'resource', 'version', 'preview'):
            with self.subTest(mode=mode):
                events: list[str] = []
                journal = Mock()
                port = suite.SuiteNativePort(intent(), journal, proposal())
                port.baseline = baseline()
                resource = {'checks': {'incus_version': False, 'structured_service_access_preflight': mode != 'resource'}, 'observed': {}}
                version = b'Client version: 6.0.5\nServer version: 6.0.5\n' if mode != 'version' else b'Client version: 6.0.4\nServer version: 6.0.5\n'
                admission = {'server_version': '6.0.5'}

                def public(args: list[str], timeout: int) -> bytes:
                    del timeout
                    self.assertEqual(args[:2], ['setup', 'run'])
                    events.append('preview' if '--preview' in args else 'live')
                    return (b'{}' if mode == 'preview' else preview) if '--preview' in args else b'{}'

                with patch.object(port, 'start_pause_budget'), patch.object(port, 'check_binding'), \
                        patch.object(port, 'interpreter', return_value='/trusted/python'), \
                        patch.object(port, 'command', return_value=native.canonical(resource)), \
                        patch.object(port, 'capture', return_value=({'incus_admission': {'initial': admission, 'final': admission}}, Mock())), \
                        patch.object(port, 'incus_env', return_value={}), \
                        patch.object(native.inventory, 'Runner', return_value=SimpleNamespace(run=Mock(return_value=(0, version, b'')))), \
                        patch.object(port, 'route_capture', return_value={'routes': 'unchanged'}), \
                        patch.object(port, 'public', side_effect=public), \
                        patch.object(port, 'child', side_effect=AssertionError('Whole-bootstrap actor facade must not enter the scoped case')) as child, \
                        patch.object(port, 'await_activation', side_effect=lambda *_: events.append('consent')) as activation, \
                        patch.object(port, 'phase'), patch.object(port, 'prepare_disposal'), \
                        patch.object(port, 'listeners_clear', return_value=True), \
                        patch.object(port, 'observe_completion', side_effect=lambda: events.append('verified')):
                    if mode == 'ready':
                        port.run_fixture()
                        self.assertEqual(events, ['preview', 'consent', 'live', 'verified'])
                        activation.assert_called_once()
                        self.assertTrue(port.restore_safe)
                    else:
                        with self.assertRaises(native.MaintenanceError):
                            port.run_fixture()
                        activation.assert_not_called()
                        self.assertNotIn('live', events)
                        self.assertEqual(events, ['preview'] if mode == 'preview' else [])
                    child.assert_not_called()

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
            injected = {key: '/do-not-use/original' for key in ('TSW_REPOSITORY_ROOT', 'TSW_INFRA_ROOT',
                'TSW_INSTALL_ENV_FILE', 'TSW_LIVE_EVIDENCE_ROOT', 'TSW_LOCAL_TLS_STATE_ROOT')}
            injected['TSW_PORTAINER_ADMIN_PASSWORD'] = 'only-for-test'
            with patch.object(port, 'interpreter', return_value=sys.executable), patch.object(suite, 'operator_values', return_value=injected), patch.object(suite, 'case_tls_root', return_value=str(root / 'tls')):
                code = ('from pathlib import Path;import sys,os;'
                    'assert len(list(Path(sys.argv[1]).glob("child-*-pid.json")))==1;'
                    'assert os.environ["TSW_REPOSITORY_ROOT"]==sys.argv[2];'
                    'assert os.environ["TSW_INFRA_ROOT"]==sys.argv[3];'
                    'assert os.environ["TSW_INSTALL_ENV_FILE"]==sys.argv[4];'
                    'assert os.environ["TSW_LIVE_EVIDENCE_ROOT"]==sys.argv[1];'
                    'assert os.environ["TSW_LOCAL_TLS_STATE_ROOT"]==str(Path(sys.argv[1])/"tls");'
                    'assert os.environ["TSW_PORTAINER_ADMIN_PASSWORD"]=="only-for-test";'
                    'sys.stderr.write("private-not-exported");print("safe-child")')
                output = port.child([sys.executable, '-c', code, str(root), str(suite.ROOT), str(suite.INFRA), str(suite.OPERATOR)], 10)
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





class ActualProductRefusalEntryTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_public_consent_stops_before_composition_for_eof_and_literal_n(self):
        from contextlib import redirect_stdout
        import io
        from tiny_swarm_world.infrastructure.adapters.cli.dispatcher import main
        for name, spec in suite.upgrades.REFUSALS.items():
            if spec.cause != 'CONSENT':
                continue
            output = io.StringIO()
            def decline(prompt):
                print(prompt, end='')
                if spec.stdin_mode == 'EOF':
                    raise EOFError
                return 'n'
            with self.subTest(case=name), redirect_stdout(output), patch('builtins.input', side_effect=decline), \
                    patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade') as build:
                with self.assertRaises(SystemExit) as stopped:
                    await main(list(spec.args))
                self.assertEqual(stopped.exception.code, 2)
                build.assert_not_called()
            actual = suite.upgrades.validate_refusal(name, list(spec.args), 2, output.getvalue().encode(), b'')
            self.assertEqual(actual['cause'], 'CONSENT_EOF' if spec.stdin_mode == 'EOF' else 'CONSENT_DECLINED_N')

    async def test_real_preview_checkpoint_guard_does_not_call_source_plan_or_recover(self):
        from contextlib import redirect_stdout
        import io
        from tiny_swarm_world.application.services.product_upgrade_preview import preview_product_upgrade
        from tiny_swarm_world.infrastructure.adapters.cli.dispatcher import main
        journal = Mock()
        journal.load.return_value = None
        installation = Mock()
        service = SimpleNamespace(journal=journal,
            preview=lambda target, recovery=False: preview_product_upgrade(installation, journal, target, recovery=recovery))
        spec = suite.upgrades.REFUSALS['refuse-product-checkpoint']
        output = io.StringIO()
        with redirect_stdout(output), patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade', return_value=service):
            with self.assertRaises(SystemExit) as stopped:
                await main(list(spec.args))
        self.assertEqual(stopped.exception.code, 1)
        installation.plan.assert_not_called()
        result = suite.upgrades.validate_refusal('refuse-product-checkpoint', list(spec.args), 1, output.getvalue().encode(), b'')
        self.assertEqual(result, {'status': 'blocked', 'cause': 'CHECKPOINT_ABSENT'})
        # A completed/matching checkpoint is preview metadata, never a proof of
        # recovery execution, runtime drift checks or a no-op.
        journal.load.return_value = SimpleNamespace(stage='completed', plan=SimpleNamespace(
            target=SimpleNamespace(product=SimpleNamespace(release='0.5.0')), preview=lambda: {'status': 'preview'}))
        self.assertEqual((await preview_product_upgrade(installation, journal, '0.5.0'))['status'], 'verification_required')
        with self.assertRaises(suite.upgrades.UpgradeError):
            suite.upgrades.validate_refusal('refuse-product-checkpoint', list(spec.args), 0,
                b'{"status":"verification_required"}\n', b'')

    async def test_real_source_guards_preserve_distinct_dirty_origin_and_root_causes(self):
        from contextlib import redirect_stdout
        import io
        from tiny_swarm_world.application.services.product_upgrade_preview import preview_product_upgrade
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission import _clean_source
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OFFICIAL_REPOSITORY
        from tiny_swarm_world.infrastructure.adapters.cli.dispatcher import main
        name = 'refuse-product-source'
        args = list(suite.upgrades.REFUSALS[name].args)
        for fault, expected in (('dirty', 'SOURCE_DIRTY'), ('origin', 'SOURCE_ORIGIN'), ('root', 'SOURCE_ROOT')):
            root = Path('/synthetic-owned-source')
            def command(command):
                if command[:2] == ('git', 'status'):
                    return ' M changed.py' if fault == 'dirty' else ''
                if command[:3] == ('git', 'rev-parse', '--show-toplevel'):
                    return '/different-root' if fault == 'root' else str(root)
                return 'https://unofficial.invalid/repository' if fault == 'origin' else OFFICIAL_REPOSITORY
            installation = SimpleNamespace(root=root, _command=command)
            installation.plan = lambda target: _clean_source(installation, allow_external=True)
            journal = Mock()
            journal.load.return_value = None
            service = SimpleNamespace(journal=journal,
                preview=lambda target, recovery=False: preview_product_upgrade(installation, journal, target, recovery=recovery))
            output = io.StringIO()
            with self.subTest(fault=fault), redirect_stdout(output), \
                    patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade', return_value=service):
                with self.assertRaises(SystemExit) as stopped:
                    await main(args)
            self.assertEqual(stopped.exception.code, 1)
            self.assertEqual(suite.upgrades.validate_refusal(name, args, 1, output.getvalue().encode(), b'')['cause'], expected)

    async def test_actual_config_refusal_precedes_source_until_fixed_official_preview_mode(self):
        from contextlib import redirect_stdout
        import hashlib
        import io
        import os
        from tiny_swarm_world.application.services.product_upgrade import ProductUpgradeService
        from tiny_swarm_world.infrastructure.adapters.cli.dispatcher import main
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_installation import PreparedProductInstallation
        from tiny_swarm_world.infrastructure.adapters.lifecycle import product_configuration_source as configuration
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_validation import validate_policy
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OFFICIAL_REPOSITORY
        from modules.tsw_core.tests.domain.lifecycle.test_models import manifest_fixture
        from tiny_swarm_world.domain.lifecycle.models import ProductIdentity, migrate_manifest_v1
        name = 'refuse-product-source'
        args = list(suite.upgrades.REFUSALS[name].args)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'pyproject.toml').write_text('[project]\nversion="0.2.0"\n')
            (root / 'requirements.lock').write_bytes(b'synthetic-source-lock')
            infra = root.parent / (root.name + '-private-infra')
            operator = infra / 'operator.env'
            manifest = migrate_manifest_v1(manifest_fixture()).model_copy(update={'product': ProductIdentity(
                release='0.2.0', revision='e' * 40, dependency_lock='sha256:' + hashlib.sha256(b'synthetic-source-lock').hexdigest())})
            manifests = Mock()
            manifests.load.return_value = SimpleNamespace(manifest=manifest, token='a' * 64, diagnostics=())
            releases, runtime, journal = Mock(), Mock(), Mock()
            journal.load.return_value = None
            installation = PreparedProductInstallation(root, manifests, Mock(), releases, Mock())
            def command(command):
                if command[:2] == ('git', 'status'):
                    return ''
                if command[:3] == ('git', 'rev-parse', '--show-toplevel'):
                    return str(root)
                if command[:3] == ('git', 'remote', 'get-url'):
                    return OFFICIAL_REPOSITORY
                return 'e' * 40
            official = SimpleNamespace(files={'config/provider.yaml': b'official'}, members={})
            effective = SimpleNamespace(files={'config/provider.yaml': b'official', 'operator.env': b'PRIVATE_CANARY'}, members={})
            def external_inputs(_installation, path):
                self.assertEqual(path, infra)
                return validate_policy(official, effective)
            service = ProductUpgradeService(manifests, installation, journal, runtime)
            inherited = {'TSW_REPOSITORY_ROOT': str(root), 'TSW_INFRA_ROOT': str(infra), 'TSW_INSTALL_ENV_FILE': str(operator)}
            for mode in ('inherited-private', 'fixed-official'):
                env = dict(inherited)
                if mode == 'fixed-official':
                    selected = suite.upgrades.select_refusal_environment(name, args, env, root, infra, operator)
                    self.assertEqual(selected['infra_mode'], 'OFFICIAL_INFRA_READ_ONLY')
                    self.assertEqual(env['TSW_INSTALL_ENV_FILE'], str(operator))
                output = io.StringIO()
                with self.subTest(mode=mode), redirect_stdout(output), patch.dict(os.environ, env), \
                        patch.object(installation, '_command', side_effect=command), \
                        patch.object(configuration, '_source_tree', side_effect=external_inputs), \
                        patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade', return_value=service):
                    with self.assertRaises(SystemExit) as stopped:
                        await main(args)
                self.assertEqual(stopped.exception.code, 1)
                if mode == 'inherited-private':
                    self.assertIn('Effective infrastructure is unsafe', output.getvalue())
                    with self.assertRaises(suite.upgrades.UpgradeError):
                        suite.upgrades.validate_refusal(name, args, 1, output.getvalue().encode(), b'')
                else:
                    self.assertEqual(suite.upgrades.validate_refusal(name, args, 1, output.getvalue().encode(), b'')['cause'], 'SOURCE_INVENTORY')
                releases.resolve.assert_not_called()
                self.assertEqual(runtime.mock_calls, [])
            self.assertFalse((root / '.tiny-swarm-world').exists())
            self.assertEqual(inherited['TSW_INFRA_ROOT'], str(infra))

    def test_native_public_refusal_routes_only_closed_case_to_the_existing_transport(self):
        case_name = 'refuse-product-consent-n'
        port = suite.SuiteNativePort(replace(intent(), case=case_name), Mock(), None)
        args = list(suite.upgrades.REFUSALS[case_name].args)
        with patch.object(port, 'public', return_value=b'bounded') as public:
            self.assertEqual(port.public_refusal(args, timeout=120), b'bounded')
            public.assert_called_once_with(args, 120, refusal_case=case_name)
            with self.assertRaises(suite.upgrades.UpgradeError):
                port.public_refusal([*args, '--approve-live'], timeout=120)
            self.assertEqual(public.call_count, 1)


if __name__ == '__main__':
    unittest.main()

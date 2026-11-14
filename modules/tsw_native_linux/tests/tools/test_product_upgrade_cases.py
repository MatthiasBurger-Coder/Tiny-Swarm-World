"""Closed qualification orchestration; no host effects or compatibility claims."""
from __future__ import annotations

import asyncio
from contextlib import ExitStack
import copy
import json
import stat
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from modules.tsw_native_linux.tools.qualification import product_upgrade_cases as cases


def proof():
    return {key: {} for key in ('node_ids', 'service_ids', 'mounts', 'data', 'owner_ids', 'exposure',
            'service_versions', 'tasks', 'managed_journals', 'stack_updates')} | {
        'status': 'UPGRADE_RUNTIME_VERIFIED', 'installation_id': 'actual-installation',
        'swarm_id': 'actual-swarm', 'preset': 'default', 'backup_journal': None,
        'manifest_sha256': 'a' * 64, 'manifest_token': 'a' * 64, 'component_journal_sha256': None}


class Transport:
    """Fake public transport; the fixture orchestration itself is real."""
    def __init__(self, case='upgrade-swagger-swarm', *, missed=False):
        self.intent = SimpleNamespace(case=case, run_id='a' * 32, source_commit='b' * 40)
        self.worker_settled = True
        self.upgrade_baseline = False
        self.upgrade_fault_observed = False
        self.calls = []
        self.records = []
        self.missed = missed

    def upgrade_validate_inputs(self):
        self.calls.append(('inputs',))

    def event(self, stage, value):
        self.records.append((stage, value))

    def upgrade_helper(self, stage):
        self.calls.append(('proof', stage))
        return proof()

    def public(self, args, *, timeout):
        self.calls.append((tuple(args), timeout, self.upgrade_baseline))
        if getattr(self, 'upgrade_fault_armed', False) and not self.missed:
            self.upgrade_fault_observed = True
            raise cases.FaultObserved('UPGRADE_ACTUAL_FAULT_OBSERVED')
        status = 'preview' if '--preview' in args else 'recovered' if '--recover' in args else 'completed'
        return json.dumps({'status': status}).encode()


class ClosedRecipeTests(unittest.TestCase):
    def test_one_owned_baseline_runs_single_recovery_then_both_change_batch(self):
        port = Transport('upgrade-batch-default-swarm-internal')
        cases.run(port)
        updates = [row[0] for row in port.calls if isinstance(row[0], tuple)
                   and row[0][:2] == ('services', 'update') and '--preview' not in row[0]]
        self.assertEqual([(args[args.index('--services') + 1], '--recover' in args) for args in updates],
                         [('swagger', False), ('swagger', True), ('swagger,traefik', False), ('swagger,traefik', False)])
        self.assertEqual(updates[0][updates[0].index('--to') + 1], 'swagger-ui-5-32-7')
        self.assertNotIn('--to', updates[1])
        self.assertIn((('services', 'list', '--json'), 120, False), port.calls)
        self.assertEqual([row[1] for row in port.calls if row[0] == 'proof'],
                         ['source', 'single-target', 'recovered', 'target', 'noop', 'persistent'])
        setup = [row for row in port.calls if isinstance(row[0], tuple) and row[0][:2] == ('setup', 'run')]
        self.assertEqual([row[2] for row in setup], [True, False])
        # The public single preview and recovery preview must precede their writes.
        public = [row[0] for row in port.calls if isinstance(row[0], tuple)]
        single = cases.UpgradeRecipe(('swagger',), exposure='internal')
        for preview, live in ((single.update(preview=True), single.update()),
                              (single.update(preview=True, recover=True), single.update(recover=True))):
            self.assertLess(public.index(tuple(preview)), public.index(tuple(live)))

    def test_single_partial_failure_or_unverified_mixed_state_never_starts_batch(self):
        for failure in ('partial', 'proof'):
            with self.subTest(failure=failure):
                port = Transport('upgrade-batch-default-swarm-internal')
                original = port.public
                def public(args, *, timeout):
                    result = original(args, timeout=timeout)
                    if failure == 'partial' and args[:2] == ['services', 'update'] and '--preview' not in args:
                        return json.dumps({'status': 'partial'}).encode()
                    return result
                helper = port.upgrade_helper
                def observe(stage):
                    return {'status': 'UNVERIFIED'} if failure == 'proof' and stage == 'single-target' else helper(stage)
                with patch.object(port, 'public', side_effect=public), patch.object(port, 'upgrade_helper', side_effect=observe):
                    with self.assertRaisesRegex(cases.UpgradeError, 'SINGLE_APPLY_FAILED|PROOF_UNAVAILABLE'):
                        cases.run(port)
                self.assertFalse(any(isinstance(row[0], tuple) and 'swagger,traefik' in row[0]
                                     and row[0][:2] == ('services', 'update') for row in port.calls))
                self.assertFalse(any(name == 'upgrade-accepted' for name, _ in port.records))

    def test_mixed_single_target_uses_actual_target_swagger_and_source_traefik(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
        definitions = {item.service_id: item for item in NativeComponentCatalog(cases.ROOT).load().services}
        value = cases.recipe('upgrade-batch-default-swarm-internal')
        for name in value.services:
            definition = definitions[name]
            mixed = cases._expected_component_versions(value, name, definition, 'single-target')
            policy = definition.update_transitions[0]
            target = next(item.versions for item in definition.update_targets if item.target_id == policy.target_id)
            self.assertEqual(mixed, target if name == 'swagger' else policy.source_versions)
            self.assertNotEqual(policy.source_versions, target)
            self.assertEqual(cases._expected_component_versions(value, name, definition, 'recovered'), policy.source_versions)
            self.assertEqual(cases._expected_component_versions(value, name, definition, 'target'), target)
        with self.assertRaisesRegex(cases.UpgradeError, 'UPGRADE_PROOF_STAGE'):
            cases.read_runtime('upgrade-batch-default-portainer-published', 'single-target')

    def test_complete_cartesian_coverage_and_preset_only_on_setup(self):
        rows = [(r.preset, r.owner, r.exposure) for name, r in cases.RECIPES.items() if name.startswith('upgrade-batch-')]
        self.assertEqual(set(rows), {(p, o, e) for p in ('default', 'service-access')
            for o in ('swarm', 'portainer') for e in ('published', 'internal')})
        self.assertEqual(len(cases.ALL_NAMES), 36)
        for name in cases.RECIPES:
            if cases.RECIPES[name].kind == 'product':
                with self.assertRaisesRegex(cases.UpgradeError, 'NOT_IMPLEMENTED'):
                    cases.recipe(name)
                continue
            if name in cases.REFUSALS:
                self.assertEqual(cases.recipe(name).kind, 'refusal')
                self.assertIn('--minimal', cases.recipe(name).args())
                self.assertNotIn('--approve-live', cases.REFUSALS[name].args)
                continue
            value = cases.recipe(name)
            setup = value.args()
            self.assertEqual(setup[setup.index('--service-profile') + 1], value.preset)
            for args in (value.update(), value.update(preview=True), value.update(recover=True)):
                self.assertNotIn('--service-profile', args)
                self.assertNotIn('--stack-owner', args)
            self.assertNotIn('--to', value.update(recover=True))
        self.assertNotIn('--swagger-exposure', cases.recipe('upgrade-traefik-swarm').args())

    def test_exact_containing_budgets_and_disposal_recovery_stays_900(self):
        for case, forward, recovery in (('upgrade-swagger-swarm', 10500, 4800), ('upgrade-product-v1', 19500, 12300)):
            for engine, expected in ((False, forward), (True, recovery)):
                wsl = cases.budgets(case, 'wsl', engine_recovery=engine)
                native = cases.budgets(case, 'native', engine_recovery=engine)
                self.assertEqual(sum(wsl[k] for k in ('admit', 'case', 'disposal', 'final')), expected)
                self.assertEqual(sum(native.values()), expected + 1980)
                self.assertEqual(wsl['recover'], 900)
        self.assertEqual(cases.budgets('minimal', 'wsl')['case'], 5400)
        self.assertEqual(sum(cases.budgets('minimal', 'native').values()), 8880)

    def test_real_baseline_and_recovery_order_never_turns_missed_fault_into_pass(self):
        port = Transport('recover-batch-portainer')
        cases.run(port)
        self.assertEqual(port.calls[0], ('inputs',))
        baseline = next(row for row in port.calls if isinstance(row[0], tuple) and row[0][:2] == ('setup', 'run'))
        self.assertTrue(baseline[2])
        writers = [row for row in port.calls if isinstance(row[0], tuple) and row[0][:2] == ('services', 'update') and '--preview' not in row[0]]
        self.assertEqual([('--recover' in row[0], row[2]) for row in writers], [(False, False), (True, False), (True, False)])
        self.assertEqual(port.records[-1][0], 'upgrade-accepted')
        missed = Transport('recover-batch-portainer', missed=True)
        with self.assertRaisesRegex(cases.UpgradeError, 'NOT_EXERCISED'):
            cases.run(missed)
        self.assertFalse(any(name == 'upgrade-accepted' for name, _ in missed.records))
        self.assertFalse(any(isinstance(row[0], tuple) and '--recover' in row[0] for row in missed.calls))

    def test_fault_monitor_requires_matching_real_checkpoint_before_own_signal(self):
        port = Transport('recover-portainer')
        port.upgrade_before = proof()
        port.upgrade_fault_armed = True
        child = Mock(pid=12345, poll=Mock(return_value=None))
        state = SimpleNamespace(installation_id='foreign', backup_digest='a' * 64, stage='upgrading',
                                model_dump=lambda **_: {'stage': 'upgrading'})
        with patch.object(cases, 'checkpoint', return_value=state), patch.object(cases.os, 'killpg') as signal:
            with self.assertRaisesRegex(cases.UpgradeError, 'INSTALLATION_DRIFT'):
                cases.poll_fault(port, child)
            signal.assert_not_called()
            state.installation_id = 'actual-installation'
            state.backup_digest = None
            cases.poll_fault(port, child)
            signal.assert_not_called()
            state.backup_digest = 'a' * 64
            with self.assertRaises(cases.FaultObserved):
                cases.poll_fault(port, child)
            signal.assert_called_once_with(child.pid, cases.signal.SIGTERM)
        self.assertEqual(port.records[-1][0], 'upgrade-fault-intent')
        self.assertFalse(port.upgrade_fault_armed)

    def test_four_closed_fault_cases_preserve_old_sigterm_and_bind_distinct_sigint(self):
        new = ('recover-batch-swarm-sigint', 'recover-batch-portainer-sigint',
               'recover-portainer-sigint', 'recover-portainer-api-down')
        self.assertEqual(cases.ALL_NAMES[-4:], new)
        self.assertTrue(all(cases.recipe(name).interrupt for name in new))
        self.assertTrue(cases.recipe(new[-1]).api_down)
        self.assertFalse(any(cases.recipe(name).interrupt for name in ('recover-batch-swarm', 'recover-batch-portainer', 'recover-portainer')))
        for fault in ('valid', 'checkpoint', 'process', 'expired', 'source'):
            with self.subTest(fault=fault):
                port = Transport('recover-portainer-sigint')
                port.upgrade_before = proof()
                port.upgrade_fault_armed = True
                port.deadline = 0 if fault == 'expired' else time.monotonic() + 120
                port.proposal = {'pins': {'actual': 'source'}, 'identity': {'actual': 'guest'}}
                port.source = Mock(return_value={} if fault == 'source' else port.proposal['pins'])
                port.identity = Mock(return_value=port.proposal['identity'])
                port.reserve = Mock()
                journal = Mock()
                binding = {'platform': 'wsl', 'proposal_sha256': 'a' * 64, 'approval': {'phase': 'wsl-case-run'}, 'activation': None}
                args = cases.recipe(port.intent.case).update()
                receipt = cases.CliReceipt(journal, 'child-' + 'a' * 32, binding, [], args,
                    released=True, process={'pid': 12345, 'start_time': 99})
                state = SimpleNamespace(installation_id='actual-installation', stage='upgrading',
                    operation_id='a' * 32, backup_digest='sha256:' + 'b' * 64,
                    model_dump=Mock(return_value={'actual': 'checkpoint'}))
                changed = SimpleNamespace(model_dump=lambda **_: {'changed': 'checkpoint'})
                states = [state, changed] if fault == 'checkpoint' else [state, state, state]
                identity = {'pid': 12345, 'start_time': 100 if fault == 'process' else 99}
                with patch.object(cases, 'checkpoint', side_effect=states), \
                        patch.object(cases, 'process_identity', return_value=identity), \
                        patch.object(cases.os, 'getpgid', return_value=12345), \
                        patch.object(cases.os, 'getsid', return_value=12345), patch.object(cases.os, 'killpg') as sent:
                    if fault == 'valid':
                        with self.assertRaises(cases.FaultObserved) as observed:
                            cases.poll_fault(port, Mock(pid=12345, poll=Mock(return_value=None)),
                                before_signal=receipt.prepare_fault, receipt=receipt)
                        fault_receipt = observed.exception.receipt
                        assert fault_receipt is not None
                        self.assertEqual(fault_receipt['signal'], 2)
                        self.assertEqual(fault_receipt['operation_id'], 'a' * 32)
                        sent.assert_called_once_with(12345, 2)
                        journal.save.assert_called_once()
                    elif fault == 'checkpoint':
                        cases.poll_fault(port, Mock(pid=12345, poll=Mock(return_value=None)),
                            before_signal=receipt.prepare_fault, receipt=receipt)
                        sent.assert_not_called()
                        journal.save.assert_not_called()
                    else:
                        with self.assertRaises(cases.UpgradeError):
                            cases.poll_fault(port, Mock(pid=12345, poll=Mock(return_value=None)),
                                before_signal=receipt.prepare_fault, receipt=receipt)
                        sent.assert_not_called()
                        journal.save.assert_not_called()

    def test_noop_and_preservation_check_actual_runtime_counters(self):
        before = proof()
        for key in before:
            if key == 'status':
                continue
            changed = copy.deepcopy(before)
            changed[key] = 'changed'
            with self.subTest(key=key), self.assertRaises(cases.UpgradeError):
                cases.preserve(before, changed, no_op=True)

    def test_retained_sibling_commit_is_not_a_partial_image_transition(self):
        port = Transport('recover-batch-swarm')
        port.upgrade_before = proof()
        port.upgrade_fault_armed = True
        first = SimpleNamespace(outcome='committed', source='same', target='same')
        second = SimpleNamespace(outcome='applying', source='old', target='new')
        state = SimpleNamespace(direction='apply', original=SimpleNamespace(installation_id='actual-installation'),
            stages=(first, second), model_dump=lambda **_: {'actual': 'checkpoint'})
        with patch.object(cases, 'checkpoint', return_value=state), patch.object(cases.os, 'killpg') as signal:
            cases.poll_fault(port, Mock(pid=12345, poll=Mock(return_value=None)))
            signal.assert_not_called()
            first.source = 'old'
            with self.assertRaises(cases.FaultObserved):
                cases.poll_fault(port, Mock(pid=12345, poll=Mock(return_value=None)))
            signal.assert_called_once()

    def test_noop_protected_bytes_detect_metadata_rewrites_and_first_transition_allows_commit(self):
        before = proof()
        for field in ('manifest_sha256', 'manifest_token', 'component_journal_sha256'):
            after = before | {field: 'b' * 64}
            cases.preserve(before, after)
            with self.subTest(field=field), self.assertRaisesRegex(cases.UpgradeError, 'UPGRADE_NOOP_MUTATION'):
                cases.preserve(before, after, no_op=True)
        raw = b'{ \"same_model\": true }\n'
        with patch.object(cases, 'private_bytes', return_value=raw):
            self.assertEqual(cases.private_file_hash(Path('/private/manifest.json')), cases.hashlib.sha256(raw).hexdigest())
        with patch.object(Path, 'lstat', side_effect=OSError('unsafe link')):
            with self.assertRaises(OSError):
                cases.private_file_hash(Path('/private/checkpoint.json'), optional=True)

    def test_exact_source_bundles_come_from_real_catalog_and_never_operator_values(self):
        result = cases.baseline_environment('upgrade-batch-default-portainer-internal')
        self.assertEqual(len(result), 5)
        self.assertTrue(all('@sha256:' in image for image in result.values()))
        self.assertTrue(all(name.endswith('_IMAGE') for name in result))
        gateway = cases.baseline_environment('upgrade-portainer')
        self.assertIn('TSW_PORTAINER_IMAGE', gateway)
        self.assertIn('TSW_PORTAINER_AGENT_IMAGE', gateway)
        self.assertEqual(len(gateway), 6)

    def test_proof_input_exact_schema_username_and_no_operator_key_expansion(self):
        valid = {'schema_version': 1, 'traefik_username': 'fixture', 'traefik_password': 'PRIVATE_CANARY'}
        with patch.object(cases, 'private_json', return_value=valid) as read:
            self.assertEqual(cases.proof_credentials('upgrade-traefik-swarm', Path('/private/infra'),
                {'TSW_TRAEFIK_GUI_USERS_HTPASSWD': 'fixture:$2y$12$' + 'a' * 53}), ('fixture', 'PRIVATE_CANARY'))
            read.assert_called_once_with(Path('/private/infra/proof-credentials.json'), limit=1024)
            for bad in (valid | {'source': 'foreign'}, valid | {'schema_version': True}, valid | {'traefik_password': ''},
                        valid | {'traefik_username': 'other'}):
                read.return_value = bad
                with self.assertRaises(cases.UpgradeError):
                    cases.proof_credentials('upgrade-traefik-swarm', Path('/private/infra'), {'TSW_TRAEFIK_GUI_USERS_HTPASSWD': 'fixture:hash'})

    def test_actual_https_probe_demands_challenge_auth_api_tls_and_no_redirects(self):
        import requests
        class Response:
            def __init__(self, status, body):
                self.status_code, self.body = status, body
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return None
            def iter_content(self, _size):
                yield self.body
        http = Mock()
        http.__enter__ = Mock(return_value=http)
        http.__exit__ = Mock(return_value=None)
        overview = json.dumps({'routers': {'dashboard@file': {'rule': 'Host(`traefik.tsw.local`)',
            'service': 'api@internal', 'status': 'enabled'}}, 'services': {}, 'middlewares': {}}).encode()
        def attributes(path):
            return SimpleNamespace(st_mode=(stat.S_IFREG | 0o600) if path.name == 'ca-bundle.pem' else (stat.S_IFDIR | 0o755),
                st_uid=0, st_nlink=1, st_size=100)
        with patch.object(requests, 'Session', return_value=http), patch.object(Path, 'lstat', attributes):
            http.get.side_effect = [Response(401, b''), Response(200, overview), Response(200, b'<title>Traefik</title>')]
            cases.authenticated_traefik(('fixture', 'PRIVATE_CANARY'), Path('/private/tls'))
            self.assertFalse(http.trust_env)
            for call in http.get.call_args_list:
                self.assertEqual(call.kwargs['verify'], '/private/tls/ca-bundle.pem')
                self.assertFalse(call.kwargs['allow_redirects'])
                self.assertEqual(call.kwargs['timeout'], (10, 10))
                self.assertNotIn('PRIVATE_CANARY', call.args[0])
            self.assertIsNone(http.get.call_args_list[0].kwargs['auth'])
            http.get.reset_mock()
            http.get.side_effect = [Response(401, b''), Response(401, b'private error')]
            with self.assertRaisesRegex(cases.UpgradeError, 'AUTH_FAILED') as error:
                cases.authenticated_traefik(('fixture', 'WRONG_PRIVATE_CANARY'), Path('/private/tls'))
            self.assertNotIn('PRIVATE', str(error.exception))
            self.assertEqual(http.get.call_count, 2)


class RealCoreDeliveryTests(unittest.TestCase):
    def test_fixture_drives_real_component_engine_observation_commit_and_repeat(self):
        # Existing boundary fixture composes real ComponentUpdateExecution,
        # ClassicComponentRuntime, ClassicUpdateWorkflow and JSON journals.
        # Only Docker/deployment transports and local lock port are fakes.
        from modules.tsw_core.tests.infrastructure.adapters.lifecycle import test_native_component_transitions as real
        core = real.NativeTransitionExecutionTests('test_batch_persistence_real_compose_artifacts_noop_and_original_recovery')
        core.setUp()
        self.addCleanup(core.doCleanups)
        outer = self
        class PublicPort(Transport):
            def public(self, args, *, timeout):
                self.calls.append((tuple(args), timeout, self.upgrade_baseline))
                if args[:2] != ['services', 'update']:
                    return b'{"status":"completed"}'
                selected = tuple(args[args.index('--services') + 1].split(','))
                if '--preview' in args:
                    return core.executor.planning.preview(selected).model_dump_json().encode()
                return json.dumps(asyncio.run(core.executor.run(selected, consent=real.CONSENT,
                    recovery='--recover' in args))).encode()
            def upgrade_helper(self, stage):
                current = core.manifests.load().manifest
                outer.assertIsNotNone(current)
                assert current is not None
                observed = proof()
                observed['installation_id'] = str(current.installation_id)
                observed['service_versions'] = {'writes': len(core.calls)}
                observed['manifest_sha256'] = cases.hashlib.sha256(core.manifests.path.read_bytes()).hexdigest()
                observed['manifest_token'] = core.manifests.load().token
                observed['component_journal_sha256'] = cases.hashlib.sha256(core.journal.path.read_bytes()).hexdigest() if core.journal.path.exists() else None
                if stage == 'target':
                    saved = core.journal.load()
                    assert saved is not None
                    outer.assertTrue(all(s.outcome == 'committed' for s in saved.stages))
                return observed
        port = PublicPort('upgrade-batch-default-swarm-published')
        cases.run(port)
        self.assertEqual([item.service_name for item in core.calls], ['swagger-ui', 'traefik'])
        saved = core.journal.load()
        assert saved is not None
        self.assertTrue(saved.settled)
        self.assertEqual(port.records[-1][0], 'upgrade-accepted')


class RealCacheDeliveryTests(unittest.TestCase):
    def setUp(self):
        from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import intent_fixture
        from modules.tsw_core.tests.infrastructure.adapters.clients.test_lxc_profile_lifecycle import instance_fixture, server_fixture
        from tiny_swarm_world.domain.lifecycle.profile_lifecycle import WorkerCreateIntent
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.args import scoped_node_config
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.observations import local_devices
        template = intent_fixture()
        workers = tuple(WorkerCreateIntent(node_name=name, image_fingerprint=template.image_fingerprint,
            base_profiles=template.base_profiles, network=template.network, storage_pool=template.storage_pool,
            cpu=1, memory='1GiB', disk='10GiB') for name in ('swarm-worker-1', 'swarm-worker-2'))
        template = template.model_copy(update={'workers': workers})
        manager_uuid = '11111111-1111-1111-1111-111111111111'
        worker_uuids = dict(zip((w.node_name for w in workers), ('22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333')))
        self.operation = SimpleNamespace(lease=Mock(), require_current_manifest=Mock(), admit_runtime=AsyncMock(), verify_effective_routes=AsyncMock())
        self.runner = cases.CacheRunner(self.operation, template, manager_uuid, worker_uuids, time.monotonic() + 900)
        self.rows = {'swarm-manager': instance_fixture(template, state='Running')}
        for worker in workers:
            config = scoped_node_config(template, worker) | {'volatile.base_image': worker.image_fingerprint,
                                                           'volatile.uuid': worker_uuids[worker.node_name]}
            self.rows[worker.node_name] = self.rows['swarm-manager'] | {'name': worker.node_name,
                'config': config, 'expanded_config': dict(config), 'profiles': list(worker.base_profiles),
                'devices': local_devices(worker), 'expanded_devices': local_devices(worker)}
        self.available = set()
        self.effects = []
        def transport(argv, timeout):
            self.effects.append((argv, timeout))
            node, image = argv[3], argv[-1]
            command = argv[argv.index('unix:///var/run/docker.sock') + 1:]
            if command[0] == 'pull':
                self.available.add((node, image))
                return subprocess.CompletedProcess(argv, 0, 'downloaded', '')
            if (node, image) not in self.available:
                return subprocess.CompletedProcess(argv, 1, '[]', 'Error response from daemon: No such image: ' + image)
            metadata = [{'Id': 'sha256:' + cases.hashlib.sha256(image.encode()).hexdigest(), 'RepoDigests': [image], 'Architecture': 'amd64', 'Os': 'linux'}]
            return subprocess.CompletedProcess(argv, 0, json.dumps(metadata), '')
        stack = self.enterContext(ExitStack())
        n = self.runner.inventory
        stack.enter_context(patch.object(n, '_systemctl_show', return_value={'main_pid': 100}))
        stack.enter_context(patch.object(n, '_resolve_executable', return_value=('incus_system', 'system:incus')))
        stack.enter_context(patch.object(n, '_endpoint', return_value=('incus_var_lib', True)))
        stack.enter_context(patch.object(n, '_require_full_local_access'))
        def detail(_runner, _prefix, kind, names, *_args, **_kwargs):
            return server_fixture() if kind == 'server-root' else self.rows[names[0]]
        stack.enter_context(patch.object(n, '_detail', side_effect=detail))
        stack.enter_context(patch.object(self.runner, 'process', side_effect=transport))
        stack.enter_context(patch('tiny_swarm_world.infrastructure.logging.logger_factory.LoggerFactory.get_logger', return_value=Mock()))

    def test_actual_artifact_workflow_ensure_publisher_guard_and_twelve_observations(self):
        from tiny_swarm_world.application.services.artifacts.workflows import ArtifactPrepareWorkflow, ArtifactWorkflowStatus
        before = {node + ':' + image: self.runner.image(node, image, absent=True)
                  for node in self.runner.nodes for image in self.runner.references}
        self.assertEqual(set(before.values()), {None})
        result = asyncio.run(ArtifactPrepareWorkflow(cases.cache_steps(self.operation, self.runner), requires_bootstrap=False).run())
        self.assertEqual(result.status, ArtifactWorkflowStatus.COMPLETED)
        after = {node + ':' + image: self.runner.image(node, image) for node in self.runner.nodes for image in self.runner.references}
        cases.verify_cache_nodes(after, self.runner.nodes, self.runner.references)
        self.assertEqual(len(after), 12)
        self.assertEqual(len(self.runner.pulled), 12)
        self.assertEqual(self.operation.admit_runtime.await_count, 24)
        for argv, timeout in self.effects:
            self.assertEqual(argv[:3], ['/usr/bin/incus', '--force-local', 'exec'])
            self.assertEqual(argv[4:9], ['--project', 'default', '--', '/usr/bin/env', '-i'])
            self.assertIn('unix:///var/run/docker.sock', argv)
            self.assertLessEqual(timeout, 60)
        self.assertGreater(self.operation.lease.require_active.call_count, 24)
        changed = copy.deepcopy(after)
        changed[next(iter(changed))]['id'] = 'sha256:' + '0' * 64
        with self.assertRaisesRegex(cases.UpgradeError, 'NODE_IMAGE_DRIFT'):
            cases.verify_cache_nodes(changed, self.runner.nodes, self.runner.references)

    def test_foreign_spec_denies_real_publisher_before_transport_and_host_probe_never_executes(self):
        from tiny_swarm_world.infrastructure.process import ProcessLaunchError
        image = self.runner.references[0]
        with self.assertRaises(ProcessLaunchError):
            self.runner.run_text(['docker', 'image', 'inspect', image], shell=False)
        self.assertEqual(self.effects, [])
        self.rows['swarm-manager']['config']['volatile.uuid'] = '99999999-9999-9999-9999-999999999999'
        with self.assertRaisesRegex(cases.UpgradeError, 'MANAGER_UUID'):
            self.runner.run_text(['incus', 'exec', 'swarm-manager', '--', 'sh', '-lc', 'docker pull ' + image], shell=False)
        self.assertEqual(self.effects, [])

    def test_one_pull_per_pair_and_aggregate_deadline_cannot_reset(self):
        image = self.runner.references[0]
        argv = ['incus', 'exec', 'swarm-manager', '--', 'sh', '-lc', 'docker pull ' + image]
        self.runner.run_text(argv, shell=False)
        count = len(self.effects)
        with self.assertRaisesRegex(cases.UpgradeError, 'REPLAY_DENIED'):
            self.runner.run_text(argv, shell=False)
        self.assertEqual(len(self.effects), count)
        self.runner.end = time.monotonic()
        with self.assertRaisesRegex(cases.UpgradeError, 'DEADLINE'):
            self.runner.run_text(['incus', 'exec', 'swarm-worker-1', '--', 'sh', '-lc', 'docker pull ' + image], shell=False)
        self.assertEqual(len(self.effects), count)

    def test_actual_workflow_cache_hit_has_no_pull_and_unknown_manifest_denies_before_exec(self):
        from tiny_swarm_world.application.services.artifacts.workflows import ArtifactPrepareWorkflow, ArtifactWorkflowStatus
        self.available = {(node, ref) for node in self.runner.nodes for ref in self.runner.references}
        result = asyncio.run(ArtifactPrepareWorkflow(cases.cache_steps(self.operation, self.runner), requires_bootstrap=False).run())
        self.assertEqual(result.status, ArtifactWorkflowStatus.COMPLETED)
        self.assertEqual(self.runner.pulled, set())
        count = len(self.effects)
        self.operation.require_current_manifest.side_effect = cases.UpgradeError('MANIFEST_CAS_CHANGED')
        with self.assertRaisesRegex(cases.UpgradeError, 'MANIFEST_CAS_CHANGED'):
            self.runner.image('swarm-manager', self.runner.references[0])
        self.assertEqual(len(self.effects), count)

    def test_unknown_cache_receipt_blocks_writer_and_disposal_across_restart(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'image-cache-intent.json').write_text('{}')
            port = SimpleNamespace(journal=SimpleNamespace(directory=directory), cache_unknown=False)
            with self.assertRaisesRegex(cases.UpgradeError, 'RECOVERY_REQUIRED'):
                cases.require_cache_settled(port)
            self.assertFalse((directory / 'image-cache-complete.json').exists())


class ProductRefusalContractTests(unittest.TestCase):
    @staticmethod
    def output(status='refused', diagnostic='missing live confirmation'):
        value = {'status': status, 'diagnostics': [diagnostic]}
        if status == 'blocked':
            value['recovery'] = 'preserve source/checkpoint; use product upgrade --to 0.5.0 --recover --preview from management checkout'
        return json.dumps(value, sort_keys=True).encode() + b'\n'

    def test_closed_public_parser_refusals_and_no_generic_nonzero_acceptance(self):
        for name in ('refuse-product-target', 'refuse-product-syntax'):
            spec = cases.REFUSALS[name]
            raw = cases.parser_refusal(list(spec.args))
            self.assertEqual(cases.validate_refusal(name, list(spec.args), 2, b'', raw),
                             {'status': 'parser_refused', 'cause': 'TARGET_SYNTAX'})
            for output, error, code in ((b'', b'arbitrary failure', 2), (b'', raw + b'extra', 2), (b'', raw, 0)):
                with self.subTest(name=name), self.assertRaises(cases.UpgradeError):
                    cases.validate_refusal(name, list(spec.args), code, output, error)

    def test_source_and_checkpoint_cause_are_exact_and_never_schema_or_recovery_success(self):
        name = 'refuse-product-source'
        args = list(cases.REFUSALS[name].args)
        for diagnostic, cause in cases.SOURCE_REFUSALS.items():
            result = cases.validate_refusal(name, args, 1, self.output('blocked', diagnostic), b'')
            self.assertEqual(result, {'status': 'blocked', 'cause': cause})
        for diagnostic in ('Product operation blocked; preserve source and checkpoint. Inspect release, inventory, host/resources and --recover --preview.',
                           'unrelated bootstrap failure', 'Target reader cannot preserve the admitted manifest schema.'):
            with self.assertRaises(cases.UpgradeError):
                cases.validate_refusal(name, args, 1, self.output('blocked', diagnostic), b'')
        name = 'refuse-product-checkpoint'
        result = cases.validate_refusal(name, list(cases.REFUSALS[name].args), 1,
            self.output('blocked', 'No matching product checkpoint; inspect the original target.'), b'')
        self.assertEqual(result['cause'], 'CHECKPOINT_ABSENT')
        with self.assertRaises(cases.UpgradeError):
            cases.validate_refusal(name, list(cases.REFUSALS[name].args), 0, b'{"status":"preview"}\n', b'')

    def test_consent_framing_and_recipe_input_modes_are_not_interchangeable(self):
        from tiny_swarm_world.domain.preflight import LIVE_CONSENT_PROMPT
        output = (LIVE_CONSENT_PROMPT + ' ').encode() + self.output()
        for name, spec in cases.REFUSALS.items():
            if spec.cause != 'CONSENT':
                continue
            result = cases.validate_refusal(name, list(spec.args), 2, output, b'')
            self.assertEqual(result['cause'], 'CONSENT_DECLINED_N' if spec.stdin_mode == 'DECLINE_N' else 'CONSENT_EOF')
            for wrong in (self.output(), b'prefix' + output, output + b'{}', output + b'\n',
                          (LIVE_CONSENT_PROMPT + ' ').encode() + b'{"status":"refused","status":"refused"}\n'):
                with self.subTest(name=name), self.assertRaises(cases.UpgradeError):
                    cases.validate_refusal(name, list(spec.args), 2, wrong, b'')
            with self.assertRaises(cases.UpgradeError):
                cases.refusal_spec(name, [*spec.args, '--approve-live'])

    def test_fixed_input_binds_actual_child_and_cannot_send_arbitrary_bytes(self):
        import io
        records = {}
        class Captured(io.BytesIO):
            sent = b''
            def close(self):
                self.sent = self.getvalue()
                super().close()
        for name in ('refuse-product-consent-eof', 'refuse-product-consent-n'):
            args = list(cases.REFUSALS[name].args)
            receipt = SimpleNamespace(args=args, binding={'case': name}, process={'pid': 42, 'start_time': 2},
                released=True, journal=SimpleNamespace(save=lambda key, value: records.update({key: value})), key='owned',
                environment=cases.expected_refusal_environment(name, Path('/source'), Path('/private'), Path('/private/operator.env')), inputs_sha256='a' * 64)
            stream = None if name.endswith('eof') else Captured()
            child = SimpleNamespace(pid=42, stdin=stream)
            cases.fixed_stdin(name, args, child, receipt)
            self.assertEqual(records['owned-cli-stdin.json']['delivered_bytes'], 0 if stream is None else 2)
            self.assertTrue(records['owned-cli-stdin.json']['writer_closed'])
            if stream is not None:
                self.assertEqual(stream.sent, b'n\n')
                self.assertTrue(stream.closed)
            child.pid = 99
            with self.assertRaises(cases.UpgradeError):
                cases.fixed_stdin(name, args, child, receipt)
        self.assertEqual(set(cases.REFUSALS[name].stdin_mode for name in cases.REFUSALS), {'EOF', 'DECLINE_N'})

    def test_fixed_official_infra_mode_is_source_only_and_preserves_private_operator(self):
        root, infra = Path('/owned/source'), Path('/owned/private-infra')
        operator = infra / 'operator.env'
        original = {'TSW_REPOSITORY_ROOT': str(root), 'TSW_INFRA_ROOT': str(infra), 'TSW_INSTALL_ENV_FILE': str(operator)}
        for case, spec in cases.REFUSALS.items():
            env = original.copy()
            selected = cases.select_refusal_environment(case, list(spec.args), env, root, infra, operator)
            self.assertEqual(selected['infra_mode'], 'OFFICIAL_INFRA_READ_ONLY' if case == 'refuse-product-source' else 'CAMPAIGN_INFRA')
            self.assertEqual(env['TSW_INFRA_ROOT'], str(root / 'modules/tsw_core/infra') if case == 'refuse-product-source' else str(infra))
            self.assertEqual(env['TSW_INSTALL_ENV_FILE'], str(operator))
            self.assertEqual(original['TSW_INFRA_ROOT'], str(infra))
        for key in ('TSW_REPOSITORY_ROOT', 'TSW_INFRA_ROOT', 'TSW_INSTALL_ENV_FILE'):
            env = original | {key: '/foreign'}
            with self.subTest(key=key), self.assertRaises(cases.UpgradeError):
                cases.select_refusal_environment('refuse-product-source', list(cases.REFUSALS['refuse-product-source'].args), env, root, infra, operator)

    def test_unavailable_historical_helpers_have_no_executed_product_result(self):
        for name in ('upgrade-product-v1', 'recover-product-v1'):
            value = cases.unavailable_product(name)
            self.assertEqual(value['status'], 'QUALIFICATION_HELPER_UNAVAILABLE')
            self.assertFalse(value['command_executed'])
            self.assertIsNone(value['product_result'])
            with self.assertRaises(cases.UpgradeError):
                cases.recipe(name)
        with self.assertRaises(cases.UpgradeError):
            cases.budgets('refuse-product-checkpoint', 'native', engine_recovery=True)


class PrivateInputCaptureTests(unittest.TestCase):
    def test_capture_compares_both_official_and_private_inputs_without_raw_credentials(self):
        import tempfile
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'source'
            official = root / 'modules/tsw_core/infra'
            official.mkdir(parents=True)
            (official / 'config.yaml').write_bytes(b'official')
            infra = Path(directory) / 'private-infra'
            infra.mkdir(mode=0o700)
            (infra / 'config.yaml').write_bytes(b'private')
            operator = infra / 'operator.env'
            operator.write_bytes(b'PRIVATE_INPUT_CANARY')
            operator.chmod(0o600)
            operator_sha = hashlib.sha256(operator.read_bytes()).hexdigest()
            rows = [('config.yaml', hashlib.sha256(b'private').hexdigest()), ('operator.env', operator_sha)]
            pin = cases.digest(rows)
            before = cases.capture_refusal_inputs(root, infra, operator, pin, operator_sha)
            self.assertNotIn('PRIVATE_INPUT_CANARY', str(before))
            self.assertEqual(before, cases.capture_refusal_inputs(root, infra, operator, pin, operator_sha))
            (official / 'config.yaml').write_bytes(b'changed official')
            self.assertNotEqual(before, cases.capture_refusal_inputs(root, infra, operator, pin, operator_sha))
            operator.write_bytes(b'changed private')
            with self.assertRaises(cases.UpgradeError):
                cases.capture_refusal_inputs(root, infra, operator, pin, operator_sha)


class RefusalPreservationOrchestrationTests(unittest.TestCase):
    def test_failed_preservation_or_unsettled_child_never_records_verified_refusal(self):
        for fault in ('changed', 'unsettled'):
            port = Transport('refuse-product-consent-n')
            saved = {}
            port.journal = SimpleNamespace(save=lambda key, value: saved.update({key: value}))
            def refuse(args, *, timeout):
                del args, timeout
                if fault == 'unsettled':
                    port.worker_settled = False
                return b'owned-child-result'
            port.public_refusal = refuse
            port.refusal_inputs = lambda: {'fixture': 'private-inputs'}
            original = {'schema_version': 1, 'paths': {name: {'kind': 'absent'} for name in cases.PROTECTED_PATHS}}
            changed = copy.deepcopy(original)
            changed['paths']['product/staging'] = {'kind': 'changed'}
            with self.subTest(fault=fault), patch.object(cases, 'observe', return_value=proof()), \
                    patch.object(cases, 'protected_state', side_effect=[original, changed]):
                with self.assertRaises(cases.UpgradeError):
                    cases.run(port)
            self.assertFalse(any(name == 'product-refusal-verified' for name, _ in port.records))
            self.assertIn('product-refusal-before.json', saved)
            self.assertNotIn('product-refusal-after.json', saved)


class ProtectedRefusalStateTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / '.tiny-swarm-world'
        (self.state / 'installation').mkdir(parents=True, mode=0o700)
        self.manifest = self.state / 'installation/manifest.json'
        self.manifest.write_bytes(b'{"fixture":"PRIVATE_CANARY"}')
        self.manifest.chmod(0o600)
        original_lstat = Path.lstat
        original_fstat = cases.os.fstat
        def owned(info):
            names = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            return SimpleNamespace(**{name: getattr(info, name) for name in names}, st_uid=0)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(Path, 'lstat', lambda path: owned(original_lstat(path))))
        self.stack.enter_context(patch.object(cases.os, 'fstat', lambda fd: owned(original_fstat(fd))))

    def test_absence_present_bytes_and_moved_inode_are_distinct_private_observations(self):
        before = cases.protected_state(self.root)
        self.assertEqual(before['paths']['installation/product-upgrade.json'], {'kind': 'absent'})
        self.assertNotIn('PRIVATE_CANARY', str(before))
        self.assertEqual(cases.protected_state(self.root), before)
        old = self.manifest.with_name('old-manifest')
        self.manifest.rename(old)
        self.manifest.write_bytes(old.read_bytes())
        self.manifest.chmod(0o600)
        self.assertNotEqual(cases.protected_state(self.root), before)
        self.manifest.write_bytes(b'{"changed":true}')
        self.assertNotEqual(cases.protected_state(self.root), before)

    def test_unreadable_and_unapproved_symlink_never_become_empty_or_preserved(self):
        original_open = cases.os.open
        def unreadable(path, *args, **kwargs):
            if Path(path) == self.manifest:
                raise PermissionError('PRIVATE_CANARY')
            return original_open(path, *args, **kwargs)
        with patch.object(cases.os, 'open', side_effect=unreadable), self.assertRaisesRegex(cases.UpgradeError, 'UNREADABLE'):
            cases.protected_state(self.root)
        self.manifest.unlink()
        self.manifest.symlink_to(self.root / 'foreign-secret')
        with self.assertRaises(cases.UpgradeError):
            cases.protected_state(self.root)

    def test_actual_staging_and_infra_and_fixed_activation_links_are_compared_without_following(self):
        product = self.state / 'product'
        (product / 'releases/revision').mkdir(parents=True, mode=0o700)
        (product / 'infra/revision').mkdir(parents=True, mode=0o700)
        code = product / 'releases/revision/code.py'
        code.write_bytes(b'original')
        code.chmod(0o644)
        (product / 'active').symlink_to(product / 'activations/revision')
        before = cases.protected_state(self.root)
        self.assertEqual(before['paths']['product/active']['kind'], 'symlink')
        code.write_bytes(b'changed')
        self.assertNotEqual(cases.protected_state(self.root), before)
        changed = copy.deepcopy(before)
        changed['paths']['product/inputs'] = {'kind': 'unreadable'}
        with self.assertRaises(cases.UpgradeError):
            cases.validate_protected(changed)


if __name__ == '__main__':
    unittest.main()

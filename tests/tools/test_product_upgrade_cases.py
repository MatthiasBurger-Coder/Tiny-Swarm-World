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

from tools.linux.qualification import product_upgrade_cases as cases


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
    def test_complete_cartesian_coverage_and_preset_only_on_setup(self):
        rows = [(r.preset, r.owner, r.exposure) for name, r in cases.RECIPES.items() if name.startswith('upgrade-batch-')]
        self.assertEqual(set(rows), {(p, o, e) for p in ('default', 'service-access')
            for o in ('swarm', 'portainer') for e in ('published', 'internal')})
        self.assertEqual(len(cases.ALL_NAMES), 24)
        for name in cases.RECIPES:
            if cases.RECIPES[name].kind == 'product':
                with self.assertRaisesRegex(cases.UpgradeError, 'NOT_IMPLEMENTED'):
                    cases.recipe(name)
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
        from tests.infrastructure.adapters.lifecycle import test_native_component_transitions as real
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
        from tests.domain.lifecycle.test_profile_lifecycle import intent_fixture
        from tests.infrastructure.adapters.clients.test_lxc_profile_lifecycle import instance_fixture, server_fixture
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

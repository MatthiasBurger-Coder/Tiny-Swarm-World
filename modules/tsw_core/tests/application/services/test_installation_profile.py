"""Actual lifecycle and checkpoint transitions with explicit host-effect ports."""
import asyncio
from copy import copy
import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import admitted_fixture, intent_fixture
from modules.tsw_core.tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import ProfileObservation, WorkerObservation
from tiny_swarm_world.application.services.installation_profile import InstallationProfileService
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileCapabilityMatrix
from tiny_swarm_world.domain.preflight import LiveConsent

CONSENT = LiveConsent(True, confirmed=True)


class Journal:
    def __init__(self):
        self.current = None
        self.events = []
        self.failure = None

    def exclusive(self, lease):
        return lease.journal('component')

    def load(self):
        return self.current

    def save(self, checkpoint, *, expected, lease):
        lease.require_active()
        if self.current != expected:
            raise LifecycleStateError('CAS')
        if self.failure == (checkpoint.generation, 'before'):
            raise OSError('private-before-canary')
        self.current = checkpoint
        self.events.append((checkpoint.stage, checkpoint.pending_action))
        if self.failure == (checkpoint.generation, 'after'):
            raise OSError('private-after-canary')


class Runtime:
    def __init__(self):
        self.state = {'profile': 'absent', 'instance': 'absent', 'uuid': None, 'forbidden': False,
                      'preservation': 'f' * 64, 'base': 'b' * 64}
        self.calls = []
        self.faults = {}
        self.unreadable = False
        self.lease = None
        self.wait = None

    def for_operation(self, lease, intent):
        lease.require_active()
        private = copy(self)
        private.lease = lease
        # Fault/read state intentionally shared, authority is private.
        return private

    async def inspect(self, intent):
        if self.state.get('unreadable'):
            raise OSError('private-read-canary')
        s = self.state
        sha = hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
        return ProfileObservation(client_version='6.0.5', server_version='6.0.5',
            preservation_sha256=s['preservation'], base_profiles_sha256=s['base'],
            profile_state=s['profile'], instance_state=s['instance'],
            effective_routes_match=s['profile'] == 'exact' and s['instance'] in {'stopped', 'running'},
            forbidden_listener=s['forbidden'], listeners_match=s['instance'] == 'running',
            listeners_clear=s['instance'] != 'running', observation_sha256=sha, instance_uuid=s['uuid'], workers=tuple(
                WorkerObservation(worker.node_name, s.get('workers', {}).get(worker.node_name, {}).get('state', 'absent'),
                    s.get('workers', {}).get(worker.node_name, {}).get('uuid'), True) for worker in intent.workers))

    async def effect(self, action):
        self.lease.require_active()
        self.calls.append(action)
        mode = self.faults.get(action, 'ack')
        if self.wait is not None:
            self.wait[0].set()
            await self.wait[1].wait()
        if mode == 'not-applied':
            raise RuntimeError('private-not-applied')
        if action.startswith('worker-init:'):
            node = action.split(':')[1]
            self.state.setdefault('workers', {})[node] = {'state': 'stopped',
                'uuid': '22222222-2222-2222-2222-22222222222' + node[-1]}
        if action.startswith('worker-start:'):
            self.state['workers'][action.split(':')[1]]['state'] = 'running'
        if action == 'profile-create':
            self.state['profile'] = 'exact'
        if action == 'instance-init':
            self.state.update(instance='stopped', uuid='11111111-1111-1111-1111-111111111111')
        if action == 'instance-start':
            self.state['instance'] = 'running'
        if action == 'instance-delete':
            self.state.update(instance='absent', uuid=None)
        if action == 'profile-delete':
            self.state['profile'] = 'absent'
        if mode == 'unreadable':
            self.state['unreadable'] = True
        if mode == 'lost':
            raise OSError('private-lost-response')

    async def update_profile(self, intent, before):
        raise AssertionError('Creation runtime may not receive existing-profile updates')
    async def create_profile(self, intent): await self.effect('profile-create')
    async def init_instance(self, intent): await self.effect('instance-init')
    async def start_instance(self, intent): await self.effect('instance-start')
    async def delete_instance(self, intent): await self.effect('instance-delete')
    async def delete_profile(self, intent): await self.effect('profile-delete')
    async def init_worker(self, intent, node_name): await self.effect('worker-init:' + node_name)
    async def start_worker(self, intent, node_name): await self.effect('worker-start:' + node_name)


class ProfileLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.intent = intent_fixture()
        self.runtime, self.journal, self.lock = Runtime(), Journal(), FakeInstallationLock()
        self.repository = Mock()
        self.repository.load.return_value = admitted_fixture()
        self.manifests = Mock()
        self.service = InstallationProfileService(self.repository, self.runtime, self.journal, self.manifests, self.lock)

    async def run_profile(self, **kwargs):
        return await self.service.run(self.intent, consent=CONSENT, **kwargs)

    async def test_exact_sequence_and_durable_stage_before_each_effect(self):
        result = await self.run_profile()
        self.assertEqual(result.stage, 'completed')
        self.assertFalse(result.settled)
        self.assertEqual(self.runtime.calls, ['profile-create', 'instance-init', 'instance-start'])
        self.assertEqual([action for _stage, action in self.journal.events if action],
                         ['profile-create', 'instance-init', 'instance-start'])
        self.assertIsNone(self.runtime.lease)
        self.assertEqual(result.instance_uuid, self.runtime.state['uuid'])
        self.assertFalse(self.lock.held)
        self.assertEqual(self.lock.events[-2:], ['journal-release:component', 'operation-release:profile-lifecycle'])

    async def test_empty_matrix_and_missing_consent_refuse_without_runtime_or_journal_effect(self):
        self.repository.load.return_value = ProfileCapabilityMatrix(admitted_versions=())
        with self.assertRaisesRegex(LifecycleStateError, 'No Incus version'):
            await self.run_profile()
        self.assertIsNone(self.journal.current)
        self.assertEqual(self.runtime.calls, [])
        self.assertEqual(self.lock.events, [])
        with self.assertRaises(LifecycleStateError):
            await self.service.run(self.intent, consent=LiveConsent(False))

    async def test_four_outcomes_at_each_create_init_start_boundary_and_recovery(self):
        for action in ('profile-create', 'instance-init', 'instance-start'):
            for mode in ('ack', 'lost', 'not-applied', 'unreadable'):
                with self.subTest(action=action, mode=mode):
                    self.setUp()
                    self.runtime.faults[action] = mode
                    if mode in {'ack', 'lost'}:
                        self.assertEqual((await self.run_profile()).stage, 'completed')
                        self.assertEqual(self.runtime.calls.count(action), 1)
                    else:
                        with self.assertRaises(LifecycleStateError) as error:
                            await self.run_profile()
                        self.assertNotIn('private-', str(error.exception))
                        self.assertEqual(self.journal.current.stage, 'recoverable')
                        self.assertEqual(self.journal.current.intent, self.intent)
                        self.assertFalse(any('delete' in call for call in self.runtime.calls))
                        self.runtime.faults.clear()
                        self.runtime.state.pop('unreadable', None)
                        self.assertEqual((await self.run_profile(recovery=True)).stage, 'completed')
                        count = 2 if mode == 'not-applied' else 1
                        self.assertEqual(self.runtime.calls.count(action), count)

    async def test_changed_owner_baseline_listener_or_instance_uuid_blocks_next_write(self):
        for field, value in (('preservation', '9' * 64), ('base', '9' * 64), ('forbidden', True), ('profile', 'foreign')):
            with self.subTest(field=field):
                self.setUp()
                self.runtime.state[field] = value
                with self.assertRaises(LifecycleStateError):
                    await self.run_profile()
                self.assertEqual(self.runtime.calls, [])
                self.assertIsNone(self.journal.current)
        self.setUp()
        await self.run_profile()
        self.runtime.state['uuid'] = '22222222-2222-2222-2222-222222222222'
        with self.assertRaises(LifecycleStateError):
            await self.run_profile(recovery=True)
        self.assertFalse(any('delete' in call for call in self.runtime.calls))

    async def test_checkpoint_interruptions_before_and_after_every_normal_generation(self):
        for generation in range(10):
            for timing in ('before', 'after'):
                with self.subTest(generation=generation, timing=timing):
                    self.setUp()
                    self.journal.failure = (generation, timing)
                    try:
                        await self.run_profile()
                    except (LifecycleStateError, OSError):
                        pass
                    self.assertFalse(any('delete' in call for call in self.runtime.calls))
                    self.assertIsNone(self.runtime.lease)
                    if self.journal.current is None:
                        self.assertEqual(self.runtime.calls, [])
                    else:
                        self.assertEqual(self.journal.current.intent, self.intent)
                        self.journal.failure = None
                        self.assertEqual((await self.run_profile(recovery=True)).stage, 'completed')

    async def test_repeated_cancellation_waits_for_started_effect_before_releasing_lease(self):
        entered, release = asyncio.Event(), asyncio.Event()
        self.runtime.wait = (entered, release)
        task = asyncio.create_task(self.run_profile())
        await entered.wait()
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        self.assertTrue(self.lock.held)
        self.assertFalse(task.done())
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(self.lock.held)
        self.assertEqual(self.journal.current.pending_action, 'profile-create')
        self.runtime.wait = None
        self.assertEqual((await self.run_profile(recovery=True)).stage, 'completed')

    async def test_installation_commit_requires_actual_bound_manifest_not_profile_completion(self):
        result = await self.run_profile()
        self.manifests.load.return_value = SimpleNamespace(manifest=None)
        with self.lock.exclusive('setup') as lease:
            with self.assertRaises(LifecycleStateError):
                await self.service.commit_installation(self.intent, consent=CONSENT, lease=lease)
        self.assertFalse(self.journal.current.settled)
        self.assertEqual(self.journal.current.intent, result.intent)

    async def test_cleanup_four_outcomes_preserve_post_start_and_foreign_state(self):
        from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileLifecycleCheckpoint
        for action in ('instance-delete', 'profile-delete'):
            for mode in ('ack', 'lost', 'not-applied', 'unreadable'):
                with self.subTest(action=action, mode=mode):
                    self.setUp()
                    self.runtime.state.update(profile='exact', instance='stopped',
                        uuid='11111111-1111-1111-1111-111111111111')
                    observed = await self.runtime.inspect(self.intent)
                    self.journal.current = ProfileLifecycleCheckpoint(intent=self.intent,
                        stage='instance-initialized', previous_stage='instance-initialized',
                        instance_uuid=observed.instance_uuid, observation_sha256=observed.observation_sha256)
                    self.runtime.faults[action] = mode
                    if mode in {'ack', 'lost'}:
                        result = await self.service.cleanup(self.intent, consent=CONSENT)
                        self.assertEqual(result.stage, 'cleaned')
                        self.assertTrue(result.settled)
                        self.assertEqual(self.runtime.calls.count(action), 1)
                    else:
                        with self.assertRaises(LifecycleStateError) as error:
                            await self.service.cleanup(self.intent, consent=CONSENT)
                        self.assertNotIn('private-', str(error.exception))
                        self.assertEqual(self.journal.current.intent, self.intent)
                        self.runtime.state.pop('unreadable', None)
                        self.runtime.faults.clear()
                        result = await self.service.cleanup(self.intent, consent=CONSENT)
                        self.assertEqual(result.stage, 'cleaned')
                        self.assertEqual(self.runtime.calls.count(action), 2 if mode == 'not-applied' else 1)
        self.setUp()
        await self.run_profile()
        with self.assertRaises(LifecycleStateError):
            await self.service.cleanup(self.intent, consent=CONSENT)
        self.assertFalse(any('delete' in call for call in self.runtime.calls))

    async def test_recovery_never_recomputes_a_changed_intent(self):
        self.runtime.faults['instance-init'] = 'not-applied'
        with self.assertRaises(LifecycleStateError):
            await self.run_profile()
        previous = self.journal.current
        changed = self.intent.model_copy(update={'memory': '11GiB'})
        count = len(self.runtime.calls)
        with self.assertRaises(LifecycleStateError):
            await self.service.run(changed, consent=CONSENT, recovery=True)
        self.assertEqual(self.journal.current, previous)
        self.assertEqual(len(self.runtime.calls), count)


class SelectedWorkerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from tiny_swarm_world.domain.lifecycle.profile_lifecycle import WorkerCreateIntent
        self.intent = intent_fixture()
        workers = tuple(WorkerCreateIntent(node_name='swarm-worker-' + str(index), image_fingerprint=self.intent.image_fingerprint,
            base_profiles=self.intent.base_profiles, network=self.intent.network, storage_pool=self.intent.storage_pool,
            cpu=2, memory='8GiB', disk='20GiB') for index in (1, 2))
        self.intent = self.intent.model_copy(update={'workers': workers})
        self.runtime, self.journal, self.lock = Runtime(), Journal(), FakeInstallationLock()
        self.service = InstallationProfileService(SimpleNamespace(load=admitted_fixture), self.runtime,
            self.journal, SimpleNamespace(load=lambda: SimpleNamespace(manifest=None)), self.lock)

    async def test_manager_then_each_exact_worker_is_stopped_verified_started_and_uuid_bound(self):
        from tiny_swarm_world.application.services.profile_setup import ensure_worker, require_workers_running
        with self.lock.exclusive('setup') as lease:
            await self.service.run(self.intent, consent=CONSENT, lease=lease)
            private = copy(self.service)
            private.runtime = self.runtime.for_operation(lease, self.intent)
            for node in ('swarm-worker-1', 'swarm-worker-2'):
                with self.journal.exclusive(lease):
                    await ensure_worker(private, self.journal.load(), admitted_fixture(), lease, node, False)
            observed = await private.runtime.inspect(self.intent)
            require_workers_running(self.journal.load(), observed)
            self.assertEqual(set(self.journal.load().worker_uuids), {'swarm-worker-1', 'swarm-worker-2'})
            self.assertEqual(self.runtime.calls, ['profile-create', 'instance-init', 'instance-start',
                'worker-init:swarm-worker-1', 'worker-start:swarm-worker-1',
                'worker-init:swarm-worker-2', 'worker-start:swarm-worker-2'])
            with self.journal.exclusive(lease), self.assertRaises(LifecycleStateError):
                await ensure_worker(private, self.journal.load(), admitted_fixture(), lease, 'unselected', False)

    async def test_worker_four_outcomes_never_blind_retry_or_adopt_unrecorded_identity(self):
        from tiny_swarm_world.application.services.profile_setup import ensure_worker
        for action in ('worker-init:swarm-worker-1', 'worker-start:swarm-worker-1'):
            for mode in ('ack', 'lost', 'not-applied', 'unreadable'):
                self.setUp()
                self.runtime.faults[action] = mode
                with self.lock.exclusive('setup') as lease:
                    await self.service.run(self.intent, consent=CONSENT, lease=lease)
                    private = copy(self.service)
                    private.runtime = self.runtime.for_operation(lease, self.intent)
                    with self.subTest(action=action, mode=mode), self.journal.exclusive(lease):
                        if mode in {'ack', 'lost'}:
                            await ensure_worker(private, self.journal.load(), admitted_fixture(), lease, 'swarm-worker-1', False)
                            self.assertIn('swarm-worker-1', self.journal.load().worker_uuids)
                        else:
                            with self.assertRaises((LifecycleStateError, OSError)):
                                await ensure_worker(private, self.journal.load(), admitted_fixture(), lease, 'swarm-worker-1', False)
                            self.assertIsNotNone(self.journal.load().pending_action)
                        self.assertEqual(self.runtime.calls.count(action), 1)
                        self.assertNotIn('instance-delete', self.runtime.calls)


class CleanupRestartTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.intent = intent_fixture()
        self.runtime, self.journal, self.lock = Runtime(), Journal(), FakeInstallationLock()
        self.service = InstallationProfileService(SimpleNamespace(load=admitted_fixture), self.runtime,
            self.journal, Mock(), self.lock)

    async def run_profile(self, **kwargs):
        return await self.service.run(self.intent, consent=CONSENT, **kwargs)

    async def test_explicit_recovery_after_cleaned_state_preserves_original_intent_and_uuid_scope(self):
        self.runtime.faults['instance-start'] = 'not-applied'
        with self.assertRaises(LifecycleStateError):
            await self.run_profile()
        # Post-start-intent cleanup is intentionally refused. Build the earlier
        # exact stopped-init checkpoint to exercise the supported cleanup case.
        checkpoint = self.journal.current
        observed = await self.runtime.inspect(self.intent)
        self.journal.current = checkpoint.model_copy(update={'stage': 'instance-initialized',
            'previous_stage': 'instance-initialized', 'pending_action': None,
            'observation_sha256': observed.observation_sha256})
        await self.service.cleanup(self.intent, consent=CONSENT)
        original = self.journal.current.intent
        self.runtime.faults.clear()
        completed = await self.run_profile(recovery=True)
        self.assertEqual(completed.intent, original)
        self.assertEqual(completed.intent.profile.installation_id, self.intent.profile.installation_id)
        self.assertEqual(completed.intent.profile.operation_id, self.intent.profile.operation_id)

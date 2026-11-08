"""Actual additive profile state machine, including uncertain-write recovery."""
from copy import copy
import hashlib
import json
from types import SimpleNamespace
import unittest

from tests.application.services.test_installation_profile import CONSENT
from tests.domain.lifecycle.test_profile_lifecycle import intent_fixture, admitted_fixture
from tests.domain.lifecycle.test_models import manifest_fixture
from tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import ProfileObservation
from tiny_swarm_world.application.services.profile_change import ProfileChangeOperation
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest, ProxyRoute, SwarmOwnership, migrate_manifest_v1
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, ProfileChangeCheckpoint, ProfileChangeIntent

_UUID = '11111111-1111-1111-1111-111111111111'


class ChangeJournal:
    """Explicit fake for the change checkpoint shape, without creation-only fields."""
    def __init__(self):
        self.current = None
        self.events = []

    def exclusive(self, lease):
        return lease.journal('component')

    def load(self):
        return self.current

    def save(self, checkpoint, *, expected, lease):
        lease.require_active()
        if self.current != expected:
            raise LifecycleStateError('Change checkpoint CAS failed.')
        self.current = checkpoint
        self.events.append(checkpoint.stage)


class Runtime:
    def __init__(self, before):
        self.state = {'devices': before.devices(), 'unreadable': False}
        self.calls = []
        self.mode = 'ack'
        self.lease = None
    def for_operation(self, lease, intent):
        lease.require_active()
        private = copy(self)
        private.lease = lease
        return private
    async def inspect(self, intent):
        if self.state['unreadable']:
            raise LifecycleStateError('Observed state is unknown.')
        exact = self.state['devices'] == intent.devices()
        return ProfileObservation(client_version='6.0.5', server_version='6.0.5', preservation_sha256='f' * 64,
            base_profiles_sha256='b' * 64, profile_state='exact' if exact else 'foreign', instance_state='running',
            effective_routes_match=exact, forbidden_listener=False, listeners_match=exact, listeners_clear=False,
            observation_sha256=hashlib.sha256(json.dumps(self.state, sort_keys=True).encode()).hexdigest(), instance_uuid=_UUID)
    async def update_profile(self, target, before):
        self.lease.require_active()
        self.calls.append((before.devices(), target.devices()))
        if self.mode == 'not-applied':
            raise RuntimeError('private-command-canary')
        self.state['devices'] = target.devices()
        if self.mode == 'unreadable':
            self.state['unreadable'] = True
        if self.mode == 'lost':
            raise OSError('private-response-canary')


def fixture():
    before = intent_fixture()
    base = migrate_manifest_v1(manifest_fixture()).model_copy(update={
        'installation_id': before.profile.installation_id, 'installation_profile': before.profile.profile})
    base = InstallationManifest.model_validate_json(base.model_dump_json())
    routes = (*before.profile.profile.routes, ProxyRoute(device_name='tsw-proxy-16080', listen_address='127.0.0.1',
        listen_port=16080, connect_port=16080))
    profile = before.profile.model_copy(update={'requested_services': ('incus', 'portainer', 'swagger'),
        'resolved_services': ('incus', 'portainer', 'swagger'), 'service_exposure': {'swagger': 'published'},
        'stack_ownership': {'swagger': SwarmOwnership()}, 'profile': before.profile.profile.model_copy(update={'routes': routes})})
    target = ManagerCreateIntent.model_validate_json(before.model_copy(update={
        'profile': profile, 'planned_stack_owners': {'swagger': 'swarm'}}).model_dump_json())
    intent = ProfileChangeIntent(operation_id='d' * 32, controller_revision='c' * 40, manifest_token='1' * 64,
        before_manifest=base, before=before, target=target, instance_uuid=_UUID, worker_uuids={})
    return intent, base


class ProfileChangeTests(unittest.IsolatedAsyncioTestCase):
    async def make_operation(self, lease):
        intent, base = fixture()
        runtime, journal = Runtime(intent.before), ChangeJournal()
        manifests = SimpleNamespace(current=SimpleNamespace(manifest=base, token='1' * 64))
        manifests.load = lambda: manifests.current
        service = SimpleNamespace(capabilities=SimpleNamespace(load=admitted_fixture), runtime=runtime, manifests=manifests)
        plan = SimpleNamespace(requested_services=intent.target.profile.requested_services)
        operation = ProfileChangeOperation(service, journal, intent, lease, plan, CONSENT)
        observed = await runtime.inspect(intent.before)
        journal.save(ProfileChangeCheckpoint(intent=intent, observation_sha256=observed.observation_sha256), expected=None, lease=lease)
        return operation, runtime, journal, manifests

    async def test_four_outcomes_require_exact_target_or_original_explicit_recovery(self):
        for mode in ('ack', 'lost', 'not-applied', 'unreadable'):
            with self.subTest(mode=mode), FakeInstallationLock().exclusive('setup') as lease:
                operation, runtime, journal, _ = await self.make_operation(lease)
                runtime.mode = mode
                if mode in {'ack', 'lost'}:
                    await operation.apply()
                    self.assertEqual(journal.current.stage, 'verified')
                else:
                    with self.assertRaises(LifecycleStateError):
                        await operation.apply()
                    self.assertEqual(journal.current.stage, 'pending')
                    with self.assertRaises(LifecycleStateError):
                        await operation.apply()
                    self.assertEqual(len(runtime.calls), 1)
                    operation.recovery = True
                    runtime.mode = 'ack'
                    runtime.state['unreadable'] = False
                    await operation.apply()
                    self.assertEqual(journal.current.stage, 'verified')
                self.assertEqual(len(runtime.calls), 2 if mode == 'not-applied' else 1)
                self.assertIsNone(runtime.lease)

    async def test_verified_target_is_idempotent_and_foreign_profile_cannot_be_pruned(self):
        with FakeInstallationLock().exclusive('setup') as lease:
            operation, runtime, journal, _ = await self.make_operation(lease)
            await operation.apply()
            generation = journal.current.generation
            await operation.apply()
            self.assertEqual(journal.current.generation, generation)
            self.assertEqual(len(runtime.calls), 1)
            runtime.state['devices']['foreign'] = {'type': 'disk', 'path': '/foreign', 'source': '/'}
            with self.assertRaises(LifecycleStateError):
                await operation.apply()
            self.assertEqual(len(runtime.calls), 1)

    async def test_manifest_write_before_profile_commit_is_recoverable_without_reapplying(self):
        with FakeInstallationLock().exclusive('setup') as lease:
            operation, runtime, journal, manifests = await self.make_operation(lease)
            await operation.apply()
            original = manifests.current.manifest
            target = operation.intent.target.profile
            payload = original.model_dump()
            payload.update(requested_services=target.requested_services, resolved_services=target.resolved_services,
                service_exposure=target.service_exposure, stack_ownership=target.stack_ownership,
                installation_profile=target.profile, checkpoint_reference='profile-change-' + operation.intent.operation_id)
            manifests.current = SimpleNamespace(manifest=InstallationManifest.model_validate(payload), token='2' * 64)
            operation.recovery = True
            await operation.admit_desired(operation.plan)
            await operation.commit_installation()
            self.assertTrue(journal.current.settled)
            self.assertEqual(len(runtime.calls), 1)
            self.assertEqual(operation.intent.before_manifest, original)


def ownership_fixture():
    from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
    return PortainerOwnership(owner='portainer', endpoint_id=1, stack_id=2, resource_control_id=3,
        ownership_fingerprint='sha256:' + 'a' * 64, definition_fingerprint='sha256:' + 'b' * 64)


def owned_change_fixture(*, existing):
    intent, manifest = fixture()
    owner = ownership_fixture()
    target_profile = intent.target.profile.model_copy(update={'stack_ownership': {'swagger': owner if existing else SwarmOwnership()}})
    target = intent.target.model_copy(update={'profile': target_profile, 'planned_stack_owners': {'swagger': 'portainer'}})
    before = intent.before
    if existing:
        before_profile = target_profile.model_copy(update={'profile': intent.before.profile.profile})
        before = before.model_copy(update={'profile': before_profile, 'planned_stack_owners': {'swagger': 'portainer'}})
        manifest = manifest.model_copy(update={'requested_services': before_profile.requested_services,
            'resolved_services': before_profile.resolved_services, 'service_exposure': before_profile.service_exposure,
            'stack_ownership': before_profile.stack_ownership})
    return ProfileChangeIntent.model_validate_json(intent.model_copy(update={
        'before_manifest': manifest, 'before': before, 'target': target}).model_dump_json())


class ProfileChangeOwnershipTests(unittest.IsolatedAsyncioTestCase):
    def malformed_owners(self):
        original = ownership_fixture().model_dump(mode='json')
        mutations: tuple[tuple[str, object], ...] = (
            ('endpoint_id', 101), ('stack_id', 102), ('resource_control_id', 103),
            ('ownership_fingerprint', 'sha256:' + 'c' * 64), ('owner', 'swarm'),
            ('endpoint_id', True), ('stack_id', '2'), ('ownership_fingerprint', 42),
        )
        return tuple({**original, field: value} for field, value in mutations)

    async def test_callback_denies_existing_identity_mode_and_type_changes_without_journal_write(self):
        intent = owned_change_fixture(existing=True)
        with FakeInstallationLock().exclusive('setup') as lease:
            journal = ChangeJournal()
            journal.current = ProfileChangeCheckpoint(intent=intent, stage='verified', observation_sha256='a' * 64,
                verified_stack_ownership={'swagger': ownership_fixture()})
            operation = ProfileChangeOperation(None, journal, intent, lease, None, CONSENT)
            original = journal.current
            for payload in self.malformed_owners():
                submitted = SimpleNamespace(model_dump_json=lambda row=payload: json.dumps(row))
                with self.subTest(payload=payload), self.assertRaises(LifecycleStateError):
                    await operation.record_stack_ownership('swagger', submitted)
                self.assertEqual(journal.current, original)
                self.assertEqual(journal.events, [])

    def test_forged_persisted_checkpoint_cannot_replace_baseline_ids_mode_or_fingerprint(self):
        intent = owned_change_fixture(existing=True)
        checkpoint = ProfileChangeCheckpoint(intent=intent, stage='verified', observation_sha256='a' * 64)
        for payload in self.malformed_owners():
            forged = checkpoint.model_dump(mode='json')
            forged['verified_stack_ownership'] = {'swagger': payload}
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                ProfileChangeCheckpoint.model_validate_json(json.dumps(forged))
        forged_intent = intent.model_dump(mode='json')
        forged_intent['before']['profile']['stack_ownership']['swagger'] = {'owner': 'swarm'}
        with self.assertRaises(ValueError):
            ProfileChangeIntent.model_validate_json(json.dumps(forged_intent))

    async def test_only_verified_definition_change_keeps_all_baseline_identity_and_new_stack_ids_are_allowed(self):
        for existing in (True, False):
            intent = owned_change_fixture(existing=existing)
            with self.subTest(existing=existing), FakeInstallationLock().exclusive('setup') as lease:
                journal = ChangeJournal()
                journal.current = ProfileChangeCheckpoint(intent=intent, stage='verified', observation_sha256='a' * 64)
                operation = ProfileChangeOperation(None, journal, intent, lease, None, CONSENT)
                owner = ownership_fixture().model_copy(update={'definition_fingerprint': 'sha256:' + 'd' * 64})
                if not existing:
                    owner = owner.model_copy(update={'endpoint_id': 91, 'stack_id': 92, 'resource_control_id': 93,
                                                    'ownership_fingerprint': 'sha256:' + 'e' * 64})
                await operation.record_stack_ownership('swagger', owner)
                self.assertEqual(journal.current.verified_stack_ownership['swagger'], owner)
                decoded = ProfileChangeCheckpoint.model_validate_json(journal.current.model_dump_json())
                self.assertEqual(decoded.verified_stack_ownership['swagger'], owner)
                if existing:
                    self.assertEqual(owner.model_dump(exclude={'definition_fingerprint'}),
                                     ownership_fixture().model_dump(exclude={'definition_fingerprint'}))
                journal.current = ProfileChangeCheckpoint(intent=intent, observation_sha256='a' * 64)
                with self.assertRaises(LifecycleStateError):
                    await operation.record_stack_ownership('swagger', owner)
                forged = journal.current.model_dump(mode='json')
                forged['verified_stack_ownership'] = {'swagger': owner.model_dump(mode='json')}
                with self.assertRaises(ValueError):
                    ProfileChangeCheckpoint.model_validate_json(json.dumps(forged))

    async def test_new_stack_first_verified_identity_cannot_be_replaced_by_later_callback(self):
        intent = owned_change_fixture(existing=False)
        with FakeInstallationLock().exclusive('setup') as lease:
            journal = ChangeJournal()
            journal.current = ProfileChangeCheckpoint(intent=intent, stage='verified', observation_sha256='a' * 64)
            operation = ProfileChangeOperation(None, journal, intent, lease, None, CONSENT)
            original = ownership_fixture()
            await operation.record_stack_ownership('swagger', original)
            checkpoint = journal.current
            for payload in self.malformed_owners():
                submitted = SimpleNamespace(model_dump_json=lambda row=payload: json.dumps(row))
                with self.subTest(payload=payload), self.assertRaises(LifecycleStateError):
                    await operation.record_stack_ownership('swagger', submitted)
                self.assertEqual(journal.current, checkpoint)
            changed_definition = original.model_copy(update={'definition_fingerprint': 'sha256:' + 'f' * 64})
            await operation.record_stack_ownership('swagger', changed_definition)
            self.assertEqual(journal.current.verified_stack_ownership['swagger'], changed_definition)

    async def test_same_identity_rule_applies_to_existing_runtime_callback_without_manifest_mutation(self):
        from tiny_swarm_world.application.services.profile_setup import ProfileRuntimeOperation
        from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileRuntimeIntent
        change = owned_change_fixture(existing=True)
        intent = ProfileRuntimeIntent(profile=change.before.profile, original=change.before,
                                      planned_stack_owners=change.before.planned_stack_owners)
        with FakeInstallationLock().exclusive('component-update') as lease:
            operation = ProfileRuntimeOperation(None, intent, lease, '1' * 64, CONSENT)
            for payload in self.malformed_owners():
                submitted = SimpleNamespace(model_dump_json=lambda row=payload: json.dumps(row))
                with self.subTest(payload=payload), self.assertRaises((LifecycleStateError, ValueError)):
                    await operation.record_stack_ownership('swagger', submitted)
                self.assertEqual(operation.verified_stack_ownership['swagger'], ownership_fixture())
            owner = ownership_fixture().model_copy(update={'definition_fingerprint': 'sha256:' + 'f' * 64})
            await operation.record_stack_ownership('swagger', owner)
            self.assertEqual(operation.verified_stack_ownership['swagger'], owner)

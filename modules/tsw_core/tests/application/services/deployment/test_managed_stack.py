"""Operation tests distinguish HTTP receipt, saved state and actual tasks."""
import unittest
from dataclasses import replace
from unittest.mock import AsyncMock

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.managed_stack import ManagedStackSnapshot, ManagedStackReceipt
from tiny_swarm_world.application.services.deployment.managed_stack import ManagedStackOperation
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
from tiny_swarm_world.domain.update.runtime_observation import UpdateRuntimeObservation, UpdateTaskObservation


SOURCE = 'sha256:' + 'a' * 64
TARGET = 'sha256:' + 'b' * 64
INSTALLATION = '11111111-1111-1111-1111-111111111111'


def ownership(fingerprint=SOURCE):
    return PortainerOwnership(owner='portainer', endpoint_id=1, stack_id=2,
        resource_control_id=3, ownership_fingerprint='sha256:' + 'c' * 64, definition_fingerprint=fingerprint)


def tasks(image='image:new', task_image=None):
    return UpdateRuntimeObservation('swagger', 'ui', 'service-id', 1, image, 1,
        (UpdateTaskObservation('task-id', task_image or image, 'running', 'running'),), 'completed')


class Journal:
    value = None
    def __init__(self):
        self.value, self.history = None, []
    def load(self):
        return self.value
    def save(self, value):
        self.value = value
        self.history.append(value)


class Lease:
    operation_id = 'd' * 32
    def require_active(self):
        pass


class Api:
    def __init__(self, exists=True):
        self.current = ManagedStackSnapshot(ownership(), StackDefinition(name='swagger', compose_content='old'), {'PRIVATE': 'do-not-persist'}) if exists else None
        self.updates, self.creates = 0, 0
        self.fail_create = False
        self.saved_after_update = True
        self.next_fingerprint = TARGET
        self.fail_update = False
    def local_endpoint(self):
        return 1
    def require_absent(self, name, endpoint):
        if self.current is not None:
            raise LifecycleStateError('foreign')
    def inspect(self, name, endpoint, stack_id):
        if self.current is None:
            raise LifecycleStateError('unavailable')
        return self.current
    def create(self, definition, endpoint, environment):
        self.creates += 1
        if self.fail_create:
            raise TimeoutError
        self.current = ManagedStackSnapshot(ownership(TARGET), definition, dict(environment))
        return ManagedStackReceipt(2, 3, ownership().ownership_fingerprint)
    def update(self, expected, definition):
        self.updates += 1
        if self.saved_after_update:
            self.current = ManagedStackSnapshot(ownership(self.next_fingerprint), definition, expected.environment)
        if self.fail_update:
            raise TimeoutError


class ManagedOperationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.api, self.journal = Api(), Journal()
        self.observer = type('Observer', (), {'observe': AsyncMock(return_value=tasks())})()
        self.callback = AsyncMock()
        self.definition = StackDefinition(name='swagger', compose_content='new')
    def operation(self):
        return ManagedStackOperation(self.api, self.journal, self.observer,
            installation_id=INSTALLATION, lease=Lease(), attempts=2, interval=0)
    async def apply(self, owner=ownership()):
        return await self.operation().apply(self.definition, {'PRIVATE': 'do-not-persist'}, {'ui': 'image:new'}, TARGET, owner, self.callback)
    async def test_update_requires_readback_and_tasks_before_verified_callback(self):
        await self.apply()
        self.assertEqual(self.api.updates, 1)
        self.assertEqual([item.phase for item in self.journal.history], ['prepared', 'uncertain', 'received', 'verified'])
        self.callback.assert_awaited_once_with(ownership(TARGET))
        self.assertNotIn('do-not-persist', self.journal.value.model_dump_json())
    async def test_http_receipt_without_saved_target_is_not_success(self):
        self.api.saved_after_update = False
        with self.assertRaises(LifecycleStateError):
            await self.apply()
        self.callback.assert_not_awaited()
        self.assertNotEqual(self.journal.value.phase, 'verified')
    async def test_old_tasks_do_not_qualify_new_saved_definition(self):
        self.observer.observe.return_value = tasks('image:new', 'image:old')
        with self.assertRaises(LifecycleStateError):
            await self.apply()
        self.callback.assert_not_awaited()
    async def test_completed_repeat_revalidates_without_put(self):
        await self.apply()
        await self.apply(owner=ownership(TARGET))
        self.assertEqual(self.api.updates, 1)
        self.assertEqual(self.observer.observe.await_count, 2)
    async def test_changed_ownership_fails_before_put(self):
        self.api.current = replace(self.api.current, ownership=ownership().model_copy(update={'resource_control_id': 99}))
        with self.assertRaises(LifecycleStateError):
            await self.apply()
        self.assertEqual(self.api.updates, 0)
    async def test_new_create_has_no_fabricated_ids_before_response(self):
        self.api = Api(False)
        await self.apply(owner=None)
        pending = self.journal.history[1]
        self.assertIsNone(pending.source)
        self.assertIsNone(pending.created_stack_id)
        self.assertIsNone(pending.result)
        self.assertEqual(self.api.creates, 1)
    async def test_same_name_existing_stack_is_not_adopted(self):
        with self.assertRaises(LifecycleStateError):
            await self.apply(owner=None)
        self.assertEqual(self.api.creates, 0)
        self.assertEqual(self.api.updates, 0)
    async def test_unknown_create_outcome_never_repeats_or_adopts(self):
        self.api = Api(False)
        self.api.fail_create = True
        with self.assertRaises(TimeoutError):
            await self.apply(owner=None)
        self.api.fail_create = False
        with self.assertRaises(LifecycleStateError):
            await self.apply(owner=None)
        self.assertEqual(self.api.creates, 1)
    async def test_known_create_id_resumes_after_convergence_failure(self):
        self.api = Api(False)
        self.observer.observe.return_value = tasks('image:new', 'image:old')
        with self.assertRaises(LifecycleStateError):
            await self.apply(owner=None)
        self.assertEqual(self.journal.value.created_stack_id, 2)
        self.observer.observe.return_value = tasks()
        await self.apply(owner=None)
        self.assertEqual(self.api.creates, 1)
    async def test_recovery_rejects_changed_definition_before_write(self):
        self.api.saved_after_update = False
        with self.assertRaises(LifecycleStateError):
            await self.apply()
        with self.assertRaises(LifecycleStateError):
            await self.operation().apply(self.definition, {}, {'ui': 'image:new'}, SOURCE, ownership(), self.callback)
        self.assertEqual(self.api.updates, 1)
    async def test_ownership_callback_failure_retains_verified_result_for_resume(self):
        self.callback.side_effect = LifecycleStateError('checkpoint unavailable')
        with self.assertRaises(LifecycleStateError):
            await self.apply()
        self.assertEqual(self.journal.value.phase, 'verified')
        self.callback.side_effect = None
        await self.apply(owner=ownership(TARGET))
        self.assertEqual(self.api.updates, 1)

    async def test_timed_out_put_resumes_by_readback_without_duplicate_put(self):
        self.api.fail_update = True
        with self.assertRaises(TimeoutError):
            await self.apply()
        self.api.fail_update = False
        await self.apply()
        self.assertEqual(self.api.updates, 1)
        self.assertEqual(self.journal.value.phase, 'verified')
    async def test_reverse_recovery_retains_original_metadata(self):
        self.observer.observe.return_value = tasks('image:new', 'image:old')
        with self.assertRaises(LifecycleStateError):
            await self.apply()
        self.api.next_fingerprint = SOURCE
        self.observer.observe.return_value = tasks('image:old')
        original = StackDefinition(name='swagger', compose_content='old')
        await self.operation().apply(original, {'PRIVATE': 'do-not-persist'}, {'ui': 'image:old'}, SOURCE,
                                     ownership(), self.callback, recovery=True)
        self.assertEqual(self.journal.value.recovery_of, TARGET)
        self.assertEqual(self.journal.value.recovery_source, ownership())
        self.assertEqual(self.journal.value.result.definition_fingerprint, SOURCE)
    async def test_changed_created_resource_control_cannot_be_adopted_on_resume(self):
        self.api = Api(False)
        self.observer.observe.return_value = tasks('image:new', 'image:old')
        with self.assertRaises(LifecycleStateError):
            await self.apply(owner=None)
        self.api.current = replace(self.api.current, ownership=ownership(TARGET).model_copy(update={'resource_control_id': 99}))
        self.observer.observe.return_value = tasks()
        with self.assertRaises(LifecycleStateError):
            await self.apply(owner=None)
        self.callback.assert_not_awaited()

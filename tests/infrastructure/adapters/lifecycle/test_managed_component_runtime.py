"""Persisted management owner chooses exactly one writer under observed authority."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tests.domain.lifecycle.test_update_planning import update_fixture
from tests.application.services.deployment.test_managed_stack import Lease
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestSnapshot
from tiny_swarm_world.application.ports.lifecycle.managed_stack import ManagedStackSnapshot
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.lifecycle.models import InstallationProfileBinding, PortainerOwnership, installation_profile_name, migrate_manifest_v1
from tiny_swarm_world.domain.lifecycle.update_execution import UpdateStage
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_component_runtime import ManagedComponentRuntime
from tiny_swarm_world.infrastructure.adapters.lifecycle.component_runtime import image_reference


class ManagedComponentRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        catalog, manifest = update_fixture(('swagger',))
        self.manifest = migrate_manifest_v1(manifest)
        self.owner = PortainerOwnership(owner='portainer', endpoint_id=1, stack_id=2, resource_control_id=3,
            ownership_fingerprint='sha256:' + 'c' * 64, definition_fingerprint='sha256:' + 'd' * 64)
        self.manifest = self.manifest.model_copy(update={
            'stack_ownership': {'swagger': self.owner},
            'installation_profile': InstallationProfileBinding(profile_name=installation_profile_name(manifest.installation_id), routes=())})
        self.manifests = Mock()
        self.manifests.load.return_value = ManifestSnapshot(self.manifest, 'a' * 64)
        self.delegate = Mock()
        self.delegate.for_operation.return_value = self.delegate
        self.delegate.transition = AsyncMock(return_value=True)
        self.delegate.workflow = SimpleNamespace()
        self.operation = SimpleNamespace(intent=SimpleNamespace(profile=Mock()), lease=Lease(),
            verify_effective_routes=AsyncMock(), record_stack_ownership=AsyncMock())
        self.factory = AsyncMock(return_value=self.operation)
        self.api = Mock()
        members = {item.component_id: item for item in self.manifest.components if item.service_id == 'swagger'}
        content = 'services:\n' + ''.join(f'  {name}:\n    image: {image_reference(item.desired)}\n' for name, item in members.items())
        self.api.inspect.return_value = ManagedStackSnapshot(self.owner, StackDefinition(name='swagger', compose_content=content), {'PRIVATE': 'retained'})
        changed = next(item for item in catalog.services if item.service_id == 'swagger').update_targets[-1]
        self.stage = UpdateStage(service_id='swagger', component_id='swagger-ui', source=members['swagger-ui'].desired,
                                 target=changed.versions['swagger-ui'])
        self.runtime = ManagedComponentRuntime(self.delegate, self.manifests, self.root, self.api, Mock(), self.factory).for_operation(Lease())
    async def test_scoped_policy_requires_actual_awaited_admission(self):
        with self.assertRaises(LifecycleStateError):
            self.runtime.validate_manifest(self.manifest)
        await self.runtime.admit_runtime(LiveConsent(True, confirmed=True), recovery=False)
        self.runtime.validate_manifest(self.manifest)
        self.factory.assert_awaited_once()
        self.operation.verify_effective_routes.assert_awaited_once()
    async def test_portainer_owner_never_calls_direct_swarm_writer(self):
        managed = Mock()
        managed.apply = AsyncMock()
        async def applied(*args, **kwargs):
            await args[5](self.owner.model_copy(update={'definition_fingerprint': args[3]}))
        managed.apply.side_effect = applied
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.managed_component_runtime.ManagedStackOperation', return_value=managed):
            result = await self.runtime.transition(self.stage, LiveConsent(True, confirmed=True), recovery=False)
        self.assertTrue(result)
        self.delegate.transition.assert_not_awaited()
        self.assertIn('swagger', self.runtime.verified_stack_ownership)
        self.operation.record_stack_ownership.assert_awaited_once()
        self.assertEqual(managed.apply.call_args.args[1], {'PRIVATE': 'retained'})
    async def test_recovery_uses_same_management_writer_and_explicit_reverse_intent(self):
        managed = Mock()
        managed.apply = AsyncMock()
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.managed_component_runtime.ManagedStackOperation', return_value=managed):
            result = await self.runtime.transition(self.stage, LiveConsent(True, confirmed=True), recovery=True)
        self.assertTrue(result)
        self.assertTrue(managed.apply.call_args.kwargs['recovery'])
        self.delegate.transition.assert_not_awaited()
    async def test_foreign_saved_definition_blocks_before_managed_write(self):
        foreign = self.api.inspect.return_value.ownership.model_copy(update={'resource_control_id': 99})
        self.api.inspect.return_value = ManagedStackSnapshot(foreign, self.api.inspect.return_value.definition, {})
        result = await self.runtime.transition(self.stage, LiveConsent(True, confirmed=True), recovery=False)
        self.assertFalse(result)
        self.delegate.transition.assert_not_awaited()

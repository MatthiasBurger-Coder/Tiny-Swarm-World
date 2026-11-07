"""Release upgrade failure injection with real private manifest/journal storage."""
from tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch
import asyncio
import threading

from tests.domain.lifecycle.test_models import manifest_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.product_upgrade import ProductUpgradeService
from tiny_swarm_world.domain.lifecycle.models import ProductIdentity
from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductCheckpoint, ProductPlan, ProductRelease, SOURCE_REVISION, TARGET_REVISION, admit_release_pair
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_journal import JsonProductJournal
from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal
from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductConfigurationSource

# Exact field fixture from the strict controller at 9a81972c. The published
# target has manifest/component readers, but no product-upgrade command/model.
from typing import Literal
from tiny_swarm_world.domain.lifecycle.models import Contract, InstallationManifest


class LegacyProductRelease(Contract):
    product: ProductIdentity
    package_version: str


class LegacyProductPlan(Contract):
    source: LegacyProductRelease
    target: LegacyProductRelease
    manifest: InstallationManifest
    manifest_token: str | None
    adoption: bool
    configuration_changes: tuple[str, ...] = ()
    migrations: tuple[str, ...] = ('protected-infra-v1', 'installation-product-v1')
    component_changes: tuple[str, ...] = ()
    resource_bytes: int = 2147483648
    configuration_source: ProductConfigurationSource | None = None


class LegacyProductCheckpoint(Contract):
    plan: LegacyProductPlan
    stage: Literal['admitted', 'staging', 'staged', 'migrating', 'migrated', 'verifying', 'verified', 'switching', 'switched', 'committing', 'completed']
    service_identities: dict[str, str]


CONSENT = LiveConsent(True, confirmed=True)


def product_plan(token=None, *, adoption=False):
    source = ProductRelease(product=ProductIdentity(release='0.4.0', revision=SOURCE_REVISION,
        dependency_lock='sha256:' + 'a' * 64), package_version='0.2.0')
    target = ProductRelease(product=ProductIdentity(release='0.5.0', revision=TARGET_REVISION,
        dependency_lock='sha256:' + 'b' * 64), package_version='0.2.0')
    return ProductPlan(source=source, target=target,
        manifest=manifest_fixture().model_copy(update={'product': source.product}),
        manifest_token=token, adoption=adoption)


class ProductUpgradeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifests = JsonManifestRepository(self.root / 'manifest.json')
        original = product_plan()
        token = self.manifests.save(original.manifest, expected_token=None).token
        self.plan = original.model_copy(update={'manifest_token': token})
        self.installation = Mock()
        self.installation.plan.return_value = self.plan
        self.runtime = Mock(verify=AsyncMock(return_value={'portainer': 'stable-id'}))
        self.journal = JsonProductJournal(self.root / 'product-upgrade.json')
        self.service = ProductUpgradeService(self.manifests, self.installation, self.journal, self.runtime, operation_lock=FakeInstallationLock())

    async def test_preview_writes_nothing_and_separates_change_families(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        result = await self.service.preview('0.5.0')
        self.assertEqual(result['status'], 'preview')
        for key in ('product_changes', 'dependency_changes', 'configuration_changes', 'component_changes', 'state_changes'):
            self.assertIn(key, result)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})
        self.runtime.verify.assert_not_awaited()
        self.installation.stage.assert_not_called()

    async def test_bound_input_persistence_follows_authentication_and_precedes_checkpoint(self):
        order = []
        self.plan = self.plan.model_copy(update={'configuration_source': ProductConfigurationSource(
            reference='effective-infra-test-operation')})
        self.installation.plan.return_value = self.plan

        async def verify(manifest, *, plan=None):
            self.assertEqual(plan, self.plan)
            order.append('authenticated')
            return {'portainer': 'stable-id'}

        def bind(plan):
            self.assertFalse(self.journal.path.exists())
            self.assertEqual(order, ['authenticated'])
            order.append('bound')

        self.runtime.verify.side_effect = verify
        self.journal.source_binder = bind
        self.installation.stage.side_effect = LifecycleStateError('injected staging interruption')
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(order, ['authenticated', 'bound'])
        self.assertEqual(self.journal.load().stage, 'staging')

    async def test_failed_authentication_creates_no_input_binding(self):
        self.plan = self.plan.model_copy(update={'configuration_source': ProductConfigurationSource(
            reference='effective-infra-test-operation')})
        self.installation.plan.return_value = self.plan
        self.runtime.verify.side_effect = LifecycleStateError('authentication failed')
        binder = Mock()
        self.journal.source_binder = binder
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.5.0', consent=CONSENT)
        binder.assert_not_called()
        self.assertFalse(self.journal.path.exists())

    async def test_upgrade_preserves_all_other_manifest_fields_and_repeats_verified_noop(self):
        result = await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(result['status'], 'completed')
        expected = self.plan.manifest.model_copy(update={'product': self.plan.target.product})
        self.assertEqual(expected, self.manifests.load().manifest)
        self.assertEqual(self.journal.load().stage, 'completed')
        self.assertEqual(self.journal.path.stat().st_mode & 0o777, 0o600)
        result = await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(result['status'], 'no_op')
        self.assertTrue(all(call.kwargs['plan'] == self.plan for call in self.runtime.verify.await_args_list))
        self.installation.stage.assert_called_once()
        self.installation.verify_active.assert_called_once_with(self.plan)

    async def test_missing_consent_never_constructs_operation_or_writes_progress(self):
        result = await self.service.run('0.5.0', consent=LiveConsent(False))
        self.assertEqual(result['status'], 'refused')
        self.installation.plan.assert_not_called()
        self.assertIsNone(self.journal.load())

    async def test_rejects_unsupported_downgrade_before_progress(self):
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.4.0', consent=CONSENT)
        self.assertIsNone(self.journal.load())
        self.installation.plan.assert_not_called()

    async def test_failure_before_stage_leaves_source_and_can_resume_original_operation(self):
        self.installation.stage.side_effect = LifecycleStateError('stage unavailable')
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(self.journal.load().stage, 'staging')
        self.assertEqual(self.manifests.load().manifest, self.plan.manifest)
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.5.0', consent=CONSENT)
        self.installation.stage.side_effect = None
        result = await self.service.run('0.5.0', consent=CONSENT, recovery=True)
        self.assertEqual(result['status'], 'completed')

    async def test_runtime_identity_drift_prevents_activation_and_manifest_commit(self):
        self.runtime.verify.side_effect = [{'portainer': 'source-id'}, {'portainer': 'changed-id'}]
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.5.0', consent=CONSENT)
        self.installation.activate.assert_not_called()
        self.assertEqual(self.manifests.load().manifest, self.plan.manifest)

    async def test_manifest_failure_after_switch_resumes_without_repeating_staging(self):
        save = self.manifests.save
        self.manifests.save = Mock(side_effect=LifecycleStateError('disk'))
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(self.journal.load().stage, 'committing')
        self.manifests.save = save
        result = await self.service.run('0.5.0', consent=CONSENT, recovery=True)
        self.assertEqual(result['status'], 'completed')
        self.installation.stage.assert_called_once()
        self.installation.migrate.assert_called_once()

    async def test_crash_after_manifest_commit_before_checkpoint_is_recoverable(self):
        await self.service.run('0.5.0', consent=CONSENT)
        self.journal.save(self.journal.load().model_copy(update={'stage': 'committing'}))
        result = await self.service.run('0.5.0', consent=CONSENT, recovery=True)
        self.assertEqual(result['status'], 'completed')

    async def test_noop_must_reverify_runtime_and_active_product(self):
        await self.service.run('0.5.0', consent=CONSENT)
        self.runtime.verify.return_value = {'portainer': 'unrelated'}
        with self.assertRaises(LifecycleStateError):
            await self.service.run('0.5.0', consent=CONSENT)

    async def test_explicit_adoption_is_only_committed_after_verification(self):
        self.manifests.path.unlink()
        self.plan = self.plan.model_copy(update={'manifest_token': None, 'adoption': True})
        self.installation.plan.return_value = self.plan
        result = await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(self.manifests.load().manifest.installation_id, self.plan.manifest.installation_id)

    async def test_component_and_gateway_writers_are_blocked_by_product_checkpoint(self):
        self.journal.save(ProductCheckpoint(plan=self.plan, stage='staging', service_identities={}))
        for gateway in (False, True):
            journal = JsonUpdateJournal(self.root / 'component-update.json', gateway=gateway)
            with self.subTest(gateway=gateway), self.assertRaises(LifecycleStateError):
                with journal.exclusive():
                    pass

    async def test_recovery_preview_is_pinned_and_read_only(self):
        self.journal.save(ProductCheckpoint(plan=self.plan, stage='staging', service_identities={}))
        before = self.journal.path.read_bytes()
        result = await self.service.preview('0.5.0', recovery=True)
        self.assertEqual(result['checkpoint'], 'staging')
        self.assertEqual(self.journal.path.read_bytes(), before)
        self.installation.plan.assert_not_called()

    async def test_cancellation_retains_shared_lock_until_started_mutation_finishes(self):
        started, release = threading.Event(), threading.Event()
        def staging(plan):
            started.set()
            if not release.wait(5):
                raise AssertionError('test did not release staging worker')
        self.installation.stage.side_effect = staging
        operation = asyncio.create_task(self.service.run('0.5.0', consent=CONSENT))
        try:
            self.assertTrue(await asyncio.to_thread(started.wait, 2))
            operation.cancel()
            await asyncio.sleep(0)
            operation.cancel()
            await asyncio.sleep(0)
            with self.assertRaises(LifecycleStateError):
                with self.journal.exclusive():
                    pass
            self.assertFalse(operation.done())
        finally:
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await operation
        with self.journal.exclusive():
            self.assertEqual(self.journal.load().stage, 'staging')

    def test_release_admission_distinguishes_real_release_from_package_alias(self):
        admit_release_pair(self.plan.source, self.plan.target)
        for target in (self.plan.target.model_copy(update={'package_version': '0.5.0'}),
                       self.plan.target.model_copy(update={'product': self.plan.source.product})):
            with self.assertRaises(ValueError):
                admit_release_pair(self.plan.source, target)

    async def test_legacy_target_keeps_v1_and_v2_source_cannot_reach_runtime(self):
        from tiny_swarm_world.domain.lifecycle.models import migrate_manifest_v1

        await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(self.manifests.load().manifest.schema_version, 1)
        self.assertEqual(self.plan.target.supported_manifest_schemas, (1,))
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ProductPlan.model_validate({**self.plan.model_dump(), 'manifest': migrate_manifest_v1(self.plan.manifest)})

    async def test_forged_or_unknown_target_reader_blocks_before_runtime_or_stage(self):
        from tiny_swarm_world.domain.lifecycle.models import migrate_manifest_v1

        self.installation.plan.return_value = self.plan.model_copy(update={'manifest': migrate_manifest_v1(self.plan.manifest)})
        with self.assertRaises(ValueError):
            await self.service.run('0.5.0', consent=CONSENT)
        self.runtime.verify.assert_not_awaited()
        self.installation.stage.assert_not_called()
        self.installation.activate.assert_not_called()
        self.assertIsNone(self.journal.load())
        with self.assertRaises(ValueError):
            ProductRelease.model_validate({**self.plan.target.model_dump(), 'supported_manifest_schemas': (1, 2)})
        self.assertEqual(self.manifests.load().manifest, self.plan.manifest)

    async def test_outer_operation_precedes_product_journal_and_missing_lock_is_not_a_fallback(self):
        lock = FakeInstallationLock()
        self.service.operation_lock = lock
        await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(lock.events[:2], ['operation:product-upgrade', 'journal:product'])
        self.assertEqual(lock.events[-2:], ['journal-release:product', 'operation-release:product-upgrade'])
        self.service.operation_lock = None
        with self.assertRaisesRegex(LifecycleStateError, 'lock'):
            await self.service.run('0.5.0', consent=CONSENT)

    def test_old_checkpoint_reader_authority_defaults_one_without_retrofit(self):
        import json

        checkpoint = ProductCheckpoint(plan=self.plan, stage='admitted', service_identities={'portainer': 'stable-id'})
        payload = json.loads(checkpoint.model_dump_json())
        payload['plan']['source'].pop('supported_manifest_schemas', None)
        payload['plan']['target'].pop('supported_manifest_schemas', None)
        payload['plan'].pop('profile_intent', None)
        self.journal.path.write_text(json.dumps(payload))
        observed = self.journal.load()
        self.assertEqual(observed.plan.target.supported_manifest_schemas, (1,))
        self.assertIsNone(observed.plan.profile_intent)
        self.assertEqual(json.loads(self.journal.path.read_text()), payload)
        payload['plan']['target']['supported_manifest_schemas'] = [1, 2]
        self.journal.path.write_text(json.dumps(payload))
        with self.assertRaises(LifecycleStateError):
            self.journal.load()

    async def test_actual_completed_journal_retains_strict_legacy_controller_shape(self):
        import json

        await self.service.run('0.5.0', consent=CONSENT)
        raw = self.journal.path.read_bytes()
        payload = json.loads(raw)
        self.assertNotIn('profile_intent', payload['plan'])
        self.assertNotIn('supported_manifest_schemas', payload['plan']['source'])
        self.assertNotIn('supported_manifest_schemas', payload['plan']['target'])
        self.assertEqual(payload['plan']['manifest']['schema_version'], 1)
        legacy = LegacyProductCheckpoint.model_validate_json(raw)
        self.assertEqual(legacy.stage, 'completed')
        self.assertEqual(legacy.plan.target.product, self.plan.target.product)
        # Exercise the actual durable loader with the strict old controller model.
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_journal.ProductCheckpoint', LegacyProductCheckpoint):
            self.assertEqual(self.journal.load(), legacy)
        self.assertEqual(self.journal.path.read_bytes(), raw)
        self.assertEqual((await self.service.run('0.5.0', consent=CONSENT))['status'], 'no_op')
        self.assertEqual(self.journal.path.read_bytes(), raw)

    def test_nondefault_reader_metadata_is_retained_and_legacy_reader_rejects_it(self):
        import json
        from pydantic import ValidationError

        future = self.plan.target.model_copy(update={
            'product': self.plan.target.product.model_copy(update={'revision': 'e' * 40}),
            'supported_manifest_schemas': (1, 2),
        })
        future = ProductRelease.model_validate(future.model_dump())
        payload = json.loads(future.model_dump_json())
        self.assertEqual(payload['supported_manifest_schemas'], [1, 2])
        self.assertEqual(ProductRelease.model_validate_json(future.model_dump_json()), future)
        malformed_schemas: tuple[object, ...] = (None, [], [True], [1.0], ['1'], [0], [3], [1, 1], [2, 1])
        for invalid in malformed_schemas:
            with self.subTest(schemas=invalid), self.assertRaises(ValidationError):
                ProductRelease.model_validate_json(json.dumps({**payload, 'supported_manifest_schemas': invalid}))
        with self.assertRaises(ValidationError):
            LegacyProductRelease.model_validate_json(future.model_dump_json())

    def test_bound_intent_is_never_discarded_to_activate_a_reader_one_target(self):
        from tiny_swarm_world.domain.lifecycle.models import InstallationProfileIntent

        manifest = self.plan.manifest
        intent = InstallationProfileIntent(
            operation_id='a' * 32, operation_kind='product-upgrade',
            installation_id=manifest.installation_id, controller_revision='c' * 40,
            product_source_revision=manifest.product.revision,
            product_target_revision=self.plan.target.product.revision,
            incus_version='6.0.5', manifest_token=self.plan.manifest_token,
            requested_services=manifest.requested_services, resolved_services=manifest.resolved_services,
            service_exposure=manifest.effective_exposure(), stack_ownership=manifest.effective_stack_ownership(),
            profile=None,
        )
        forged = self.plan.model_copy(update={'profile_intent': intent})
        self.assertIn('profile_intent', forged.model_dump())
        with self.assertRaisesRegex(ValueError, 'bound profile intent'):
            ProductPlan.model_validate(forged.model_dump())

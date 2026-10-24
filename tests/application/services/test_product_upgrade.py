"""Release upgrade failure injection with real private manifest/journal storage."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock
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
        self.service = ProductUpgradeService(self.manifests, self.installation, self.journal, self.runtime)

    async def test_preview_writes_nothing_and_separates_change_families(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        result = await self.service.preview('0.5.0')
        self.assertEqual(result['status'], 'preview')
        for key in ('product_changes', 'dependency_changes', 'configuration_changes', 'component_changes', 'state_changes'):
            self.assertIn(key, result)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})
        self.runtime.verify.assert_not_awaited()
        self.installation.stage.assert_not_called()

    async def test_upgrade_preserves_all_other_manifest_fields_and_repeats_verified_noop(self):
        result = await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(result['status'], 'completed')
        expected = self.plan.manifest.model_copy(update={'product': self.plan.target.product})
        self.assertEqual(expected, self.manifests.load().manifest)
        self.assertEqual(self.journal.load().stage, 'completed')
        self.assertEqual(self.journal.path.stat().st_mode & 0o777, 0o600)
        result = await self.service.run('0.5.0', consent=CONSENT)
        self.assertEqual(result['status'], 'no_op')
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
            with self.subTest(gateway=gateway), self.assertRaises(LifecycleStateError):
                with JsonUpdateJournal(self.root / 'component-update.json', gateway=gateway).exclusive():
                    self.fail('writer admitted')

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
            with self.assertRaises(LifecycleStateError):
                with self.journal.exclusive():
                    self.fail('cancelled worker released shared lock early')
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

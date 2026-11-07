"""Synthetic transition policies exercise real Classic convergence and persistence."""
from tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import json
from unittest.mock import AsyncMock, Mock, patch

from tests.domain.lifecycle.test_update_planning import update_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.component_execution import ComponentUpdateExecution
from tiny_swarm_world.application.services.component_updates import ComponentUpdateService
from tiny_swarm_world.application.services.deployment.workflows import DeploymentWorkflowStatus
from tiny_swarm_world.application.services.platform.workflow.update import ClassicUpdateWorkflow
from tiny_swarm_world.domain.deployment import ComposeServiceDefinition
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.domain.update import UpdateRuntimeObservation, UpdateTaskObservation
from tiny_swarm_world.infrastructure.adapters.lifecycle.component_runtime import ClassicComponentRuntime, image_reference
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal
from tiny_swarm_world.infrastructure.adapters.update.json_state_store import JsonUpdateStateStore

CONSENT = LiveConsent(True, confirmed=True)


class ComponentExecutionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        catalog, self.original = update_fixture()
        self.catalog = catalog.model_copy(update={'services': tuple(item.model_copy(update={
            'backup_policy': 'not-applicable', 'update_transitions': tuple(t.model_copy(update={
                'backup_required': False, 'migrations': ()}) for t in item.update_transitions)}) for item in catalog.services)})
        self.catalogs = Mock()
        self.catalogs.load.return_value = self.catalog
        self.manifests = JsonManifestRepository(self.root / '.tiny-swarm-world/installation/manifest.json')
        self.manifests.save(self.original, expected_token=None)
        self.journal = JsonUpdateJournal(self.manifests.path.parent / 'component-update.json')
        self.images = {item.component_id: image_reference(item.desired) for item in self.original.components if item.service_id in {'nexus', 'jenkins'}}
        self.identities = {name: 'service-' + name for name in self.images}
        self.fail = set()
        self.old_tasks = set()
        self.calls = []
        self.observer = Mock()
        self.observer.observe = AsyncMock(side_effect=self.observe)
        compose = Mock()
        compose.get_services_of.side_effect = lambda stack: (ComposeServiceDefinition(name=stack, image_ref=self.images[stack]),)
        self.store = JsonUpdateStateStore(self.root / 'classic-updates')
        workflow = ClassicUpdateWorkflow(compose, self.deployment, self.store, self.observer,
                                         verification_attempts=2, poll_interval_seconds=0, operation_lock=FakeInstallationLock())
        self.runtime = ClassicComponentRuntime(workflow)
        self.planning = ComponentUpdateService(self.manifests, self.catalogs)
        self.executor = ComponentUpdateExecution(self.planning, self.manifests, self.journal, self.runtime, operation_lock=FakeInstallationLock())

    async def observe(self, stack, name):
        image = self.images[name]
        task = image_reference(next(c.desired for c in self.original.components if c.component_id == name)) if name in self.old_tasks else image
        return UpdateRuntimeObservation(stack, name, self.identities[name], 1, image, 1,
                                        (UpdateTaskObservation('task-' + name, task, 'running', 'running'),), 'completed')

    def deployment(self, plan, *, operation_lease=None):
        async def run():
            self.calls.append(plan)
            if plan.service_name in self.fail:
                return SimpleNamespace(status=DeploymentWorkflowStatus.FAILED_TO_APPLY, verification_results=())
            self.images[plan.service_name] = plan.target_image
            return SimpleNamespace(status=DeploymentWorkflowStatus.COMPLETED, verification_results=())
        return SimpleNamespace(run=run)

    async def apply(self, selection=('nexus', 'jenkins'), **kwargs):
        return await self.executor.run(selection, consent=CONSENT, **kwargs)

    async def test_batch_convergence_commit_preservation_and_repeat_noop(self):
        result = await self.apply()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual([p.service_name for p in self.calls], ['nexus', 'jenkins'])
        current = self.manifests.load().manifest
        self.assertEqual(current.credential_references, self.original.credential_references)
        self.assertEqual(current.resolved_services, self.original.resolved_services)
        for component in current.components:
            if component.service_id in {'jenkins', 'nexus'}:
                self.assertEqual(component.desired.image_digest, 'sha256:' + 'b' * 64)
                self.assertEqual(component.observed, component.desired)
            else:
                self.assertIn(component, self.original.components)
        calls = len(self.calls)
        observed = self.observer.observe.await_count
        metadata = self.store.load('nexus', 'nexus')
        journal = self.journal.load()
        self.assertEqual((await self.apply())['status'], 'completed')
        self.assertEqual(len(self.calls), calls)
        self.assertGreater(self.observer.observe.await_count, observed)
        self.assertEqual(self.store.load('nexus', 'nexus'), metadata)
        self.assertEqual(self.journal.load().original, journal.original)

    async def test_single_service_updates_only_selected_service(self):
        self.assertEqual((await self.apply(('nexus',)))['status'], 'completed')
        self.assertEqual([p.service_name for p in self.calls], ['nexus'])
        self.assertEqual(next(c for c in self.manifests.load().manifest.components if c.service_id == 'jenkins'),
                         next(c for c in self.original.components if c.service_id == 'jenkins'))

    async def test_partial_deployment_failure_and_resume(self):
        # A simulated deployment failure must retain the original retry intent.
        self.fail.add('jenkins')
        result = await self.apply()
        self.assertEqual(result['status'], 'partial')
        self.assertEqual([s['outcome'] for s in result['stages']], ['committed', 'failed'])
        original_metadata = self.store.load('jenkins', 'jenkins')
        self.fail.clear()
        self.assertEqual((await self.apply())['status'], 'completed')
        self.assertEqual([p.service_name for p in self.calls], ['nexus', 'jenkins', 'jenkins'])
        self.assertEqual(original_metadata, self.store.load('jenkins', 'jenkins'))

    async def test_healthy_old_tasks_cannot_establish_success_and_waits_are_bounded(self):
        self.old_tasks.add('nexus')
        result = await self.apply()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.observer.observe.await_count, 3)
        self.assertEqual(self.manifests.load().manifest, self.original)
        self.assertEqual(self.journal.load().stages[1].outcome, 'pending')

    async def test_configuration_commit_interruption_resume_and_setup_guard(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import require_settled_updates
        save = self.manifests.save
        self.manifests.save = Mock(side_effect=LifecycleStateError('commit interrupted'))
        with self.assertRaisesRegex(LifecycleStateError, 'interrupted'):
            await self.apply()
        self.assertEqual(self.journal.load().stages[0].outcome, 'runtime_verified')
        with self.assertRaisesRegex(LifecycleStateError, 'incomplete'):
            require_settled_updates(self.root)
        self.manifests.save = save
        self.assertEqual((await self.apply())['status'], 'completed')
        self.assertEqual([p.service_name for p in self.calls], ['nexus', 'jenkins'])
        require_settled_updates(self.root)

    async def test_recovery_reverses_order_preserves_metadata_and_repeat_is_verified_noop(self):
        await self.apply()
        metadata = self.store.load('nexus', 'nexus')
        intent = self.journal.load().plan
        result = await self.apply(recovery=True)
        self.assertEqual(result['status'], 'recovered')
        self.assertEqual([p.service_name for p in self.calls], ['nexus', 'jenkins', 'jenkins', 'nexus'])
        for item in self.manifests.load().manifest.components:
            self.assertEqual(item.desired, next(c.desired for c in self.original.components if c.component_id == item.component_id))
        calls = len(self.calls)
        self.assertEqual((await self.apply(recovery=True))['status'], 'recovered')
        self.assertEqual(len(self.calls), calls)
        self.assertEqual(self.store.load('nexus', 'nexus'), metadata)
        self.assertEqual(self.journal.load().plan, intent)
        self.assertEqual(self.journal.load().original, self.original)

    async def test_recovery_of_partial_batch_skips_unreached_services(self):
        self.fail.add('nexus')
        self.assertEqual((await self.apply())['status'], 'failed')
        self.fail.clear()
        self.assertEqual((await self.apply(recovery=True))['status'], 'recovered')
        self.assertEqual(len(self.calls), 1)

    async def test_refusal_and_unsupported_policy_do_not_start_runtime_or_write_intent(self):
        self.assertEqual((await self.executor.run(('nexus',), consent=None))['status'], 'refused')
        self.assertIsNone(self.journal.load())
        self.catalogs.load.return_value = update_fixture()[0]
        with self.assertRaisesRegex(LifecycleStateError, 'Backup/migration'):
            await self.apply()
        self.assertIsNone(self.journal.load())
        self.observer.observe.assert_not_awaited()

    async def test_drift_and_different_operation_block_resume(self):
        self.fail.add('nexus')
        await self.apply()
        with self.assertRaisesRegex(LifecycleStateError, 'Another transition'):
            await self.apply(('jenkins',))
        snapshot = self.manifests.load()
        changed = snapshot.manifest.model_copy(update={'installation_id': '12345678-1234-1234-1234-123456789012'})
        self.manifests.save(changed, expected_token=snapshot.token)
        with self.assertRaisesRegex(LifecycleStateError, 'another installation'):
            await self.apply()

    async def test_committed_pins_feed_later_compose_artifacts_and_setup_inventory(self):
        from unittest.mock import patch
        from tests.domain.lifecycle.test_update_planning import ROOT
        from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_state import SetupSelectionState
        from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
        from tiny_swarm_world.infrastructure.composition_artifacts import _selected_image_contracts
        from tiny_swarm_world.infrastructure.project_paths import ProjectPaths
        from tiny_swarm_world.domain.lifecycle.selection import plan_selection
        await self.apply()
        manifest = self.manifests.load().manifest
        paths = ProjectPaths.from_roots(self.root, ROOT / 'infra')
        with patch.dict('os.environ', {}, clear=True):
            repository = ComposeFileRepositoryYaml(project_paths=paths, write_logs=False)
            self.assertEqual(repository.get_services_of('nexus')[0].image_ref, self.images['nexus'])
            self.assertEqual(repository.get_services_of('jenkins')[0].image_ref, self.images['jenkins'])
            contracts = _selected_image_contracts(None, self.root)
            self.assertEqual(next(c.image_ref for c in contracts if c.build_context == 'nexus'), self.images['nexus'])
            lifecycle = SimpleNamespace(manifests=self.manifests, catalog=self.catalogs)
            plan = plan_selection(self.catalog, ('nexus', 'jenkins'), persisted=manifest)
            state = SetupSelectionState(lifecycle, plan, self.root)
            self.assertEqual(state._effective_inventory(manifest), manifest.components)
            # A second image transition receives committed sibling pins in the same stack.
            target = 'registry.test/next@sha256:' + 'c' * 64
            update_repository = ComposeFileRepositoryYaml(project_paths=paths, write_logs=False,
                                                          transition_overrides={'TSW_JENKINS_IMAGE': target})
            self.assertEqual(update_repository.get_services_of('jenkins')[0].image_ref, target)
            self.assertEqual(update_repository.get_services_of('nexus')[0].image_ref, self.images['nexus'])

    async def test_conflicting_environment_cannot_restore_old_desired_configuration(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import effective_image_environment
        await self.apply()
        with self.assertRaisesRegex(LifecycleStateError, 'conflicts'):
            effective_image_environment({'TSW_NEXUS_IMAGE': 'old:1'}, self.root)

    async def test_interrupted_final_journal_commit_resumes_without_redeployment(self):
        save = self.journal.save
        interrupted = False
        def save_until_commit(batch):
            nonlocal interrupted
            if not interrupted and batch.stages[0].outcome == 'committed':
                interrupted = True
                raise LifecycleStateError('journal interrupted')
            save(batch)
        self.journal.save = save_until_commit
        with self.assertRaisesRegex(LifecycleStateError, 'interrupted'):
            await self.apply()
        self.assertEqual(self.journal.load().stages[0].outcome, 'runtime_verified')
        self.journal.save = save
        self.assertEqual((await self.apply())['status'], 'completed')
        self.assertEqual([p.service_name for p in self.calls], ['nexus', 'jenkins'])

    async def test_journal_failure_before_apply_starts_no_deployment(self):
        self.journal.save = Mock(side_effect=LifecycleStateError('unavailable'))
        with self.assertRaisesRegex(LifecycleStateError, 'unavailable'):
            await self.apply()
        self.assertEqual(self.calls, [])
        self.observer.observe.assert_not_awaited()

    async def test_runtime_identity_change_cannot_commit_target(self):
        deploy = self.deployment
        def changed(plan, *, operation_lease=None):
            workflow = deploy(plan)
            run = workflow.run
            async def run_changed():
                result = await run()
                self.identities[plan.service_name] = 'replacement-service'
                return result
            return SimpleNamespace(run=run_changed)
        self.runtime.workflow.deployment_workflow_factory = changed
        self.assertEqual((await self.apply())['status'], 'failed')
        self.assertEqual(self.manifests.load().manifest, self.original)

    async def test_batch_lock_prevents_second_executor(self):
        with self.journal.exclusive():
            with self.assertRaisesRegex(LifecycleStateError, 'another update'):
                await self.apply()
        self.assertEqual(self.calls, [])

    async def test_actual_stack_deployment_receives_pins_and_preserves_credentials(self):
        from unittest.mock import patch
        from tests.domain.lifecycle.test_update_planning import ROOT
        from tests.infrastructure.test_composition import _required_infisical_bootstrap_env
        from tiny_swarm_world.infrastructure import composition
        from tiny_swarm_world.infrastructure.project_paths import ProjectPaths
        await self.apply()
        (self.root / 'src/tiny_swarm_world').mkdir(parents=True)
        (self.root / 'infra/config').mkdir(parents=True)
        (self.root / 'AGENTS.md').touch()
        (self.root / 'QUALITY.md').touch()
        paths = ProjectPaths.from_roots(self.root, ROOT / 'infra')
        environment = _required_infisical_bootstrap_env()
        with patch.dict('os.environ', environment, clear=True), patch.object(composition, 'default_project_paths', return_value=paths), patch.object(composition, 'LxcSwarmRuntime'), patch.object(composition, 'InfisicalCliClient', side_effect=AssertionError('Update cannot bootstrap Infisical')):
            services = composition.build_lxc_deployment_services(backend=composition.ManagedLxcBackend.INCUS,
                service_profile='service-access', update_stack_name='jenkins')
            self.assertEqual(services.workflows.bootstrap.steps, ())
            self.assertEqual(len(services.workflows.apply.steps), 1)
            step = services.workflows.apply.steps[0]
            step.swarm_runtime = Mock()
            await step.run()
            definition, deployed_env = step.swarm_runtime.deploy_stack.call_args.args
            self.assertEqual(definition.name, 'jenkins')
            self.assertEqual(deployed_env['TSW_JENKINS_IMAGE'], self.images['jenkins'])
            self.assertEqual(deployed_env['TSW_JENKINS_ADMIN_PASSWORD'], environment['TSW_JENKINS_ADMIN_PASSWORD'])
            self.assertEqual(dict(__import__('os').environ), environment)
        # A normal later deployment must pass the same pin to actual interpolation.
        with patch.dict('os.environ', environment, clear=True), patch.object(composition, 'default_project_paths', return_value=paths), patch.object(composition, 'LxcSwarmRuntime'):
            services = composition.build_lxc_deployment_services(backend=composition.ManagedLxcBackend.INCUS,
                                                                service_profile='default')
            step = next(s for s in (*services.workflows.bootstrap.steps, *services.workflows.apply.steps) if getattr(getattr(s, 'service_stack', None), 'stack_name', None) == 'nexus')
            step.swarm_runtime = Mock()
            await step.run()
            self.assertEqual(step.swarm_runtime.deploy_stack.call_args.args[1]['TSW_NEXUS_IMAGE'], self.images['nexus'])

    async def test_journal_semantic_corruption_blocks_empty_duplicate_or_changed_stage(self):
        import json
        await self.apply()
        batch = self.journal.load()
        payload = json.loads(batch.model_dump_json())
        for stages in ([], [payload['stages'][0], payload['stages'][0]],
                       [{**payload['stages'][0], 'component_id': 'unrelated'}, payload['stages'][1]]):
            corrupted = {**payload, 'stages': stages}
            self.journal.path.write_text(json.dumps(corrupted))
            with self.assertRaisesRegex(LifecycleStateError, 'Invalid'):
                self.journal.load()
        self.journal.save(batch)

    async def test_recovery_preview_is_readonly_and_contains_original_targets(self):
        from tiny_swarm_world.application.services.component_execution import component_recovery_preview
        await self.apply()
        before = self.journal.path.read_bytes()
        calls = len(self.calls)
        preview = component_recovery_preview(self.journal, ('jenkins', 'nexus'))
        self.assertEqual(preview['status'], 'preview')
        self.assertEqual([s['service_id'] for s in preview['stages']], ['jenkins', 'nexus'])
        self.assertEqual(preview['stages'][0]['to']['image_digest'], 'sha256:' + 'a' * 64)
        self.assertEqual(self.journal.path.read_bytes(), before)
        self.assertEqual(len(self.calls), calls)

    async def test_already_target_runtime_retains_recovery_source_before_commit(self):
        for name in self.images:
            self.images[name] = self.images[name].replace('a' * 64, 'b' * 64)
        self.assertEqual((await self.apply())['status'], 'completed')
        self.assertEqual(self.calls, [])
        state = self.store.load('nexus', 'nexus')
        self.assertIn('a' * 64, state.plan.source_image)
        self.assertEqual((await self.apply(recovery=True))['status'], 'recovered')
        self.assertEqual([p.service_name for p in self.calls], ['jenkins', 'nexus'])
        self.assertEqual(self.store.load('nexus', 'nexus'), state)

    async def test_multicomponent_bundle_commits_each_image_and_keeps_sibling_pins_in_deployment(self):
        from unittest.mock import patch
        from tests.domain.lifecycle.test_update_planning import ROOT
        from tests.infrastructure.test_composition import _required_infisical_bootstrap_env
        from tiny_swarm_world.infrastructure import composition
        from tiny_swarm_world.infrastructure.project_paths import ProjectPaths
        catalog, original = update_fixture(('pulsar',))
        catalog = catalog.model_copy(update={'services': tuple(item.model_copy(update={
            'backup_policy': 'not-applicable', 'update_transitions': tuple(t.model_copy(update={
                'backup_required': False, 'migrations': ()}) for t in item.update_transitions)}) for item in catalog.services)})
        self.original = original
        self.catalogs.load.return_value = catalog
        self.manifests.save(original, expected_token=self.manifests.load().token)
        self.images = {c.component_id: image_reference(c.desired) for c in original.components if c.service_id == 'pulsar'}
        self.identities = {name: 'id-' + name for name in self.images}
        self.runtime.workflow.compose_repository.get_services_of.side_effect = lambda stack: tuple(
            ComposeServiceDefinition(name=name, image_ref=image) for name, image in self.images.items())
        self.assertEqual((await self.apply(('pulsar',)))['status'], 'completed')
        self.assertEqual(len(self.calls), 3)
        self.assertTrue(all(s.outcome == 'committed' for s in self.journal.load().stages))
        (self.root / 'src/tiny_swarm_world').mkdir(parents=True)
        (self.root / 'infra/config').mkdir(parents=True)
        (self.root / 'AGENTS.md').touch()
        (self.root / 'QUALITY.md').touch()
        paths = ProjectPaths.from_roots(self.root, ROOT / 'infra')
        new_manager = 'registry.test/manager@sha256:' + 'c' * 64
        with patch.dict('os.environ', _required_infisical_bootstrap_env(), clear=True), patch.object(composition, 'default_project_paths', return_value=paths), patch.object(composition, 'LxcSwarmRuntime'):
            services = composition.build_lxc_deployment_services(backend=composition.ManagedLxcBackend.INCUS,
                service_profile='service-access', update_stack_name='pulsar',
                image_overrides={'TSW_PULSAR_MANAGER_IMAGE': new_manager})
            step = services.workflows.apply.steps[0]
            step.swarm_runtime = Mock()
            await step.run()
            environment = step.swarm_runtime.deploy_stack.call_args.args[1]
        self.assertEqual(environment['TSW_PULSAR_IMAGE'], self.images['pulsar'])
        self.assertEqual(environment['TSW_PULSAR_MANAGER_BOOTSTRAP_IMAGE'], self.images['pulsar-manager-bootstrap'])
        self.assertEqual(environment['TSW_PULSAR_MANAGER_IMAGE'], new_manager)

    async def test_interrupted_recovery_blocks_setup_and_unrelated_new_batch(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import require_settled_updates
        await self.apply()
        save = self.journal.save
        def stop_after_first_recovery(batch):
            save(batch)
            if batch.direction == 'recover' and sum(s.outcome == 'recovered' for s in batch.stages) == 1:
                raise LifecycleStateError('recovery interrupted')
        self.journal.save = stop_after_first_recovery
        with self.assertRaisesRegex(LifecycleStateError, 'interrupted'):
            await self.apply(recovery=True)
        self.journal.save = save
        self.assertEqual([s.outcome for s in self.journal.load().stages], ['committed', 'recovered'])
        with self.assertRaisesRegex(LifecycleStateError, 'incomplete'):
            require_settled_updates(self.root)
        with self.assertRaisesRegex(LifecycleStateError, 'Another transition'):
            await self.apply(('nexus',))
        self.assertEqual((await self.apply(recovery=True))['status'], 'recovered')
        require_settled_updates(self.root)

    async def test_component_reassignment_cannot_be_persisted_on_resume(self):
        self.fail.add('nexus')
        await self.apply()
        snapshot = self.manifests.load()
        components = tuple(c.model_copy(update={'service_id': 'jenkins'}) if c.component_id == 'nexus' else c
                           for c in snapshot.manifest.components)
        self.manifests.save(snapshot.manifest.model_copy(update={'components': components}), expected_token=snapshot.token)
        with self.assertRaisesRegex(LifecycleStateError, 'outside this update'):
            await self.apply()

    async def test_portainer_authentication_denial_never_commits_or_rotates_credentials(self):
        import json
        from tests.infrastructure.adapters.clients.test_portainer_http_client import _FakeSession, _FakeResponse, OPERATOR_CREDENTIAL
        from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
        session = _FakeSession(post_responses=[_FakeResponse(401, {'message': 'private-response'})], request_responses=[])
        client = PortainerHttpClient('https://portainer.local', 'admin', OPERATOR_CREDENTIAL, session=session)
        async def denied():
            client.get_endpoint_id_by_name('local')
        self.runtime.workflow.deployment_workflow_factory = lambda plan, **_options: SimpleNamespace(run=denied)
        result = await self.apply()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(self.manifests.load().manifest, self.original)
        self.assertEqual(session.post_calls[0]['json'], {'Username': 'admin', 'Password': OPERATOR_CREDENTIAL})
        self.assertEqual(len(session.post_calls), 1)
        self.assertEqual(session.request_calls, [])
        self.assertNotIn(OPERATOR_CREDENTIAL, json.dumps(result))
        self.assertNotIn('private-response', self.journal.path.read_text())

    async def test_outer_lock_is_required_and_success_migrates_after_runtime_verification(self):
        original_bytes = self.manifests.path.read_bytes()
        self.executor.operation_lock = None
        with self.assertRaisesRegex(LifecycleStateError, 'lock'):
            await self.apply()
        self.assertEqual(self.manifests.path.read_bytes(), original_bytes)
        self.assertIsNone(self.journal.load())
        self.assertEqual(self.calls, [])
        lock = FakeInstallationLock()
        self.executor.operation_lock = lock
        await self.apply()
        self.assertEqual(self.manifests.load().manifest.schema_version, 2)
        self.assertEqual(self.journal.load().original.schema_version, 1)
        self.assertNotIn('profile_intent', json.loads(self.journal.path.read_text()))
        self.assertIsNone(self.runtime.workflow.operation_lease)
        self.assertEqual(lock.events[0:2], ['operation:component-update', 'journal:component'])
        self.assertEqual(lock.events[-2:], ['journal-release:component', 'operation-release:component-update'])

    async def test_new_profile_policy_is_not_executed_by_legacy_component_runtime(self):
        from tiny_swarm_world.domain.lifecycle.models import InstallationProfileBinding, installation_profile_name, migrate_manifest_v1

        changed = migrate_manifest_v1(self.original)
        payload = changed.model_dump()
        payload['installation_profile'] = InstallationProfileBinding(
            profile_name=installation_profile_name(changed.installation_id), routes=())
        from tiny_swarm_world.domain.lifecycle.models import InstallationManifest
        changed = InstallationManifest.model_validate(payload)
        self.manifests.save(changed, expected_token=self.manifests.load().token)
        with self.assertRaisesRegex(LifecycleStateError, 'capability'):
            await self.apply()
        self.assertEqual(self.calls, [])
        self.assertIsNone(self.journal.load())
        self.assertIsNone(self.runtime.workflow.operation_lease)
        self.assertEqual(self.manifests.load().manifest, changed)

    async def test_runtime_lease_is_cleared_on_admission_failure_and_cancellation(self):
        with patch.object(self.planning, 'preview', side_effect=LifecycleStateError('stale')):
            with self.assertRaisesRegex(LifecycleStateError, 'stale'):
                await self.apply()
        self.assertIsNone(self.runtime.workflow.operation_lease)
        entered = asyncio.Event()
        async def wait_transition(*args, **kwargs):
            entered.set()
            await asyncio.Event().wait()
        with patch.object(self.runtime, 'transition', new=wait_transition):
            task = asyncio.create_task(self.apply())
            await entered.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertIsNone(self.runtime.workflow.operation_lease)
        self.assertFalse(self.executor.operation_lock.held)

    async def test_runtime_delegation_copies_authority_without_mutating_public_workflow(self):
        lock = FakeInstallationLock()
        with lock.exclusive('component-update') as lease:
            private = self.runtime.for_operation(lease)
            self.assertIsNot(private, self.runtime)
            self.assertIsNot(private.workflow, self.runtime.workflow)
            self.assertIs(private.workflow.operation_lease, lease)
            self.assertIsNone(self.runtime.workflow.operation_lease)
        with self.assertRaises(LifecycleStateError):
            private.workflow.operation_lease.require_active()
        self.assertIsNone(self.runtime.workflow.operation_lease)

    async def test_bound_intent_roundtrip_rejects_tampering_before_checkpoint_overwrite(self):
        from tiny_swarm_world.domain.lifecycle.models import InstallationProfileIntent
        from tiny_swarm_world.domain.lifecycle.update_execution import UpdateBatch
        import json

        await self.apply()
        batch = self.journal.load()
        original = batch.original
        intent = InstallationProfileIntent(operation_id='c' * 32, operation_kind='component-update',
            installation_id=original.installation_id, controller_revision='d' * 40,
            product_source_revision=original.product.revision, product_target_revision=None,
            incus_version='6.0.5', manifest_token=batch.plan.manifest_token,
            requested_services=original.requested_services, resolved_services=original.resolved_services,
            service_exposure=original.effective_exposure(), stack_ownership=original.effective_stack_ownership(), profile=None)
        bound = batch.model_copy(update={'profile_intent': intent})
        self.journal.save(bound)
        self.assertEqual(self.journal.load().profile_intent, intent)
        content = self.journal.path.read_bytes()
        forged = bound.model_copy(update={'profile_intent': intent.model_copy(update={'installation_id': 'private-intent-canary'})})
        with self.assertRaises(LifecycleStateError) as error:
            self.journal.save(forged)
        self.assertEqual(self.journal.path.read_bytes(), content)
        self.assertNotIn('private-intent-canary', str(error.exception))
        legacy = json.loads(content)
        legacy.pop('profile_intent', None)
        self.journal.path.write_text(json.dumps(legacy))
        self.assertIsNone(self.journal.load().profile_intent)
        self.assertEqual(json.loads(self.journal.path.read_text()), legacy)
        # An invalid explicitly supplied target must not acquire a new authority.
        legacy['profile_intent'] = intent.model_dump(mode='json')
        legacy['profile_intent']['product_target_revision'] = 'a' * 40
        with self.assertRaises(ValueError):
            UpdateBatch.model_validate_json(json.dumps(legacy))

    async def test_fresh_v1_already_target_noop_and_recovery_preserve_exact_manifest(self):
        targets = {name: version for service in self.catalog.services
                   if service.service_id in {'nexus', 'jenkins'}
                   for name, version in service.update_targets[0].versions.items()}
        self.original = self.original.model_copy(update={'components': tuple(
            item.model_copy(update={'desired': targets[item.component_id], 'observed': targets[item.component_id]})
            if item.component_id in targets else item for item in self.original.components)})
        self.manifests.save(self.original, expected_token=self.manifests.load().token)
        self.images = {name: image_reference(version) for name, version in targets.items()}
        self.assertIsNone(self.journal.load())
        self.assertEqual(self.original.schema_version, 1)
        plan = self.planning.preview(('nexus', 'jenkins'))
        self.assertEqual(plan.status, 'no_op')
        self.assertTrue(all(item.status == 'no_op' for item in plan.services))
        content = self.manifests.path.read_bytes()
        stamp = self.manifests.path.stat().st_mtime_ns
        self.assertEqual((await self.apply())['status'], 'completed')
        self.assertEqual(self.manifests.path.read_bytes(), content)
        self.assertEqual(self.manifests.path.stat().st_mtime_ns, stamp)
        self.assertEqual(self.manifests.load().manifest.schema_version, 1)
        self.assertEqual(self.calls, [])
        self.assertTrue(self.journal.load().settled)
        self.assertTrue(all(item.status == 'no_op' for item in self.journal.load().plan.services))
        self.assertEqual((await self.apply(recovery=True))['status'], 'recovered')
        self.assertEqual(self.manifests.path.read_bytes(), content)
        self.assertEqual(self.manifests.path.stat().st_mtime_ns, stamp)
        self.assertEqual(self.calls, [])

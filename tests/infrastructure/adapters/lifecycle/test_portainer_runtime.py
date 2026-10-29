"""Mocked integration of orchestration, cold backup, manager runtime and gateway API."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.domain.lifecycle.test_update_planning import update_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.portainer_upgrade import PortainerUpgradeService
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import PortainerCheckpoint, images, versions
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_journal import JsonPortainerJournal
from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_runtime import ClassicPortainerUpgradeRuntime


class PortainerRuntimeIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.manifests = JsonManifestRepository(self.root / 'manifest.json')
        _, manifest = update_fixture()
        manifest = manifest.model_copy(update={'components': tuple(item.model_copy(update={
            'desired': versions('2.45.0')[item.component_id], 'observed': versions('2.45.0')[item.component_id]})
            if item.service_id == 'portainer' else item for item in manifest.components)})
        self.manifests.save(manifest, expected_token=None)
        self.journal = JsonPortainerJournal(self.root / 'portainer-upgrade.json')
        self.version = '2.45.0'
        self.api_unavailable = False
        self.commands = []
        self.http_calls = []
        self.backup_digest = 'a' * 64
        self.fail_command = None
        self.owner_changed = False
        self.replicas = 1
        self.shell = Mock()
        self.shell.run_manager_shell.side_effect = self.command
        self.client = Mock()
        self.client._send.side_effect = self.request
        self.client.stack_request_timeout_seconds = 180
        self.runtime = ClassicPortainerUpgradeRuntime(self.shell, self.client, managed_stacks=('nexus',))
        self.service = PortainerUpgradeService(self.manifests, self.journal, self.runtime)

    def command(self, script, **kwargs):
        self.commands.append(script)
        if self.fail_command and self.fail_command in script:
            return SimpleNamespace(returncode=1, stdout='private runtime output')
        result = ''
        if script == 'docker service inspect portainer_portainer portainer_agent':
            result = json.dumps([{'ID': name + '-id', 'Spec': {'Name': name, 'Mode': mode, 'TaskTemplate': {
                'Placement': {'Constraints': ['node.role == manager']},
                'ContainerSpec': {'Image': images(self.version)[key], 'Mounts': [
                    {'Type': 'volume', 'Source': 'portainer_portainer_data', 'Target': '/data'}]}}}}
                for name, key, mode in (('portainer_portainer', 'portainer', {'Replicated': {'Replicas': self.replicas}}),
                                        ('portainer_agent', 'portainer-agent', {'Global': {}}))])
        elif script.startswith('docker info '):
            result = 'swarm-id'
        elif script.startswith('docker node ls'):
            result = 'manager-node-id'
        elif script.startswith('docker volume inspect'):
            result = json.dumps([{'Driver': 'local', 'Options': None, 'Mountpoint': '/var/lib/docker/volumes/portainer_portainer_data/_data'}])
        elif script.startswith('sha256sum '):
            result = self.backup_digest + '  state.tar'
        elif script.startswith('docker service scale'):
            self.replicas = int(script[-1])
        elif script.startswith('docker service update') and script.endswith('portainer_portainer'):
            self.version = '2.45.1' if images('2.45.1')['portainer'] in script else '2.45.0'
            self.api_unavailable = False
        return SimpleNamespace(returncode=0, stdout=result)

    def request(self, method, path, **kwargs):
        self.http_calls.append((method, path, kwargs))
        if self.api_unavailable:
            raise LifecycleStateError('API unavailable')
        endpoints = [{'Id': 1, 'Name': 'local', 'URL': 'unix:///var/run/docker.sock', 'Type': 1, 'Status': 1}]
        stacks = [{'Id': 10, 'Name': 'nexus', 'Type': 1, 'EndpointId': 1,
                   'ResourceControl': {'UserAccesses': [2 if self.owner_changed else 1]}}]
        data = {'/api/system/status': {'Version': self.version}, '/api/endpoints': endpoints,
                '/api/stacks': stacks, '/api/endpoints/1/docker/info': {'Swarm': {'Cluster': {'ID': 'swarm-id'}}},
                '/api/stacks/10': {'Env': [{'name': 'EXISTING', 'value': 'private-value'}]},
                '/api/stacks/10/file': {'StackFileContent': 'services: {nexus: {image: example/image}}'}}
        payload = {} if method == 'PUT' else data[path]
        return SimpleNamespace(json=lambda: payload, status_code=200)

    async def checkpoint(self, stage='upgrading', backup=True):
        before = await self.runtime.inspect()
        snapshot = self.manifests.load()
        checkpoint = PortainerCheckpoint(
            operation_id='operation', installation_id=snapshot.manifest.installation_id,
            original=snapshot.manifest, before=before, manifest_token=snapshot.token,
            stage=stage, backup_digest='sha256:' + self.backup_digest if backup else None,
        )
        self.journal.save(checkpoint)
        return checkpoint

    async def test_upgrade_blocks_matching_visible_inventory_without_effect(self):
        with self.assertRaisesRegex(LifecycleStateError, 'ownership proof'):
            await self.service.run(target=None, consent=LiveConsent(True, confirmed=True))
        self.assertIsNone(self.journal.load())
        self.assertFalse(any(method == 'PUT' for method, _, _ in self.http_calls))
        self.assertFalse(any('docker service scale' in item or 'docker service update' in item for item in self.commands))

    async def test_legacy_restore_with_api_down_remains_uncertain(self):
        await self.checkpoint()
        self.api_unavailable = True
        self.assertEqual((await self.service.run(target=None, consent=LiveConsent(True, confirmed=True), recovery=True))['status'], 'unknown')
        self.assertEqual(self.journal.load().stage, 'recovering')
        self.assertFalse(any(method == 'PUT' for method, _, _ in self.http_calls))

    async def test_tampered_backup_blocks_restore_before_scale_or_images(self):
        await self.checkpoint()
        self.backup_digest = 'b' * 64
        start = len(self.commands)
        self.assertEqual((await self.service.run(target=None, consent=LiveConsent(True, confirmed=True), recovery=True))['status'], 'unknown')
        self.assertFalse(any('docker service scale' in item or 'docker service update' in item for item in self.commands[start:]))

    async def test_admitted_cancel_keeps_source_and_waits_for_proof(self):
        await self.checkpoint('admitted', backup=False)
        self.assertEqual((await self.service.run(target=None, consent=LiveConsent(True, confirmed=True), recovery=True))['status'],
                         'recovery_pending_proof')
        self.assertEqual(self.journal.load().stage, 'recovery_pending_proof')
        self.assertEqual(self.version, '2.45.0')
        self.assertFalse(any('docker service update' in item for item in self.commands))

    async def test_disconnected_api_and_unsupported_runtime_block_without_mutation(self):
        self.api_unavailable = True
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=LiveConsent(True, confirmed=True))
        self.assertFalse(any('docker service scale' in item or 'docker service update' in item for item in self.commands))
        self.assertIsNone(self.journal.load())

    async def test_ownership_drift_fails_read_only_inspection(self):
        checkpoint = await self.checkpoint('recovery_pending_proof')
        self.owner_changed = True
        self.assertEqual((await self.service.run(target=None, consent=LiveConsent(True, confirmed=True), recovery=True))['status'], 'unknown')
        self.assertEqual(self.journal.load().stage, checkpoint.stage)
        self.assertFalse(any(method == 'PUT' for method, _, _ in self.http_calls))

    async def test_task_convergence_failure_never_reports_success(self):
        self.fail_command = 'timeout 120 sh -c'
        with self.assertRaises(LifecycleStateError):
            await self.runtime.inspect()

    async def test_interrupted_cancel_never_replays_source_mutation(self):
        await self.checkpoint('cancel_in_progress', backup=False)
        start = len(self.commands)
        self.assertEqual((await self.service.run(target=None, consent=LiveConsent(True, confirmed=True), recovery=True))['status'], 'unknown')
        self.assertFalse(any('docker service scale' in item or 'docker service update' in item for item in self.commands[start:]))

    async def test_recovery_rejects_changed_volume_binding_before_mutation(self):
        await self.checkpoint()
        original = self.command
        def changed_mount(script, **kwargs):
            result = original(script, **kwargs)
            if script.startswith('docker service inspect'):
                payload = json.loads(result.stdout)
                payload[0]['Spec']['TaskTemplate']['ContainerSpec']['Mounts'][0]['Source'] = 'another-volume'
                result.stdout = json.dumps(payload)
            return result
        self.shell.run_manager_shell.side_effect = changed_mount
        start = len(self.commands)
        self.assertEqual((await self.service.run(target=None, consent=LiveConsent(True, confirmed=True), recovery=True))['status'], 'unknown')
        self.assertFalse(any('docker service scale' in item or 'tar -xpf' in item for item in self.commands[start:]))

    async def test_direct_recovery_port_errors_are_fixed_and_redacted(self):
        before = await self.runtime.inspect()
        checkpoint = await self.checkpoint()
        for name, operation, argument in (
            ('cancel_backup', self.runtime.backups, checkpoint),
            ('restore', self.runtime.backups, checkpoint),
            ('_inspect_recovery', self.runtime, before),
        ):
            for failure in (RuntimeError('runtime-secret'), LifecycleStateError('lifecycle-secret')):
                with self.subTest(operation=name, failure=type(failure).__name__):
                    with patch.object(operation, name, side_effect=failure):
                        action = self.runtime.inspect_recovery if name == '_inspect_recovery' else getattr(self.runtime, name)
                        with self.assertRaises(LifecycleStateError) as raised:
                            await action(argument)
                    self.assertNotIn('secret', str(raised.exception))

    async def test_direct_proof_and_verify_fail_before_any_put(self):
        before = await self.runtime.inspect()
        checkpoint = await self.checkpoint()
        start_commands, start_http = len(self.commands), len(self.http_calls)
        with self.assertRaisesRegex(LifecycleStateError, 'ownership proof'):
            self.runtime.api.prove_update()
        with self.assertRaisesRegex(LifecycleStateError, 'ownership proof'):
            await self.runtime.verify(before, recovery=False)
        with self.assertRaisesRegex(LifecycleStateError, 'ownership proof'):
            await self.runtime.backup(checkpoint)
        with self.assertRaisesRegex(LifecycleStateError, 'ownership proof'):
            await self.runtime.upgrade(checkpoint)
        self.assertEqual(len(self.commands), start_commands)
        self.assertEqual(len(self.http_calls), start_http)

    async def test_unreadable_proof_definition_blocks_before_backup(self):
        original = self.request
        def missing_file(method, path, **kwargs):
            if path.endswith('/file'):
                return SimpleNamespace(json=lambda: {}, status_code=200)
            return original(method, path, **kwargs)
        self.client._send.side_effect = missing_file
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=LiveConsent(True, confirmed=True))
        self.assertFalse(any('docker service scale' in item for item in self.commands))

    async def test_wrong_swarm_and_uninstalled_proof_stack_block_before_backup(self):
        self.runtime.api.managed_stacks = ('jenkins',)
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=LiveConsent(True, confirmed=True))
        self.assertFalse(any('docker service scale' in item for item in self.commands))
        self.runtime.api.managed_stacks = ('nexus',)
        original = self.command
        def wrong_swarm(script, **kwargs):
            result = original(script, **kwargs)
            if script.startswith('docker info'):
                result.stdout = 'another-swarm'
            return result
        self.shell.run_manager_shell.side_effect = wrong_swarm
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=LiveConsent(True, confirmed=True))
        self.assertFalse(any('docker service scale' in item for item in self.commands))

    async def test_missing_image_cache_is_a_pre_mutation_blocker(self):
        self.fail_command = 'docker image inspect'
        with self.assertRaises(LifecycleStateError):
            await self.service.run(target=None, consent=LiveConsent(True, confirmed=True))
        self.assertFalse(any('docker service scale' in item for item in self.commands))

    async def test_generic_component_journal_rejects_gateway_interruption_under_lock(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal

        for stage in ('cancel_in_progress', 'recovery_pending_proof'):
            with self.subTest(stage=stage):
                await self.checkpoint(stage, backup=stage != 'cancel_in_progress')
                with self.assertRaises(LifecycleStateError):
                    with JsonUpdateJournal(self.root / 'component-update.json').exclusive():
                        self.fail('unsettled gateway checkpoint was bypassed')

    async def test_upgrade_authenticates_using_existing_http_client_and_credentials(self):
        from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient

        session = Mock()
        session.post.return_value = SimpleNamespace(status_code=200, json=lambda: {'jwt': 'private-jwt'})
        session.request.side_effect = lambda method, url, **kwargs: self.request(method, url.removeprefix('http://manager:10001'), **kwargs)
        self.runtime.api.client = PortainerHttpClient('http://manager:10001', 'admin', 'existing-private-password', session=session)
        with self.assertRaisesRegex(LifecycleStateError, 'ownership proof'):
            await self.service.run(target=None, consent=LiveConsent(True, confirmed=True))
        self.assertGreaterEqual(session.post.call_count, 1)
        self.assertTrue(all(call.kwargs['json']['Password'] == 'existing-private-password' for call in session.post.call_args_list))
        self.assertIsNone(self.journal.load())
        self.assertFalse(any(call.args[0] == 'PUT' for call in session.request.call_args_list))

    def test_shutdown_shell_fails_closed_when_docker_inventory_fails(self):
        import os
        from tiny_swarm_world.infrastructure.process.runner import run_process

        docker = self.root / 'docker'
        docker.write_text('#!/bin/sh\nexit 7\n')
        docker.chmod(0o700)
        def run_inventory(script, **kwargs):
            if script.startswith('timeout 60'):
                return run_process(['sh', '-c', script], capture_output=True, text=True,
                                   env=dict(os.environ, PATH=str(self.root) + ':' + os.environ['PATH']), timeout=3)
            return SimpleNamespace(returncode=0, stdout='')
        self.shell.run_manager_shell.side_effect = run_inventory
        with self.assertRaises(LifecycleStateError):
            self.runtime.state.stop()

    async def test_unsupported_version_mode_and_storage_block_before_mutation(self):
        original_request = self.request
        def unsupported_version(method, path, **kwargs):
            if path == '/api/system/status':
                return SimpleNamespace(json=lambda: {'Version': '2.39.4'}, status_code=200)
            return original_request(method, path, **kwargs)
        self.client._send.side_effect = unsupported_version
        with self.assertRaises(LifecycleStateError):
            await self.runtime.inspect()
        self.client._send.side_effect = self.request
        original_command = self.command
        for mode, driver in (({'Global': {}}, 'local'), ({'Replicated': {'Replicas': 1}}, 'remote')):
            def unsupported_layout(script, **kwargs):
                result = original_command(script, **kwargs)
                if script.startswith('docker service inspect'):
                    payload = json.loads(result.stdout)
                    payload[0]['Spec']['Mode'] = mode
                    result.stdout = json.dumps(payload)
                elif script.startswith('docker volume inspect'):
                    payload = json.loads(result.stdout)
                    payload[0]['Driver'] = driver
                    result.stdout = json.dumps(payload)
                return result
            self.shell.run_manager_shell.side_effect = unsupported_layout
            with self.subTest(mode=mode, driver=driver), self.assertRaises(LifecycleStateError):
                await self.runtime.inspect()
        self.assertFalse(any('docker service scale' in item or 'docker service update' in item for item in self.commands))

    async def test_committed_portainer_pins_feed_compose_artifacts_setup_and_stack_environment(self):
        from unittest.mock import patch
        from tests.domain.lifecycle.test_update_planning import ROOT
        from tiny_swarm_world.domain.lifecycle.selection import plan_selection
        from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
        from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import apply_desired_stack_images, effective_image_environment
        from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_state import SetupSelectionState
        from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
        from tiny_swarm_world.infrastructure.composition_artifacts import _selected_image_contracts
        from tiny_swarm_world.infrastructure.project_paths import ProjectPaths

        catalog, manifest = update_fixture(qualified=False)
        manifest = manifest.model_copy(update={'components': tuple(item.model_copy(update={
            'desired': versions('2.45.0')[item.component_id], 'observed': versions('2.45.0')[item.component_id]})
            if item.service_id == 'portainer' else item for item in manifest.components)})
        repository = JsonManifestRepository(self.root / '.tiny-swarm-world/installation/manifest.json')
        repository.save(manifest, expected_token=None)
        journal = JsonPortainerJournal(repository.path.parent / 'portainer-upgrade.json')
        service = PortainerUpgradeService(repository, journal, self.runtime)
        # A previously committed legacy target manifest still feeds downstream readers.
        service._commit(repository.load(), '2.45.1')
        after = repository.load().manifest
        with patch.dict('os.environ', {}, clear=True):
            environment = effective_image_environment({}, self.root)
            self.assertEqual(environment['TSW_PORTAINER_IMAGE'], images('2.45.1')['portainer'])
            self.assertEqual(environment['TSW_PORTAINER_AGENT_IMAGE'], images('2.45.1')['portainer-agent'])
            compose = ComposeFileRepositoryYaml(project_paths=ProjectPaths.from_roots(self.root, ROOT / 'infra'), write_logs=False)
            self.assertEqual({item.name: item.image_ref for item in compose.get_services_of('portainer')},
                             {'portainer': images('2.45.1')['portainer'], 'agent': images('2.45.1')['portainer-agent']})
            contracts = _selected_image_contracts(None, self.root)
            self.assertEqual({item.build_context: item.image_ref for item in contracts if item.build_context in images('2.45.1')}, images('2.45.1'))
            lifecycle = SimpleNamespace(manifests=repository, catalog=NativeComponentCatalog(ROOT))
            state = SetupSelectionState(lifecycle, plan_selection(catalog, ('nexus', 'jenkins'), persisted=after), self.root)
            self.assertEqual(state._effective_inventory(after), after.components)
            stack_environment = {'portainer': {}}
            apply_desired_stack_images(stack_environment, environment)
            self.assertEqual(stack_environment['portainer'], {key: environment[key] for key in ('TSW_PORTAINER_IMAGE', 'TSW_PORTAINER_AGENT_IMAGE')})
        with self.assertRaises(LifecycleStateError):
            effective_image_environment({'TSW_PORTAINER_IMAGE': images('2.45.0')['portainer']}, self.root)

    async def test_unsettled_gateway_blocks_setup_admission_and_other_component_batches(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import require_settled_updates
        from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal
        from tiny_swarm_world.domain.lifecycle.update_execution import UpdateBatch, UpdateStage
        from tiny_swarm_world.domain.lifecycle.update_planning import plan_component_updates

        canonical = JsonPortainerJournal(self.root / '.tiny-swarm-world/installation/portainer-upgrade.json')
        canonical.path.parent.mkdir(parents=True, exist_ok=True)
        self.service.journal = canonical
        self.journal = canonical
        for stage in ('cancel_in_progress', 'recovery_pending_proof'):
            with self.subTest(stage=stage):
                await self.checkpoint(stage, backup=stage != 'cancel_in_progress')
                with self.assertRaisesRegex(LifecycleStateError, 'Portainer upgrade incomplete'):
                    require_settled_updates(self.root)
        # The reverse direction is checked while the same execution lock is held.
        catalog, manifest = update_fixture()
        plan = plan_component_updates(catalog, manifest, ('nexus',))
        stages = tuple(UpdateStage(service_id=item.service_id, component_id=component.component_id,
                                   source=component.desired, target=component.target)
                       for item in plan.services for component in item.components)
        batch = UpdateBatch(original=manifest, plan=plan, stages=stages)
        other = JsonUpdateJournal(canonical.path.with_name('component-update.json'))
        other.path.parent.mkdir(parents=True, exist_ok=True)
        other.save(batch)
        with self.assertRaisesRegex(LifecycleStateError, 'component batch'):
            with self.journal.exclusive():
                self.fail('unsettled component batch was bypassed')

"""Official metadata and real filesystem migration/activation boundary tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import os
import sys
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tests.application.services.test_product_upgrade import product_plan
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_installation import PreparedProductInstallation
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration import migrate_product_infra
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_runtime import ClassicProductRuntime, verify_service
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OfficialProductSource, release_policy
from tiny_swarm_world.domain.lifecycle.product_upgrade import SOURCE_REVISION, TARGET_REVISION


def response(payload):
    result = Mock(status_code=200)
    result.json.return_value = payload
    result.content = json.dumps(payload).encode()
    return result


class OfficialReleaseTests(unittest.TestCase):
    def setUp(self):
        self.source = OfficialProductSource()
        self.release = response({'tag_name': '0.5.0', 'draft': False, 'prerelease': False})
        self.ref = response({'object': {'type': 'commit', 'sha': TARGET_REVISION}})
        self.project = response({})
        self.project.text = '[project]\nversion="0.2.0"\n'
        self.lock = response({})
        self.lock.content = b'example==1.0\n'
        self.comparison = response({'status': 'ahead', 'files': [
            {'filename': 'infra/config/compose/portainer/docker-compose.yml', 'status': 'modified'}]})
        self.before_tree = response({'truncated': False, 'tree': [{'path': 'infra/config/compose/portainer/docker-compose.yml',
                                   'mode': '100644', 'type': 'blob', 'sha': 'a' * 40}]})
        self.after_tree = response({'truncated': False, 'tree': [{'path': 'infra/config/compose/portainer/docker-compose.yml',
                                  'mode': '100644', 'type': 'blob', 'sha': 'b' * 40}]})
        self.responses = [self.release, self.ref, self.project, self.lock, self.comparison, self.before_tree, self.after_tree]

    def test_official_release_is_pinned_to_actual_revision_and_lock(self):
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_source.requests.get', side_effect=self.responses) as get:
            release, changes = self.source.resolve('0.5.0')
        self.assertEqual(release.product.revision, TARGET_REVISION)
        self.assertEqual(release.product.dependency_lock, 'sha256:' + hashlib.sha256(self.lock.content).hexdigest())
        self.assertEqual(changes, ('infra/config/compose/portainer/docker-compose.yml',))
        self.assertTrue(all(call.kwargs['allow_redirects'] is False for call in get.call_args_list))

    def test_moved_target_ref_is_rejected(self):
        self.ref.json.return_value['object']['sha'] = 'a' * 40
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_source.requests.get', side_effect=self.responses):
            with self.assertRaises(LifecycleStateError):
                self.source.resolve('0.5.0')

    def test_draft_prerelease_or_wrong_tag_cannot_be_admitted(self):
        for update in ({'draft': True}, {'prerelease': True}, {'tag_name': 'main'}):
            self.release.json.return_value = dict(tag_name='0.5.0', draft=False, prerelease=False, **{}) | update
            with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_source.requests.get', side_effect=self.responses):
                with self.assertRaises(LifecycleStateError):
                    self.source.resolve('0.5.0')

    def test_configuration_deletion_and_truncated_tree_are_blocked(self):
        for payload in ({'truncated': False, 'tree': []}, {'truncated': True, 'tree': []}):
            self.after_tree.json.return_value = payload
            with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_source.requests.get', side_effect=self.responses):
                with self.assertRaises(LifecycleStateError):
                    self.source.resolve('0.5.0')

    def test_large_comparison_uses_complete_trees_instead_of_truncated_file_list(self):
        self.comparison.json.return_value['files'] *= 300
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_source.requests.get', side_effect=self.responses):
            _, changes = self.source.resolve('0.5.0')
        self.assertEqual(changes, ('infra/config/compose/portainer/docker-compose.yml',))

    def test_support_asset_matches_machine_policy(self):
        root = Path(__file__).resolve().parents[4]
        self.assertEqual(json.loads((root / 'infra/config/product-releases.json').read_text()), release_policy())


class ProductFilesystemTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.installation = PreparedProductInstallation(self.root, Mock(), Mock(), Mock(), Mock())
        self.plan = product_plan().model_copy(update={'configuration_changes': ('infra/config/default.yml',)})
        self.code = self.installation.directory(self.plan)
        (self.root / 'infra/config').mkdir(parents=True)
        (self.code / 'infra/config').mkdir(parents=True)
        (self.root / 'infra/config/default.yml').write_text('old-default')
        (self.root / 'infra/config/local.env').write_text('PRIVATE_SENTINEL')
        (self.code / 'infra/config/default.yml').write_text('new-default')
        self.installation._command = Mock(return_value='infra/config/default.yml')

    def test_migration_preserves_overrides_and_originals_while_updating_defaults(self):
        migrate_product_infra(self.installation, self.plan)
        effective = self.installation.state / 'infra' / TARGET_REVISION
        self.assertEqual((effective / 'config/default.yml').read_text(), 'new-default')
        self.assertEqual((effective / 'config/local.env').read_text(), 'PRIVATE_SENTINEL')
        self.assertEqual((effective / 'config/local.env').stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.root / 'infra/config/default.yml').read_text(), 'old-default')
        self.assertEqual((self.root / 'infra/config/local.env').read_text(), 'PRIVATE_SENTINEL')

    def test_interrupted_private_copy_is_rebuilt_without_modifying_source(self):
        pending = self.installation.state / 'infra' / (TARGET_REVISION + '.pending')
        pending.mkdir(parents=True)
        (pending / 'partial').write_text('incomplete')
        migrate_product_infra(self.installation, self.plan)
        self.assertFalse(pending.exists())
        self.assertTrue((self.root / 'infra/config/local.env').exists())

    def test_symlinked_configuration_is_rejected_without_copy(self):
        (self.root / 'infra/config/external').symlink_to('/etc/passwd')
        with self.assertRaises(LifecycleStateError):
            migrate_product_infra(self.installation, self.plan)

    def test_conflicting_new_asset_does_not_overwrite_operator_override(self):
        self.installation._command.return_value = ''
        with self.assertRaises(LifecycleStateError):
            migrate_product_infra(self.installation, self.plan)
        self.assertEqual((self.root / 'infra/config/default.yml').read_text(), 'old-default')

    def test_atomic_activation_and_repetition_point_to_real_code_and_private_infra(self):
        migrate_product_infra(self.installation, self.plan)
        self.installation.activate(self.plan)
        self.installation.activate(self.plan)
        self.assertEqual((self.installation.state / 'active/code').resolve(), self.code)
        launcher = self.installation.state / 'tiny-swarm-world'
        self.assertIn('TSW_REPOSITORY_ROOT=', launcher.read_text())
        self.assertNotIn('PRIVATE_SENTINEL', launcher.read_text())
        self.assertEqual(launcher.stat().st_mode & 0o777, 0o700)

    def test_tampered_migration_blocks_activation_and_recovery(self):
        migrate_product_infra(self.installation, self.plan)
        effective = self.installation.state / 'infra' / TARGET_REVISION
        (effective / 'config/local.env').write_text('changed')
        with self.assertRaises(LifecycleStateError):
            self.installation.activate(self.plan)
        with self.assertRaises(LifecycleStateError):
            migrate_product_infra(self.installation, self.plan)

    def test_ancestor_symlink_cannot_redirect_managed_writes(self):
        outside = self.root / 'outside'
        outside.mkdir()
        self.installation.state.mkdir(parents=True, exist_ok=True)
        (self.installation.state / 'infra').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(LifecycleStateError):
            migrate_product_infra(self.installation, self.plan)
        self.assertEqual(list(outside.iterdir()), [])

    def test_unrelated_activation_is_preserved(self):
        migrate_product_infra(self.installation, self.plan)
        active = self.installation.state / 'active'
        active.symlink_to(self.root / 'unrelated')
        with self.assertRaises(LifecycleStateError):
            self.installation.activate(self.plan)
        self.assertEqual(active.readlink(), self.root / 'unrelated')

    def test_dirty_source_blocks_before_release_resolution(self):
        self.installation._command.return_value = ' M operator.yml'
        with self.assertRaises(LifecycleStateError):
            self.installation.plan('0.5.0')
        self.installation.source.resolve.assert_not_called()

    def test_source_identity_reads_lock_and_revision_separately(self):
        (self.root / 'requirements.lock').write_bytes(b'locked')
        (self.root / 'pyproject.toml').write_text('[project]\nversion="0.2.0"\n')
        self.installation._command.return_value = SOURCE_REVISION
        identity = self.installation._source_identity()
        self.assertEqual(identity.product.release, '0.4.0')
        self.assertEqual(identity.product.dependency_lock, 'sha256:' + hashlib.sha256(b'locked').hexdigest())

    def test_nonanchor_effective_infra_is_rejected_before_git_or_network(self):
        with patch.dict('os.environ', {'TSW_INFRA_ROOT': str(self.root / 'elsewhere')}):
            with self.assertRaises(LifecycleStateError):
                self.installation._clean_source()
        self.installation._command.assert_not_called()

    def test_target_verification_runs_target_code_and_migrated_config_with_explicit_selection(self):
        migrate_product_infra(self.installation, self.plan)
        self.installation._command.reset_mock()
        self.installation._command.return_value = 'target-runtime-verified'
        self.installation.verify_target_runtime(self.plan)
        call = self.installation._command.call_args
        self.assertEqual(call.args[0][0], str(self.code / '.venv/bin/python'))
        self.assertEqual(call.kwargs['env']['PYTHONPATH'], str(self.code / 'src'))
        self.assertEqual(call.kwargs['env']['TSW_REPOSITORY_ROOT'], str(self.root))
        self.assertEqual(call.kwargs['env']['TSW_INFRA_ROOT'], str(self.installation.state / 'infra' / TARGET_REVISION))
        self.assertEqual(json.loads(call.kwargs['input'])['resolved_services'], list(self.plan.manifest.resolved_services))


class ProductRuntimeTests(unittest.TestCase):
    def shell(self, *, image='example:1', task_image=None, state='running', desired='running', mode=None, exit_code=0, changed=False):
        service = {'id': 'service-id', 'version': 1, 'image': image, 'mode': mode or {'Replicated': {'Replicas': 1}}}
        task = {'image': task_image or image, 'state': state, 'desired': desired, 'exit': exit_code}
        after = dict(service, version=2) if changed else service
        shell = Mock()
        shell.run_manager_shell.side_effect = [
            subprocess.CompletedProcess([], 0, json.dumps(service)),
            subprocess.CompletedProcess([], 0, 'taskid'),
            subprocess.CompletedProcess([], 0, json.dumps(task)),
            subprocess.CompletedProcess([], 0, json.dumps(after))]
        return shell

    def test_running_replicated_and_global_services_are_verified(self):
        for mode in ({'Replicated': {'Replicas': 1}}, {'Global': {}}):
            self.assertEqual(verify_service(self.shell(mode=mode), 'portainer_agent', 'example:1'), 'service-id')

    def test_successful_one_shot_requires_completed_target_task(self):
        self.assertEqual(verify_service(self.shell(state='complete', desired='shutdown'),
            'pulsar_bootstrap', 'example:1', one_shot=True), 'service-id')
        failed = self.shell(state='complete', desired='shutdown', exit_code=1)
        with self.assertRaises(LifecycleStateError):
            verify_service(failed, 'pulsar_bootstrap', 'example:1', one_shot=True)

    def test_old_task_drift_failed_rollout_and_changed_service_are_rejected(self):
        for kwargs in ({'task_image': 'example:old'}, {'image': 'example:old'}, {'state': 'failed'}, {'changed': True}):
            shell = self.shell(**kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(LifecycleStateError):
                verify_service(shell, 'jenkins_jenkins', 'example:1')

    def test_tag_only_inventory_still_requires_actual_service_digest_convergence(self):
        shell = self.shell(image='example:1@sha256:' + 'a' * 64, task_image='example:1@sha256:' + 'b' * 64)
        with self.assertRaises(LifecycleStateError):
            verify_service(shell, 'jenkins_jenkins', 'example:1')


class ProductRuntimeFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_expected_authenticated_gateway_failure_is_redacted_at_adapter(self):
        from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure

        runtime = ClassicProductRuntime(Path('/unused'), Mock(), Mock(), Mock(), Mock())
        runtime._verify = AsyncMock(side_effect=OperationError(OperationFailure.for_cause(
            'product.verify', 'gateway', 'request_failed')))
        manifest = product_plan().manifest
        with self.assertRaises(LifecycleStateError) as caught:
            await runtime.verify(manifest)
        self.assertIsNone(caught.exception.__cause__)
        self.assertIn('authenticated', str(caught.exception))

    async def test_programming_defects_and_cancellation_are_not_hidden(self):
        import asyncio

        runtime = ClassicProductRuntime(Path('/unused'), Mock(), Mock(), Mock(), Mock())
        manifest = product_plan().manifest
        for failure in (AssertionError('defect'), asyncio.CancelledError()):
            runtime._verify = AsyncMock(side_effect=failure)
            with self.assertRaises(type(failure)):
                await runtime.verify(manifest)


class ProductEnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.installation = PreparedProductInstallation(self.root, Mock(), Mock(), Mock(), Mock())
        self.plan = product_plan()
        self.code = self.installation.directory(self.plan)
        (self.code / '.venv/bin').mkdir(parents=True)
        (self.code / '.venv/bin/python').write_text('fixture, never executed')
        (self.code / 'pyproject.toml').write_text('[project]\nversion="0.2.0"\n')
        lock = b'example==1.0\n'
        (self.code / 'requirements.lock').write_bytes(lock)
        target = self.plan.target.model_copy(update={'product': self.plan.target.product.model_copy(
            update={'dependency_lock': 'sha256:' + hashlib.sha256(lock).hexdigest()})})
        self.plan = self.plan.model_copy(update={'target': target})
        self.installation._command = Mock(side_effect=self.command)

    def command(self, args, **kwargs):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OFFICIAL_REPOSITORY

        if tuple(args[:2]) == ('git', 'clone'):
            shutil.copytree(self.template, Path(args[-1]))
        if tuple(args[:3]) == ('git', 'remote', 'get-url'):
            return OFFICIAL_REPOSITORY
        if tuple(args[:2]) == ('git', 'rev-parse'):
            return TARGET_REVISION
        if '-c' in args and 'print(tomllib' in args[-1]:
            return '0.2.0'
        return ''

    def test_staging_verifies_checkout_and_installs_hash_locked_dependencies(self):
        self.installation.stage(self.plan)
        commands = [call.args[0] for call in self.installation._command.call_args_list]
        install = next(command for command in commands if 'install' in command)
        self.assertIn('--require-hashes', install)
        self.assertEqual(install[-1], str(self.code / 'requirements.lock'))
        self.assertTrue(any('check' in command for command in commands))
        self.assertTrue(any('importlib.metadata.version' in command[-1] for command in commands))

    def test_interrupted_clone_is_preserved_and_private_slot_rebuilt(self):
        self.template = self.code.with_name('fixture-template')
        self.code.rename(self.template)
        pending = self.installation.state / 'staging' / TARGET_REVISION
        pending.mkdir(parents=True)
        (pending / 'partial').write_text('interrupted checkout')
        self.installation.stage(self.plan)
        retained = list(pending.parent.glob(TARGET_REVISION + '.interrupted-*'))
        self.assertEqual(len(retained), 1)
        self.assertEqual((retained[0] / 'partial').read_text(), 'interrupted checkout')
        self.assertTrue((self.code / 'pyproject.toml').exists())

    def test_staged_revision_lock_package_or_dirty_state_drift_blocks(self):
        for kind in ('revision', 'lock', 'package', 'dirty'):
            with self.subTest(kind=kind):
                self.installation._command.side_effect = self.command
                (self.code / 'requirements.lock').write_text('example==1.0\n')
                (self.code / 'pyproject.toml').write_text('[project]\nversion="0.2.0"\n')
                if kind == 'lock':
                    (self.code / 'requirements.lock').write_text('example==2.0\n')
                elif kind == 'package':
                    (self.code / 'pyproject.toml').write_text('[project]\nversion="unexpected"\n')
                else:
                    def changed(args, **kwargs):
                        if kind == 'revision' and tuple(args[:2]) == ('git', 'rev-parse'):
                            return 'f' * 40
                        if kind == 'dirty' and tuple(args[:2]) == ('git', 'status'):
                            return ' M operator.py'
                        return self.command(args, **kwargs)
                    self.installation._command.side_effect = changed
                with self.assertRaises(LifecycleStateError):
                    self.installation._verify_checkout(self.plan)

    def test_incompatible_installed_dependencies_fail_environment_verification(self):
        def incompatible(args, **kwargs):
            if '-c' in args and 'importlib.metadata.version' in args[-1]:
                raise LifecycleStateError('installed dependency differs from lock')
            return self.command(args, **kwargs)
        self.installation._command.side_effect = incompatible
        with self.assertRaises(LifecycleStateError):
            self.installation.verify_product(self.plan)

    def test_dependency_verification_cannot_be_disabled_by_python_optimization(self):
        self.installation.verify_product(self.plan)
        scripts = [call.args[0][-1] for call in self.installation._command.call_args_list if '-c' in call.args[0]]
        dependency = next(script for script in scripts if 'importlib.metadata.version' in script)
        # The fixture's example distribution is absent; optimized Python must still reject it.
        result = subprocess.run([sys.executable, '-O', '-c', dependency], cwd=self.code, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        version = next(script for script in scripts if 'sys.version_info' in script)
        wrong_interpreter = version.replace('(3,12)', '(0,0)')
        environment = {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[4] / 'src')}
        result = subprocess.run([sys.executable, '-O', '-c', wrong_interpreter], cwd=self.code, env=environment,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, '')

    def test_wrong_host_python_or_disk_blocks_before_staging(self):
        from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
        path = 'tiny_swarm_world.infrastructure.adapters.host.host_environment_detector.HostEnvironmentDetector'
        for host, version, disk in ((HostEnvironmentKind.WSL2, (3, 12), 3 * 1024**3),
                                    (HostEnvironmentKind.NATIVE_LINUX, (3, 11), 3 * 1024**3),
                                    (HostEnvironmentKind.NATIVE_LINUX, (3, 12), 1)):
            with self.subTest(host=host, version=version, disk=disk), patch(path) as detector:
                detector.return_value.detect.return_value.environment = host
                with patch.object(sys, 'version_info', version), patch('shutil.disk_usage', return_value=SimpleNamespace(free=disk)):
                    with self.assertRaises(LifecycleStateError):
                        self.installation._host_and_resources(self.plan)

    def test_matching_host_python_and_capacity_admit_without_mutation(self):
        from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
        path = 'tiny_swarm_world.infrastructure.adapters.host.host_environment_detector.HostEnvironmentDetector'
        with patch(path) as detector:
            detector.return_value.detect.return_value.environment = HostEnvironmentKind.NATIVE_LINUX
            with patch.object(sys, 'version_info', (3, 12)), patch('shutil.disk_usage', return_value=SimpleNamespace(free=3 * 1024**3)):
                self.installation._host_and_resources(self.plan)
        self.installation._command.assert_not_called()


class ProductWholeInventoryTests(unittest.TestCase):
    def test_bound_inventory_reads_same_infrastructure_authority_and_keeps_authentication(self):
        import yaml
        from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog

        root = Path(__file__).resolve().parents[4]
        catalog = NativeComponentCatalog(root).load()
        services = ('incus', 'portainer')
        components = tuple(item for service in catalog.services if service.service_id in services for item in service.components)
        manifest = product_plan().manifest.model_copy(update={'components': components})
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        infra = Path(temporary.name)
        portainer = next(service for service in catalog.services if service.service_id == 'portainer')
        native = yaml.safe_load((root / portainer.native_asset).read_text())
        native['services'] = {'authority_' + name: definition for name, definition in native['services'].items()}
        asset = infra / Path(portainer.native_asset).relative_to('infra')
        asset.parent.mkdir(parents=True)
        asset.write_text(yaml.safe_dump(native))
        api = Mock()
        api._send.return_value.json.return_value = [{'Id': 1, 'Status': 1}]
        runtime = ClassicProductRuntime(root, Mock(), Mock(return_value=api), Mock(), Mock())
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_runtime.verify_service', return_value='stable-id') as verify:
            identities = runtime._inventory(manifest, infra)
        self.assertTrue(all(call.args[1].startswith('portainer_authority_') for call in verify.call_args_list))
        self.assertEqual(set(identities) - {'portainer.endpoints'}, {item.component_id for item in components} - {'incus'})
        api._send.assert_called_once_with('GET', '/api/endpoints')

    def test_actual_catalog_maps_every_selected_database_agent_and_bootstrap_only(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog

        root = Path(__file__).resolve().parents[4]
        catalog = NativeComponentCatalog(root).load()
        services = ('incus', 'portainer', 'pulsar', 'sonarqube')
        components = tuple(item for service in catalog.services if service.service_id in services for item in service.components)
        manifest = product_plan().manifest.model_copy(update={'requested_services': services, 'resolved_services': services,
                                                            'components': components})
        api = Mock()
        api._send.return_value.json.return_value = [{'Id': 1, 'Status': 1}]
        runtime = ClassicProductRuntime(root, Mock(), Mock(return_value=api), Mock(), Mock())
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_runtime.verify_service', return_value='stable-id') as verify:
            identities = runtime._inventory(manifest)
        self.assertEqual(set(identities) - {'portainer.endpoints'}, {item.component_id for item in components} - {'incus'})
        names = {call.args[1]: call for call in verify.call_args_list}
        self.assertIn('portainer_agent', names)
        self.assertIn('sonarqube_sonar_db', names)
        self.assertTrue(names['pulsar_pulsar-manager-bootstrap'].kwargs['one_shot'])
        self.assertTrue(all(name.split('_', 1)[0] in services for name in names))
        api._send.assert_called_once_with('GET', '/api/endpoints')

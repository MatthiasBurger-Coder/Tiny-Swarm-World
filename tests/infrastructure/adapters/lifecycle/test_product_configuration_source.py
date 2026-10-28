"""Bound input authority, private capture, failure recovery and memory migration."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import asyncio
import traceback
from uuid import uuid4
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from ruamel.yaml import YAML

from tests.application.services.test_product_upgrade import product_plan
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductCheckpoint, TARGET_REVISION
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind
from tiny_swarm_world.domain.preflight.resources import HostResources
from tiny_swarm_world.infrastructure.adapters.lifecycle import product_configuration_capture as capture_adapter
from tiny_swarm_world.infrastructure.adapters.lifecycle import product_configuration_source as source_adapter
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_validation import PROVIDER, read_tree
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_installation import PreparedProductInstallation
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_journal import JsonProductJournal
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration import migrate_product_infra
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.process.runner import ProcessRunnerError


class BoundConfigurationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root, self.external = self.base / 'anchor', self.base / 'effective'
        self.root.mkdir(mode=0o700)
        self.external.mkdir(mode=0o700)
        self.installation = PreparedProductInstallation(self.root, Mock(), Mock(), Mock(), Mock())
        self.installation._host_and_resources = Mock()
        official = self.root / 'infra'
        (official / Path(PROVIDER).parent).mkdir(parents=True, mode=0o700)
        repository = Path(__file__).resolve().parents[4]
        shutil.copyfile(repository / 'infra' / PROVIDER, official / PROVIDER)
        for name in ('config/ports.yaml', 'config/compose/portainer/docker-compose.yml'):
            path = official / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'official-source\n')
        (official / 'setup.sh').write_bytes(b'#!/bin/sh\ntrue\n')
        (official / 'setup.sh').chmod(0o755)
        shutil.copytree(official, self.external, dirs_exist_ok=True)
        self.external.chmod(0o700)
        provider = self.external / PROVIDER
        provider.write_bytes(provider.read_bytes().replace(b'memory: 8GiB', b'memory: 6GiB'))
        tree = read_tree(official, private=False)
        listing = []
        for name, content in tree.files.items():
            mode = '100755' if tree.members[name][3] & 0o111 else '100644'
            digest = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content, usedforsecurity=False).hexdigest()
            listing.append(f'{mode} blob {digest}\tinfra/{name}')
        self.installation._command = Mock(return_value='\n'.join(listing))
        def hash_object(_args, **kwargs):
            content = kwargs['input']
            digest = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content, usedforsecurity=False).hexdigest()
            return SimpleNamespace(returncode=0, stdout=digest.encode() + b'\n', stderr=b'')
        self.installation.runner.run_bytes.side_effect = hash_object
        self.environment = patch.dict(os.environ, {'TSW_INFRA_ROOT': str(self.external)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        resources = patch('tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector.WslResourceInspector')
        self.resource_inspector = resources.start()
        self.addCleanup(resources.stop)
        self.resource_inspector.return_value.inspect.return_value = HostResources(8, 20_111_052_800, None, 0, 200 * 1024**3)
        host_detector = patch('tiny_swarm_world.infrastructure.adapters.host.host_environment_detector.HostEnvironmentDetector')
        self.host_detector = host_detector.start()
        self.addCleanup(host_detector.stop)
        self.host_detector.return_value.detect.return_value = SimpleNamespace(
            environment=HostEnvironmentKind.WSL2)
        self.plan = product_plan().model_copy(update={
            'configuration_changes': ('infra/config/ports.yaml', 'infra/config/compose/portainer/docker-compose.yml')})

    def prepare(self):
        binding = source_adapter.prepare(self.installation)
        self.plan = self.plan.model_copy(update={'configuration_source': binding,
                                               'resource_bytes': 2147483648 + source_adapter.reserve_bytes(binding)})
        return self.plan

    def bind(self):
        self.prepare()
        source_adapter.bind(self.installation, self.plan)
        return self.installation.state / 'inputs' / self.plan.configuration_source.reference

    def test_preview_is_read_only_random_and_contains_no_physical_metadata(self):
        first = self.prepare()
        self.assertFalse(self.installation.state.exists())
        preview = json.dumps(first.preview())
        self.assertNotIn(str(self.external), preview)
        self.assertNotIn('source_metadata', preview)
        second = source_adapter.prepare(self.installation)
        self.assertNotEqual(first.configuration_source.reference, second.reference)
        self.assertEqual(source_adapter.reserve_bytes(second), 128 * 1024 * 1024)

    def test_official_blob_identity_preserves_binary_payload_and_read_only_git_flags(self):
        payload = b'\x00\xff\r\ntrailing whitespace \n\n'
        binary = self.root / 'infra' / 'binary.dat'
        binary.write_bytes(payload)
        digest = hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload, usedforsecurity=False).hexdigest()
        self.installation._command.return_value += f'\n100644 blob {digest}\tinfra/binary.dat'
        tree = source_adapter._official(self.installation)
        self.assertEqual(tree.files['binary.dat'], payload)
        call = next(call for call in self.installation.runner.run_bytes.call_args_list if call.kwargs['input'] == payload)
        self.assertEqual(call.args[0], ('git', 'hash-object', '--no-filters', '--stdin'))
        self.assertEqual(call.kwargs['cwd'], self.root)
        self.assertFalse(call.kwargs['shell'])
        self.assertGreater(call.kwargs['timeout'], 0)
        self.assertLessEqual(call.kwargs['timeout'], 30)

    def test_git_blob_failure_or_unexpected_output_is_refused_without_raw_details(self):
        good = b'a' * 40 + b'\n'
        results = (
            SimpleNamespace(returncode=1, stdout=good, stderr=b''),
            SimpleNamespace(returncode=0, stdout=good, stderr=b'private-payload'),
            SimpleNamespace(returncode=0, stdout=good + b'\n', stderr=b''),
            SimpleNamespace(returncode=0, stdout=b'A' * 40 + b'\n', stderr=b''),
            SimpleNamespace(returncode=0, stdout=b'a' * 40 + b'\r\n', stderr=b''),
            SimpleNamespace(returncode=0, stdout=b'a' * 64 + b'\n', stderr=b''),
            SimpleNamespace(returncode=0, stdout=b'private-payload', stderr=b''),
            SimpleNamespace(returncode=0, stdout=good, stderr=b''),  # Valid shape, wrong identity.
        )
        self.installation.runner.run_bytes.side_effect = None
        for result in results:
            with self.subTest(output_size=len(result.stdout)):
                self.installation.runner.run_bytes.return_value = result
                with self.assertRaises(LifecycleStateError) as caught:
                    source_adapter._official(self.installation)
                self.assertNotIn('private-payload', str(caught.exception))
                self.assertFalse(self.installation.state.exists())

    def test_git_blob_runner_exceptions_are_sanitized_and_fail_closed(self):
        for error in (ProcessRunnerError('private-payload'), OSError('private-payload')):
            with self.subTest(error_type=type(error).__name__):
                self.installation.runner.run_bytes.side_effect = error
                with self.assertRaises(LifecycleStateError) as caught:
                    source_adapter._official(self.installation)
                self.assertNotIn('private-payload', str(caught.exception))

    def test_official_blob_hashing_shares_one_deadline_across_all_files(self):
        with patch.object(source_adapter.time, 'monotonic', side_effect=[0.0, 1.0, 2.0, 31.0]):
            with self.assertRaises(LifecycleStateError):
                source_adapter._official(self.installation)
        self.installation.runner.run_bytes.assert_called_once()
        self.assertEqual(self.installation.runner.run_bytes.call_args.kwargs['timeout'], 29.0)

    def test_changed_anchor_bytes_and_execute_mode_still_refuse_official_source(self):
        anchor = self.root / 'infra' / 'setup.sh'
        original = anchor.read_bytes()
        anchor.write_bytes(original + b'# changed\n')
        with self.assertRaises(LifecycleStateError):
            source_adapter._official(self.installation)
        anchor.write_bytes(original)
        anchor.chmod(0o644)
        with self.assertRaises(LifecycleStateError):
            source_adapter._official(self.installation)

    def test_native_host_uses_native_filesystem_classification(self):
        self.host_detector.return_value.detect.return_value = SimpleNamespace(
            environment=HostEnvironmentKind.NATIVE_LINUX)
        with patch('tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector.ProjectFilesystemInspector') as inspector:
            inspector.return_value.inspect.return_value = SimpleNamespace(
                kind=ProjectFilesystemKind.NATIVE_LINUX)
            self.prepare()
        inspector.return_value.inspect.assert_called_with(
            str(self.external), HostEnvironmentKind.NATIVE_LINUX)

    def test_external_source_rejects_windows_mounted_and_unknown_filesystems(self):
        for kind in (ProjectFilesystemKind.WINDOWS_MOUNTED, ProjectFilesystemKind.UNKNOWN):
            with self.subTest(kind=kind), patch(
                    'tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector.ProjectFilesystemInspector') as inspector:
                inspector.return_value.inspect.return_value = SimpleNamespace(kind=kind)
                with self.assertRaises(LifecycleStateError):
                    self.prepare()
                self.assertFalse(self.installation.state.exists())

    def test_wsl_host_requires_wsl_linux_classification(self):
        with patch('tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector.ProjectFilesystemInspector') as inspector:
            inspector.return_value.inspect.return_value = SimpleNamespace(
                kind=ProjectFilesystemKind.NATIVE_LINUX)
            with self.assertRaises(LifecycleStateError):
                self.prepare()
        inspector.return_value.inspect.assert_called_with(str(self.external), HostEnvironmentKind.WSL2)

    def test_private_binding_capture_and_unset_environment_resume(self):
        directory = self.bind()
        self.assertEqual((directory / 'binding.json').stat().st_mode & 0o777, 0o600)
        snapshot = source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual(snapshot.stat().st_mode & 0o777, 0o700)
        self.assertEqual((snapshot / 'setup.sh').stat().st_mode & 0o777, 0o700)
        self.assertEqual((snapshot / PROVIDER).stat().st_mode & 0o777, 0o600)
        del os.environ['TSW_INFRA_ROOT']
        self.installation._configuration_candidate = None
        source_adapter.validate(self.installation, self.plan)
        self.assertEqual(source_adapter.effective_source(self.installation, self.plan), snapshot)

    def test_explicit_repoint_and_legacy_ambient_retrofit_are_rejected(self):
        self.bind()
        os.environ['TSW_INFRA_ROOT'] = str(self.root / 'infra')
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, self.plan)
        os.environ['TSW_INFRA_ROOT'] = str(self.external)
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, product_plan())

    def test_orphan_binding_cannot_be_adopted_or_replaced_by_a_new_plan(self):
        directory = self.bind()
        original = (directory / 'binding.json').read_bytes()
        with self.assertRaises(LifecycleStateError):
            source_adapter.prepare(self.installation)
        self.assertEqual((directory / 'binding.json').read_bytes(), original)

    def test_missing_corrupt_and_replaced_binding_fail_closed(self):
        directory = self.bind()
        record = directory / 'binding.json'
        original = record.read_bytes()
        for invalid in (b'{}', b'not-json'):
            record.write_bytes(invalid)
            with self.assertRaises(LifecycleStateError):
                source_adapter.validate(self.installation, self.plan)
        record.write_bytes(original)
        record.unlink()
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, self.plan)

    def test_source_content_drift_and_same_path_replacement_block(self):
        self.bind()
        provider = self.external / PROVIDER
        provider.write_bytes(provider.read_bytes().replace(b'6GiB', b'5GiB'))
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, self.plan)
        self.external.rename(self.base / 'old-effective')
        shutil.copytree(self.base / 'old-effective', self.external)
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, self.plan)

    def test_capture_recovery_before_destination_and_after_partial_write(self):
        directory = self.bind()
        record = capture_adapter.load_record(directory)
        capture_adapter.atomic_record(directory, dict(record, capture_state='capturing'))
        with patch.object(capture_adapter, '_write_tree', side_effect=OSError('interruption')):
            with self.assertRaises(LifecycleStateError):
                source_adapter.capture_source(self.installation, self.plan)
        snapshot = directory / 'snapshot'
        (snapshot / 'config').mkdir(mode=0o700)
        (snapshot / 'config/ports.yaml').write_bytes(b'official-')
        (snapshot / 'config/ports.yaml').chmod(0o600)
        source_adapter.validate(self.installation, self.plan)
        self.assertEqual(source_adapter.capture_source(self.installation, self.plan), snapshot)
        self.assertEqual((snapshot / 'config/ports.yaml').read_bytes(), b'official-source\n')

    def test_capture_recovers_if_process_stops_immediately_after_snapshot_stage_mkdir(self):
        directory = self.bind()
        original_mkdir = os.mkdir
        interrupted = False

        def mkdir_then_interrupt(name, *args, **kwargs):
            nonlocal interrupted
            original_mkdir(name, *args, **kwargs)
            if isinstance(name, str) and name.startswith('.snapshot-stage-') and not interrupted:
                interrupted = True
                raise OSError('process stopped after stage directory creation')

        with patch.object(capture_adapter.os, 'mkdir', side_effect=mkdir_then_interrupt):
            with self.assertRaises(LifecycleStateError):
                source_adapter.capture_source(self.installation, self.plan)

        record = capture_adapter.load_record(directory)
        stage_name = record['snapshot_metadata']['stage_name']
        self.assertTrue((directory / stage_name).is_dir())
        self.assertEqual(list((directory / stage_name).iterdir()), [])
        snapshot = source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual(capture_adapter.load_record(directory)['capture_state'], 'captured')
        self.assertFalse((directory / stage_name).exists())
        self.assertEqual((snapshot / 'config/ports.yaml').read_bytes(), b'official-source\n')

    def test_capture_recovers_after_stage_identity_record_before_atomic_publish(self):
        directory = self.bind()
        original_rename = capture_adapter._rename_new

        def interrupt_before_publish(source_parent, source, target_parent, target):
            if target == 'snapshot':
                raise OSError('process stopped before snapshot rename')
            return original_rename(source_parent, source, target_parent, target)

        with patch.object(capture_adapter, '_rename_new', side_effect=interrupt_before_publish):
            with self.assertRaises(LifecycleStateError):
                source_adapter.capture_source(self.installation, self.plan)

        record = capture_adapter.load_record(directory)
        metadata = record['snapshot_metadata']
        self.assertIn('root_identity', metadata)
        self.assertTrue((directory / metadata['stage_name']).is_dir())
        snapshot = source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual(capture_adapter.load_record(directory)['capture_state'], 'captured')
        self.assertEqual((snapshot / 'config/ports.yaml').read_bytes(), b'official-source\n')

    def test_capture_completed_bytes_resume_after_final_record_interruption(self):
        directory = self.bind()
        original = capture_adapter.atomic_record

        def interrupted_record(destination, record):
            if record['capture_state'] == 'captured':
                raise OSError('interrupted final record')
            return original(destination, record)

        with patch.object(capture_adapter, 'atomic_record', side_effect=interrupted_record):
            with self.assertRaises(LifecycleStateError):
                source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual(capture_adapter.load_record(directory)['capture_state'], 'capturing')
        source_adapter.validate(self.installation, self.plan)
        source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual(capture_adapter.load_record(directory)['capture_state'], 'captured')
        snapshot = directory / 'snapshot'
        self.assertEqual((snapshot / 'config/ports.yaml').read_bytes(), b'official-source\n')
        self.assertEqual(source_adapter.capture_source(self.installation, self.plan), snapshot)

    def test_unknown_or_replaced_partial_snapshot_is_preserved(self):
        directory = self.bind()
        foreign = directory / 'snapshot'
        foreign.mkdir(mode=0o700)
        (foreign / 'foreign').write_text('preserve')
        with self.assertRaises(LifecycleStateError):
            source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual((foreign / 'foreign').read_text(), 'preserve')

    def test_replaced_partial_root_cannot_resume_even_with_identical_members(self):
        directory = self.bind()
        with patch.object(capture_adapter, '_write_tree', side_effect=OSError('interruption')):
            with self.assertRaises(LifecycleStateError):
                source_adapter.capture_source(self.installation, self.plan)
        snapshot = directory / 'snapshot'
        snapshot.rename(directory / 'retained-partial')
        snapshot.mkdir(mode=0o700)
        with self.assertRaises(LifecycleStateError):
            source_adapter.capture_source(self.installation, self.plan)
        self.assertTrue((directory / 'retained-partial').exists())

    def test_complete_snapshot_tampering_and_binding_directory_replacement_block(self):
        directory = self.bind()
        snapshot = source_adapter.capture_source(self.installation, self.plan)
        (snapshot / 'config/ports.yaml').write_bytes(b'changed')
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, self.plan)
        directory.rename(directory.with_name(directory.name + '.retained'))
        shutil.copytree(directory.with_name(directory.name + '.retained'), directory)
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, self.plan)

    def test_no_follow_blocks_a_member_swap_between_stat_and_open(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle import product_configuration_validation as validation

        original = os.open
        replaced = False

        def swapping_open(name, flags, *args, **kwargs):
            nonlocal replaced
            if name == 'setup.sh' and not replaced:
                replaced = True
                (self.external / 'setup.sh').unlink()
                (self.external / 'setup.sh').symlink_to('/etc/passwd')
            return original(name, flags, *args, **kwargs)

        with patch.object(validation.os, 'open', side_effect=swapping_open):
            with self.assertRaises(LifecycleStateError):
                self.prepare()
        self.assertTrue(replaced)
        self.assertFalse(self.installation.state.exists())

    def test_source_change_during_copy_is_detected_before_capture_completion(self):
        directory = self.bind()
        original = capture_adapter._write_tree

        def changing_copy(destination, tree, expected_root):
            original(destination, tree, expected_root)
            provider = self.external / PROVIDER
            provider.write_bytes(provider.read_bytes().replace(b'6GiB', b'5GiB'))

        with patch.object(capture_adapter, '_write_tree', side_effect=changing_copy):
            with self.assertRaises(LifecycleStateError):
                source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual(capture_adapter.load_record(directory)['capture_state'], 'capturing')

    def test_snapshot_swap_after_preparation_cannot_receive_writes_or_new_identity(self):
        directory = self.bind()
        original = capture_adapter._prepare_snapshot

        def swapped_snapshot(destination, record, tree):
            prepared = original(destination, record, tree)
            snapshot = destination / 'snapshot'
            snapshot.rename(destination / 'preserved-owned-snapshot')
            snapshot.mkdir(mode=0o700)
            (snapshot / 'foreign-bytes').write_bytes(b'preserve exactly')
            return prepared

        with patch.object(capture_adapter, '_prepare_snapshot', side_effect=swapped_snapshot):
            with self.assertRaises(LifecycleStateError):
                source_adapter.capture_source(self.installation, self.plan)
        self.assertEqual({path.name: path.read_bytes() for path in (directory / 'snapshot').iterdir()},
                         {'foreign-bytes': b'preserve exactly'})
        record = json.loads((directory / 'binding.json').read_bytes())
        self.assertEqual(record['capture_state'], 'capturing')
        self.assertNotEqual(record['snapshot_metadata']['root_identity'][1], (directory / 'snapshot').stat().st_ino)

    def test_competing_target_provider_change_blocks_three_way_migration(self):
        self.bind()
        source_adapter.capture_source(self.installation, self.plan)
        self.plan = self.plan.model_copy(update={'configuration_changes': ('infra/' + PROVIDER,)})
        target = self.installation.directory(self.plan) / 'infra'
        shutil.copytree(self.root / 'infra', target)
        provider = target / PROVIDER
        provider.write_bytes(provider.read_bytes().replace(b'8GiB', b'7GiB'))
        with self.assertRaises(LifecycleStateError):
            migrate_product_infra(self.installation, self.plan)
        self.assertIn(b'6GiB', (self.external / PROVIDER).read_bytes())

    def test_disk_floor_includes_capture_and_migrated_copy_budget(self):
        from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission import _host_and_resources

        self.prepare()
        self.plan = self.plan.model_copy(update={'resource_bytes': 2147483648 + source_adapter.reserve_bytes(self.plan.configuration_source)})
        detected = {'native-linux': HostEnvironmentKind.NATIVE_LINUX, 'wsl2': HostEnvironmentKind.WSL2}[self.plan.manifest.host]
        with (patch('tiny_swarm_world.infrastructure.adapters.host.host_environment_detector.HostEnvironmentDetector') as detector,
              patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission.sys.version_info', (3, 12)),
              patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission.shutil.disk_usage') as usage):
            detector.return_value.detect.return_value.environment = detected
            usage.return_value = SimpleNamespace(free=self.plan.resource_bytes - 1)
            with self.assertRaises(LifecycleStateError):
                _host_and_resources(self.installation, self.plan)
            usage.return_value = SimpleNamespace(free=self.plan.resource_bytes)
            _host_and_resources(self.installation, self.plan)

    def test_foreign_member_ownership_is_rejected_without_capture(self):
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_validation.os.getuid',
                   return_value=os.getuid() + 1):
            with self.assertRaises(LifecycleStateError):
                self.prepare()
        self.assertFalse(self.installation.state.exists())

    def test_effective_host_cpu_memory_and_cgroup_capacity_are_enforced(self):
        self.prepare()
        inspector = self.resource_inspector.return_value.inspect
        unsuitable = (HostResources(7, 20_111_052_800, None, 0, 200 * 1024**3),
                      HostResources(8, 16 * 1024**3, None, 0, 200 * 1024**3),
                      HostResources(8, 32 * 1024**3, 16 * 1024**3, 0, 200 * 1024**3))
        for resources in unsuitable:
            inspector.return_value = resources
            with self.assertRaises(LifecycleStateError):
                source_adapter.validate(self.installation, self.plan)
        inspector.return_value = HostResources(8, 20_111_052_800, None, 0, 200 * 1024**3)
        source_adapter.validate(self.installation, self.plan)

    def test_bound_resume_rechecks_capacity_before_any_staging_mutation(self):
        self.bind()
        self.resource_inspector.return_value.inspect.return_value = HostResources(
            8, 32 * 1024**3, 16 * 1024**3, 0, 200 * 1024**3)
        with self.assertRaises(LifecycleStateError):
            source_adapter.validate(self.installation, self.plan)
        self.assertFalse((self.installation.state / 'releases').exists())

    def test_exact_changed_assets_migrate_while_17gib_and_executable_survive(self):
        self.bind()
        source_adapter.capture_source(self.installation, self.plan)
        target = self.installation.directory(self.plan) / 'infra'
        shutil.copytree(self.root / 'infra', target)
        for relative in self.plan.configuration_changes:
            (self.installation.directory(self.plan) / relative).write_bytes(b'official-target\n')
        migrate_product_infra(self.installation, self.plan)
        effective = self.installation.state / 'infra' / TARGET_REVISION
        provider = YAML(typ='safe').load((effective / PROVIDER).read_text())
        self.assertEqual([node['resources']['memory'] for node in provider['nodes']], ['10GiB', '6GiB', '1GiB'])
        self.assertEqual((effective / 'config/ports.yaml').read_bytes(), b'official-target\n')
        self.assertTrue((effective / 'setup.sh').stat().st_mode & 0o100)
        migrate_product_infra(self.installation, self.plan)

    def migrate_bound(self):
        self.bind()
        source_adapter.capture_source(self.installation, self.plan)
        target = self.installation.directory(self.plan) / 'infra'
        shutil.copytree(self.root / 'infra', target)
        for relative in self.plan.configuration_changes:
            (self.installation.directory(self.plan) / relative).write_bytes(b'official-target\n')
        migrate_product_infra(self.installation, self.plan)
        return self.installation.state / 'infra' / TARGET_REVISION

    def test_foreign_migration_pending_is_never_removed_or_adopted(self):
        self.bind()
        source_adapter.capture_source(self.installation, self.plan)
        pending = self.installation.state / 'infra' / (TARGET_REVISION + '.pending')
        pending.mkdir(parents=True, mode=0o700)
        (pending / 'foreign').write_bytes(b'preserve foreign migration')
        with self.assertRaises(LifecycleStateError):
            migrate_product_infra(self.installation, self.plan)
        self.assertEqual((pending / 'foreign').read_bytes(), b'preserve foreign migration')

    def test_foreign_code_pending_is_never_renamed_removed_or_adopted(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_environment import _clone_release

        self.bind()
        pending = self.installation.state / 'staging' / TARGET_REVISION
        pending.mkdir(parents=True, mode=0o700)
        (pending / 'foreign').write_bytes(b'preserve foreign code')
        with self.assertRaises(LifecycleStateError):
            _clone_release(self.installation, self.plan)
        self.assertEqual((pending / 'foreign').read_bytes(), b'preserve foreign code')
        self.assertFalse(any(call.args[0][:2] == ('git', 'clone') for call in self.installation._command.call_args_list))

    def test_owned_interrupted_migration_is_retained_then_rebuilt_with_disk_guard(self):
        self.bind()
        source_adapter.capture_source(self.installation, self.plan)
        target = self.installation.directory(self.plan) / 'infra'
        shutil.copytree(self.root / 'infra', target)
        for relative in self.plan.configuration_changes:
            (self.installation.directory(self.plan) / relative).write_bytes(b'official-target\n')
        with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration._migrate_changed_assets',
                   side_effect=OSError('injected migration interruption')):
            with self.assertRaises(OSError):
                migrate_product_infra(self.installation, self.plan)
        pending = self.installation.state / 'infra' / (TARGET_REVISION + '.pending')
        original_inode = pending.stat().st_ino
        migrate_product_infra(self.installation, self.plan)
        retained = tuple(pending.parent.glob(pending.name + '.interrupted-*'))
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].stat().st_ino, original_inode)
        self.assertEqual(self.installation._host_and_resources.call_count, 2)

    def test_owned_interrupted_clone_is_retained_then_rebuilt(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_environment import _clone_release

        self.bind()
        listing = self.installation._command.return_value
        attempts = 0

        def clone_command(args, **kwargs):
            nonlocal attempts
            if args[:2] == ('git', 'clone'):
                attempts += 1
                (Path(args[-1]) / 'owned-fixture').write_text(str(attempts))
                if attempts == 1:
                    raise OSError('injected clone interruption')
                return ''
            if args[:2] == ('git', 'rev-parse'):
                return TARGET_REVISION
            return '' if args[:2] == ('git', 'status') else listing

        self.installation._command.side_effect = clone_command
        self.installation.directory(self.plan).parent.mkdir(parents=True, mode=0o700)
        with self.assertRaises(OSError):
            _clone_release(self.installation, self.plan)
        _clone_release(self.installation, self.plan)
        self.assertEqual((self.installation.directory(self.plan) / 'owned-fixture').read_text(), '2')
        retained = tuple((self.installation.state / 'staging').glob(TARGET_REVISION + '.interrupted-*'))
        self.assertEqual((retained[0] / 'owned-fixture').read_text(), '1')
        self.assertEqual(self.installation._host_and_resources.call_count, 2)

    def test_pending_replacement_before_publication_is_not_adopted(self):
        directory = self.bind()
        pending = self.installation.state / 'staging' / TARGET_REVISION
        pending.parent.mkdir(parents=True, mode=0o700)
        source_adapter.prepare_pending(self.installation, self.plan, pending, 'code')
        pending.rename(pending.with_name('retained-original'))
        pending.mkdir(mode=0o700)
        (pending / 'foreign').write_bytes(b'preserve replacement')
        destination = self.installation.directory(self.plan)
        destination.parent.mkdir(parents=True, mode=0o700)
        with self.assertRaises(LifecycleStateError):
            source_adapter.publish_pending(self.installation, self.plan, pending, destination, 'code')
        self.assertFalse(destination.exists())
        self.assertEqual((pending / 'foreign').read_bytes(), b'preserve replacement')
        self.assertIn('code', capture_adapter.load_record(directory)['pending_roots'])

    def test_bound_activation_target_execution_and_unset_resume_use_managed_17gib(self):
        effective = self.migrate_bound()
        del os.environ['TSW_INFRA_ROOT']
        self.installation.activate(self.plan)
        self.assertEqual((self.installation.state / 'active/infra').resolve(), effective)
        launcher = (self.installation.state / 'tiny-swarm-world').read_text()
        self.assertIn(str(self.installation.state / 'active/infra'), launcher)
        self.assertNotIn(str(self.external), launcher)
        listing = self.installation._command.return_value
        self.installation._command.side_effect = lambda args, **kwargs: ('target-runtime-verified' if '-c' in args else listing)
        self.installation.verify_target_runtime(self.plan)
        command = self.installation._command.call_args
        self.assertEqual(command.args[0][0], str(self.installation.directory(self.plan) / '.venv/bin/python'))
        self.assertEqual(command.kwargs['env']['TSW_INFRA_ROOT'], str(effective))
        provider = YAML(typ='safe').load((effective / PROVIDER).read_text())
        self.assertEqual([node['resources']['memory'] for node in provider['nodes']], ['10GiB', '6GiB', '1GiB'])
        os.environ['TSW_INFRA_ROOT'] = str(self.root / 'infra')
        with self.assertRaises(LifecycleStateError):
            self.installation.activate(self.plan)

    def test_real_product_composition_freezes_child_authority_initial_resume_and_noop(self):
        from tiny_swarm_world.infrastructure.composition import build_product_upgrade

        lifecycle = SimpleNamespace(catalog=Mock(root=self.root),
            manifests=JsonManifestRepository(self.root / '.tiny-swarm-world/installation/manifest.json'))
        with patch('tiny_swarm_world.infrastructure.composition_lifecycle.build_installation_lifecycle_service', return_value=lifecycle):
            service = build_product_upgrade()
        service.installation._command = self.installation._command
        self.installation = service.installation
        self.installation._host_and_resources = Mock()
        self.prepare()
        listing = self.installation._command.return_value
        self.installation._command.side_effect = lambda args, **kwargs: ('target-runtime-verified' if '-c' in args else listing)
        service.runtime._inventory = Mock(return_value={'portainer': 'stable-id'})
        environment = dict(os.environ)
        asyncio.run(service.runtime.verify(self.plan.manifest, plan=self.plan))
        first = self.installation._command.call_args
        self.assertEqual(first.args[0][0], sys.executable)
        self.assertEqual(first.kwargs['env']['TSW_INFRA_ROOT'], str(self.external))
        self.assertEqual(json.loads(first.kwargs['input']), self.plan.manifest.model_dump(mode='json'))
        self.assertEqual(dict(os.environ), environment)
        source_adapter.bind(self.installation, self.plan)
        source_adapter.capture_source(self.installation, self.plan)
        target = self.installation.directory(self.plan) / 'infra'
        shutil.copytree(self.root / 'infra', target)
        for relative in self.plan.configuration_changes:
            (self.installation.directory(self.plan) / relative).write_bytes(b'official-target\n')
        migrate_product_infra(self.installation, self.plan)
        del os.environ['TSW_INFRA_ROOT']
        environment = dict(os.environ)
        effective = self.installation.state / 'infra' / TARGET_REVISION
        for manifest in (self.plan.manifest, self.plan.manifest.model_copy(update={'product': self.plan.target.product})):
            asyncio.run(service.runtime.verify(manifest, plan=self.plan))
            command = self.installation._command.call_args
            self.assertEqual(command.kwargs['env']['TSW_INFRA_ROOT'], str(effective))
            self.assertEqual(json.loads(command.kwargs['input']), manifest.model_dump(mode='json'))
            service.runtime._inventory.assert_called_with(manifest, effective)
            self.assertEqual(dict(os.environ), environment)

    def test_public_preview_checkpoint_errors_and_traceback_exclude_private_values(self):
        sentinel = 'private-' + uuid4().hex
        provider = self.external / PROVIDER
        provider.write_bytes(provider.read_bytes() + ('\n# ' + sentinel + '\n').encode())
        directory = self.bind()
        checkpoint = ProductCheckpoint(plan=self.plan, stage='admitted', service_identities={})
        public = json.dumps(self.plan.preview()) + checkpoint.model_dump_json()
        os.environ['TSW_INFRA_ROOT'] = str(self.root / 'infra')
        with self.assertRaises(LifecycleStateError) as caught:
            source_adapter.validate(self.installation, self.plan)
        public += ''.join(traceback.format_exception(caught.exception))
        for value in (sentinel, hashlib.sha256(sentinel.encode()).hexdigest(), str(self.external),
                      'source_metadata', 'directory_identity', 'snapshot_metadata'):
            self.assertNotIn(value, public)
        self.assertIn(str(self.external), (directory / 'binding.json').read_text())

    def test_unknown_files_or_nonmemory_provider_changes_are_rejected(self):
        extra = self.external / 'backup'
        extra.write_text('not admitted')
        with self.assertRaises(LifecycleStateError):
            self.prepare()
        extra.unlink()
        provider = self.external / PROVIDER
        provider.write_bytes(provider.read_bytes().replace(b'cpu: "2"', b'cpu: "3"'))
        with self.assertRaises(LifecycleStateError):
            self.prepare()

    def test_invalid_memory_is_not_a_typed_override(self):
        provider = self.external / PROVIDER
        provider.write_bytes(provider.read_bytes().replace(b'6GiB', b'banana'))
        with self.assertRaises(LifecycleStateError):
            self.prepare()

    def test_symlink_hardlink_fifo_overlap_and_nonprivate_root_are_rejected(self):
        extra = self.external / 'unsafe'
        creators = (lambda: extra.symlink_to('/etc/passwd'),
                    lambda: os.link(self.external / 'setup.sh', extra), lambda: os.mkfifo(extra))
        for create in creators:
            create()
            with self.assertRaises(LifecycleStateError):
                self.prepare()
            extra.unlink()
        self.external.chmod(0o755)
        with self.assertRaises(LifecycleStateError):
            self.prepare()
        os.environ['TSW_INFRA_ROOT'] = str(self.root / '.tiny-swarm-world/product/infra')
        with self.assertRaises(LifecycleStateError):
            self.prepare()

    def test_doubled_leading_slash_cannot_disguise_anchor_or_managed_source(self):
        for source in (self.root / 'infra', self.installation.state / 'inputs', self.external):
            os.environ['TSW_INFRA_ROOT'] = '/' + str(source)
            with self.assertRaises(LifecycleStateError):
                self.prepare()
        self.assertFalse(self.installation.state.exists())

    def test_finite_file_total_members_and_depth_bounds(self):
        module = 'tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_validation.'
        for limit in ('MAX_FILE_BYTES', 'MAX_BYTES', 'MAX_MEMBERS', 'MAX_DEPTH'):
            with patch(module + limit, 1):
                with self.assertRaises(LifecycleStateError):
                    self.prepare()

    def test_journal_requires_binding_before_admitted_checkpoint(self):
        self.prepare()
        checkpoint = ProductCheckpoint(plan=self.plan, stage='admitted', service_identities={})
        journal = JsonProductJournal(self.installation.state / 'product-upgrade.json')
        with self.assertRaises(LifecycleStateError):
            journal.save(checkpoint)
        self.assertFalse(journal.path.exists())
        journal.source_binder = self.installation.bind_configuration
        journal.save(checkpoint)
        self.assertEqual(journal.load(), checkpoint)
        directory = self.installation.state / 'inputs' / self.plan.configuration_source.reference
        self.assertEqual(capture_adapter.load_record(directory)['capture_state'], 'admitted')

    def test_legacy_checkpoint_and_anchor_migration_remain_unbound(self):
        legacy = ProductCheckpoint(plan=product_plan(), stage='admitted', service_identities={})
        payload = legacy.model_dump(mode='json')
        del payload['plan']['configuration_source']
        restored = ProductCheckpoint.model_validate_json(json.dumps(payload))
        self.assertIsNone(restored.plan.configuration_source)
        del os.environ['TSW_INFRA_ROOT']
        source_adapter.validate(self.installation, restored.plan)
        self.assertEqual(source_adapter.effective_source(self.installation, restored.plan), self.root / 'infra')


if __name__ == '__main__':
    unittest.main()

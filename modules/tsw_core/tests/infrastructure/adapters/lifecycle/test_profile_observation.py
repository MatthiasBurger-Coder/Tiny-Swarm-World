"""Public composed verification observes dedicated profiles with no write authority."""
import json
import os
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import admitted_fixture, intent_fixture
from modules.tsw_core.tests.domain.lifecycle.test_models import manifest_fixture
from modules.tsw_core.tests.infrastructure.adapters.clients.test_lxc_profile_lifecycle import FrameRunner, instance_fixture
from modules.tsw_core.tests.infrastructure.adapters.clients.test_lxc_node_provider import _node_spec, _selection
from modules.tsw_core.tests.test_network_process_identity import process
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.lifecycle.models import migrate_manifest_v1, InstallationManifest
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, ProfileLifecycleCheckpoint
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import LxcNodeCommandResult
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime
from tiny_swarm_world.infrastructure.adapters.network_preparation.trusted_process import PROBE
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
from tiny_swarm_world.infrastructure.composition_platform import build_platform_services

_ROOT = Path(__file__).resolve().parents[6]
_LISTENER_ARGS = ('/usr/bin/sudo', '-n', '--', '/usr/bin/ss', '-H', '-O', '-ltnp')
_PROBE_ARGS = ('/usr/bin/sudo', '-n', '--', '/usr/bin/python3', '-I', '-B', '-c', PROBE, '201', '100', '202')


class OwnedFrameRunner(FrameRunner):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.live = False
    def activate(self, intent):
        self.live = True
        row = instance_fixture(intent, state='Running')
        row['expanded_config'].update(self.frames['/1.0/profiles?recursion=1&project=default'][0]['config'])
        self.frames['/1.0/instances?recursion=1&project=default'] = [row]
        self.frames['/1.0/instances/swarm-manager?project=default'] = row
        self.frames['/1.0/instances/swarm-manager/state?project=default'] = {
            'status': 'Running', 'status_code': 103, 'disk': None, 'network': None, 'pid': 202, 'processes': 1,
            'started_at': '', 'os_info': None, 'memory': dict(usage=1, usage_peak=1, total=1, swap_usage=0, swap_usage_peak=0),
            'cpu': dict(usage=1, allocated_time=1)}
        profiles = self.frames['/1.0/profiles?recursion=1&project=default']
        profiles[0]['used_by'] = ['/1.0/instances/swarm-manager']
        profiles.append({'name': intent.profile.profile.profile_name, 'project': 'default',
            'description': 'Tiny Swarm World installation profile', 'config': intent.markers(), 'devices': intent.devices(),
            'used_by': ['/1.0/instances/swarm-manager']})
    async def run(self, args, timeout_seconds):
        if '/usr/bin/git' in args:
            self.calls.append(tuple(args))
            if '--show-toplevel' in args:
                return LxcNodeCommandResult(0, str(self.root) + '\n')
            if 'ls-files' in args:
                if '--stage' not in args:
                    raise AssertionError('Expected staged Git file metadata.')
                return LxcNodeCommandResult(0, f'H 100644 {"a" * 40} 0\tsrc/tracked.py\0')
            if '--verify' in args:
                return LxcNodeCommandResult(0, 'c' * 40 + '\n')
            return LxcNodeCommandResult(0, '')
        if tuple(args) == _LISTENER_ARGS:
            self.calls.append(tuple(args))
            stdout = ('LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=201,fd=4))\n'
                      if self.live else '')
            return LxcNodeCommandResult(0, stdout)
        if tuple(args) == ('/usr/bin/ss', '-H', '-O', '-ltnp') and self.live:
            self.calls.append(tuple(args))
            return LxcNodeCommandResult(0, 'LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:*\n')
        if tuple(args) == _PROBE_ARGS:
            self.calls.append(tuple(args))
            return LxcNodeCommandResult(0, json.dumps(dict(listener=process(201), daemon=process(100), manager=process(202))))
        if args[0] == '/usr/bin/sudo':
            raise AssertionError('Unexpected privileged command in owned frame')
        return await super().run(args, timeout_seconds)


class PublicScopedVerificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_root_owned_listener_observation_requires_privileged_pid_and_existing_trusted_proof(self):
        intent = intent_fixture()
        runner = OwnedFrameRunner(_ROOT)
        runner.activate(intent)
        with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
            observed = await IncusProfileLifecycleRuntime(runner).for_observation(intent).inspect(intent)
        self.assertTrue(observed.listeners_match)
        self.assertFalse(observed.forbidden_listener)
        self.assertIn(_LISTENER_ARGS, runner.calls)
        self.assertIn(_PROBE_ARGS, runner.calls)
        self.assertFalse(any(args[0] == '/usr/bin/ss' for args in runner.calls))
        for args in runner.calls:
            if '/usr/bin/sudo' in args:
                self.assertIn(args, (_LISTENER_ARGS, _PROBE_ARGS))
            if 'query' in args:
                self.assertEqual(args[args.index('--request') + 1], 'GET')

    async def test_actual_public_composed_node_and_exposure_verification_are_read_only_and_keep_unbound_writers_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(_ROOT / 'modules/tsw_core/infra', root / 'modules/tsw_core/infra')
            for name in ('AGENTS.md', 'QUALITY.md'):
                shutil.copy2(_ROOT / name, root / name)
            package = root / 'modules/tsw_core/src'
            package.mkdir(parents=True)
            shutil.copy2(_ROOT / 'modules/tsw_core/src/__init__.py', package / '__init__.py')
            asset = root / 'modules/tsw_core/infra/config/incus-profile-capabilities.json'
            asset.parent.mkdir(parents=True, exist_ok=True)
            asset.write_text(admitted_fixture().model_dump_json())
            runner = OwnedFrameRunner(root)
            runtime = IncusProfileLifecycleRuntime(runner)
            intent = intent_fixture()
            with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
                baseline = await runtime.inspect(intent)
            intent = ManagerCreateIntent.model_validate_json(intent.model_copy(update={
                'base_profiles_sha256': baseline.base_profiles_sha256, 'preservation_sha256': baseline.preservation_sha256}).model_dump_json())
            runner.activate(intent)
            manifest = migrate_manifest_v1(manifest_fixture()).model_copy(update={
                'installation_id': intent.profile.installation_id, 'installation_profile': intent.profile.profile,
                'checkpoint_reference': 'profile-' + intent.profile.operation_id,
                'components': tuple(component for service in NativeComponentCatalog(root).load().services
                                    if service.service_id in intent.profile.resolved_services
                                    for component in service.components)})
            NativeComponentCatalog(root).load().validate_manifest(manifest)
            repository = JsonManifestRepository(root / '.tiny-swarm-world/installation/manifest.json')
            creation = JsonProfileLifecycleJournal(root)
            with JsonInstallationOperationLock(root).exclusive('profile-lifecycle') as lease:
                with creation.exclusive(lease):
                    creation.save(ProfileLifecycleCheckpoint(intent=intent, stage='completed', previous_stage='completed',
                        instance_uuid='11111111-1111-1111-1111-111111111111', installation_committed=True,
                        observation_sha256='a' * 64), expected=None, lease=lease)
                repository.save(InstallationManifest.model_validate_json(manifest.model_dump_json()), expected_token=None)
            before = repository.path.read_bytes()
            with patch.dict(os.environ, {'TSW_REPOSITORY_ROOT': str(root), 'TSW_INFRA_ROOT': str(_ROOT / 'modules/tsw_core/infra')}), \
                    patch('tiny_swarm_world.infrastructure.adapters.lifecycle.profile_observation.AsyncLxcNodeCommandRunner', return_value=runner), \
                    patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
                services = build_platform_services(service_profile='default', resolved_services=('incus', 'portainer'))
                self.assertIsNone(services.lxc_node_provider.profile_operation)
                self.assertFalse(services.lxc_node_provider.allow_live_mutation)
                self.assertIsNotNone(services.lxc_node_provider.profile_observer)
                self.assertIs(services.lxc_node_provider.profile_observer, services.lxc_service_exposure.profile_observer)
                result = await services.lxc_node_provider.verify_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))
                self.assertEqual(result.status, VerificationStatus.VERIFIED)
                result = await services.lxc_service_exposure.verify_service_exposure()
                self.assertEqual(result.status, VerificationStatus.VERIFIED)
                calls = len(runner.calls)
                with self.assertRaises(LifecycleStateError):
                    await services.lxc_node_provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))
                with self.assertRaises(LifecycleStateError):
                    await services.lxc_service_exposure.ensure_service_exposure()
                with self.assertRaises(LifecycleStateError):
                    await services.workflows.init.run()
                self.assertEqual(len(runner.calls), calls)
                asset.write_text('{"schema_version":1,"capability":"installation-scoped-incus-manager-profile","admitted_versions":[]}')
                with self.assertRaises(LifecycleStateError):
                    await services.lxc_node_provider.verify_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))
                self.assertEqual(len(runner.calls), calls)
            self.assertEqual(repository.path.read_bytes(), before)
            for args in runner.calls:
                if 'query' in args:
                    self.assertEqual(args[args.index('--request') + 1], 'GET')
                self.assertFalse(any(value in {'init', 'launch', 'start', 'stop', 'delete', 'PUT', 'POST', 'PATCH'} for value in args))

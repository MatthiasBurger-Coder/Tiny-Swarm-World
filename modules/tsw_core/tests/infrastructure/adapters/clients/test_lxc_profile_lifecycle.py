"""Real stopped-create renderer and strict observed ownership boundaries."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch

from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import admitted_fixture, intent_fixture
from modules.tsw_core.tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.args import scoped_init_args, scoped_node_config
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner, LxcNodeCommandResult
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile import observations as dto
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.cas import PROFILE_CAS
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import _ENV, IncusProfileLifecycleRuntime
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import clean_source_revision, local_image
from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository

_UUID = '11111111-1111-1111-1111-111111111111'
_SOCKET_FRAME = ('LoadState=loaded\nActiveState=active\nSubState=listening\nUnitFileState=enabled\n'
                 'Listen=/var/lib/incus/unix.socket (Stream)\n')
_EMPTY_MATRIX = '{"admitted_versions":[]}'
_LISTENER_ARGS = ('/usr/bin/sudo', '-n', '--', '/usr/bin/ss', '-H', '-O', '-ltnp')


def effect_runner(versions=('6.0.5', '6.0.5')):
    runner = AsyncMock()

    def respond(args, _timeout):
        if args[0] == '/usr/bin/systemctl':
            return LxcNodeCommandResult(0, _SOCKET_FRAME)
        if args[-1] == 'version':
            return LxcNodeCommandResult(0, f'Client version: {versions[0]}\nServer version: {versions[1]}\n')
        return LxcNodeCommandResult(0, json.dumps(dict(type='sync', status='Success', status_code=200,
            operation='', error_code=0, error='', metadata={})))

    runner.run.side_effect = respond
    return runner


def capability_repository(root: Path, contents: str | None) -> IncusProfileCapabilityRepository:
    repository = IncusProfileCapabilityRepository(root)
    if contents is not None:
        repository.path.parent.mkdir(parents=True)
        repository.path.write_text(contents)
    return repository


def instance_fixture(intent, *, state='Stopped'):
    config = {**scoped_node_config(intent, intent), 'volatile.base_image': intent.image_fingerprint, 'volatile.uuid': _UUID}
    devices = dto.local_devices(intent)
    return dict(name=intent.node_name, project='default', description='', architecture='x86_64', config=config,
        expanded_config=dict(config), devices=devices, expanded_devices={**devices, **intent.devices()},
        profiles=list(intent.attachments()), ephemeral=False, stateful=False, location='none', type='container',
        status=state, status_code=102 if state == 'Stopped' else 103, created_at='', last_used_at='')


class ProfileAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_installation_lease_cannot_admit_typed_mutation_without_capability(self):
        runner, intent = effect_runner(), intent_fixture()
        with TemporaryDirectory() as directory, JsonInstallationOperationLock(Path(directory)).exclusive('setup') as lease:
            runtime = IncusProfileLifecycleRuntime(runner).for_operation(lease, intent)
            with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'), \
                    self.assertRaises(LifecycleStateError):
                await runtime.create_profile(intent)
        runner.run.assert_not_called()

    async def test_raw_read_gateway_refuses_incus_effects_with_active_lease(self):
        intent = intent_fixture()
        payload = json.dumps({'name': intent.profile.profile.profile_name,
            'description': 'Tiny Swarm World installation profile', 'config': intent.markers(),
            'devices': intent.devices()}, sort_keys=True, separators=(',', ':'))
        commands = (
            ('start', (*_ENV, '--project', 'default', 'start', intent.node_name)),
            ('delete', (*_ENV, '--project', 'default', 'delete', intent.node_name)),
            ('POST', (*_ENV, 'query', '--request', 'POST', '--data', payload, '--raw', '--wait', '/1.0/profiles?project=default')),
            ('CAS', (*_ENV[:4], '/usr/bin/python3', '-I', '-B', '-c', PROFILE_CAS, '{}')),
            ('altered GET', (*_ENV, 'query', '--request', 'GET', '--raw', '--data', '{}', '/1.0')),
            ('arbitrary script', ('/usr/bin/sudo', '-n', '--', '/usr/bin/python3', '-I', '-B', '-c', 'pass', '1', '2', '3')),
            ('raw Git', ('/usr/bin/git', 'status', '--porcelain=v1')),
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            capabilities = capability_repository(root, admitted_fixture().model_dump_json())
            with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                for label, args in commands:
                    for mutation in (False, True):
                        with self.subTest(command=label, declared_mutation=mutation):
                            runner = effect_runner()
                            runtime = IncusProfileLifecycleRuntime(runner, capabilities=capabilities).for_operation(lease, intent)
                            with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'), \
                                    self.assertRaises(LifecycleStateError):
                                await runtime.run(args, mutation=mutation)
                            runner.run.assert_not_called()

    async def test_bad_capability_assets_block_typed_effects_before_preparation_reads(self):
        intent = intent_fixture()
        wrong = admitted_fixture().model_dump_json().replace('6.0.5', '6.0.6')
        for label, contents in (('missing', None), ('empty', _EMPTY_MATRIX),
                                ('malformed', '{"admitted_versions":"private-canary"}'), ('wrong version', wrong)):
            with self.subTest(asset=label), TemporaryDirectory() as directory:
                root = Path(directory)
                capabilities = capability_repository(root, contents)
                runner = effect_runner()
                with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                    runtime = IncusProfileLifecycleRuntime(runner, capabilities=capabilities).for_operation(lease, intent)
                    with self.assertRaises(LifecycleStateError):
                        await runtime.create_profile(intent)
                    with self.assertRaises(LifecycleStateError):
                        await runtime.update_profile(intent, intent)
                    with self.assertRaises(LifecycleStateError):
                        await runtime.delete_profile(intent)
                    with self.assertRaises(LifecycleStateError):
                        await runtime.delete_instance(intent)
                runner.run.assert_not_called()

    async def test_actual_client_or_server_version_mismatch_blocks_before_profile_read_or_effect(self):
        intent = intent_fixture()
        for versions in (('6.0.6', '6.0.5'), ('6.0.5', '6.0.6')):
            with self.subTest(versions=versions), TemporaryDirectory() as directory:
                root = Path(directory)
                capabilities = capability_repository(root, admitted_fixture().model_dump_json())
                runner = effect_runner(versions)
                with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                    runtime = IncusProfileLifecycleRuntime(runner, capabilities=capabilities).for_operation(lease, intent)
                    with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'), \
                            self.assertRaises(LifecycleStateError):
                        await runtime.update_profile(intent, intent)
                self.assertEqual([call.args[0][-1] for call in runner.run.call_args_list], ['--no-pager', 'version'])

    async def test_revocation_during_final_socket_read_prevents_effect_dispatch(self):
        intent = intent_fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            capabilities = capability_repository(root, admitted_fixture().model_dump_json())
            runner = effect_runner()
            respond = runner.run.side_effect
            version_seen = False

            def revoke_after_version(args, timeout):
                nonlocal version_seen
                if args[-1] == 'version':
                    version_seen = True
                elif version_seen and args[:3] == ('/usr/bin/systemctl', 'show', 'incus.socket'):
                    capabilities.path.write_text(_EMPTY_MATRIX)
                return respond(args, timeout)

            runner.run.side_effect = revoke_after_version
            with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                runtime = IncusProfileLifecycleRuntime(runner, capabilities=capabilities).for_operation(lease, intent)
                with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'), \
                        self.assertRaises(LifecycleStateError):
                    await runtime.init_instance(intent)
            self.assertEqual([call.args[0][-1] for call in runner.run.call_args_list],
                             ['--no-pager', 'version', '--no-pager'])

    def test_renderer_never_launches_or_uses_mutable_alias_or_shared_manager_profile(self):
        intent = intent_fixture()
        args = scoped_init_args(intent, intent.node_name)
        self.assertEqual(args[:5], ('--project', 'default', 'init', intent.image_fingerprint, 'swarm-manager'))
        self.assertNotIn('launch', args)
        self.assertNotIn('--force', args)
        self.assertNotIn('docker-swarm-manager', args)
        self.assertIn('root,size=20GiB', args)
        self.assertIn('boot.autostart=false', args)
        with self.assertRaises(ValueError):
            scoped_init_args(intent, 'unselected')

    def test_real_observed_local_expanded_and_uuid_ownership_all_required(self):
        intent = intent_fixture()
        row = instance_fixture(intent)
        dto.instance_rows([row], 'default')
        self.assertEqual(dto.owned_instance(row, intent), ('stopped', _UUID, True))
        invalid: tuple[tuple[str, object], ...] = (('profiles', ['default']), ('type', 'virtual-machine'),
            ('ephemeral', True), ('status_code', 103))
        for key, value in invalid:
            changed = {**row, key: value}
            with self.subTest(field=key):
                self.assertEqual(dto.owned_instance(changed, intent)[0], 'foreign')
        changed = deepcopy(row)
        changed['expanded_devices']['inherited-extra'] = {'type': 'proxy', 'listen': 'tcp:0.0.0.0:16080', 'connect': 'tcp:127.0.0.1:16080'}
        self.assertFalse(dto.owned_instance(changed, intent)[2])
        changed = deepcopy(row)
        changed['config']['user.tiny_swarm_world.installation_id'] = 'foreign'
        self.assertEqual(dto.owned_instance(changed, intent)[0], 'foreign')

    async def test_real_mutation_port_requires_private_active_lease_and_atomic_complete_profile(self):
        runner, intent = effect_runner(), intent_fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            capabilities = capability_repository(root, admitted_fixture().model_dump_json())
            runtime = IncusProfileLifecycleRuntime(runner, capabilities=capabilities)
            with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                observer = runtime.for_observation(intent)
                for view in (runtime, observer, observer.for_operation(lease, intent), runtime.for_preparation(lease)):
                    with self.assertRaises(LifecycleStateError):
                        await view.create_profile(intent)
                runner.run.assert_not_called()
                private = runtime.for_operation(lease, intent)
                with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
                    await private.create_profile(intent)
                args = runner.run.call_args.args[0]
                payload = json.loads(args[args.index('--data') + 1])
                self.assertEqual(payload['config'], intent.markers())
                self.assertEqual(payload['devices'], intent.devices())
                self.assertIn('--wait', args)
                self.assertIsNone(runtime.lease)
                self.assertEqual(sum('POST' in call.args[0] for call in runner.run.call_args_list), 1)
                with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
                    await private.delete_instance(intent)
                    self.assertEqual(runner.run.call_args.args[0][-2:], ('delete', intent.node_name))
                    await private.delete_profile(intent)
                    self.assertEqual(runner.run.call_args.args[0][-3:],
                                     ('profile', 'delete', intent.profile.profile.profile_name))
            calls = runner.run.call_count
            with self.assertRaises(LifecycleStateError):
                await private.init_instance(intent)
            self.assertEqual(runner.run.call_count, calls)

    async def test_clean_source_read_suppresses_git_filter_and_preserves_index_bytes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*args: str) -> str:
                return subprocess.run(('/usr/bin/git', '-C', str(root), '-c', 'core.hooksPath=/dev/null', *args),
                    env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
                         'GIT_CONFIG_GLOBAL': '/dev/null'}, capture_output=True, check=True, text=True).stdout

            git('init', '-q')
            tracked = root / 'tracked.txt'
            tracked.write_text('fixture\n')
            (root / '.gitattributes').write_text('tracked.txt filter=sentinel\n')
            git('add', 'tracked.txt', '.gitattributes')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@localhost', 'commit', '-q', '--no-gpg-sign', '-m', 'fixture')
            revision = git('rev-parse', 'HEAD').strip()
            sentinel = root / '.git' / 'filter-fired'
            git('config', 'filter.sentinel.clean', f'/usr/bin/touch {shlex.quote(str(sentinel))}; /usr/bin/cat')
            git('config', 'filter.sentinel.required', 'true')
            previous = tracked.stat()
            os.utime(tracked, ns=(previous.st_atime_ns, previous.st_mtime_ns + 2_000_000_000))
            index = root / '.git' / 'index'
            before = index.read_bytes()
            runtime = IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner()).for_observation(intent_fixture())
            self.assertEqual(await clean_source_revision(runtime, root), revision)
            self.assertFalse(sentinel.exists())
            self.assertEqual(index.read_bytes(), before)

    async def test_fixed_image_query_binds_fingerprint_and_rejects_alias_drift(self):
        runtime = AsyncMock()
        runtime.query.return_value = {'name': 'ubuntu-24.04', 'target': 'e' * 64, 'type': 'container', 'description': ''}
        self.assertEqual(await local_image(runtime, 'ubuntu-24.04'), 'e' * 64)
        runtime.query.assert_awaited_once_with('/1.0/images/aliases/ubuntu-24.04?project=default')
        runtime.query.return_value['name'] = 'different'
        with self.assertRaises(LifecycleStateError):
            await local_image(runtime, 'ubuntu-24.04')
        for unsafe in ('images:ubuntu/24.04', '../ubuntu', 'ubuntu?project=foreign'):
            with self.assertRaises(LifecycleStateError):
                await local_image(runtime, unsafe)

    def test_uri_and_raw_response_protocol_reject_before_command(self):
        for unsafe in ('https://remote/1.0', '/1.0/images/aliases/a?project=foreign', '/1.0/instances/other?project=default'):
            with self.assertRaises(LifecycleStateError):
                dto.allowed_read_uri(unsafe)
        for raw in ('{}', '{"type":"sync","type":"sync"}', '{"type":"error"}'):
            with self.assertRaises(LifecycleStateError):
                dto.metadata(raw)


def server_fixture():
    environment = dict(certificate='private-certificate-canary', certificate_fingerprint='fixture', driver='lxc',
        driver_version='6.0', firewall='nftables', kernel='Linux', kernel_architecture='x86_64', kernel_version='6.8',
        os_name='Ubuntu', os_version='26.04', project='default', server='incus', server_event_mode='full-mesh',
        server_name='private-host-canary', server_version='6.0.5', storage='dir', storage_version='1',
        server_clustered=False, server_pid=100, addresses=[], architectures=['x86_64'], kernel_features={},
        lxc_features={}, storage_supported_drivers=[{'Name': 'dir', 'Version': '1', 'Remote': False}])
    return dict(api_status='stable', api_version='1.0', auth='trusted', auth_user_name='private-user-canary',
        auth_user_method='unix', public=False, api_extensions=[], auth_methods=['tls'], config={}, environment=environment)


class FrameRunner:
    def __init__(self):
        base = {'name': 'docker-swarm', 'project': 'default', 'description': 'base', 'config': {
            'security.nesting': 'true', 'security.syscalls.intercept.mknod': 'true',
            'security.syscalls.intercept.setxattr': 'true'}, 'devices': {}, 'used_by': []}
        self.frames = {'/1.0': server_fixture(), '/1.0/projects?recursion=1': [
            {'name': 'default', 'description': '', 'config': {}, 'used_by': []}],
            '/1.0/profiles?recursion=1&project=default': [base, {'name': 'docker-swarm-manager', 'project': 'default',
                'description': 'foreign-profile-canary', 'config': {'user.private': 'private-profile-canary'},
                'devices': {}, 'used_by': []}], '/1.0/instances?recursion=1&project=default': [],
            '/1.0/networks/incusbr0?project=default': {'name': 'incusbr0', 'description': '', 'managed': True,
                'type': 'bridge', 'status': 'Created', 'config': {'ipv4.nat': 'true', 'ipv6.address': 'none'}, 'used_by': [], 'locations': []},
            '/1.0/storage-pools/default?project=default': {'name': 'default', 'description': '', 'driver': 'dir',
                'status': 'Created', 'config': {}, 'used_by': [], 'locations': []}}
        self.calls = []
        self.final_drift = False
        self.root_reads = 0
    async def run(self, args, timeout_seconds):
        self.calls.append(tuple(args))
        if args[0] == '/usr/bin/systemctl' and args[2] == 'incus.socket':
            return LxcNodeCommandResult(0, 'LoadState=loaded\nActiveState=active\nSubState=listening\nUnitFileState=enabled\nListen=/var/lib/incus/unix.socket (Stream)\n')
        if args[0] == '/usr/bin/systemctl':
            return LxcNodeCommandResult(0, 'LoadState=loaded\nActiveState=active\nUnitFileState=enabled\nMainPID=100\n')
        if tuple(args) in {_LISTENER_ARGS, ('/usr/bin/ss', '-H', '-O', '-ltnp')}:
            return LxcNodeCommandResult(0, '')
        if args[0] == '/usr/bin/sudo':
            raise AssertionError('Unexpected privileged command in read-only frame')
        if args[-1] == 'version':
            return LxcNodeCommandResult(0, 'Client version: 6.0.5\nServer version: 6.0.5\n')
        if 'query' not in args or args[args.index('--request') + 1] != 'GET':
            raise AssertionError('Unexpected effect in read-only frame')
        row = deepcopy(self.frames[args[-1]])
        if args[-1] == '/1.0':
            self.root_reads += 1
            if self.final_drift and self.root_reads == 2:
                row['environment']['server_clustered'] = True
        return LxcNodeCommandResult(0, json.dumps(dict(type='sync', status='Success', status_code=200,
            operation='', error_code=0, error='', metadata=row)))


class ListenerFrameRunner(FrameRunner):
    def __init__(self, result):
        super().__init__()
        self.listener_result = result

    async def run(self, args, timeout_seconds):
        if tuple(args) != _LISTENER_ARGS and args[0] != '/usr/bin/ss':
            return await super().run(args, timeout_seconds)
        self.calls.append(tuple(args))
        if tuple(args) == ('/usr/bin/ss', '-H', '-O', '-ltnpe'):
            return LxcNodeCommandResult(0, self.listener_result.stdout, 'Failed to open cgroup2 by ID\n')
        if tuple(args) != _LISTENER_ARGS:
            raise AssertionError('Unexpected listener observation command')
        return self.listener_result


class RealObservationFrameTests(unittest.IsolatedAsyncioTestCase):
    async def test_listener_observation_avoids_unused_cgroup_expansion_without_losing_pid_data(self):
        stdout = 'LISTEN 0 4096 127.0.0.53:53 0.0.0.0:* users:(("systemd-resolve",pid=41,fd=14))\n'
        runner = ListenerFrameRunner(LxcNodeCommandResult(0, stdout))
        with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
            observed = await IncusProfileLifecycleRuntime(runner).inspect(intent_fixture())
        self.assertTrue(observed.listeners_clear)
        self.assertFalse(observed.forbidden_listener)
        self.assertEqual([args for args in runner.calls if '/usr/bin/ss' in args], [_LISTENER_ARGS])
        managed = 'LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=314,fd=8))\n'
        self.assertEqual(dto.listener_rows(managed, intent_fixture()), [('127.0.0.1', 10001, 314)])

    async def test_corrected_listener_command_still_rejects_every_transport_failure(self):
        results = (
            LxcNodeCommandResult(0, '', 'Failed to open cgroup2 by ID\n'),
            LxcNodeCommandResult(0, '', 'unexpected diagnostic\n'),
            LxcNodeCommandResult(1, '', 'sudo: a password is required\n'),
            LxcNodeCommandResult(1, ''),
            LxcNodeCommandResult(0, '', timed_out=True),
            LxcNodeCommandResult(0, '', failure_hint='incomplete output'),
        )
        for result in results:
            runner = ListenerFrameRunner(result)
            with self.subTest(result=result), patch(
                    'tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'), \
                    self.assertRaises(LifecycleStateError):
                await IncusProfileLifecycleRuntime(runner).run(_LISTENER_ARGS)
            self.assertEqual(runner.calls, [_LISTENER_ARGS])

    async def test_listener_privilege_is_limited_to_exact_noninteractive_read_only_arguments(self):
        commands = (
            ('/usr/bin/ss', '-H', '-O', '-ltnp'),
            ('/usr/bin/sudo', '--', '/usr/bin/ss', '-H', '-O', '-ltnp'),
            ('/usr/bin/sudo', '-n', '/usr/bin/ss', '-H', '-O', '-ltnp'),
            ('/usr/bin/sudo', '-n', '--', '/bin/ss', '-H', '-O', '-ltnp'),
            (*_LISTENER_ARGS, '-K'),
            (*_LISTENER_ARGS, '--kill'),
            (*_LISTENER_ARGS, 'sport = :10001'),
            (*_LISTENER_ARGS[:4], '-K'),
        )
        for args in commands:
            runner = AsyncMock()
            with self.subTest(args=args), self.assertRaises(LifecycleStateError):
                await IncusProfileLifecycleRuntime(runner).run(args)
            runner.run.assert_not_called()

    async def test_listener_observation_retains_ambiguous_foreign_and_duplicate_refusal(self):
        intent = intent_fixture()
        for process in ('', 'users:(("incusd",pid=314,fd=8),("foreign",pid=315,fd=9))'):
            with self.subTest(process=process), self.assertRaises(LifecycleStateError):
                dto.listener_rows('LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:* ' + process, intent)
        own = 'LISTEN 0 4096 127.0.0.1:10001 0.0.0.0:* users:(("incusd",pid=314,fd=8))\n'
        for stdout, forbidden in ((own + own, False), (own.replace(':10001', ':16080'), True)):
            runtime = AsyncMock()
            runtime.run.return_value = stdout
            with self.subTest(stdout=stdout):
                observed = await dto.listeners(runtime, intent, 100, True, True, _UUID)
                self.assertEqual(observed[:3], (forbidden, False, False))
                self.assertEqual(observed[3], ())
                runtime.run.assert_awaited_once_with(_LISTENER_ARGS)
        runtime = AsyncMock()
        runtime.run.return_value = own
        with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.observations.listener_proof',
                   side_effect=LifecycleStateError('Untrusted listener')) as proof, \
                self.assertRaises(LifecycleStateError):
            await dto.listeners(runtime, intent, 100, True, True, _UUID)
        proof.assert_awaited_once_with(runtime, 314, 100, intent, _UUID)

    async def test_actual_command_adapter_collects_strict_complete_frame_without_exporting_raw_metadata(self):
        from dataclasses import asdict
        runner = FrameRunner()
        runtime = IncusProfileLifecycleRuntime(runner)
        with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
            observed = await runtime.inspect(intent_fixture())
        self.assertEqual(observed.profile_state, 'absent')
        self.assertEqual(observed.instance_state, 'absent')
        self.assertTrue(observed.listeners_clear)
        self.assertEqual(runner.root_reads, 2)
        rendered = json.dumps(asdict(observed))
        for canary in ('private-certificate-canary', 'private-host-canary', 'private-user-canary', 'private-profile-canary'):
            self.assertNotIn(canary, rendered)
        self.assertTrue(any('/1.0/instances?recursion=1&project=default' in args for args in runner.calls))
        self.assertFalse(any('recursion=2' in value for args in runner.calls for value in args))

    async def test_final_cluster_drift_inherited_view_drift_and_unknown_instance_dto_refuse(self):
        for mutation in ('final', 'view', 'instance'):
            runner = FrameRunner()
            if mutation == 'final':
                runner.final_drift = True
            elif mutation == 'view':
                runner.frames['/1.0/projects?recursion=1'].append({'name': 'alpha', 'description': '', 'config': {}, 'used_by': []})
                runner.frames['/1.0/profiles?recursion=1&project=alpha'] = []
                runner.frames['/1.0/instances?recursion=1&project=alpha'] = []
            else:
                row = instance_fixture(intent_fixture())
                row['unexpected'] = 'private-canary'
                runner.frames['/1.0/instances?recursion=1&project=default'] = [row]
            with self.subTest(mutation=mutation), \
                    patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'), \
                    self.assertRaises(LifecycleStateError) as error:
                await IncusProfileLifecycleRuntime(runner).inspect(intent_fixture())
            self.assertNotIn('private-canary', str(error.exception))


class AdapterBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def test_foreign_phase_idle_does_not_consume_command_time_and_private_templates_share_budget(self):
        runner = AsyncMock()
        runner.run.return_value = LxcNodeCommandResult(0, '')
        runtime = IncusProfileLifecycleRuntime(runner)
        with FakeInstallationLock().exclusive('setup') as lease:
            prepared = runtime.for_preparation(lease)
            with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.time.monotonic',
                       side_effect=[0.0, 5.0, 10000.0, 10007.0]):
                await prepared.run(dto._OWNER_ARGS)
                private = prepared.for_operation(lease, intent_fixture())
                self.assertIs(private.budget, prepared.budget)
                await private.run(dto._OWNER_ARGS)
            self.assertEqual(prepared.budget.remaining, 288.0)
            self.assertEqual(prepared.budget.commands, 2)
            self.assertEqual(runtime.budget.commands, 0)

    async def test_over_budget_timeout_cleanup_and_negative_clock_refuse_subsequent_spawn(self):
        for clock in ([1.0, 3.0], [3.0, 1.0]):
            runner = AsyncMock()
            runner.run.return_value = LxcNodeCommandResult(0, '')
            runtime = IncusProfileLifecycleRuntime(runner)
            runtime.budget.remaining = 1.0
            with self.subTest(clock=clock), patch(
                    'tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.time.monotonic', side_effect=clock):
                with self.assertRaises(LifecycleStateError):
                    await runtime.run(dto._OWNER_ARGS)
            self.assertEqual(runner.run.call_args.args[1], 1.0)
            with self.assertRaises(LifecycleStateError):
                await runtime.run(dto._OWNER_ARGS)
            self.assertEqual(runner.run.call_count, 1)

    async def test_concurrent_copy_cannot_reenter_shared_command_budget(self):
        import asyncio
        entered, release = asyncio.Event(), asyncio.Event()
        async def slow(args, timeout):
            entered.set()
            await release.wait()
            return LxcNodeCommandResult(0, '')
        runner = AsyncMock()
        runner.run.side_effect = slow
        runtime = IncusProfileLifecycleRuntime(runner)
        with FakeInstallationLock().exclusive('setup') as lease:
            private = runtime.for_preparation(lease)
            other = private.for_operation(lease, intent_fixture())
            active = asyncio.create_task(private.run(dto._OWNER_ARGS))
            await entered.wait()
            with self.assertRaises(LifecycleStateError):
                await other.run(dto._OWNER_ARGS)
            self.assertEqual(runner.run.call_count, 1)
            release.set()
            await active
            self.assertFalse(private.budget.busy)


class SocketBindingTests(unittest.IsolatedAsyncioTestCase):
    def test_only_authoritative_unit_listen_binds_either_allowlisted_socket_kind(self):
        prefix = 'LoadState=loaded\nActiveState=active\nSubState=listening\nUnitFileState=enabled\n'
        for path, expected in (('/var/lib/incus/unix.socket', 'incus_var_lib'), ('/run/incus/unix.socket', 'incus_run')):
            self.assertEqual(dto.socket_binding(prefix + 'Listen=' + path + ' (Stream)\n'), expected)
        for listen in ('/tmp/incus.socket', '/run/incus/unix.socket (Stream) /var/lib/incus/unix.socket (Stream)', ''):
            with self.assertRaises(LifecycleStateError):
                dto.socket_binding(prefix + 'Listen=' + listen + '\n')
        for broken in ('LoadState=not-found\nActiveState=inactive\nSubState=dead\nUnitFileState=not-found\nListen=\n',
                       prefix + 'MainPID=42\nListen=/var/lib/incus/unix.socket (Stream)\n'):
            with self.assertRaises(LifecycleStateError):
                dto.socket_binding(broken)

    async def test_changed_unit_endpoint_cannot_rebind_retained_create_intent_or_fallback(self):
        runner = AsyncMock()
        runner.run.return_value = LxcNodeCommandResult(0, 'LoadState=loaded\nActiveState=active\nSubState=listening\nUnitFileState=enabled\nListen=/run/incus/unix.socket (Stream)\n')
        intent = intent_fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            capabilities = capability_repository(root, admitted_fixture().model_dump_json())
            with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                runtime = IncusProfileLifecycleRuntime(runner, capabilities=capabilities).for_operation(lease, intent)
                with self.assertRaises(LifecycleStateError):
                    await runtime.init_instance(intent)
        self.assertEqual(runner.run.call_count, 1)
        self.assertEqual(runner.run.call_args.args[0][:3], ('/usr/bin/systemctl', 'show', 'incus.socket'))


class ExistingScopedProviderTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_provider_helper_uses_typed_runtime_original_and_change_target(self):
        from types import SimpleNamespace
        from modules.tsw_core.tests.application.services.test_profile_change import fixture
        from modules.tsw_core.tests.infrastructure.adapters.clients.test_lxc_node_provider import _node_spec, _selection
        from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileRuntimeIntent
        from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
        from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import _scoped_node
        from tiny_swarm_world.domain.inventory import VerificationStatus

        change, _ = fixture()
        runtime = ProfileRuntimeIntent(profile=change.before.profile, original=change.before,
                                       planned_stack_owners=change.before.planned_stack_owners)
        for intent in (runtime, change):
            with self.subTest(kind=type(intent).__name__), FakeInstallationLock().exclusive('setup') as lease:
                operation = SimpleNamespace(intent=intent, lease=lease, ensure_manager=AsyncMock(),
                    ensure_worker=AsyncMock(), verify_node=AsyncMock())
                selected = _selection(ManagedLxcBackend.INCUS)
                result = await _scoped_node(operation, _node_spec(), selected, ensure=True)
                self.assertEqual(result.status, VerificationStatus.VERIFIED)
                operation.ensure_manager.assert_awaited_once_with()
                operation.ensure_worker.assert_not_awaited()
                await _scoped_node(operation, _node_spec(), selected, ensure=False)
                operation.verify_node.assert_awaited_once_with('swarm-manager')
                with self.assertRaises(LifecycleStateError):
                    await _scoped_node(operation, _node_spec(name='unselected'), selected, ensure=True)
                operation.ensure_manager.assert_awaited_once_with()
                operation.intent = SimpleNamespace(node_name='swarm-manager', workers=())
                with self.assertRaises(LifecycleStateError):
                    await _scoped_node(operation, _node_spec(), selected, ensure=True)

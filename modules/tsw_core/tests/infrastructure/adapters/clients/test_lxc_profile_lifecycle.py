"""Real stopped-create renderer and strict observed ownership boundaries."""
from copy import deepcopy
import json
import unittest
from unittest.mock import AsyncMock, patch

from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import intent_fixture
from modules.tsw_core.tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.args import scoped_init_args, scoped_node_config
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import LxcNodeCommandResult
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile import observations as dto
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import local_image

_UUID = '11111111-1111-1111-1111-111111111111'


def instance_fixture(intent, *, state='Stopped'):
    config = {**scoped_node_config(intent, intent), 'volatile.base_image': intent.image_fingerprint, 'volatile.uuid': _UUID}
    devices = dto.local_devices(intent)
    return dict(name=intent.node_name, project='default', description='', architecture='x86_64', config=config,
        expanded_config=dict(config), devices=devices, expanded_devices={**devices, **intent.devices()},
        profiles=list(intent.attachments()), ephemeral=False, stateful=False, location='none', type='container',
        status=state, status_code=102 if state == 'Stopped' else 103, created_at='', last_used_at='')


class ProfileAdapterTests(unittest.IsolatedAsyncioTestCase):
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
        runner = AsyncMock()
        runner.run.side_effect = [LxcNodeCommandResult(0, 'LoadState=loaded\nActiveState=active\nSubState=listening\nUnitFileState=enabled\nListen=/var/lib/incus/unix.socket (Stream)\n'),
            LxcNodeCommandResult(0, json.dumps(dict(type='sync', status='Success', status_code=200,
            operation='', error_code=0, error='', metadata={})))]
        runtime = IncusProfileLifecycleRuntime(runner)
        intent = intent_fixture()
        with self.assertRaises(LifecycleStateError):
            await runtime.create_profile(intent)
        runner.run.assert_not_called()
        with FakeInstallationLock().exclusive('setup') as lease:
            private = runtime.for_operation(lease, intent)
            with patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle.assert_local_socket'):
                await private.create_profile(intent)
            args = runner.run.call_args.args[0]
            payload = json.loads(args[args.index('--data') + 1])
            self.assertEqual(payload['config'], intent.markers())
            self.assertEqual(payload['devices'], intent.devices())
            self.assertIn('--wait', args)
            self.assertIsNone(runtime.lease)
        with self.assertRaises(LifecycleStateError):
            await private.init_instance(intent)

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
        if args[0] == '/usr/bin/ss':
            return LxcNodeCommandResult(0, '')
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


class RealObservationFrameTests(unittest.IsolatedAsyncioTestCase):
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
                await prepared.run(('/usr/bin/true',))
                private = prepared.for_operation(lease, intent_fixture())
                self.assertIs(private.budget, prepared.budget)
                await private.run(('/usr/bin/true',))
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
                    await runtime.run(('/usr/bin/true',))
            self.assertEqual(runner.run.call_args.args[1], 1.0)
            with self.assertRaises(LifecycleStateError):
                await runtime.run(('/usr/bin/true',))
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
            active = asyncio.create_task(private.run(('/usr/bin/true',)))
            await entered.wait()
            with self.assertRaises(LifecycleStateError):
                await other.run(('/usr/bin/true',))
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
        with FakeInstallationLock().exclusive('setup') as lease:
            runtime = IncusProfileLifecycleRuntime(runner).for_operation(lease, intent)
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

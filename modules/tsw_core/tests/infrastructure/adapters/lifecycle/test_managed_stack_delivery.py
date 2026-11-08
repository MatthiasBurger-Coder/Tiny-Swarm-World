"""Real ownership delivery path; only HTTP and Docker/Incus transports are fake."""
import copy
import json
import os
import shutil
import shlex
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlsplit

import yaml

from modules.tsw_core.tests.application.services.test_installation_profile import Runtime as IncusTransport
from modules.tsw_core.tests.domain.lifecycle.test_models import manifest_fixture
from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import admitted_fixture, intent_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.deployment.ensure_managed_stack import EnsureManagedStack
from tiny_swarm_world.application.services.installation_profile import InstallationProfileService
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.application.services.profile_setup import ScopedProfileSetupOperation, proxy_routes_from_setup_manifest
from tiny_swarm_world.domain.deployment import service_stack_contracts_for_profile
from tiny_swarm_world.domain.lifecycle.models import InstallationProfileBinding, SwarmOwnership, installation_profile_name
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent
from tiny_swarm_world.domain.lifecycle.selection import plan_selection
from tiny_swarm_world.domain.preflight import LiveConsent, default_setup_manifest
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_journal import JsonManagedStackJournal
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_state import SetupSelectionState
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
from tiny_swarm_world.infrastructure.composition_management import ManagedDeploymentWriter
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


ROOT = Path(__file__).resolve().parents[6]
CONSENT = LiveConsent(True, confirmed=True)
RAM_VALUE = 'fixture-env-only-in-memory'


class Response:
    status_code = 200
    def __init__(self, payload):
        self.payload = copy.deepcopy(payload)
    def json(self):
        return copy.deepcopy(self.payload)


class ManagementTransport:
    """Portainer HTTP fixture retains one actual returned identity across restarts."""
    def __init__(self, manifest, profile, root):
        self.manifest, self.profile, self.root = manifest, profile, root
        self.stack = None
        self.content = None
        self.writes = []
        self.events = []
        self.old_task = False
        self.completion_readonly = False
        self.endpoint_connected = True
        self.deployment_images = {}
        self.bad_task = None
        self.nodes = {'node1': 'swarm-manager'}
        self.agent_nodes = None
        self.bootstrap_exit = 0
        self.cookies = SimpleNamespace(clear=lambda: None)
    def post(self, url, **kwargs):
        if urlsplit(url).path != '/api/auth':
            raise AssertionError('Unexpected authentication transport route.')
        return Response({'jwt': 'fixture-jwt-only-in-memory'})
    def request(self, method, url, **kwargs):
        path = urlsplit(url).path
        if method in {'POST', 'PUT'}:
            self.writes.append(method)
            self.events.append('http-write')
            if self.manifest.load().manifest is not None or self.profile.load().verified_stack_ownership:
                raise AssertionError('Ownership or manifest committed before deployment proof.')
            raw = json.loads((self.root / '.tiny-swarm-world/installation/managed-stack-swagger.json').read_text())
            if raw['phase'] != 'uncertain' or raw['created_stack_id'] is not None:
                raise AssertionError('Create response identity was invented before request.')
            if method != 'POST' or self.stack is not None:
                raise AssertionError('Unexpected competing update/repeated create.')
            payload = kwargs['json']
            self.content = payload['stackFileContent']
            self.stack = {'Id': 41, 'Name': 'swagger', 'EndpointId': 7, 'Type': 1,
                          'ResourceControl': {'Id': 53, 'ResourceId': '7_swagger', 'Type': 6, 'AdministratorsOnly': True},
                          'Env': payload['env']}
            return Response(self.stack)
        if method != 'GET':
            raise AssertionError('Unexpected HTTP transport operation.')
        self.events.append('http-readback')
        if path == '/api/endpoints':
            return Response([{'Id': 7, 'Name': 'local', 'Type': 1, 'Status': 1 if self.endpoint_connected else 0}])
        if path == '/api/endpoints/7/docker/info':
            return Response({'Swarm': {'Cluster': {'ID': 'fixture-local-swarm'}}})
        if path == '/api/stacks':
            return Response([] if self.stack is None else [self.stack])
        if path == '/api/stacks/41':
            return Response(self.stack)
        if path == '/api/stacks/41/file':
            return Response({'StackFileContent': self.content})
        raise AssertionError('Unexpected HTTP read route.')


class DockerTransport:
    def __init__(self, server):
        self.server = server
        self.direct_deploys = []
        self.prepared_assets = []
        self.tasks = {}
    def deploy_stack(self, *args, **kwargs):
        self.direct_deploys.append(args)
        raise AssertionError('Portainer-owned stack reached a competing direct-Swarm writer.')
    def prepare_stack_assets(self, name):
        self.prepared_assets.append(name)
    def service(self, name):
        stack, member = name.split('_', 1)
        if stack == 'swagger' and self.server.content is not None:
            image = yaml.safe_load(self.server.content)['services'][member]['image']
        else:
            image = self.server.deployment_images[stack][member]
        return member, image if '@' in image else image + '@sha256:' + 'e' * 64
    def run_manager_shell(self, command, **kwargs):
        if command.startswith('docker info '):
            return SimpleNamespace(returncode=0, stdout='fixture-local-swarm\n')
        argv = shlex.split(command)
        if argv[:3] == ['docker', 'node', 'ls']:
            return SimpleNamespace(returncode=0, stdout='\n'.join(self.server.nodes) + '\n')
        if argv[:3] == ['docker', 'node', 'inspect']:
            rows = [{'id': node, 'hostname': self.server.nodes[node], 'state': 'ready', 'availability': 'active'}
                    for node in argv[argv.index('--') + 1:]]
            return SimpleNamespace(returncode=0, stdout='\n'.join(json.dumps(row) for row in rows) + '\n')
        if argv[:4] == ['docker', 'inspect', '--type', 'task']:
            template = argv[argv.index('--format') + 1]
            rows = []
            for identifier in argv[argv.index('--') + 1:]:
                name, node = self.tasks[identifier]
                member, image = self.service(name)
                if self.server.old_task or name == self.server.bad_task:
                    image = 'foreign/image:old'
                complete = member == 'pulsar-manager-bootstrap'
                row = {'image': image, 'state': 'complete' if complete else 'running',
                       'desired': 'shutdown' if complete else 'running'}
                if '"node"' in template:
                    row['node'] = node
                if '"exit"' in template:
                    row['exit'] = self.server.bootstrap_exit if complete else 0
                rows.append(row)
            return SimpleNamespace(returncode=0, stdout='\n'.join(json.dumps(row) for row in rows) + '\n')
        name = argv[-1]
        service, image = self.service(name)
        if command.startswith('docker service inspect '):
            template = argv[argv.index('--format') + 1]
            record = {'id': 'service-' + service, 'version': 1, 'image': image,
                      'mode': {'Global': {}} if name == 'portainer_agent' else {'Replicated': {'Replicas': 1}}}
            if '"name"' in template:
                record['name'] = name
            if '"rollout"' in template:
                record['rollout'] = 'completed'
        elif command.startswith('docker service ps '):
            self.server.events.append('tasks-old' if self.server.old_task else 'tasks-running')
            if (not self.server.completion_readonly and
                    (self.server.manifest.load().manifest is not None or self.server.profile.load().verified_stack_ownership)):
                raise AssertionError('Ownership or manifest committed before actual task observation.')
            template = argv[argv.index('--format') + 1]
            if template == '{{.ID}}':
                nodes = ((self.server.agent_nodes if self.server.agent_nodes is not None else list(self.server.nodes))
                         if name == 'portainer_agent' else ['node1'])
                ids = []
                for node in nodes:
                    identifier = 'task' + name.replace('_', '').replace('-', '') + node
                    self.tasks[identifier] = (name, node)
                    ids.append(identifier)
                return SimpleNamespace(returncode=0, stdout='\n'.join(ids) + '\n')
            record = {'id': 'task-' + service, 'image': 'foreign/image:old' if self.server.old_task else image,
                      'state': 'Running 1 second ago', 'desired_state': 'running'}
        else:
            raise AssertionError('Unexpected Docker observation transport route.')
        return SimpleNamespace(returncode=0, stdout=json.dumps(record) + '\n')


async def no_wait(_seconds):
    """Timer boundary: retain bounded attempts without a real convergence delay."""


class ManagedStackDeliveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / 'modules/tsw_core/infra', self.root / 'infra')
        self.catalog = NativeComponentCatalog(ROOT)
        self.plan = plan_selection(self.catalog.load(), ('swagger',), stack_owner='portainer',
                                   service_exposure={'swagger': 'internal'})
        self.manifests = JsonManifestRepository(self.root / '.tiny-swarm-world/installation/manifest.json')
        self.journal = JsonProfileLifecycleJournal(self.root)
        self.lock = JsonInstallationOperationLock(self.root)
        self.lifecycle = InstallationLifecycleService(self.manifests, self.catalog, operation_lock=self.lock)
        base = manifest_fixture()
        self.fresh = base.model_copy(update={'requested_services': self.plan.requested_services,
            'resolved_services': self.plan.resolved_services, 'selection_reasons': self.plan.selection_reasons,
            'service_preset': self.plan.service_preset,
            'components': tuple(component for service in self.catalog.load().services
                                if service.service_id in self.plan.resolved_services for component in service.components)})
        self.runtime = IncusTransport()
        capabilities = Mock()
        capabilities.load.return_value = admitted_fixture()
        self.profile = InstallationProfileService(capabilities, self.runtime, self.journal, self.manifests, self.lock)
        self.server = ManagementTransport(self.manifests, self.journal, self.root)
        self.docker = DockerTransport(self.server)
        self.http = PortainerHttpClient('http://fixture.invalid', 'admin', RAM_VALUE, session=self.server)
        self.transport_client = SimpleNamespace(_client=lambda: self.http,
                                                _ensure_external_overlay_networks=lambda _definition: None)
        self.compose = ComposeFileRepositoryYaml(project_paths=ProjectPaths.from_roots(self.root, ROOT / 'modules/tsw_core/infra'),
            resolved_services=self.plan.resolved_services, service_exposure=self.plan.service_exposure)
        self.compose.validate_and_snapshot(('swagger',))
        self.server.deployment_images['portainer'] = {item.name: item.image_ref for item in self.compose.get_services_of('portainer')}
        self.contract = next(item for item in service_stack_contracts_for_profile(self.plan.service_preset,
            self.plan.resolved_services) if item.stack_name == 'swagger')
        self.addCleanup(patch.stopall)
        patch('tiny_swarm_world.infrastructure.composition_management.LxcManagerShellGateway', return_value=self.docker).start()
        patch('tiny_swarm_world.application.services.deployment.managed_stack.asyncio.sleep', new=no_wait).start()
    async def operation(self, lease):
        template = intent_fixture()
        setup_manifest = default_setup_manifest(service_profile=self.plan.service_preset,
            resolved_services=self.plan.resolved_services, service_exposure=self.plan.service_exposure)
        binding = InstallationProfileBinding(profile_name=installation_profile_name(self.fresh.installation_id),
            routes=proxy_routes_from_setup_manifest(setup_manifest, '127.0.0.1'))
        profile = template.profile.model_copy(update={'installation_id': self.fresh.installation_id,
            'operation_id': lease.operation_id, 'product_source_revision': self.fresh.product.revision,
            'requested_services': self.plan.requested_services, 'resolved_services': self.plan.resolved_services,
            'service_exposure': self.plan.service_exposure,
            'stack_ownership': {name: SwarmOwnership() for name in self.plan.stack_owners}, 'profile': binding})
        intent = ManagerCreateIntent.model_validate_json(template.model_copy(update={'profile': profile,
            'initial_manifest': self.fresh, 'planned_stack_owners': self.plan.stack_owners}).model_dump_json())
        retained = self.journal.load()
        if retained is None:
            await self.profile.run(intent, consent=CONSENT, lease=lease)
        else:
            intent = retained.intent
        operation = ScopedProfileSetupOperation(self.profile, intent, lease, self.plan,
            default_setup_manifest(service_profile=self.plan.service_preset, resolved_services=self.plan.resolved_services,
                                   service_exposure=self.plan.service_exposure), CONSENT, recovery=retained is not None)
        await operation.admit_desired(self.plan)
        return operation
    def step(self, operation):
        writer = ManagedDeploymentWriter(root=self.root, profile_operation=operation, client=self.transport_client,
            runtime=self.docker, compose_repository=self.compose, backend='incus')
        return EnsureManagedStack(compose_repository=self.compose, swarm_runtime=self.docker,
            service_stack=self.contract, stack_environment={'TSW_FIXTURE_SETTING': RAM_VALUE}, apply_managed=writer.apply)
    def commit(self, operation, lease):
        state = SetupSelectionState(self.lifecycle, self.plan, self.root)
        state.operation_lease, state.profile_operation, state.fresh = lease, operation, self.fresh
        state.commit()
        return state
    async def test_actual_saved_definition_tasks_profile_callback_and_durable_manifest(self):
        with self.lock.exclusive('setup') as lease:
            operation = await self.operation(lease)
            with self.assertRaises(LifecycleStateError):
                self.commit(operation, lease)
            self.assertIsNone(self.manifests.load().manifest)
            self.assertEqual(self.journal.load().verified_stack_ownership, {})
            step = self.step(operation)
            await step.run()
            result = await step.verify()
            self.assertEqual(result.status.value, 'verified')
            self.assertIn('tasks-running', self.server.events)
            managed = JsonManagedStackJournal(self.root / '.tiny-swarm-world/installation/managed-stack-swagger.json', lease).load()
            self.assertEqual(managed.phase, 'verified')
            self.assertEqual(managed.created_stack_id, 41)
            self.assertEqual(managed.created_resource_control_id, 53)
            checkpoint = self.journal.load()
            self.assertEqual(checkpoint.verified_stack_ownership['swagger'], managed.result)
            self.assertIsNone(self.manifests.load().manifest)
            self.commit(operation, lease)
            await operation.commit_installation()
            saved = JsonManifestRepository(self.manifests.path).load().manifest
            self.assertEqual(saved.stack_ownership['swagger'], managed.result)
            self.assertEqual(saved.installation_id, self.fresh.installation_id)
            self.assertEqual(saved.service_exposure, {'swagger': 'internal'})
            self.assertTrue(self.journal.load().installation_committed)
            self.assertEqual(self.server.writes, ['POST'])
            deployed = yaml.safe_load(self.server.content)
            self.assertFalse(any(item.get('ports') for item in deployed['services'].values()))
            self.assertEqual(self.docker.direct_deploys, [])
            self.assertNotIn(RAM_VALUE, self.manifests.path.read_text())
            self.assertNotIn(RAM_VALUE, self.journal.path.read_text())
            self.assertNotIn(RAM_VALUE, managed.model_dump_json())
    async def test_old_tasks_block_ownership_and_restart_resumes_same_returned_ids(self):
        with self.lock.exclusive('setup') as lease:
            operation = await self.operation(lease)
            self.server.old_task = True
            with self.assertRaises(LifecycleStateError):
                await self.step(operation).run()
            self.assertEqual(self.server.writes, ['POST'])
            self.assertEqual(self.journal.load().verified_stack_ownership, {})
            self.assertIsNone(self.manifests.load().manifest)
            with self.assertRaises(LifecycleStateError):
                self.commit(operation, lease)
            pending = JsonManagedStackJournal(self.root / '.tiny-swarm-world/installation/managed-stack-swagger.json', lease).load()
            self.assertEqual(pending.phase, 'received')
            self.assertEqual(pending.created_stack_id, 41)
            self.assertEqual(pending.created_resource_control_id, 53)
        # New lock/lease, reconstructed profile context and a new writer: no operation object is reused.
        self.server.old_task = False
        with self.lock.exclusive('profile-recovery') as lease:
            operation = await self.operation(lease)
            step = self.step(operation)
            await step.run()
            self.assertEqual(self.server.writes, ['POST'])
            self.assertEqual(self.journal.load().verified_stack_ownership['swagger'].stack_id, 41)
            self.commit(operation, lease)
            await operation.commit_installation()
            saved = JsonManifestRepository(self.manifests.path).load().manifest
            self.assertEqual(saved.stack_ownership['swagger'].stack_id, 41)
            self.assertEqual(saved.stack_ownership['swagger'].resource_control_id, 53)
            self.assertEqual(saved.installation_id, self.fresh.installation_id)
            self.assertEqual(self.docker.direct_deploys, [])

    async def test_public_recovery_after_manifest_adoption_only_finishes_original_checkpoint(self):
        from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
        from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
        from tiny_swarm_world.domain.lifecycle.profile_lifecycle import installation_manifest_sha256
        from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
        from tiny_swarm_world.infrastructure.adapters.cli.selective_setup import run_selective_setup

        with self.lock.exclusive('setup') as lease:
            operation = await self.operation(lease)
            await self.step(operation).run()
            self.commit(operation, lease)
            checkpoint = self.journal.load()
            saved = self.manifests.load().manifest
            self.assertFalse(checkpoint.installation_committed)
            self.assertEqual(checkpoint.installation_manifest_sha256, installation_manifest_sha256(saved))
        # Simulated crash after the actual adoption write, before the original final mark.
        original = self.manifests.path.read_bytes()
        actions = list(self.runtime.calls)
        writes = list(self.server.writes)
        self.server.completion_readonly = True
        (self.root / 'modules/tsw_core/infra/config/incus-profile-capabilities.json').write_text(admitted_fixture().model_dump_json())
        intent = checkpoint.intent
        root = self.root
        class GitTransport:
            async def run(self, args):
                if '/usr/bin/git' not in args:
                    raise AssertionError('Unexpected source transport.')
                if '--show-toplevel' in args:
                    return str(root) + '\n'
                if 'ls-files' in args:
                    return 'H src/tracked.py\0'
                if '--verify' in args:
                    return intent.profile.controller_revision + '\n'
                return ''
        runtime = SimpleNamespace(for_preparation=lambda lease: GitTransport(),
                                  for_operation=self.runtime.for_operation)
        args = parse_args(['setup', 'run', '--recover', '--live', '--approve-live', '--json'])
        with patch.dict(os.environ, {'TSW_REPOSITORY_ROOT': str(self.root),
                'TSW_INFRA_ROOT': str(self.root / 'infra'), 'TSW_PORTAINER_ADMIN_PASSWORD': RAM_VALUE}), \
                patch('tiny_swarm_world.infrastructure.adapters.cli.selective_setup.composition.build_installation_lifecycle_service', return_value=self.lifecycle), \
                patch('tiny_swarm_world.infrastructure.composition._runtime.resolve_runtime_profile', return_value=SimpleNamespace(backend=ManagedLxcBackend.INCUS)), \
                patch('tiny_swarm_world.infrastructure.adapters.host.host_environment_detector.HostEnvironmentDetector.detect', return_value=SimpleNamespace(environment=HostEnvironmentKind.NATIVE_LINUX)), \
                patch('tiny_swarm_world.infrastructure.adapters.lifecycle.profile_completion.IncusProfileLifecycleRuntime', return_value=runtime), \
                patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client.LxcPortainerHttpClient', return_value=self.transport_client), \
                patch('tiny_swarm_world.infrastructure.adapters.cli.selective_setup.composition.run_setup_with_terminal_status', side_effect=AssertionError('Runtime redeployment forbidden')) as deploy, \
                patch.object(self.lifecycle, 'adopt', side_effect=AssertionError('Repeated adoption forbidden')) as adopt:
            env = copy.deepcopy(self.server.stack['Env'])
            self.server.stack['Env'].append({'name': 'FOREIGN', 'value': 'changed'})
            denied = await run_selective_setup(args, CONSENT)
            self.assertEqual(denied.status.value, 'blocked')
            self.assertFalse(self.journal.load().installation_committed)
            self.server.stack['Env'] = env
            result = await run_selective_setup(args, CONSENT)
            self.assertEqual(result.status.value, 'completed', {
                'reason': result.reason, 'message': result.message,
                'runtime_actions': self.runtime.calls, 'http_writes': self.server.writes,
                'last_readback_events': self.server.events[-12:],
            })
            self.assertEqual(result.reason, 'creation_completion_recovered')
            self.assertFalse(result.executed)
            deploy.assert_not_called()
            adopt.assert_not_called()
        self.assertTrue(self.journal.load().installation_committed)
        self.assertEqual(self.server.writes, writes)
        self.assertEqual(self.runtime.calls, actions)
        self.assertEqual(self.manifests.path.read_bytes(), original)

    async def test_completion_refuses_unknown_manifest_and_owner_history_without_mutations(self):
        from tiny_swarm_world.application.services.profile_completion import CreationCompletionOperation
        from unittest.mock import AsyncMock
        with self.lock.exclusive('setup') as lease:
            operation = await self.operation(lease)
            await self.step(operation).run()
            self.commit(operation, lease)
        with self.lock.exclusive('profile-recovery') as lease:
            plan = plan_selection(self.catalog.load(), persisted=self.manifests.load().manifest)
            plan = plan.model_copy(update={'manifest_token': self.manifests.load().token})
            verify = AsyncMock()
            completion = CreationCompletionOperation(self.profile, self.journal.load(), lease, plan, CONSENT, verify)
            original = self.manifests.path.read_bytes()
            saved = self.manifests.load().manifest
            changed = saved.model_copy(update={'checkpoint_reference': 'foreign-checkpoint'})
            self.manifests.save(changed, expected_token=self.manifests.load().token)
            with self.assertRaises(LifecycleStateError):
                await completion.admit_desired(plan)
            self.manifests.path.write_bytes(original)
            altered = plan.model_copy(update={'stack_owners': {'swagger': 'swarm'}})
            with self.assertRaises(LifecycleStateError):
                await completion.admit_desired(altered)
            self.runtime.state['uuid'] = '99999999-9999-9999-9999-999999999999'
            with self.assertRaises(LifecycleStateError):
                await completion.admit_desired(plan)
            verify.assert_not_awaited()
            self.assertFalse(self.journal.load().installation_committed)
            checkpoint = self.journal.load()
            changed_checkpoint = checkpoint.model_copy(update={
                'generation': checkpoint.generation + 1, 'installation_manifest_sha256': 'f' * 64})
            with self.journal.exclusive(lease):
                with self.assertRaises(LifecycleStateError):
                    self.journal.save(changed_checkpoint, expected=checkpoint, lease=lease)
            self.assertEqual(self.journal.load(), checkpoint)

    def selected_manifest(self, requested):
        from tiny_swarm_world.domain.lifecycle.models import migrate_manifest_v1
        plan = plan_selection(self.catalog.load(), requested or None, minimal=not requested)
        components = tuple(item for service in self.catalog.load().services
                           if service.service_id in plan.resolved_services for item in service.components)
        manifest = self.fresh.model_copy(update={'requested_services': plan.requested_services,
            'resolved_services': plan.resolved_services, 'selection_reasons': plan.selection_reasons,
            'service_preset': plan.service_preset, 'components': components})
        return plan, migrate_manifest_v1(manifest)

    async def completion_without_managed_owner(self, requested):
        from tiny_swarm_world.application.services.profile_completion import CreationCompletionOperation
        from tiny_swarm_world.infrastructure.adapters.lifecycle.completion_runtime import verify_selected_runtime
        self.plan, self.fresh = self.selected_manifest(requested)
        repository = ComposeFileRepositoryYaml(project_paths=ProjectPaths.from_roots(self.root, self.root / 'infra'),
            resolved_services=self.plan.resolved_services, service_exposure=self.plan.service_exposure, write_logs=False)
        for stack in set(self.plan.resolved_services) - {'incus'}:
            self.server.deployment_images[stack] = {item.name: item.image_ref for item in repository.get_services_of(stack)}
        with self.lock.exclusive('setup') as lease:
            operation = await self.operation(lease)
            self.commit(operation, lease)
        original = self.manifests.path.read_bytes()
        self.server.completion_readonly = True
        with self.lock.exclusive('profile-recovery') as lease:
            plan = plan_selection(self.catalog.load(), persisted=self.manifests.load().manifest)
            plan = plan.model_copy(update={'manifest_token': self.manifests.load().token})
            async def verify(manifest):
                verify_selected_runtime(self.docker, self.http, ROOT, manifest, ('swarm-manager',))
            operation = CreationCompletionOperation(self.profile, self.journal.load(), lease, plan, CONSENT, verify)
            for bad in ('portainer_portainer', 'portainer_agent'):
                self.server.bad_task = bad
                with self.subTest(bad=bad), self.assertRaises(LifecycleStateError):
                    await operation.commit_installation()
                self.assertFalse(self.journal.load().installation_committed)
            self.server.bad_task = None
            self.server.endpoint_connected = False
            with self.assertRaises(LifecycleStateError):
                await operation.commit_installation()
            self.assertFalse(self.journal.load().installation_committed)
            self.server.endpoint_connected = True
            await operation.commit_installation()
            self.assertTrue(self.journal.load().installation_committed)
        self.assertEqual(self.manifests.path.read_bytes(), original)
        self.assertEqual(self.server.writes, [])
        self.assertEqual(self.docker.direct_deploys, [])

    async def test_minimal_completion_requires_both_mandatory_tasks_and_authenticated_local_endpoint(self):
        await self.completion_without_managed_owner(())

    async def test_swarm_only_completion_requires_mandatory_gateway_without_managed_owners(self):
        await self.completion_without_managed_owner(('swagger',))

    def test_global_agent_covers_admitted_workers_and_completed_pulsar_job_is_valid(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.completion_runtime import verify_selected_runtime
        plan, manifest = self.selected_manifest(('pulsar',))
        repository = ComposeFileRepositoryYaml(project_paths=ProjectPaths.from_roots(self.root, self.root / 'infra'),
            resolved_services=plan.resolved_services, service_exposure=plan.service_exposure, write_logs=False)
        for stack in set(plan.resolved_services) - {'incus'}:
            self.server.deployment_images[stack] = {item.name: item.image_ref for item in repository.get_services_of(stack)}
        self.server.completion_readonly = True
        self.server.nodes = {'node1': 'swarm-manager', 'node2': 'swarm-worker-1'}
        self.server.agent_nodes = ['node1']
        names = ('swarm-manager', 'swarm-worker-1')
        with self.assertRaisesRegex(LifecycleStateError, 'every admitted node'):
            verify_selected_runtime(self.docker, self.http, ROOT, manifest, names)
        self.server.agent_nodes = None
        verify_selected_runtime(self.docker, self.http, ROOT, manifest, names)
        self.server.bootstrap_exit = 1
        with self.assertRaises(LifecycleStateError):
            verify_selected_runtime(self.docker, self.http, ROOT, manifest, names)
        self.assertEqual(self.server.writes, [])
        self.assertEqual(self.docker.direct_deploys, [])

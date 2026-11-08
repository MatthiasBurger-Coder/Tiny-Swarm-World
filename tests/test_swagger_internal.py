"""Internal exposure has no publication fallback and preserves lifecycle policy."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ruamel.yaml import YAML

from tests.application.services.test_lifecycle import adoption_fixture
from tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock
from tiny_swarm_world.__main__ import main
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.deployment import ServiceStackProfile, service_stack_contracts_for_profile
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.ingress import desired_https_ingress_for_profile
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.lifecycle.exposure import service_exposure_for
from tiny_swarm_world.domain.lifecycle.models import legacy_runtime_compatible
from tiny_swarm_world.domain.lifecycle.selection import plan_selection
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.domain.preflight import default_setup_manifest
from tiny_swarm_world.infrastructure import composition_artifacts, composition_deployment, composition_platform, composition_runtime
from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swagger_readiness import SCRIPT, probe_internal_swagger
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository, decode_manifest
from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_state import SetupSelectionState
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import PortRegistryYamlRepository
from tiny_swarm_world.infrastructure.adapters.repositories.swagger_exposure import internal_swagger_payload
from tiny_swarm_world.infrastructure.composition_internal_readiness import InternalSwaggerReadinessCheck

ROOT = Path(__file__).resolve().parents[1]
SELECTED = ('incus', 'portainer', 'swagger')
INTERNAL = {'swagger': 'internal'}


class SwaggerExposurePolicyTests(unittest.TestCase):
    def test_complete_selection_policy_and_published_defaults(self) -> None:
        catalog = NativeComponentCatalog(ROOT).load()
        self.assertEqual(plan_selection(catalog, ('swagger',)).service_exposure, {'swagger': 'published'})
        self.assertEqual(plan_selection(catalog, minimal=True).service_exposure, {})
        plan = plan_selection(catalog, ('swagger',), service_exposure=INTERNAL)
        self.assertEqual(plan.service_exposure, INTERNAL)
        invalid: tuple[Any, ...] = ({}, {'swagger': True}, {'swagger': None}, {'swagger': 'INTERNAL'},
                                    {'swagger': 'internal', 'nexus': 'published'})
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                service_exposure_for(SELECTED, value)
        with self.assertRaises(ValueError):
            plan_selection(catalog, minimal=True, service_exposure=INTERNAL)
        with self.assertRaises(ValueError):
            type(plan).model_validate(plan.model_dump() | {'service_exposure': {}})

    def test_canonical_ports_only_publish_actually_selected_ingress(self) -> None:
        published = default_setup_manifest(service_profile='service-access', resolved_services=SELECTED)
        internal = default_setup_manifest(service_profile='service-access', resolved_services=SELECTED, service_exposure=INTERNAL)
        self.assertEqual({port.port for port in published.required_ports}, {10001, 16080, 16081})
        self.assertEqual({port.port for port in internal.required_ports}, {10001})
        self.assertIn('Swagger/NGINX', internal.service_names)
        self.assertEqual(internal.metadata['swagger_exposure'], 'internal')
        traefik = default_setup_manifest(service_profile='service-access',
            resolved_services=(*SELECTED, 'traefik'), service_exposure=INTERNAL)
        self.assertEqual({port.port for port in traefik.required_ports}, {10001, 80, 443})
        contract = next(item for item in service_stack_contracts_for_profile('service-access', SELECTED,
            service_exposure=INTERNAL) if item.stack_name == 'swagger')
        self.assertFalse(contract.port_ids)
        self.assertFalse(contract.endpoints)
        self.assertEqual(len(contract.required_services), 4)

    def test_preflight_bridge_and_socat_use_filtered_policy(self) -> None:
        registry = PortRegistryYamlRepository().load()
        selected = composition_runtime._project_port_registry(registry, SELECTED, INTERNAL)
        self.assertFalse(any(mapping.service_id in {'swagger', 'traefik'} for mapping in selected.mappings))
        plans = composition_runtime._wsl_socat_forwarding_plans(ServiceStackProfile.SERVICE_ACCESS, SELECTED, INTERNAL)
        self.assertEqual({item.listen_port for item in plans}, {10001})
        options = composition_platform._selected_bridge_options(SELECTED, INTERNAL)
        self.assertFalse({'swagger-ui', 'openapi-aggregator', 'traefik-http', 'traefik-https'} & set(options['selected_port_ids']))
        config = composition_runtime._preflight_configuration_for_provider('service-access', None,
            host_environment=HostEnvironmentKind.NATIVE_LINUX, resolved_services=SELECTED, service_exposure=INTERNAL)
        self.assertFalse({80, 443, 16080, 16081} & {item.port for item in config.required_ports})

    def test_conditional_route_ids_do_not_enter_stack_contract_validation(self) -> None:
        registry = PortRegistryYamlRepository().load()
        desired = desired_https_ingress_for_profile(port_registry=registry,
            resolved_services=('portainer', 'traefik', 'grafana'),
            conditional_service_names=('grafana', 'prometheus'))
        self.assertEqual(desired.hostnames, ('portainer.tsw.local', 'grafana.tsw.local'))
        direct = desired_https_ingress_for_profile(port_registry=registry,
            resolved_services=('portainer', 'grafana'), conditional_service_names=('grafana',))
        self.assertFalse(direct.gateway_enabled)
        self.assertEqual({endpoint.service_name for endpoint in direct.direct_endpoints}, {'portainer'})

    def test_actual_compose_and_access_model_have_no_internal_publication(self) -> None:
        repository = ComposeFileRepositoryYaml(resolved_services=SELECTED, service_exposure=INTERNAL, write_logs=False)
        payload = YAML(typ='safe').load(repository.get_compose_of('swagger').compose_content)
        self.assertEqual(len(payload['services']), 4)
        for service in payload['services'].values():
            self.assertNotIn('ports', service)
            self.assertNotIn('traefik.', json.dumps(service).lower())
        self.assertTrue(all(not service.published_ports for service in repository.get_services_of('swagger')))
        access = repository.get_effective_access_model().to_dict()
        self.assertNotIn('16080', json.dumps(access))
        self.assertNotIn('16081', json.dumps(access))
        self.assertNotIn('swagger.tsw.local', json.dumps(access))
        dashboard = repository.render_service_access_dashboard()
        self.assertNotIn('http://localhost:16080', dashboard)
        self.assertNotIn('http://localhost:16081', dashboard)
        published = ComposeFileRepositoryYaml(resolved_services=SELECTED, write_logs=False)
        self.assertEqual({port for service in published.get_services_of('swagger') for port in service.published_ports}, {16080, 16081})

    def test_override_cannot_restore_host_network_or_traefik_publication(self) -> None:
        payload: dict[str, Any] = {'services': {'swagger-ui': {'ports': ['16080:8080'],
            'labels': {'traefik.enable': 'true', 'site': 'keep'},
            'deploy': {'labels': ['traefik.http.routers.swagger.rule=Host(`x`)', 'site=keep']}}}}
        internal_swagger_payload(payload)
        self.assertNotIn('ports', payload['services']['swagger-ui'])
        self.assertEqual(payload['services']['swagger-ui']['labels'], {'site': 'keep'})
        self.assertEqual(payload['services']['swagger-ui']['deploy']['labels'], ['site=keep'])
        host_networks: tuple[dict[str, Any], ...] = ({'services': {'swagger': {'network_mode': 'host'}}},
                        {'services': {'swagger': {'networks': ['host']}}},
                        {'services': {'swagger': {}}, 'networks': {'foreign': {'name': 'host', 'external': True}}})
        for network in host_networks:
            with self.subTest(network=network), self.assertRaises(ValueError):
                internal_swagger_payload(network)

    def test_public_deployment_builder_forwards_explicit_policy(self) -> None:
        marker = object()
        with patch.object(composition_deployment, '_lxc_backend_for_provider_request', return_value=ManagedLxcBackend.INCUS), \
                patch.object(composition_deployment.shutil, 'which', return_value='/usr/bin/incus'), \
                patch.object(composition_deployment, 'build_lxc_deployment_services', return_value=marker) as build:
            result = composition_deployment.build_deployment_services_for_provider(
                node_provider_request=Mock(), resolved_services=SELECTED, service_exposure=INTERNAL)
        self.assertIs(result, marker)
        self.assertEqual(build.call_args.kwargs['service_exposure'], INTERNAL)


    def test_public_artifact_builder_forwards_explicit_policy(self) -> None:
        marker = object()
        with patch.object(composition_artifacts, '_lxc_backend_for_provider_request', return_value=ManagedLxcBackend.INCUS), \
                patch.object(composition_artifacts, 'build_lxc_artifact_services', return_value=marker) as build:
            result = composition_artifacts.build_artifact_services_for_provider(
                node_provider_request=Mock(), resolved_services=SELECTED, service_exposure=INTERNAL)
        self.assertIs(result, marker)
        self.assertEqual(build.call_args.kwargs['resolved_services'], SELECTED)
        self.assertEqual(build.call_args.kwargs['service_exposure'], INTERNAL)


class SwaggerExposurePersistenceTests(unittest.TestCase):
    def test_verified_migration_and_addition_preserve_internal_policy_and_identity(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            manifests = JsonManifestRepository(path)
            catalog = NativeComponentCatalog(ROOT)
            original = adoption_fixture(catalog.load())
            manifests.save(original, expected_token=None)
            service = ServiceSelectionService(manifests, catalog, operation_lock=FakeInstallationLock())
            plan = service.preview(('swagger',), add=True, service_exposure=INTERNAL)
            raw, stamp = path.read_bytes(), path.stat().st_mtime_ns
            with self.assertRaisesRegex(LifecycleStateError, 'verified runtime commit'):
                service.persist(plan, approved=True)
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), (raw, stamp))
            saved = service.persist(plan, approved=True, verified_migration=True).manifest
            assert saved is not None
            self.assertEqual(saved.schema_version, 2)
            self.assertEqual(saved.effective_exposure(), INTERNAL)
            self.assertEqual(saved.installation_id, original.installation_id)
            self.assertEqual(saved.credential_references, original.credential_references)
            self.assertFalse(legacy_runtime_compatible(saved))
            self.assertEqual(decode_manifest(path.read_bytes()).effective_exposure(), INTERNAL)
            addition = service.preview(('jenkins',), add=True)
            self.assertEqual(addition.service_exposure, INTERNAL)
            added = service.persist(addition, approved=True).manifest
            assert added is not None
            self.assertEqual(added.effective_exposure(), INTERNAL)
            self.assertEqual(added.installation_id, saved.installation_id)
            before = path.read_bytes()
            self.assertEqual(service.preview().service_exposure, INTERNAL)
            self.assertEqual(path.read_bytes(), before)


class SwaggerInternalReadinessTests(unittest.IsolatedAsyncioTestCase):
    async def test_internal_http_verification_never_uses_host_client(self) -> None:
        contract = next(item for item in service_stack_contracts_for_profile('service-access', SELECTED,
            service_exposure=INTERNAL) if item.stack_name == 'swagger')
        probe = Mock(side_effect=[False, True])
        with patch('requests.Session', side_effect=AssertionError('host HTTP forbidden')):
            check = InternalSwaggerReadinessCheck(contract, probe, max_attempts=2, wait_seconds=0)
            result = await check.verify_async()
        self.assertEqual(result.status, VerificationStatus.VERIFIED)
        self.assertEqual(result.evidence['evidence_kind'], 'container_internal_http')
        self.assertEqual(probe.call_count, 2)
        await check.run()
        self.assertEqual(probe.call_count, 2)
        failed = InternalSwaggerReadinessCheck(contract, lambda: False, max_attempts=1)
        self.assertEqual((await failed.verify_async()).status, VerificationStatus.FAILED_TO_VERIFY)

    async def test_shared_profile_cannot_admit_desired_internal_even_from_published_state(self) -> None:
        plan = plan_selection(NativeComponentCatalog(ROOT).load(), ('swagger',), service_exposure=INTERNAL)
        state = SetupSelectionState(Mock(), plan, ROOT)
        with self.assertRaisesRegex(LifecycleStateError, 'private.*installation profile'):
            await state.admit_exposure()
        lock = FakeInstallationLock()
        with lock.exclusive('setup') as lease:
            operation = SimpleNamespace(lease=lease, admit_desired=AsyncMock(
                side_effect=lambda _: lease.require_active()))
            with patch.object(state, 'profile_operation', operation):
                await state.admit_exposure()
            operation.admit_desired.assert_awaited_once_with(plan)
        operation.admit_desired.reset_mock()
        with patch.object(state, 'profile_operation', operation):
            with self.assertRaises(LifecycleStateError):
                await state.admit_exposure()
        operation.admit_desired.assert_awaited_once_with(plan)

    def test_fixed_probe_binds_all_services_and_only_returns_closed_success(self) -> None:
        run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout='SWAGGER_INTERNAL_READY\n'))
        self.assertTrue(probe_internal_swagger(run))
        self.assertEqual(run.call_args.kwargs['timeout_seconds'], 30)
        self.assertTrue(run.call_args.kwargs['retry_safe'])
        self.assertIn('docker service inspect', SCRIPT)
        self.assertIn('com.docker.stack.namespace', SCRIPT)
        self.assertIn('.Endpoint.Ports', SCRIPT)
        self.assertIn('--noproxy', SCRIPT)
        for forbidden in ('16080', '16081', '--publish', 'docker run', 'iptables', '--location'):
            self.assertNotIn(forbidden, SCRIPT)
        for result in (subprocess.CompletedProcess([], 1, stdout='SWAGGER_INTERNAL_READY\n'),
                       subprocess.CompletedProcess([], 0, stdout=''),
                       subprocess.CompletedProcess([], 0, stdout='SWAGGER_INTERNAL_READY\nUNEXPECTED')):
            run.return_value = result
            self.assertFalse(probe_internal_swagger(run))

    def test_actual_shell_probe_refuses_publication_before_internal_requests(self) -> None:
        fake = r"""#!/usr/bin/python3
import json,os,sys
args=sys.argv[1:]
case=os.environ['CASE']
log=os.environ['LOG']
prior=[]
if os.path.exists(log):
 with open(log) as stream:prior=[json.loads(line) for line in stream]
after=any(call[0]=='exec' for call in prior)
with open(log,'a') as stream:stream.write(json.dumps(args)+'\n')
services={'swagger_swagger-editor','swagger_swagger-ui','swagger_swagger-api','swagger_swagger-nginx'}
identifier='a'*64
network='n'*25
if args[0]=='ps':
 print(identifier+'\n'+'b'*64 if case=='multiple' else 'b'*64 if case=='task_changed' and after else identifier)
elif args[:2]==['service','inspect'] and args[2]=='--format' and args[4] in services:
 template=args[3]
 if 'com.docker.stack.namespace' in template:print('foreign' if case=='namespace' else 'swagger')
 elif 'Ports' in template:print('[{"PublishedPort":16081}]' if case=='published' else 'null')
 elif '.Spec.TaskTemplate.Networks' in template:
  if args[4]=='swagger_swagger-ui':
   if case=='network_empty':print('')
   elif case=='network_extra':print(network+'\n'+'m'*25)
   elif case=='network_bad_id':print('bad-id')
   elif case=='network_unknown' or (case=='network_changed' and after):print('z'*25)
   else:print(network)
  else:print(network)
 elif 'range' in template:print('traefik.enable' if case=='traefik' else '')
 else:sys.exit(2)
elif args[:2]==['network','inspect'] and args[2]=='--format':
 if args[4]!=network:sys.exit(1)
 driver='host' if case=='service_host' else 'bridge' if case=='service_bridge' else 'overlay'
 scope='local' if case=='network_local' else 'swarm'
 name='foreign' if case=='network_name' else 'service_access_link'
 print(network+' '+name+' '+driver+' '+scope)
elif args[:2]==['inspect','--format'] and args[3]==identifier:
 template=args[2]
 if '.HostConfig.NetworkMode' in template:
  print('host' if case=='task_host' or (case=='task_host_after' and after) else
        'bridge' if case=='task_bridge' else 'service_access_link' if case=='task_named_mode' else
        network if case=='task_id_mode' else 'foreign' if case=='task_unknown_mode' else 'default')
 elif '.NetworkSettings.Networks' in template:
  if case=='task_empty':print('')
  elif case=='task_extra':print('service_access_link '+network+'\nbridge '+'b'*64)
  else:print('service_access_link '+('m'*25 if case=='task_wrong_network' else network))
 elif '.Id' in template:print(identifier+' swagger_swagger-nginx true')
 else:sys.exit(2)
elif args[:3]==['exec',identifier,'/usr/bin/curl']:
 assert args[3]=='--disable' and args[4:6]==['--noproxy','*']
 assert args[args.index('--max-time')+1]=='5' and args[args.index('--max-redirs')+1]=='0'
 assert args[-1] in {'http://127.0.0.1:8084/status','http://tasks.swagger-ui:8080/','http://tasks.swagger-editor:8080/'}
 assert '--location' not in args and '-L' not in args
 print('302' if case=='redirect' else '200',end='')
else:sys.exit(2)
"""
        positive = ('success', 'task_bridge', 'task_named_mode', 'task_id_mode')
        after_requests = ('redirect', 'task_changed', 'task_host_after', 'network_changed')
        negative = ('published', 'traefik', 'namespace', 'multiple', 'service_host', 'service_bridge',
                    'network_empty', 'network_extra', 'network_bad_id', 'network_unknown',
                    'network_local', 'network_name', 'task_host', 'task_unknown_mode',
                    'task_empty', 'task_extra', 'task_wrong_network', *after_requests)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / 'docker'
            docker.write_text(fake)
            docker.chmod(0o700)
            for case in (*positive, *negative):
                log = root / (case + '.jsonl')
                result = subprocess.run(['/bin/sh', '-c', SCRIPT], capture_output=True, text=True, timeout=10,
                    env={'PATH': str(root) + ':/usr/bin:/bin', 'CASE': case, 'LOG': str(log)})
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                if case in positive:
                    self.assertEqual((result.returncode, result.stdout), (0, 'SWAGGER_INTERNAL_READY\n'), case)
                    self.assertEqual({call[-1] for call in calls if call[0] == 'exec'},
                        {'http://127.0.0.1:8084/status', 'http://tasks.swagger-ui:8080/', 'http://tasks.swagger-editor:8080/'})
                    self.assertEqual({call[4] for call in calls if call[:2] == ['service', 'inspect'] and
                                      '.Spec.TaskTemplate.Networks' in call[3]},
                        {'swagger_swagger-editor', 'swagger_swagger-ui', 'swagger_swagger-api', 'swagger_swagger-nginx'})
                else:
                    self.assertNotEqual(result.returncode, 0, case)
                    self.assertNotIn('SWAGGER_INTERNAL_READY', result.stdout)
                    if case not in after_requests:
                        self.assertFalse(any(call[0] == 'exec' for call in calls), case)
                    else:
                        self.assertTrue(any(call[0] == 'exec' for call in calls), case)

    async def test_cli_internal_preview_has_policy_without_mutation_composition(self) -> None:
        with TemporaryDirectory() as directory:
            lifecycle = SimpleNamespace(manifests=JsonManifestRepository(Path(directory) / 'manifest.json'),
                                        catalog=NativeComponentCatalog(ROOT))
            with patch('tiny_swarm_world.infrastructure.adapters.cli.selection.build_installation_lifecycle_service', return_value=lifecycle), \
                    patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher.ensure_common_executable_paths') as paths, \
                    patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher.build_application_logger') as logger, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                await main(['setup', 'run', '--services', 'swagger', '--swagger-exposure', 'internal', '--preview', '--json'])
            report = json.loads(output.getvalue())
            self.assertEqual(report['plan']['service_exposure'], INTERNAL)
            self.assertEqual(set(report['plan']['resolved_services']), set(SELECTED))
            self.assertEqual(list(Path(directory).iterdir()), [])
            paths.assert_not_called()
            logger.assert_not_called()
        for argv in (['services', 'remove', '--services', 'swagger', '--swagger-exposure', 'internal', '--preview'],
                     ['services', 'update', '--services', 'swagger', '--swagger-exposure', 'internal', '--preview']):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parse_args(argv)

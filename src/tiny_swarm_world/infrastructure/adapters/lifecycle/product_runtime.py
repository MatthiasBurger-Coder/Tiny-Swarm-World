"""Fresh whole-selection runtime proof without changing images or services."""
import asyncio
import json
import re
import shlex

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.domain.update.runtime_observation import image_matches
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog


class ClassicProductRuntime:
    def __init__(self, root, shell_factory, api_factory, platform_factory, deployment_factory):
        self.root = root
        self.shell_factory = shell_factory
        self.api_factory = api_factory
        self.platform_factory = platform_factory
        self.deployment_factory = deployment_factory

    async def verify(self, manifest):
        try:
            return await self._verify(manifest)
        except OperationError:
            raise LifecycleStateError('Selected runtime or authenticated gateway observation failed; inspect access and preserve progress.') from None

    async def _verify(self, manifest):
        options = {'service_profile': manifest.service_preset, 'resolved_services': manifest.resolved_services}
        platform = self.platform_factory(**options)
        for workflow in (platform.workflows.cluster.verify, platform.workflows.verify):
            self._require_completed(await workflow.run())
        deployment = self.deployment_factory(**options)
        self._require_completed(await deployment.workflows.verify.run())
        return await asyncio.to_thread(self._inventory, manifest)

    @staticmethod
    def _require_completed(result):
        if getattr(result.status, 'value', result.status) != 'completed':
            raise LifecycleStateError('Whole-selection verification failed; preserve product checkpoint and inspect runtime.')

    def _inventory(self, manifest):
        import yaml

        shell = self.shell_factory()
        identities = {}
        selected = {item.component_id: item for item in manifest.components}
        for service in NativeComponentCatalog(self.root).load().services:
            if service.service_id not in manifest.resolved_services or service.native_asset is None:
                continue
            native = yaml.safe_load((self.root / service.native_asset).read_text())['services']
            for member, definition in sorted(native.items()):
                component = NativeComponentCatalog._component(service.service_id, definition)
                expected = selected[component.component_id].desired
                image = expected.image_repository
                if image is None:
                    raise LifecycleStateError('Selected component has no image identity.')
                image += '@' + expected.image_digest if expected.image_digest else ':' + str(expected.image_tag)
                name = service.service_id + '_' + member
                identities[component.component_id] = verify_service(shell, name, image,
                    one_shot=component.component_id == 'pulsar-manager-bootstrap')
        expected_ids = set(selected) - {'incus'}
        if set(identities) != expected_ids:
            raise LifecycleStateError('Runtime inventory does not cover every selected component.')
        api = self.api_factory()
        api._jwt_token = None
        response = api._send('GET', '/api/endpoints')
        api._ensure_success(response, 'product gateway verification')
        endpoints = response.json()
        if not isinstance(endpoints, list) or not endpoints or any(item.get('Status') != 1 for item in endpoints):
            raise LifecycleStateError('Authenticated Portainer endpoint verification failed.')
        identities['portainer.endpoints'] = ','.join(str(item['Id']) for item in sorted(endpoints, key=lambda item: item['Id']))
        return identities


def verify_service(shell, name, expected, *, one_shot=False):
    if re.fullmatch('[a-z0-9][a-z0-9_.-]*', name) is None:
        raise LifecycleStateError('Invalid selected runtime service identity.')
    template = '{"id":{{json .ID}},"version":{{json .Version.Index}},"image":{{json .Spec.TaskTemplate.ContainerSpec.Image}},"mode":{{json .Spec.Mode}},"rollout":{{if .UpdateStatus}}{{json .UpdateStatus.State}}{{else}}""{{end}}}'
    command = 'docker service inspect --format ' + shlex.quote(template) + ' -- ' + shlex.quote(name)
    before = _read_json(shell, command)
    tasks = shell.run_manager_shell('docker service ps --no-trunc --format ' + shlex.quote('{{.ID}}') + ' -- ' + shlex.quote(name), check=False)
    ids = tasks.stdout.split()
    if tasks.returncode or not ids or any(re.fullmatch('[a-z0-9]+', item) is None for item in ids):
        raise LifecycleStateError('Selected service tasks cannot be verified.')
    task_template = '{"image":{{json .Spec.ContainerSpec.Image}},"state":{{json .Status.State}},"desired":{{json .DesiredState}},"exit":{{if .Status.ContainerStatus}}{{json .Status.ContainerStatus.ExitCode}}{{else}}null{{end}}}'
    records = shell.run_manager_shell('docker inspect --type task --format ' + shlex.quote(task_template) + ' -- ' + ' '.join(ids), check=False)
    after = _read_json(shell, command)
    try:
        if records.returncode or before != after or not image_matches(before['image'], expected):
            raise ValueError
        if before.get('rollout', '') not in {'', 'completed'}:
            raise ValueError
        observed = [json.loads(line) for line in records.stdout.splitlines() if line.strip()]
        current = [item for item in observed if item['desired'] == 'running' or item['state'] == 'running']
        if one_shot:
            if current or not observed or not (observed[0]['state'] == 'complete' and observed[0]['exit'] == 0
                    and image_matches(observed[0]['image'], before['image'])):
                raise ValueError
        else:
            replicas = before['mode'].get('Replicated', {}).get('Replicas')
            if not current or (replicas is not None and len(current) != replicas):
                raise ValueError
            if any(item['state'] != 'running' or item['desired'] != 'running' or not image_matches(item['image'], before['image']) for item in current):
                raise ValueError
        return before['id']
    except (ValueError, TypeError, KeyError):
        raise LifecycleStateError('Selected service image/task convergence failed; no product success recorded.') from None


def _read_json(shell, command):
    result = shell.run_manager_shell(command, check=False)
    try:
        if result.returncode:
            raise ValueError
        return json.loads(result.stdout)
    except ValueError:
        raise LifecycleStateError('Runtime identity observation unavailable.') from None

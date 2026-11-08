"""Bounded Portainer stack ownership probes; credentials and Env stay in memory."""
import hashlib
import json
from collections.abc import Callable, Mapping

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.managed_stack import ManagedStackSnapshot, ManagedStackReceipt
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership


def fingerprint(value: object) -> str:
    return 'sha256:' + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def definition_fingerprint(definition: StackDefinition, environment: Mapping[str, str]) -> str:
    return fingerprint({'definition': definition.compose_content, 'environment': sorted(environment.items())})


def _positive(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise LifecycleStateError('Managed stack identity is invalid.')
    return value


def _environment(value: object) -> dict[str, str]:
    if not isinstance(value, list) or len(value) > 4096:
        raise LifecycleStateError('Managed stack environment unavailable.')
    result = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {'name', 'value'}:
            raise LifecycleStateError('Managed stack environment malformed.')
        name, content = item['name'], item['value']
        if not isinstance(name, str) or not name or name in result or not isinstance(content, str):
            raise LifecycleStateError('Managed stack environment ambiguous.')
        result[name] = content
    return result


class GuardedPortainerStackApi:
    def __init__(self, client, swarm_identity: Callable[[], str]):
        self.client = client
        self.swarm_identity = swarm_identity

    def _get(self, path):
        response = self.client._send('GET', path)
        self.client._ensure_success(response, 'Inspect managed stack')
        try:
            value = response.json()
            if len(json.dumps(value).encode()) > 2 * 1024 * 1024:
                raise ValueError
            return value
        except (TypeError, ValueError):
            raise LifecycleStateError('Managed stack response unreadable or oversized.') from None

    def local_endpoint(self) -> int:
        self.client._jwt_token = None
        endpoints = self._get('/api/endpoints')
        if not isinstance(endpoints, list) or any(not isinstance(item, dict) for item in endpoints):
            raise LifecycleStateError('Managed endpoint inventory unavailable.')
        selected = [item for item in endpoints if item.get('Name') == 'local']
        if (len(selected) != 1 or type(selected[0].get('Status')) is not int or selected[0].get('Status') != 1
                or type(selected[0].get('Type')) is not int or selected[0].get('Type') not in {1, 2}):
            raise LifecycleStateError('Unique connected local Docker endpoint required.')
        identifier = _positive(selected[0].get('Id'))
        info = self._get(f'/api/endpoints/{identifier}/docker/info')
        try:
            actual = info['Swarm']['Cluster']['ID']
            expected = self.swarm_identity()
            if not isinstance(expected, str) or not expected or actual != expected:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise LifecycleStateError('Portainer endpoint differs from the actual local Swarm.') from None
        return identifier

    def _named(self, name):
        stacks = self._get('/api/stacks')
        if not isinstance(stacks, list) or any(not isinstance(item, dict) for item in stacks):
            raise LifecycleStateError('Managed stack inventory unavailable.')
        return [item for item in stacks if item.get('Name') == name]

    def require_absent(self, name: str, endpoint: int) -> None:
        if self.local_endpoint() != endpoint or self._named(name):
            raise LifecycleStateError('Same-name stack exists or endpoint changed; adoption is forbidden.')

    def inspect(self, name: str, endpoint: int, stack_id: int) -> ManagedStackSnapshot:
        if self.local_endpoint() != endpoint:
            raise LifecycleStateError('Managed stack endpoint changed.')
        named = self._named(name)
        if len(named) != 1 or named[0].get('Id') != stack_id:
            raise LifecycleStateError('Managed stack identity is ambiguous or foreign.')
        detail = self._get(f'/api/stacks/{stack_id}')
        if (not isinstance(detail, dict) or detail.get('Id') != stack_id or detail.get('Name') != name
                or _positive(detail.get('EndpointId')) != endpoint
                or type(detail.get('Type')) is not int or detail.get('Type') != 1
                or any(named[0].get(key) != detail.get(key) for key in ('Id', 'Name', 'EndpointId', 'Type', 'ResourceControl'))):
            raise LifecycleStateError('Managed stack detail changed or belongs to another endpoint.')
        control = detail.get('ResourceControl')
        if (not isinstance(control, dict) or type(control.get('Type')) is not int or control.get('Type') != 6
                or not isinstance(control.get('ResourceId'), str) or not control['ResourceId']):
            raise LifecycleStateError('Managed stack ResourceControl ownership unavailable.')
        resource_id = _positive(control.get('Id'))
        content = self._get(f'/api/stacks/{stack_id}/file')
        if not isinstance(content, dict) or not isinstance(content.get('StackFileContent'), str) or not content['StackFileContent'].strip():
            raise LifecycleStateError('Managed stack saved definition unavailable.')
        environment = _environment(detail.get('Env'))
        definition = StackDefinition(name=name, compose_content=content['StackFileContent'])
        # Read again after the definition to reject concurrent saved-state changes.
        after = self._get(f'/api/stacks/{stack_id}')
        after_file = self._get(f'/api/stacks/{stack_id}/file')
        if after != detail or after_file != content:
            raise LifecycleStateError('Managed stack changed during ownership inspection.')
        ownership = PortainerOwnership(owner='portainer', endpoint_id=endpoint, stack_id=_positive(stack_id),
            resource_control_id=resource_id,
            ownership_fingerprint=fingerprint({key: detail[key] for key in ('Id', 'Name', 'EndpointId', 'Type', 'ResourceControl')}),
            definition_fingerprint=definition_fingerprint(definition, environment))
        return ManagedStackSnapshot(ownership, definition, environment)

    def create(self, definition: StackDefinition, endpoint: int, environment: Mapping[str, str]) -> ManagedStackReceipt:
        self.require_absent(definition.name, endpoint)
        swarm = self.swarm_identity()
        response = self.client._send('POST', f'/api/stacks/create/swarm/string?endpointId={endpoint}',
            timeout=self.client.stack_request_timeout_seconds,
            json={'name': definition.name, 'SwarmID': swarm, 'stackFileContent': definition.compose_content,
                  'env': [{'name': key, 'value': value} for key, value in sorted(environment.items())], 'fromAppTemplate': False})
        self.client._ensure_success(response, 'Create managed stack')
        try:
            payload = response.json()
            if not isinstance(payload, dict) or payload.get('Name') != definition.name or payload.get('EndpointId') != endpoint:
                raise ValueError
            control = payload.get('ResourceControl')
            if (not isinstance(control, dict) or type(control.get('Type')) is not int or control.get('Type') != 6
                    or not isinstance(control.get('ResourceId'), str) or not control['ResourceId']
                    or type(payload.get('Type')) is not int or payload.get('Type') != 1):
                raise ValueError
            return ManagedStackReceipt(_positive(payload.get('Id')), _positive(control.get('Id')),
                fingerprint({key: payload[key] for key in ('Id', 'Name', 'EndpointId', 'Type', 'ResourceControl')}))
        except (ValueError, TypeError):
            raise LifecycleStateError('Managed create receipt unreadable; retain uncertain intent.') from None

    def update(self, expected: ManagedStackSnapshot, definition: StackDefinition) -> None:
        owner = expected.ownership
        if definition.name != expected.definition.name:
            raise LifecycleStateError('Managed stack target name differs.')
        current = self.inspect(definition.name, owner.endpoint_id, owner.stack_id)
        if current != expected:
            raise LifecycleStateError('Managed stack CAS rejected changed definition/Env/ownership.')
        response = self.client._send('PUT', f'/api/stacks/{owner.stack_id}?endpointId={owner.endpoint_id}',
            timeout=self.client.stack_request_timeout_seconds,
            json={'stackFileContent': definition.compose_content,
                  'env': [{'name': key, 'value': value} for key, value in sorted(expected.environment.items())],
                  'prune': False, 'pullImage': False})
        self.client._ensure_success(response, 'Update managed stack')

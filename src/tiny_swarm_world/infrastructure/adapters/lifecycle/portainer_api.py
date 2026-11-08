"""Strict authenticated inventory and an existing-stack update through the gateway."""
import hashlib
import json

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class PortainerUpgradeApi:
    def __init__(self, client, *, managed_stacks, managed_ownership=None):
        self.client = client
        self.managed_stacks = managed_stacks
        self.managed_ownership = dict(managed_ownership or {})
        self.swarm_id = None
        self.proof_stack = None

    def get(self, path):
        response = self.client._send('GET', path)
        self.client._ensure_success(response, 'Portainer lifecycle inspection')
        return response.json()

    def inventory(self):
        # Force authentication with the existing credentials rather than a cached JWT.
        self.client._jwt_token = None
        version = self.get('/api/system/status')['Version']
        endpoints = self.get('/api/endpoints')
        stacks = self.get('/api/stacks')
        if not isinstance(endpoints, list) or not endpoints or not isinstance(stacks, list) or not stacks:
            raise LifecycleStateError('Connected endpoints and an existing managed stack are required for gateway proof.')
        if not any(item.get('Type') == 1 for item in stacks):
            raise LifecycleStateError('Existing managed Swarm stack required before mutation.')
        endpoint_ids = set()
        local_endpoints = set()
        for endpoint in endpoints:
            identifier = endpoint['Id']
            if type(identifier) is not int or endpoint['Status'] != 1:
                raise LifecycleStateError('Portainer endpoint disconnected or invalid.')
            info = self.get(f'/api/endpoints/{identifier}/docker/info')
            if not info['Swarm']['Cluster']['ID']:
                raise LifecycleStateError('Portainer endpoint has no Swarm identity.')
            endpoint_ids.add(identifier)
            if info['Swarm']['Cluster']['ID'] == self.swarm_id:
                local_endpoints.add(identifier)
        for stack in stacks:
            if stack['EndpointId'] not in endpoint_ids or type(stack['Id']) is not int:
                raise LifecycleStateError('Portainer stack endpoint ownership is ambiguous.')
        candidates = [item for item in stacks if item.get('Type') == 1 and item['EndpointId'] in local_endpoints
                      and item['Name'] in self.managed_stacks]
        if not candidates:
            raise LifecycleStateError('No installed managed stack belongs to the local Swarm; proof blocked.')
        from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
        from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi

        verified = []
        guard = GuardedPortainerStackApi(self.client, lambda: self.swarm_id)
        for item in candidates:
            owner = self.managed_ownership.get(item['Name'])
            if not isinstance(owner, PortainerOwnership):
                continue
            observed = guard.inspect(item['Name'], owner.endpoint_id, owner.stack_id)
            if observed.ownership != owner:
                raise LifecycleStateError('Gateway proof ownership differs from persisted installation identity.')
            verified.append(item)
        if not verified:
            raise LifecycleStateError('No verified Portainer-owned optional stack is installed; explicit creation is required.')
        self.proof_stack = min(verified, key=lambda item: item['Id'])
        endpoint_state = tuple(sorted(fingerprint({key: item.get(key) for key in ('Id', 'Name', 'URL', 'Type')}) for item in endpoints))
        ownership = tuple(sorted(fingerprint({key: item.get(key) for key in ('Id', 'Name', 'EndpointId', 'Type', 'ResourceControl')}) for item in stacks))
        return version, endpoint_state, ownership

    def proof_definition(self):
        stack = self.proof_stack
        if stack is None:
            raise LifecycleStateError('Managed Swarm proof stack was not admitted.')
        from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi

        owner = self.managed_ownership.get(stack['Name'])
        if owner is None:
            raise LifecycleStateError('Managed proof requires persisted ownership.')
        observed = GuardedPortainerStackApi(self.client, lambda: self.swarm_id).inspect(stack['Name'], owner.endpoint_id, owner.stack_id)
        if observed.ownership != owner:
            raise LifecycleStateError('Managed proof definition/Env or ownership changed.')
        return stack, observed.definition.compose_content, [
            {'name': key, 'value': value} for key, value in sorted(observed.environment.items())]

    def prove_update(self):
        stack, content, environment = self.proof_definition()
        from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi

        owner = self.managed_ownership[stack['Name']]
        guard = GuardedPortainerStackApi(self.client, lambda: self.swarm_id)
        snapshot = guard.inspect(stack['Name'], owner.endpoint_id, owner.stack_id)
        if snapshot.ownership != owner:
            raise LifecycleStateError('Managed proof changed immediately before request.')
        guard.update(snapshot, snapshot.definition)
        after = guard.inspect(stack['Name'], owner.endpoint_id, owner.stack_id)
        if after.ownership != owner:
            raise LifecycleStateError('Managed proof saved definition/Env changed after request.')
        return stack['Name']

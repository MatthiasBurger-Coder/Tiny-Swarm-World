"""Authenticated ownership and saved Env CAS prevent same-name adoption."""
import copy
import unittest

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi, definition_fingerprint


class Response:
    status_code = 200
    def __init__(self, value):
        self.value = copy.deepcopy(value)
    def json(self):
        return copy.deepcopy(self.value)


class Client:
    stack_request_timeout_seconds = 120
    def __init__(self):
        self.endpoint = {'Id': 1, 'Name': 'local', 'Type': 1, 'Status': 1}
        self.detail = {'Id': 2, 'Name': 'swagger', 'EndpointId': 1, 'Type': 1,
            'ResourceControl': {'Id': 3, 'ResourceId': '1_swagger', 'Type': 6, 'AdministratorsOnly': True},
            'Env': [{'name': 'SECRET', 'value': 'keep-private'}]}
        self.content = 'services: {ui: {image: image:old}}'
        self.stacks = [self.detail]
        self.writes = []
    def _send(self, method, path, **kwargs):
        if method in {'PUT', 'POST'}:
            self.writes.append((method, path, kwargs))
            return Response(self.detail)
        if path == '/api/endpoints':
            return Response([self.endpoint])
        if path.endswith('/docker/info'):
            return Response({'Swarm': {'Cluster': {'ID': 'local-swarm'}}})
        if path == '/api/stacks':
            return Response(self.stacks)
        if path.endswith('/file'):
            return Response({'StackFileContent': self.content})
        return Response(self.detail)
    def _ensure_success(self, response, action):
        pass


class ManagedApiTests(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.api = GuardedPortainerStackApi(self.client, lambda: 'local-swarm')
        self.target = StackDefinition(name='swagger', compose_content='services: {ui: {image: image:new}}')
    def test_snapshot_binds_full_definition_and_environment(self):
        snapshot = self.api.inspect('swagger', 1, 2)
        self.assertEqual(snapshot.ownership.definition_fingerprint, definition_fingerprint(snapshot.definition, snapshot.environment))
        self.client.detail['Env'][0]['value'] = 'changed'
        self.assertNotEqual(snapshot.ownership, self.api.inspect('swagger', 1, 2).ownership)
        self.assertNotIn('keep-private', repr(snapshot))
    def test_put_preserves_env_and_disables_pruning(self):
        snapshot = self.api.inspect('swagger', 1, 2)
        self.api.update(snapshot, self.target)
        payload = self.client.writes[0][2]['json']
        self.assertFalse(payload['prune'])
        self.assertFalse(payload['pullImage'])
        self.assertEqual(payload['env'], [{'name': 'SECRET', 'value': 'keep-private'}])
    def test_env_and_saved_file_changes_fail_cas_before_put(self):
        snapshot = self.api.inspect('swagger', 1, 2)
        for change in ('env', 'definition', 'resource'):
            with self.subTest(change=change):
                client = Client()
                api = GuardedPortainerStackApi(client, lambda: 'local-swarm')
                if change == 'env':
                    client.detail['Env'][0]['value'] = 'foreign'
                elif change == 'definition':
                    client.content = 'foreign'
                else:
                    client.detail['ResourceControl']['Id'] = 4
                with self.assertRaises(LifecycleStateError):
                    api.update(snapshot, self.target)
                self.assertEqual(client.writes, [])
    def test_same_name_other_endpoint_or_id_is_rejected(self):
        for field in ('Id', 'EndpointId', 'Type'):
            with self.subTest(field=field):
                self.client = Client()
                self.api = GuardedPortainerStackApi(self.client, lambda: 'local-swarm')
                self.client.detail[field] = 99
                with self.assertRaises(LifecycleStateError):
                    self.api.inspect('swagger', 1, 2)
    def test_duplicate_stack_names_are_not_disambiguated_by_first_match(self):
        self.client.stacks.append({**self.client.detail, 'Id': 7})
        with self.assertRaises(LifecycleStateError):
            self.api.inspect('swagger', 1, 2)
    def test_create_refuses_same_name_without_post(self):
        with self.assertRaises(LifecycleStateError):
            self.api.create(self.target, 1, {})
        self.assertEqual(self.client.writes, [])
    def test_endpoint_must_be_unique_connected_and_actual_local_swarm(self):
        self.client.endpoint['Status'] = 2
        with self.assertRaises(LifecycleStateError):
            self.api.local_endpoint()
        self.client.endpoint['Status'] = 1
        api = GuardedPortainerStackApi(self.client, lambda: 'different-swarm')
        with self.assertRaises(LifecycleStateError):
            api.local_endpoint()
    def test_missing_resource_control_blocks(self):
        del self.client.detail['ResourceControl']
        with self.assertRaises(LifecycleStateError):
            self.api.inspect('swagger', 1, 2)
    def test_duplicate_env_is_not_silently_overwritten(self):
        self.client.detail['Env'].append({'name': 'SECRET', 'value': 'foreign'})
        with self.assertRaises(LifecycleStateError):
            self.api.inspect('swagger', 1, 2)

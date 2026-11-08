"""Qualification disposal preserves unowned resources and uncertain receipts."""
from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import Mock, patch

from tools.linux.qualification import owned_case_disposal as disposal
from tools.linux.qualification import native_lxd_maintenance as native

INSTALLATION = '11111111-1111-4111-8111-111111111111'
OPERATION = 'a' * 32
PROFILE = 'tsw-manager-' + 'b' * 24


def case() -> tuple[disposal.DisposalIntent, dict[str, Any]]:
    markers = {disposal.INSTALLATION: INSTALLATION, disposal.OPERATION: OPERATION}
    profile = {'name': PROFILE, 'project': 'default', 'description': 'Tiny Swarm World installation profile',
        'config': markers, 'devices': {}, 'used_by': ['/1.0/instances/swarm-manager?project=default']}
    rows: dict[str, Any] = {}
    nodes = []
    for index, name in enumerate(disposal.NAMES):
        uuid = f'00000000-0000-4000-8000-{index + 1:012d}'
        row = {'name': name, 'type': 'container', 'ephemeral': False, 'stateful': False,
            'status': 'Running', 'status_code': 103, 'created_at': '2026-11-08T00:00:00Z',
            'config': markers | {'volatile.uuid': uuid, 'limits.memory': '1GiB'},
            'expanded_config': markers | {'volatile.uuid': uuid, 'limits.memory': '1GiB'},
            'profiles': ['docker-swarm', PROFILE] if name == 'swarm-manager' else ['docker-swarm'],
            'devices': {'root': {'type': 'disk', 'path': '/', 'pool': 'default'}},
            'expanded_devices': {'root': {'type': 'disk', 'path': '/', 'pool': 'default'}}}
        rows[name] = row
        nodes.append(disposal.OwnedNode(name, uuid, disposal.specification(row)))
    intent = disposal.DisposalIntent(INSTALLATION, OPERATION, 'c' * 64, PROFILE,
        disposal.profile_identity(profile), 'default', tuple(nodes))
    volumes = [{'name': name, 'type': 'container', 'owner_project': 'default', 'content_type': 'filesystem',
        'used_by': [{'kind': 'instances', 'name': name, 'project': 'default'}]} for name in disposal.NAMES]
    return intent, {'instances': rows, 'profile': profile, 'volumes': volumes, 'snapshots': [], 'checkpoint_sha256': 'c' * 64}


class Port:
    def __init__(self, graph: dict[str, Any]):
        self.graph = copy.deepcopy(graph)
        self.calls: list[tuple[str, str]] = []
        self.intents: set[tuple[str, str]] = set()
        self.fail: str | None = None

    def inspect(self) -> dict[str, Any]:
        return copy.deepcopy(self.graph)

    def pending(self, action: str, name: str) -> bool:
        return (action, name) in self.intents

    def event(self, action: str, name: str) -> None:
        self.intents.add((action, name))

    def stop(self, node: disposal.OwnedNode) -> None:
        assert ('stop', node.name) in self.intents
        self.calls.append(('stop', node.name))
        if self.fail == 'stop-before':
            raise native.MaintenanceError('STOP_UNKNOWN')
        self.graph['instances'][node.name].update(status='Stopped', status_code=102)
        if self.fail == 'stop-after':
            raise native.MaintenanceError('STOP_UNKNOWN')

    def delete(self, node: disposal.OwnedNode) -> None:
        assert ('delete', node.name) in self.intents
        self.calls.append(('delete', node.name))
        if self.fail == 'delete-before':
            raise native.MaintenanceError('DELETE_UNKNOWN')
        del self.graph['instances'][node.name]
        self.graph['volumes'] = [row for row in self.graph['volumes'] if row['name'] != node.name]
        if node.name == 'swarm-manager':
            self.graph['profile']['used_by'] = []
        if self.fail == 'delete-after':
            raise native.MaintenanceError('DELETE_UNKNOWN')

    def delete_profile(self, intent: disposal.DisposalIntent) -> None:
        assert ('profile-delete', intent.profile_name) in self.intents
        self.calls.append(('profile-delete', intent.profile_name))
        self.graph['profile'] = None


class OwnedCaseDisposalTests(unittest.TestCase):
    def test_real_transaction_stops_workers_before_manager_then_deletes_exact_profile(self) -> None:
        intent, graph = case()
        port = Port(graph)
        disposal.dispose(port, intent)
        self.assertEqual(port.calls, [('stop', name) for name in disposal.NAMES] + [('delete', name) for name in disposal.NAMES]
            + [('profile-delete', PROFILE)])
        self.assertFalse(port.graph['instances'])
        self.assertFalse(port.graph['volumes'])
        self.assertIsNone(port.graph['profile'])

    def test_incusemitted_default_project_profile_consumer_and_explicit_spelling_both_dispose(self) -> None:
        for consumer in ('/1.0/instances/swarm-manager', '/1.0/instances/swarm-manager?project=default'):
            intent, graph = case()
            graph['profile']['used_by'] = [consumer]
            port = Port(graph)
            disposal.dispose(port, intent)
            self.assertFalse(port.graph['instances'])
            self.assertIsNone(port.graph['profile'])

    def test_other_project_or_query_aliases_and_duplicate_consumers_are_never_default_scope(self) -> None:
        path = '/1.0/instances/swarm-manager'
        invalid: tuple[object, ...] = ([path + '?project=issue447'], [path + '?project='],
            [path + '?target=none'], [path + '?project=default&target=none'],
            [path + '?project=default&project=issue447'], [path + '?project=%64efault'],
            [path + '#ignored'], [path + '?'], [path + '\n'], ['https://host' + path],
            ['/1.0/instances/foreign'], [path, path], [path, path + '?project=default'], None, False, {})
        for consumers in invalid:
            with self.subTest(consumers=consumers):
                intent, graph = case()
                graph['profile']['used_by'] = consumers
                port = Port(graph)
                with self.assertRaisesRegex(native.MaintenanceError, 'CASE_PROFILE_FOREIGN_CONSUMER'):
                    disposal.dispose(port, intent)
                self.assertFalse(port.calls)

    def test_replacement_uuid_marker_and_current_spec_never_stopped_or_deleted(self) -> None:
        mutations: tuple[dict[str, str], ...] = ({'volatile.uuid': '99999999-9999-4999-8999-999999999999'},
            {disposal.INSTALLATION: '22222222-2222-4222-8222-222222222222'},
            {disposal.OPERATION: 'd' * 32}, {'limits.memory': '8GiB'})
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                intent, graph = case()
                graph['instances'][disposal.NAMES[0]]['config'].update(mutation)
                port = Port(graph)
                with self.assertRaises(native.MaintenanceError):
                    disposal.dispose(port, intent)
                self.assertEqual([], port.calls)

    def test_foreign_root_consumer_snapshot_external_disk_and_profile_consumer_block_before_effect(self) -> None:
        for change in ('root-consumer', 'snapshot', 'disk', 'profile-consumer', 'foreign-instance', 'checkpoint'):
            with self.subTest(change=change):
                intent, graph = case()
                if change == 'root-consumer':
                    graph['volumes'][0]['used_by'].append({'kind': 'instances', 'name': 'foreign', 'project': 'issue447'})
                elif change == 'snapshot':
                    graph['snapshots'].append({'parent': 'swarm-manager', 'name': 'data'})
                elif change == 'disk':
                    graph['instances'][disposal.NAMES[0]]['expanded_devices']['data'] = {'type': 'disk', 'path': '/data', 'source': '/srv'}
                elif change == 'profile-consumer':
                    graph['profile']['used_by'].append('/1.0/instances/foreign?project=issue447')
                elif change == 'foreign-instance':
                    graph['instances']['foreign'] = copy.deepcopy(graph['instances']['swarm-manager'])
                else:
                    graph['checkpoint_sha256'] = 'e' * 64
                port = Port(graph)
                with self.assertRaises(native.MaintenanceError):
                    disposal.dispose(port, intent)
                self.assertEqual([], port.calls)

    def test_uncertain_stop_that_did_not_happen_is_not_replayed(self) -> None:
        intent, graph = case()
        port = Port(graph)
        port.fail = 'stop-before'
        with self.assertRaisesRegex(native.MaintenanceError, 'STOP_UNKNOWN'):
            disposal.dispose(port, intent)
        port.fail = None
        with self.assertRaisesRegex(native.MaintenanceError, 'CASE_STOP_OUTCOME_UNCERTAIN'):
            disposal.dispose(port, intent)
        self.assertEqual([('stop', disposal.NAMES[0])], port.calls)

    def test_uncertain_stop_observed_stopped_continues_without_second_stop(self) -> None:
        intent, graph = case()
        port = Port(graph)
        port.fail = 'stop-after'
        with self.assertRaises(native.MaintenanceError):
            disposal.dispose(port, intent)
        port.fail = None
        disposal.dispose(port, intent)
        self.assertEqual(1, port.calls.count(('stop', disposal.NAMES[0])))

    def test_uncertain_delete_is_only_observed_never_replayed(self) -> None:
        for failure in ('delete-before', 'delete-after'):
            intent, graph = case()
            port = Port(graph)
            port.fail = failure
            with self.assertRaises(native.MaintenanceError):
                disposal.dispose(port, intent)
            port.fail = None
            if failure == 'delete-before':
                with self.assertRaisesRegex(native.MaintenanceError, 'CASE_DELETE_OUTCOME_UNCERTAIN'):
                    disposal.dispose(port, intent)
            else:
                disposal.dispose(port, intent)
            self.assertEqual(1, port.calls.count(('delete', disposal.NAMES[0])))

    def test_current_stopped_state_does_not_modify_specification_identity(self) -> None:
        intent, graph = case()
        for row in graph['instances'].values():
            row.update(status='Stopped', status_code=102)
        port = Port(graph)
        disposal.dispose(port, intent)
        self.assertFalse(any(action == 'stop' for action, _name in port.calls))

    def test_uuid_drift_after_an_own_stop_blocks_every_delete(self) -> None:
        intent, graph = case()
        port = Port(graph)
        original_stop = port.stop
        def stop(node: disposal.OwnedNode) -> None:
            original_stop(node)
            port.graph['instances'][node.name]['config']['volatile.uuid'] = '99999999-9999-4999-8999-999999999999'
        with patch.object(port, 'stop', side_effect=stop):
            with self.assertRaisesRegex(native.MaintenanceError, 'CASE_INSTANCE_IDENTITY_DRIFT'):
                disposal.dispose(port, intent)
        self.assertEqual(port.calls, [('stop', disposal.NAMES[0])])

    def test_duplicate_unknown_nodes_and_noncanonical_ids_are_denied(self) -> None:
        intent, _graph = case()
        for nodes in (intent.nodes + (intent.nodes[0],), (replace(intent.nodes[0], name='foreign'),),
                      (replace(intent.nodes[0], uuid='not-a-uuid'),)):
            with self.assertRaises(native.MaintenanceError):
                replace(intent, nodes=nodes)
        with self.assertRaises(native.MaintenanceError):
            replace(intent, installation_id='a' * 32)

    def test_real_adapter_has_fixed_noforce_default_project_commands_and_durable_intent(self) -> None:
        intent, _graph = case()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.chmod(0o700)
            with patch.object(native, 'private_directory') as storage:
                journal = native.Journal(root)
            storage.assert_called_once_with(root)
            suite = Mock()
            port = disposal.IncusDisposalPort(suite, intent, journal)
            node = intent.nodes[0]
            port.event('stop', node.name)
            self.assertTrue(port.pending('stop', node.name))
            port.stop(node)
            port.delete(node)
            port.delete_profile(intent)
            self.assertEqual(suite.incus_effect.call_args_list[0].args, (['--project', 'default', 'stop', node.name, '--timeout', '60'], 75))
            self.assertEqual(suite.incus_effect.call_args_list[1].args, (['--project', 'default', 'delete', node.name], 120))
            self.assertEqual(suite.incus_effect.call_args_list[2].args, (['--project', 'default', 'profile', 'delete', PROFILE], 30))
            for item in suite.incus_effect.call_args_list:
                self.assertNotIn('--force', item.args[0])
            receipt = next(root.glob('case-stop-*.json'))
            self.assertEqual(0o600, receipt.stat().st_mode & 0o777)
            self.assertEqual(native.inventory.strict_json(native.read_private(receipt))['name'], node.name)


if __name__ == '__main__':
    unittest.main()

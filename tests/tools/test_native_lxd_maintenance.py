"""Preserving maintenance failures must recover; no hosts or real commands."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
import multiprocessing
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from typing import Any

from tools.linux.qualification import native_lxd_maintenance as maintenance


def baseline(socket: str = 'inactive') -> dict[str, Any]:
    return {'nodes': {name: {'status': 'Running', 'identity': 'a' * 64} for name in maintenance.NODES},
            'socket': socket, 'preserve': {'config': 'digest', 'incus': ['issue447', 'snapshots']},
            'binding': {'installed': 'pinned', 'incus_unit': 'unchanged'}}


class FakePort:
    def __init__(self, state: dict[str, Any]):
        self.state = copy.deepcopy(state)
        self.daemon = 'active'
        self.calls: list[tuple[str, str]] = []
        self.failure: str | None = None
        self.start_failure = False
        self.fixture_drift = False
        self.reactivate = False
        self.reserve = False
        self.late_drift: str | None = None
        self.node_drift: tuple[str, str] | None = None
        self.snapshot_calls = 0

    def begin_recovery(self) -> None:
        self.reserve = True

    def snapshot(self) -> dict[str, Any]:
        self.snapshot_calls += 1
        if self.snapshot_calls == 2 and self.late_drift is not None:
            self.state['preserve'][self.late_drift] = ['foreign']
        if self.failure == 'prestate':
            return {**self.state, 'preserve': {'drift': True}}
        return copy.deepcopy(self.state)

    def check_binding(self, expected: dict[str, Any], *, active: bool) -> None:
        maintenance.require(self.daemon == ('active' if active else 'inactive'), 'DAEMON_STATE_DRIFT')
        maintenance.require(self.state['binding'] == expected['binding'], 'INSTALLED_BINDING_DRIFT')

    def node(self, name: str) -> dict[str, str]:
        if self.node_drift is not None and self.node_drift[0] == name and not self.reserve:
            self.state['nodes'][name]['status'] = self.node_drift[1]
            self.node_drift = None
        return copy.deepcopy(self.state['nodes'][name])

    def unit(self, name: str) -> str:
        return self.daemon if name == maintenance.DAEMON else str(self.state['socket'])

    def stop_node(self, name: str) -> None:
        self.calls.append(('stop-node', name))
        if self.failure == 'stop-before':
            raise maintenance.MaintenanceError('STOP_REFUSED')
        self.state['nodes'][name]['status'] = 'Stopped'
        if self.failure == 'stop-after':
            raise maintenance.MaintenanceError('STOP_UNCERTAIN')

    def start_node(self, name: str) -> None:
        self.calls.append(('start-node', name))
        if self.start_failure:
            raise maintenance.MaintenanceError('START_FAILED')
        self.state['nodes'][name]['status'] = 'Running'

    def stop_socket(self) -> None:
        self.calls.append(('stop-socket', ''))
        self.state['socket'] = 'inactive'
        if self.failure == 'socket':
            raise maintenance.MaintenanceError('SOCKET_UNCERTAIN')

    def shutdown(self) -> None:
        self.calls.append(('shutdown', ''))
        if self.failure == 'shutdown-before':
            raise maintenance.MaintenanceError('SHUTDOWN_UNCERTAIN')
        self.daemon = 'inactive'
        if self.failure == 'shutdown-after':
            raise maintenance.MaintenanceError('SHUTDOWN_UNCERTAIN')

    def wait_inactive(self) -> None:
        maintenance.require(self.daemon == 'inactive', 'SHUTDOWN_UNCERTAIN')

    def start_daemon(self) -> None:
        self.calls.append(('start-daemon', ''))
        maintenance.require(self.reserve, 'RECOVERY_RESERVE_NOT_STARTED')
        if self.start_failure:
            raise maintenance.MaintenanceError('START_FAILED')
        self.daemon = 'active'

    def restore_socket(self, state: str) -> None:
        self.calls.append(('restore-socket', state))
        self.state['socket'] = state

    def run_fixture(self) -> None:
        self.calls.append(('fixture', ''))
        if self.fixture_drift:
            self.state['preserve']['incus'] = ['CHANGED']
        if self.reactivate:
            self.daemon = 'active'
        if self.failure == 'fixture':
            raise maintenance.MaintenanceError('FIXTURE_FAILED')
        if self.failure == 'interrupt':
            raise KeyboardInterrupt


class Events:
    def __init__(self, port: FakePort):
        self.events: list[tuple[str, str]] = []
        self.port = port
        self.fail = False

    def stopped_nodes(self) -> set[str]:
        return {node for action, node in self.events if action == 'stop-node'}

    def event(self, action: str, node: str = '') -> None:
        if self.fail:
            raise OSError('fsync failed')
        # Intent must precede the corresponding effect, never be a success claim.
        if action not in {'qualification-failed', 'recovery-failed'}:
            self.events.append((action, node))


class NativeMaintenanceTests(unittest.TestCase):
    def transaction(self, state: dict[str, Any] | None = None) -> tuple[FakePort, Events, maintenance.Transaction]:
        saved = baseline() if state is None else state
        port = FakePort(saved)
        events = Events(port)
        return port, events, maintenance.Transaction(port, events, saved)

    def test_success_restores_running_nodes_and_original_inactive_socket(self) -> None:
        port, events, transaction = self.transaction()
        self.assertEqual(transaction.execute(), {'status': 'PASS'})
        self.assertEqual(port.state, baseline())
        self.assertEqual(port.daemon, 'active')
        self.assertNotIn(('stop-socket', ''), port.calls)
        self.assertFalse(any(action == 'restore-socket' for action, _ in port.calls))
        self.assertEqual(events.events, port.calls)
        self.assertEqual([name for action, name in port.calls if action == 'stop-node'], list(maintenance.NODES))

    def test_originally_stopped_nodes_are_neither_stopped_nor_started(self) -> None:
        saved = baseline('active')
        saved['nodes']['swarm-worker-1']['status'] = 'Stopped'
        port, _events, transaction = self.transaction(saved)
        self.assertEqual(transaction.execute()['status'], 'PASS')
        self.assertEqual(port.state, saved)
        self.assertNotIn(('stop-node', 'swarm-worker-1'), port.calls)
        self.assertNotIn(('start-node', 'swarm-worker-1'), port.calls)
        self.assertIn(('stop-socket', ''), port.calls)
        self.assertIn(('restore-socket', 'active'), port.calls)

    def test_each_uncertain_failure_and_interruption_recovers_before_return(self) -> None:
        for failure in ('stop-before', 'stop-after', 'socket', 'shutdown-before', 'shutdown-after', 'fixture', 'interrupt'):
            with self.subTest(failure=failure):
                saved = baseline('active')
                port, _events, transaction = self.transaction(saved)
                port.failure = failure
                self.assertEqual(transaction.execute()['status'], 'QUALIFICATION_FAILED_RECOVERED')
                self.assertEqual(port.state, saved)
                self.assertEqual(port.daemon, 'active')
                if failure not in {'fixture', 'interrupt'}:
                    self.assertNotIn(('fixture', ''), port.calls)

    def test_concurrent_node_state_changes_are_not_stopped_or_blindly_started(self) -> None:
        for original, observed in (('Running', 'Stopped'), ('Stopped', 'Running')):
            with self.subTest(original=original):
                saved = baseline()
                saved['nodes']['swarm-manager']['status'] = original
                port, _events, transaction = self.transaction(saved)
                port.node_drift = ('swarm-manager', observed)
                with self.assertRaisesRegex(maintenance.MaintenanceError, 'RECOVERY_REQUIRED'):
                    transaction.execute()
                self.assertNotIn(('stop-node', 'swarm-manager'), port.calls)
                self.assertNotIn(('start-node', 'swarm-manager'), port.calls)
                self.assertEqual(port.state['nodes']['swarm-manager']['status'], observed)
                for name in ('swarm-worker-1', 'swarm-worker-2'):
                    self.assertEqual(port.state['nodes'][name]['status'], 'Running')
                self.assertNotIn(('shutdown', ''), port.calls)
                self.assertNotIn(('fixture', ''), port.calls)

    def test_full_pre_shutdown_snapshot_rejects_late_foreign_resources(self) -> None:
        for drift in ('fourth_instance', 'new_project', 'foreign_profile', 'incus_snapshot'):
            with self.subTest(drift=drift):
                port, _events, transaction = self.transaction()
                port.late_drift = drift
                with self.assertRaisesRegex(maintenance.MaintenanceError, 'RECOVERY_REQUIRED'):
                    transaction.execute()
                self.assertNotIn(('shutdown', ''), port.calls)
                self.assertNotIn(('stop-socket', ''), port.calls)
                self.assertNotIn(('fixture', ''), port.calls)
                self.assertTrue(all(row['status'] == 'Running' for row in port.state['nodes'].values()))
                self.assertEqual(port.daemon, 'active')

    def test_reactivation_is_failure_even_when_recovery_can_restore(self) -> None:
        port, _events, transaction = self.transaction()
        port.reactivate = True
        self.assertEqual(transaction.execute()['status'], 'QUALIFICATION_FAILED_RECOVERED')
        self.assertEqual(port.state, baseline())
        self.assertNotIn(('start-daemon', ''), port.calls)

    def test_existing_incus_data_or_identity_drift_never_passes(self) -> None:
        port, _events, transaction = self.transaction()
        port.fixture_drift = True
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'RECOVERY_REQUIRED'):
            transaction.execute()
        self.assertEqual(port.daemon, 'active')
        self.assertTrue(all(row['status'] == 'Running' for row in port.state['nodes'].values()))
        port, _events, transaction = self.transaction()
        port.state['nodes']['swarm-manager']['identity'] = 'b' * 64
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'PRESTATE_DRIFT'):
            transaction.execute()
        self.assertEqual(port.calls, [])

    def test_failed_recovery_is_distinct_and_can_resume_from_durable_baseline(self) -> None:
        port, _events, transaction = self.transaction()
        port.start_failure = True
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'RECOVERY_REQUIRED'):
            transaction.execute()
        self.assertEqual(port.daemon, 'inactive')
        port.start_failure = False
        transaction.recover()
        self.assertEqual(port.state, baseline())
        self.assertEqual(port.daemon, 'active')
        before = list(port.calls)
        transaction.recover()
        self.assertEqual(port.calls, before)  # Already restored: no effect replay.

    def test_prestate_drift_and_missing_durable_intent_prevent_effects(self) -> None:
        port, _events, transaction = self.transaction()
        port.failure = 'prestate'
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'PRESTATE_DRIFT'):
            transaction.execute()
        self.assertEqual(port.calls, [])
        port, events, transaction = self.transaction()
        events.fail = True
        self.assertEqual(transaction.execute()['status'], 'QUALIFICATION_FAILED_RECOVERED')
        self.assertEqual(port.calls, [])

    def test_fixed_adapter_commands_never_stop_live_systemd_daemon_or_force_nodes(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        port.baseline = baseline()
        with patch.object(port, 'check_binding'), patch.object(port, 'command', return_value=b'') as run:
            port.stop_node('swarm-manager')
            port.start_node('swarm-manager')
            port.shutdown()
            port.stop_socket()
            self.assertEqual(run.call_args_list[0].args[0], ['/snap/bin/lxc', '--force-local', 'stop',
                'swarm-manager', '--project', 'default', '--timeout', '60'])
            self.assertTrue(run.call_args_list[0].kwargs['lxd'])
            self.assertTrue(run.call_args_list[1].kwargs['lxd'])
            self.assertEqual(run.call_args_list[2].args[0], ['/snap/bin/lxd', 'shutdown', '--timeout', '60'])
            for call in run.call_args_list:
                self.assertNotIn('--force', call.args[0])
                self.assertNotEqual(call.args[0], ['/usr/bin/systemctl', 'stop', maintenance.DAEMON])
            with self.assertRaises(maintenance.MaintenanceError):
                port.stop_node('foreign')
            with self.assertRaises(maintenance.MaintenanceError):
                port.start_node('foreign')
            self.assertEqual(run.call_count, 4)

    def test_shutdown_timeout_enters_recovery_without_running_fixture(self) -> None:
        port, _events, transaction = self.transaction()
        port.failure = 'shutdown-before'
        self.assertEqual(transaction.execute()['status'], 'QUALIFICATION_FAILED_RECOVERED')
        self.assertFalse(any(action in {'fixture', 'start-daemon'} for action, _ in port.calls))

    def test_fresh_source_host_fixture_expiry_and_reviews_are_required(self) -> None:
        now = datetime.now(timezone.utc)
        proposal: dict[str, Any] = {'source_commit': 'a' * 40, 'pins': {'source': 'a' * 64},
                    'host_id_sha256': 'b' * 64, 'fixture_go_sha256': 'c' * 64, 'baseline': baseline()}
        go = {'schema_version': 1, 'decision': 'GO', 'proposal_sha256': 'd' * 64,
              'source_commit': proposal['source_commit'], 'pins': proposal['pins'],
              'host_id_sha256': proposal['host_id_sha256'], 'fixture_go_sha256': proposal['fixture_go_sha256'],
              'expires_at_utc': (now + timedelta(minutes=10)).isoformat(),
              'reviews': dict.fromkeys(maintenance.fixture.REVIEW_KEYS, 'APPROVED')}
        maintenance.validate_approval(go, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now)
        for field, value in (('schema_version', True), ('decision', 'PENDING'), ('proposal_sha256', 'f' * 64),
                             ('source_commit', 'b' * 40), ('host_id_sha256', 'f' * 64),
                             ('fixture_go_sha256', 'f' * 64), ('pins', {}), ('reviews', {}),
                             ('expires_at_utc', now.isoformat()),
                             ('expires_at_utc', (now + timedelta(hours=1)).isoformat())):
            bad = {**go, field: value}
            with self.subTest(field=field), self.assertRaises(maintenance.MaintenanceError):
                maintenance.validate_approval(bad, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now)

    def test_invalid_cli_go_cannot_create_host_lock_or_construct_effect_adapter(self) -> None:
        now = datetime.now(timezone.utc)
        fixture_raw = b'{}'
        proposal: dict[str, Any] = {'source_commit': 'a' * 40, 'pins': {}, 'host_id_sha256': maintenance.digest(b'host'),
                    'fixture_go_sha256': maintenance.digest(fixture_raw), 'baseline': baseline()}
        proposal_raw = maintenance.canonical(proposal)
        go = {'schema_version': 1, 'decision': 'PENDING', 'proposal_sha256': maintenance.digest(proposal_raw),
              'source_commit': 'a' * 40, 'pins': {}, 'host_id_sha256': proposal['host_id_sha256'],
              'fixture_go_sha256': proposal['fixture_go_sha256'],
              'expires_at_utc': (now + timedelta(minutes=10)).isoformat(),
              'reviews': dict.fromkeys(maintenance.fixture.REVIEW_KEYS, 'APPROVED')}
        go_raw = maintenance.canonical(go)
        with patch.object(maintenance.os, 'geteuid', return_value=0), \
                patch.object(maintenance.signal, 'signal'), \
                patch.object(maintenance, 'private_directory'), \
                patch.object(maintenance, 'source_pins', return_value=('a' * 40, {})), \
                patch.object(maintenance, 'read_private', side_effect=[fixture_raw, go_raw, proposal_raw]), \
                patch.object(maintenance.fixture, 'validate_go'), \
                patch.object(maintenance.fixture, '_assert_host_identity'), \
                patch.object(maintenance.Path, 'read_bytes', return_value=b'host'), \
                patch.object(maintenance, 'host_lock') as lock, \
                patch.object(maintenance, 'NativePort') as adapter, \
                patch.object(maintenance.sys, 'stderr'):
            self.assertEqual(maintenance.main(['execute', '--run-id', 'a' * 32,
                '--fixture-go-sha256', maintenance.digest(fixture_raw),
                '--expected-go-sha256', maintenance.digest(go_raw)]), 2)
            lock.assert_not_called()
            adapter.assert_not_called()

    def test_snapshot_schema_does_not_admit_foreign_names_or_coerced_status(self) -> None:
        changes: tuple[dict[str, Any], ...] = ({'nodes': {}}, {'socket': 'failed'}, {'binding': []})
        for changed in changes:
            with self.assertRaises(maintenance.MaintenanceError):
                maintenance.validate_snapshot(baseline() | changed)
        saved = baseline()
        saved['nodes']['swarm-manager']['status'] = True
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.validate_snapshot(saved)

    def test_journal_is_exclusive_private_and_durable_before_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(maintenance, 'private_directory'):
                journal = maintenance.Journal(directory)
            journal.save('proposal.json', {'canary': 'private'})
            self.assertEqual((directory / 'proposal.json').stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads((directory / 'proposal.json').read_bytes()), {'canary': 'private'})
            with self.assertRaises(FileExistsError):
                journal.save('proposal.json', {})
            for path in ('../escape.json', '/escape.json', 'x/y.json'):
                with self.assertRaises(maintenance.MaintenanceError):
                    journal.save(path, {})
            symlink = directory / 'alias.json'
            symlink.symlink_to(directory / 'proposal.json')
            with self.assertRaises(FileExistsError):
                journal.save('alias.json', {})
            with patch.object(maintenance.os, 'fsync', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    journal.event('stop-node', 'swarm-manager')

    def test_new_controller_recovers_only_durably_intended_stops(self) -> None:
        saved = baseline()
        port = FakePort(saved)
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(maintenance, 'private_directory'):
                journal = maintenance.Journal(Path(temporary))
            port.start_failure = True
            transaction = maintenance.Transaction(port, journal, saved)
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'RECOVERY_REQUIRED'):
                transaction.execute()
            self.assertEqual(journal.stopped_nodes(), set(maintenance.NODES))
            port.start_failure = False
            resumed = maintenance.Transaction(port, journal, saved)
            resumed.recover()
            self.assertEqual(port.state, saved)
            self.assertEqual(port.daemon, 'active')

    def test_existing_collector_response_retains_hashes_without_secret_values(self) -> None:
        canary = 'private-value-never-in-proposal'
        row = {'config': {'user.secret': canary}, 'description': canary, 'name': 'web', 'devices': {}}
        response = maintenance.canonical({'metadata': row})
        runner = maintenance.ConfigRunner()
        with patch.object(maintenance.inventory.Runner, 'run', return_value=(0, response, b'')):
            runner.run(['/snap/bin/lxc'], command_id='lxd_instance_config_show', safe_args=['swarm-manager', 'default'])
        self.assertEqual(len(runner.configs), 1)
        self.assertNotIn(canary, json.dumps(runner.configs))
        self.assertTrue(all(maintenance.HEX.fullmatch(value) for value in runner.configs.values()))

    def test_single_host_lock_refuses_nested_process_and_unsafe_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            location = Path(temporary) / 'maintenance'
            with patch.object(maintenance, 'HOST_LOCK_PARENT', location):
                with maintenance.host_lock():
                    with self.assertRaisesRegex(maintenance.MaintenanceError, 'MAINTENANCE_BUSY'):
                        with maintenance.host_lock():
                            self.fail('second independent descriptor entered')
                    context = multiprocessing.get_context('fork')
                    result: Any = context.Queue()
                    def contender():
                        try:
                            with maintenance.host_lock():
                                result.put('ENTERED')
                        except maintenance.MaintenanceError as exc:
                            result.put(str(exc))
                    child = context.Process(target=contender)
                    child.start()
                    child.join(timeout=5)
                    if child.is_alive():
                        child.terminate()
                        child.join(timeout=5)
                        self.fail('lock contender did not terminate')
                    self.assertEqual(result.get(timeout=2), 'MAINTENANCE_BUSY')
                    result.close()
                with maintenance.host_lock():
                    pass  # Owner exit released flock.
                (location / 'maintenance.lock').unlink()
                target = Path(temporary) / 'foreign'
                target.write_text('preserve')
                (location / 'maintenance.lock').symlink_to(target)
                with self.assertRaises(OSError):
                    with maintenance.host_lock():
                        self.fail('symlink lock entered')
                self.assertEqual(target.read_text(), 'preserve')

    def test_config_projection_preserves_immutable_uuid_and_all_user_settings(self) -> None:
        raw: dict[str, Any] = {'config': {'volatile.uuid': 'uuid', 'volatile.uuid.generation': 'generation',
                          'volatile.eth0.host_name': 'dynamic', 'user.secret': 'canary'}, 'devices': {'root': {'pool': 'fixed'}}}
        projected = maintenance.config_projection(raw, instance=True)
        self.assertEqual(projected['config'], {'volatile.uuid': 'uuid', 'volatile.uuid.generation': 'generation', 'user.secret': 'canary'})
        self.assertEqual(projected['devices'], raw['devices'])
        self.assertEqual(raw['config']['volatile.eth0.host_name'], 'dynamic')
        self.assertEqual(maintenance.config_projection(raw), raw)
        self.assertNotIn('used_by', maintenance.config_projection(raw | {'used_by': ['observed']}))
        self.assertEqual(maintenance.config_projection(raw | {'description': 'preserve'})['description'], 'preserve')


if __name__ == '__main__':
    unittest.main()

"""Preserving maintenance failures must recover; no hosts or real commands."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
import multiprocessing
import subprocess
import sys
import time
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from typing import Any

from tools.linux.qualification import native_lxd_maintenance as maintenance



def wrapped_provenance(reason: str) -> maintenance.inventory.InventoryError:
    error = maintenance.inventory.InventoryError(reason)
    error.__cause__ = maintenance.provenance.ProvenanceError(reason)
    return error

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

    def recovery_state(self, *, transition_owned: bool, start_owned: bool) -> str:
        return self.unit(maintenance.DAEMON)

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
        self.failures: list[tuple[str, str]] = []

    def failure(self, stage: str, reason: str) -> None:
        if self.fail:
            raise OSError('fsync failed')
        self.failures.append((stage, reason))

    def stopped_nodes(self) -> set[str]:
        return {node for action, node in self.events if action == 'stop-node'}

    def transition_intents(self) -> set[str]:
        return {action for action, _ in self.events if action in maintenance.TRANSITION_INTENTS}

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

    def test_production_start_waits_for_full_proof_after_active_without_repeating_start(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        port.baseline = baseline()
        port.recovering = True
        with patch.object(port, 'check_binding') as check, patch.object(port, 'command') as command, \
                patch.object(port, 'ready_binding', side_effect=[wrapped_provenance('SNAP_WRAPPER_CHILD_ABSENT'), None]) as ready, \
                patch.object(maintenance.time, 'monotonic', return_value=10), patch.object(maintenance.time, 'sleep'), \
                patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)), \
                patch.object(maintenance.signal, 'getsignal', return_value=maintenance.signal.SIG_DFL), \
                patch.object(maintenance.signal, 'signal') as handler, patch.object(maintenance.signal, 'setitimer') as timer:
            port.start_daemon()
            check.assert_called_once_with(port.baseline, active=False)
            command.assert_called_once_with(['/usr/bin/systemctl', 'start', maintenance.DAEMON], 90)
            self.assertEqual(ready.call_count, 2)
            self.assertEqual(timer.call_args_list[0].args, (maintenance.signal.ITIMER_REAL, 25))
            self.assertEqual(timer.call_args_list[-1].args, (maintenance.signal.ITIMER_REAL, 0))
            self.assertEqual(handler.call_args_list[-1].args, (maintenance.signal.SIGALRM, maintenance.signal.SIG_DFL))

    def test_readiness_permanent_drift_and_expired_window_never_repeat_or_start_nodes(self) -> None:
        for reason in ('INSTALLED_BINDING_DRIFT', 'INCUS_SOCKET_DRIFT', 'INCUS_SERVICE_DRIFT',
                       'SOURCE_HEAD_DRIFT', 'SERVER_ADMISSION_BLOCKED'):
            port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
            port.baseline = baseline()
            port.recovering = True
            with self.subTest(reason=reason), patch.object(port, 'ready_binding', side_effect=maintenance.MaintenanceError(reason)) as ready, \
                    patch.object(maintenance.time, 'monotonic', return_value=10), \
                    patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)), \
                    patch.object(maintenance.signal, 'getsignal', return_value=maintenance.signal.SIG_DFL), \
                    patch.object(maintenance.signal, 'signal'), patch.object(maintenance.signal, 'setitimer'), \
                    patch.object(port, 'command') as command:
                with self.assertRaisesRegex(maintenance.MaintenanceError, reason):
                    port.wait_ready()
                ready.assert_called_once()
                command.assert_not_called()
        with patch.object(maintenance.time, 'monotonic', return_value=1000), patch.object(port, 'ready_binding') as ready:
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'RECOVERY_READINESS_RESERVE_MISSING'):
                port.wait_ready()
            ready.assert_not_called()
        port.deadline = 1000
        with patch.object(maintenance.time, 'monotonic', side_effect=[10, 10, 36]), \
                patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)), \
                patch.object(maintenance.signal, 'getsignal', return_value=maintenance.signal.SIG_DFL), \
                patch.object(maintenance.signal, 'signal'), patch.object(maintenance.signal, 'setitimer'), \
                patch.object(port, 'ready_binding') as ready:
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'LXD_READINESS_TIMEOUT'):
                port.wait_ready()
            ready.assert_not_called()

    def test_readiness_alarm_reaps_actual_runner_client_before_returning(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        port.baseline = baseline()
        port.recovering = True
        handlers: list[Any] = []
        process = Mock()
        process.stdout.fileno.return_value = 101
        process.stderr.fileno.return_value = 102
        selector = Mock()
        selector.get_map.return_value = {101: object()}
        def alarm(_timeout: float) -> None:
            handlers[0](maintenance.signal.SIGALRM, None)
        selector.select.side_effect = alarm
        runner = maintenance.inventory.Runner(popen=Mock(return_value=process))
        def read() -> None:
            runner.run(['/usr/bin/systemctl', 'show'], command_id='fixture')
        with (patch.object(port, 'ready_binding', side_effect=read),
              patch.object(maintenance.time, 'monotonic', return_value=10),
              patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)),
              patch.object(maintenance.signal, 'getsignal', return_value=maintenance.signal.SIG_DFL),
              patch.object(maintenance.signal, 'signal', side_effect=lambda _s, handler: handlers.append(handler)),
              patch.object(maintenance.signal, 'setitimer') as timer,
              patch.object(maintenance.inventory.selectors, 'DefaultSelector', return_value=selector),
              patch.object(maintenance.inventory, '_kill_reap') as reap):
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'LXD_READINESS_TIMEOUT'):
                port.wait_ready()
            reap.assert_called_once_with(process)
            self.assertEqual(timer.call_args_list[-1].args, (maintenance.signal.ITIMER_REAL, 0))
            self.assertEqual(runner.records, [])

    def test_readiness_rebinds_actual_root_api_authority_and_full_process_proof(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        expected = {'server_version': '5.21.9', 'server_lts': True, 'auth': 'trusted'}
        port.baseline = baseline()
        port.baseline['preserve']['lxd_admission'] = {'initial': expected}
        with patch.object(port, 'check_binding') as check, \
                patch.object(maintenance.inventory, '_read_server_root', return_value=expected) as api:
            port.ready_binding()
            api.call_args.args[3]()
            self.assertEqual(check.call_count, 3)  # before, API-before-query callback, after
            self.assertEqual(api.call_args.args[1], ['/snap/bin/lxc', '--force-local'])
            self.assertEqual(api.call_args.args[2]['LXD_SOCKET'], maintenance.SOCKET_PATH)
            self.assertEqual(api.call_args.kwargs['cli_version'], '5.21.9 LTS')
            api.return_value = expected | {'auth': 'untrusted'}
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'LXD_API_AUTHORITY_DRIFT'):
                port.ready_binding()
            api.side_effect = maintenance.inventory.InventoryError('COMMAND_FAILED')
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'LXD_API_NOT_READY'):
                port.ready_binding()
            api.side_effect = maintenance.inventory.InventoryError('SERVER_SCHEMA_INVALID')
            with self.assertRaisesRegex(maintenance.inventory.InventoryError, 'SERVER_SCHEMA_INVALID'):
                port.ready_binding()

    def test_fixture_child_failure_retains_only_same_source_go_symbolic_result_reason(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        port.final_expiry = datetime.now(timezone.utc) + timedelta(minutes=25)
        failed: dict[str, Any] = {'status': 'BLOCKED_TARGET_DRIFT', 'source_commit': 'a' * 40,
                                'go_sha256': 'c' * 64, 'code': 'INCUS_INVENTORY_COMMAND_FAILED'}
        variants: tuple[dict[str, Any], ...] = ({}, {'go_sha256': 'd' * 64}, {'source_commit': 'f' * 40},
                                               {'code': 'PRIVATE raw canary'}, {'status': 'PASS'})
        with patch.object(port, 'unit', return_value='inactive'), \
                patch.object(port, 'await_admission', return_value='c' * 64), \
                patch.object(maintenance, 'source_pins', return_value=('a' * 40, {})), \
                patch.object(port, 'command', side_effect=maintenance.MaintenanceError('COMMAND_FAILED_UNCERTAIN')), \
                patch.object(maintenance, 'read_private') as read:
            for change in variants:
                read.return_value = maintenance.canonical(failed | change)
                reason = 'COMMAND_FAILED_UNCERTAIN' if change else 'INCUS_INVENTORY_COMMAND_FAILED'
                with self.subTest(change=change), self.assertRaisesRegex(maintenance.MaintenanceError, reason):
                    port.run_fixture()

    def test_durable_failures_keep_safe_symbolic_reason_and_never_exception_text(self) -> None:
        port, events, transaction = self.transaction()
        port.failure = 'fixture'
        self.assertEqual(transaction.execute()['status'], 'QUALIFICATION_FAILED_RECOVERED')
        self.assertIn(('qualification', 'FIXTURE_FAILED'), events.failures)
        port, events, transaction = self.transaction()
        port.failure = 'fixture'
        port.start_failure = True
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'RECOVERY_REQUIRED'):
            transaction.execute()
        self.assertIn(('recovery', 'START_FAILED'), events.failures)
        self.assertEqual(maintenance.failure_reason(RuntimeError('PRIVATE canary/address/pid')), 'UNCLASSIFIED_FAILURE_REDACTED')
        self.assertEqual(maintenance.failure_reason(wrapped_provenance('SNAP_WRAPPER_CHILD_ABSENT')), 'SNAP_WRAPPER_CHILD_ABSENT')
        self.assertEqual(maintenance.failure_reason(maintenance.MaintenanceError('PRIVATE raw value')), 'UNCLASSIFIED_FAILURE_REDACTED')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            with patch.object(maintenance, 'private_directory') as directory_proof:
                journal = maintenance.Journal(root)
            directory_proof.assert_called_once_with(root)
            journal.failure('recovery', 'LXD_READINESS_TIMEOUT')
            record = json.loads(next(root.glob('failure-*.json')).read_text())
            self.assertEqual(set(record), {'stage', 'reason', 'utc'})
            self.assertEqual(record['reason'], 'LXD_READINESS_TIMEOUT')
            self.assertEqual(journal.stopped_nodes(), set())

    def test_stopped_restart_admission_rejects_implicit_and_explicit_autostart(self) -> None:
        safe: tuple[dict[str, str], ...] = ({}, {'volatile.last_state.power': 'STOPPED'},
                                          {'volatile.last_state.power': 'RUNNING'})
        for config in safe:
            maintenance.require_restart_safe({'expanded_config': {'boot.autostart': 'false'}, 'config': config})
        for autostart in ('', None):
            expanded = {} if autostart is None else {'boot.autostart': autostart}
            for config in ({}, {'volatile.last_state.power': 'STOPPED'}):
                maintenance.require_restart_safe({'expanded_config': expanded, 'config': config})
            for last_power in ('RUNNING', '', 'stopped', 'unknown'):
                with self.assertRaisesRegex(maintenance.MaintenanceError, 'STOPPED_NODE_AUTOSTART_UNSAFE'):
                    maintenance.require_restart_safe({'expanded_config': expanded,
                                                      'config': {'volatile.last_state.power': last_power}})
        for autostart in ('true', '1', 'FALSE', 'unknown'):
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'STOPPED_NODE_AUTOSTART_UNSAFE'):
                maintenance.require_restart_safe({'expanded_config': {'boot.autostart': autostart}, 'config': {}})

    def test_real_node_read_rechecks_originally_stopped_but_allows_own_stopped_running_node(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        port.baseline = baseline()
        row: dict[str, Any] = {'config': {'volatile.uuid': '12345678-1234-1234-1234-123456789abc',
                          'volatile.last_state.power': 'RUNNING'},
               'expanded_config': {}, 'type': 'container', 'status': 'Stopped',
               'created_at': 'fixed', 'profiles': ['default']}
        with patch.object(port, 'budget'), patch.object(port, 'check_binding'), \
                patch.object(maintenance.inventory, '_detail', return_value={}), \
                patch.object(maintenance.inventory, '_validate_instance_config', return_value=row), \
                patch.object(maintenance, 'config_projection', return_value={}):
            self.assertEqual(port.node('swarm-manager')['status'], 'Stopped')
            port.baseline['nodes']['swarm-manager']['status'] = 'Stopped'
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'STOPPED_NODE_AUTOSTART_UNSAFE'):
                port.node('swarm-manager')
            port.baseline = None
            with patch.object(maintenance.inventory, '_systemctl_show', return_value={}), \
                    patch.object(maintenance.inventory, '_resolve_executable', return_value=('lxd_snap', 'snap:lxd')), \
                    patch.object(maintenance.inventory, '_endpoint', return_value=('', True)), \
                    patch.object(maintenance.inventory, '_require_full_local_access'):
                with self.assertRaisesRegex(maintenance.MaintenanceError, 'STOPPED_NODE_AUTOSTART_UNSAFE'):
                    port.node('swarm-manager')
            port.baseline = baseline()
            port.baseline['nodes']['swarm-manager']['status'] = 'Stopped'
            row['expanded_config']['boot.autostart'] = 'false'
            self.assertEqual(port.node('swarm-manager')['status'], 'Stopped')

    def test_shutdown_timeout_enters_recovery_without_running_fixture(self) -> None:
        port, _events, transaction = self.transaction()
        port.failure = 'shutdown-before'
        self.assertEqual(transaction.execute()['status'], 'QUALIFICATION_FAILED_RECOVERED')
        self.assertFalse(any(action in {'fixture', 'start-daemon'} for action, _ in port.calls))

    def test_fresh_source_host_fixture_expiry_and_reviews_are_required(self) -> None:
        now = datetime.now(timezone.utc)
        proposal: dict[str, Any] = {'source_commit': 'a' * 40, 'pins': {'source': 'a' * 64},
                    'host_id_sha256': 'b' * 64, 'fixture_intent_sha256': 'c' * 64, 'baseline': baseline()}
        go = {'schema_version': 2, 'operation': 'execute', 'decision': 'GO', 'proposal_sha256': 'd' * 64,
              'source_commit': proposal['source_commit'], 'pins': proposal['pins'],
              'host_id_sha256': proposal['host_id_sha256'], 'fixture_intent_sha256': proposal['fixture_intent_sha256'],
              'expires_at_utc': (now + timedelta(minutes=29)).isoformat(),
              'reviews': dict.fromkeys(maintenance.fixture.REVIEW_KEYS, 'APPROVED')}
        maintenance.validate_approval(go, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now)
        for field, value in (('schema_version', True), ('decision', 'PENDING'), ('proposal_sha256', 'f' * 64),
                             ('source_commit', 'b' * 40), ('host_id_sha256', 'f' * 64),
                             ('fixture_intent_sha256', 'f' * 64), ('pins', {}), ('reviews', {}),
                             ('expires_at_utc', now.isoformat()),
                             ('expires_at_utc', (now + timedelta(hours=1)).isoformat())):
            bad = {**go, field: value}
            with self.subTest(field=field), self.assertRaises(maintenance.MaintenanceError):
                maintenance.validate_approval(bad, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now)

    def test_invalid_cli_go_cannot_create_host_lock_or_construct_effect_adapter(self) -> None:
        now = datetime.now(timezone.utc)
        fixture_raw = b'{}'
        proposal: dict[str, Any] = {'source_commit': 'a' * 40, 'pins': {}, 'host_id_sha256': maintenance.digest(b'host'),
                    'fixture_intent_sha256': maintenance.digest(fixture_raw), 'baseline': baseline()}
        proposal_raw = maintenance.canonical(proposal)
        go = {'schema_version': 2, 'operation': 'execute', 'decision': 'PENDING', 'proposal_sha256': maintenance.digest(proposal_raw),
              'source_commit': 'a' * 40, 'pins': {}, 'host_id_sha256': proposal['host_id_sha256'],
              'fixture_intent_sha256': proposal['fixture_intent_sha256'],
              'expires_at_utc': (now + timedelta(minutes=29)).isoformat(),
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
                '--fixture-intent-sha256', maintenance.digest(fixture_raw),
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




class PausedAdmissionTests(unittest.TestCase):
    def inputs(self) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes, bytes, datetime]:
        now = datetime.now(timezone.utc)
        static = {'source_commit': 'a' * 40, 'target': {'run_id': 'b' * 32}}
        intent: dict[str, Any] = {'fixture': static, 'provider_config_sha256': 'c' * 64}
        resource = maintenance.canonical({'schema_version': 'tsw.resource-admission.v1',
            'target_host': maintenance.HOST, 'platform': 'native_linux', 'scenario_id': 'R449-33',
            'source_commit': 'a' * 40, 'decision': 'PASS', 'checks': dict.fromkeys(maintenance.RESOURCE_CHECKS, True),
            'candidate': {'provider_config_sha256': 'c' * 64}})
        route = maintenance.canonical({'schema_version': 'tsw.route-state.v2', 'source_commit': 'a' * 40,
                                      'target_host': maintenance.HOST, 'approved_route_state_sha256': 'd' * 64})
        go = maintenance.canonical(static | {'decision': 'GO', 'resource_admission_sha256': maintenance.digest(resource),
                                             'approved_route_state_sha256': 'd' * 64})
        activation = {'decision': 'GO', 'intent_sha256': 'e' * 64,
            'resource_sha256': maintenance.digest(resource), 'route_sha256': maintenance.digest(route),
            'fixture_go_sha256': maintenance.digest(go), 'expires_at_utc': (now + timedelta(minutes=20)).isoformat()}
        return intent, activation, resource, route, go, now

    def test_final_go_binds_actual_paused_files_and_independent_static_intent(self) -> None:
        intent, activation, resource, route, go, now = self.inputs()
        with patch.object(maintenance.fixture, 'validate_go') as checked, \
                patch.object(maintenance.Path, 'read_bytes', return_value=b'fixed'):
            result = maintenance.validate_paused_admission(activation, intent, 'e' * 64, resource, route, go, 'a' * 40, now)
            self.assertEqual(result, maintenance.digest(go))
            self.assertEqual(checked.call_args.args[0], json.loads(go))
            for field, value in (('resource_sha256', 'f' * 64), ('route_sha256', 'f' * 64),
                                 ('intent_sha256', 'f' * 64), ('fixture_go_sha256', 'f' * 64),
                                 ('decision', 'INTENT_ONLY'), ('expires_at_utc', now.isoformat())):
                with self.subTest(field=field), self.assertRaises(maintenance.MaintenanceError):
                    maintenance.validate_paused_admission(dict(activation, **{field: value}), intent, 'e' * 64,
                                                          resource, route, go, 'a' * 40, now)
            payloads: tuple[dict[str, Any], ...] = ({'decision': 'BLOCKED'}, {'checks': {}}, {'checks': {'capacity': 1}},
                                                  {'source_commit': 'f' * 40}, {'target_host': 'other'})
            for payload in payloads:
                bad_resource = maintenance.canonical(json.loads(resource) | payload)
                rebound = dict(activation, resource_sha256=maintenance.digest(bad_resource))
                bad_go = maintenance.canonical(json.loads(go) | {'resource_admission_sha256': maintenance.digest(bad_resource)})
                rebound['fixture_go_sha256'] = maintenance.digest(bad_go)
                with self.subTest(payload=payload), self.assertRaises(maintenance.MaintenanceError):
                    maintenance.validate_paused_admission(rebound, intent, 'e' * 64, bad_resource, route, bad_go, 'a' * 40, now)


    def socket_baseline(self, endpoint: str = 'incus_var_lib') -> dict[str, Any]:
        # Actual service DTO intentionally has no Listen field.
        service = {'unit': 'incus.service', 'load_state': 'loaded', 'active_state': 'active',
                   'sub_state': 'running', 'unit_file_state': 'enabled', 'main_pid': 42}
        socket = {'unit': 'incus.socket', 'load_state': 'loaded', 'active_state': 'active',
                  'sub_state': 'running', 'unit_file_state': 'enabled', 'main_pid': 0, 'listen': endpoint}
        return {'binding': {'installed': {}, 'incus_unit': service},
                'preserve': {'incus_units': [service, socket]}}

    def test_actual_await_admission_uses_socket_dto_and_rechecks_it_before_version_query(self) -> None:
        for endpoint, socket_path in (('incus_run', '/run/incus/unix.socket'),
                                      ('incus_var_lib', '/var/lib/incus/unix.socket')):
            with self.subTest(endpoint=endpoint), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                port = maintenance.NativePort('a' * 40, 'e' * 64, 0)
                port.baseline = self.socket_baseline(endpoint)
                port.admission_directory = directory
                self.assertNotIn('listen', port.baseline['binding']['incus_unit'])
                resource: dict[str, Any] = {'candidate': {}, 'observed': {}, 'checks': {}, 'commands': []}
                intent = {'provider_config_sha256': 'c' * 64}
                intent_raw = maintenance.canonical(intent)
                port.fixture_sha = maintenance.digest(intent_raw)
                route_raw = b'{"schema_version":"tsw.route-state.v2"}'
                activation = {'expires_at_utc': (datetime.now(timezone.utc) + timedelta(minutes=25)).isoformat()}
                captured: dict[str, bytes] = {}
                def save(name: str, value: Any) -> None:
                    captured[name] = maintenance.canonical(value)
                def read(path: Path) -> bytes:
                    if path == maintenance.ROOT / maintenance.INTENT_REL:
                        return intent_raw
                    if path == directory / 'activation.json':
                        return maintenance.canonical(activation)
                    if path == directory / 'paused-resource.json':
                        return captured['paused-resource.json']
                    if path == maintenance.ROOT / maintenance.fixture.GO_REL:
                        return b'{}'
                    return route_raw
                def unit(_runner: Any, name: str) -> dict[str, Any]:
                    assert port.baseline is not None
                    if name == 'incus.socket':
                        return maintenance.incus_socket(port.baseline)
                    if name == 'incus.service':
                        return port.baseline['binding']['incus_unit']
                    self.assertEqual(name, maintenance.DAEMON)
                    return {'active_state': 'inactive'}
                with patch.object(maintenance, 'read_private', side_effect=read), \
                        patch.object(maintenance, 'validate_fixture_intent', return_value=intent), \
                        patch.object(maintenance, 'source_pins', return_value=('a' * 40, dict.fromkeys(maintenance.FILES, 'f' * 64))), \
                        patch.object(port, 'installed_binding', return_value={}), \
                        patch.object(maintenance.inventory, '_systemctl_show', side_effect=unit) as observed_units, \
                        patch.object(maintenance.inventory, '_resolve_executable', return_value=('incus_system', 'system:incus')), \
                        patch.object(port, 'interpreter', return_value='/trusted/python'), \
                        patch.object(port, 'command', return_value=maintenance.canonical(resource)) as command, \
                        patch.object(maintenance.inventory.Runner, 'run', return_value=(0, b'Client version: 6.0.5\nServer version: 6.0.5\n', b'')) as version, \
                        patch.object(maintenance, 'Journal') as journal, \
                        patch.object(maintenance.Path, 'exists', return_value=True), \
                        patch.object(maintenance, 'validate_paused_admission', return_value='b' * 64) as validate, \
                        patch.object(port, 'unit', return_value='inactive'):
                    journal.return_value.save.side_effect = save
                    self.assertEqual(port.await_admission(), 'b' * 64)
                    version.assert_called_once()
                    self.assertEqual(version.call_args.args[0], ['/usr/bin/incus', '--force-local', 'version'])
                    self.assertEqual(version.call_args.kwargs['env']['INCUS_SOCKET'], socket_path)
                    self.assertEqual(command.call_count, 2)  # fixed resource child and route capture, no effects
                    self.assertEqual(json.loads(captured['paused-resource.json'])['observed']['incus_server_version'], ['6.0.5'])
                    self.assertEqual(validate.call_args.args[4], route_raw)
                    self.assertEqual(sum(call.args[1] == 'incus.socket' for call in observed_units.call_args_list), 3)

    def test_missing_duplicate_unloaded_and_noncanonical_socket_observations_refuse(self) -> None:
        valid = self.socket_baseline()
        socket = copy.deepcopy(valid['preserve']['incus_units'][1])
        variants: tuple[list[dict[str, Any]], ...] = ([], [socket, socket],
            [socket | {'listen': 'foreign'}], [socket | {'listen': []}],
            [socket | {'load_state': 'not-found'}], [socket | {'main_pid': True}],
            [socket | {'extra': 'unknown'}])
        for rows in variants:
            value = copy.deepcopy(valid)
            value['preserve']['incus_units'] = rows
            port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
            with self.subTest(rows=rows), patch.object(port, 'budget'), \
                    patch.object(port, 'installed_binding', return_value={}), \
                    patch.object(maintenance.inventory, '_systemctl_show') as show, \
                    patch.object(maintenance.inventory.Runner, 'run') as command:
                with self.assertRaisesRegex(maintenance.MaintenanceError, 'INCUS_SOCKET_INVALID'):
                    port.check_binding(value, active=False)
                show.assert_not_called()
                command.assert_not_called()

    def test_current_full_socket_drift_blocks_before_service_or_version_query(self) -> None:
        value = self.socket_baseline()
        current = maintenance.incus_socket(value) | {'unit_file_state': 'disabled'}
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        with patch.object(port, 'budget'), patch.object(port, 'installed_binding', return_value={}), \
                patch.object(maintenance.inventory, '_systemctl_show', return_value=current) as show, \
                patch.object(maintenance.inventory.Runner, 'run') as command:
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'INCUS_SOCKET_DRIFT'):
                port.check_binding(value, active=False)
            self.assertEqual(show.call_args.args[1], 'incus.socket')
            self.assertEqual(show.call_count, 1)
            command.assert_not_called()

    def test_named_phase_budgets_are_fresh_and_commands_never_shrink(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        with patch.object(maintenance.time, 'monotonic', return_value=1100):
            port.phase('capture')
            self.assertEqual(port.deadline, 1460)
        with patch.object(maintenance.time, 'monotonic', return_value=1400):
            port.phase('approval')
            self.assertEqual(port.deadline, 1580)
        with patch.object(maintenance.time, 'monotonic', return_value=1570):
            port.phase('fixture')
            self.assertEqual(port.deadline, 2595)
        with patch.object(maintenance.time, 'monotonic', return_value=1571), \
                patch.object(maintenance, 'bounded', return_value=b'ok') as command:
            self.assertEqual(port.command(['/fixed/fixture'], 900, interrupt_grace=120), b'ok')
            self.assertEqual(command.call_args.args, (['/fixed/fixture'], 900))
            self.assertEqual(command.call_args.kwargs['interrupt_grace'], 120)
        with patch.object(maintenance.time, 'monotonic', return_value=1576), \
                patch.object(maintenance, 'bounded') as command:
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'MAINTENANCE_DEADLINE'):
                port.command(['/fixed/fixture'], 900, interrupt_grace=120)
            command.assert_not_called()
        self.assertEqual(maintenance.MAINTENANCE_START_RESERVE, 1740)
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'PHASE_INVALID'):
            port.phase('arbitrary')

    def test_timeout_refusal_and_capture_failure_recover_own_stops_without_fixture_effect(self) -> None:
        for code in ('PAUSED_ADMISSION_TIMEOUT', 'RESOURCE_ADMISSION_NOT_PASS', 'FINAL_FIXTURE_GO_MISMATCH'):
            original = baseline()
            port = FakePort(original)
            events = Events(port)
            transaction = maintenance.Transaction(port, events, original)
            with patch.object(port, 'run_fixture', side_effect=maintenance.MaintenanceError(code)):
                self.assertEqual(transaction.execute()['status'], 'QUALIFICATION_FAILED_RECOVERED')
            self.assertEqual(port.state, original)
            self.assertEqual(port.daemon, 'active')
            self.assertFalse(any(action == 'fixture' for action, _ in port.calls))

    def test_preservation_only_admits_actual_fixture_cache_addition(self) -> None:
        fingerprint = 'b' * 64
        original = baseline()
        original['binding']['fixture_image'] = fingerprint
        project = {'project': 'default', 'images': [{'fingerprint': fingerprint}],
            'profiles': [{'name': 'default', 'api_storage_devices': [{'selector': 'root', 'pool': 'pool'}]}],
            'pools': [{'name': 'pool', 'image_cache': [], 'used_by': []}]}
        original['preserve'].update(incus_projects=[project], incus_pools=[{'name': 'pool', 'used_by': []}],
                                    configuration_digests={})
        after = copy.deepcopy(original)
        cache = {'fingerprint': fingerprint, 'owner_project': 'default', 'content_type': 'filesystem',
                 'storage_location': 'none', 'metadata_digest': 'c' * 64, 'used_by': []}
        after['preserve']['incus_projects'][0]['pools'][0]['image_cache'] = [cache]
        links = [{'kind': 'images', 'name': fingerprint, 'project': 'default'}]
        after['preserve']['incus_projects'][0]['pools'][0]['used_by'] = links
        after['preserve']['incus_pools'][0]['used_by'] = links
        after['preserve']['configuration_digests']['incus_image_cache_show:pool:' + fingerprint + ':default'] = 'c' * 64
        self.assertTrue(maintenance.preserved_snapshot(original, after))
        for change in ('foreign_cache', 'foreign_config', 'wrong_digest', 'existing_image_change', 'wrong_pool'):
            bad = copy.deepcopy(after)
            if change == 'foreign_cache':
                bad['preserve']['incus_projects'][0]['pools'][0]['image_cache'][0]['fingerprint'] = 'f' * 64
            elif change == 'foreign_config':
                bad['preserve']['foreign'] = True
            elif change == 'wrong_digest':
                bad['preserve']['configuration_digests']['incus_image_cache_show:pool:' + fingerprint + ':default'] = 'f' * 64
            elif change == 'existing_image_change':
                bad['preserve']['incus_projects'][0]['images'][0]['fingerprint'] = 'f' * 64
            else:
                bad['preserve']['incus_projects'][0]['pools'][0]['name'] = 'foreign'
            with self.subTest(change=change):
                self.assertFalse(maintenance.preserved_snapshot(original, bad))
        self.assertEqual(original['preserve']['incus_projects'][0]['pools'][0]['image_cache'], [])



class RecoveryAdmissionCorrectionTests(unittest.TestCase):
    def approval(self, operation: str, seconds: int, now: datetime) -> tuple[dict[str, Any], dict[str, Any]]:
        proposal: dict[str, Any] = {'source_commit': 'a' * 40, 'pins': {'source': 'a' * 64},
            'host_id_sha256': 'b' * 64, 'fixture_intent_sha256': 'c' * 64, 'baseline': baseline()}
        go: dict[str, Any] = {'schema_version': 2, 'operation': operation, 'decision': 'GO',
            'proposal_sha256': 'd' * 64, 'source_commit': proposal['source_commit'], 'pins': proposal['pins'],
            'host_id_sha256': proposal['host_id_sha256'], 'fixture_intent_sha256': proposal['fixture_intent_sha256'],
            'expires_at_utc': (now + timedelta(seconds=seconds)).isoformat(),
            'reviews': dict.fromkeys(maintenance.fixture.REVIEW_KEYS, 'APPROVED')}
        return go, proposal

    def test_recovery_has_its_real_reserve_and_cannot_authorize_qualification(self) -> None:
        now = datetime.now(timezone.utc)
        for seconds in (600, 1680, 1800):
            go, proposal = self.approval('recover', seconds, now)
            maintenance.validate_approval(go, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now, operation='recover')
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'APPROVAL_OPERATION_MISMATCH'):
                maintenance.validate_approval(go, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now, operation='execute')
        for seconds in (599, 0, -1, 1801):
            go, proposal = self.approval('recover', seconds, now)
            with self.subTest(seconds=seconds), self.assertRaisesRegex(maintenance.MaintenanceError, 'APPROVAL_EXPIRED'):
                maintenance.validate_approval(go, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now, operation='recover')
        go, proposal = self.approval('execute', 1680, now)
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'APPROVAL_EXPIRED'):
            maintenance.validate_approval(go, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now)
        self.assertEqual(maintenance.RECOVERY_SECONDS, 600)
        self.assertEqual(maintenance.MAINTENANCE_START_RESERVE, 1740)
        malformed: tuple[dict[str, Any], ...] = ({**go, 'schema_version': 1}, {key: value for key, value in go.items() if key != 'operation'},
            {**go, 'operation': True}, {**go, 'operation': 'all'}, {**go, 'unexpected': True})
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(maintenance.MaintenanceError):
                maintenance.validate_approval(value, proposal, 'd' * 64, 'a' * 40, proposal['pins'], now)

    def test_operation_mismatch_in_actual_cli_refuses_before_host_lock_or_effect_adapter(self) -> None:
        fixture_raw = b'{}'
        proposal: dict[str, Any] = {'source_commit': 'a' * 40, 'pins': {}, 'host_id_sha256': maintenance.digest(b'host'),
            'fixture_intent_sha256': maintenance.digest(fixture_raw), 'baseline': baseline()}
        proposal_raw = maintenance.canonical(proposal)
        go: dict[str, Any] = {'schema_version': 2, 'operation': 'recover', 'decision': 'GO',
            'proposal_sha256': maintenance.digest(proposal_raw), 'source_commit': 'a' * 40, 'pins': {},
            'host_id_sha256': proposal['host_id_sha256'], 'fixture_intent_sha256': proposal['fixture_intent_sha256'],
            'expires_at_utc': (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
            'reviews': dict.fromkeys(maintenance.fixture.REVIEW_KEYS, 'APPROVED')}
        go_raw = maintenance.canonical(go)
        with patch.object(maintenance.os, 'geteuid', return_value=0), patch.object(maintenance.signal, 'signal'), \
                patch.object(maintenance, 'private_directory'), patch.object(maintenance, 'source_pins', return_value=('a' * 40, {})), \
                patch.object(maintenance, 'read_private', side_effect=[fixture_raw, go_raw, proposal_raw]), \
                patch.object(maintenance, 'validate_fixture_intent'), patch.object(maintenance.fixture, '_assert_host_identity'), \
                patch.object(maintenance.Path, 'read_bytes', return_value=b'host'), patch.object(maintenance, 'host_lock') as lock, \
                patch.object(maintenance, 'NativePort') as adapter, patch.object(maintenance.sys, 'stderr'):
            self.assertEqual(maintenance.main(['execute', '--run-id', 'a' * 32,
                '--fixture-intent-sha256', maintenance.digest(fixture_raw), '--expected-go-sha256', maintenance.digest(go_raw)]), 2)
        lock.assert_not_called()
        adapter.assert_not_called()

    def test_owned_start_proc_transition_requires_a_subsequent_full_proof_and_never_reissues_start(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        port.baseline = baseline()
        port.recovering = True
        with patch.object(port, 'check_binding') as binding, patch.object(port, 'command') as command, \
                patch.object(port, 'ready_binding', side_effect=[wrapped_provenance('SNAP_WRAPPER_PROC_INVALID'), None]) as ready, \
                patch.object(maintenance.time, 'monotonic', return_value=10), patch.object(maintenance.time, 'sleep'), \
                patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)), \
                patch.object(maintenance.signal, 'getsignal', return_value=maintenance.signal.SIG_DFL), \
                patch.object(maintenance.signal, 'signal'), patch.object(maintenance.signal, 'setitimer') as timer, \
                patch.object(port, 'start_node') as nodes:
            port.start_daemon()
        binding.assert_called_once_with(port.baseline, active=False)
        command.assert_called_once_with(['/usr/bin/systemctl', 'start', maintenance.DAEMON], 90)
        self.assertEqual(ready.call_count, 2)
        nodes.assert_not_called()
        self.assertEqual(timer.call_args_list[-1].args, (maintenance.signal.ITIMER_REAL, 0))

    def test_permanent_proc_invalid_times_out_without_accepting_unknown_or_starting_any_node(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, 1000)
        port.baseline = baseline()
        port.recovering = port._owned_start = True
        with patch.object(port, 'ready_binding', side_effect=wrapped_provenance('SNAP_WRAPPER_PROC_INVALID')) as ready, \
                patch.object(maintenance.time, 'monotonic', side_effect=[10, 10, 10, 10, 35]), \
                patch.object(maintenance.time, 'sleep'), patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)), \
                patch.object(maintenance.signal, 'getsignal', return_value=maintenance.signal.SIG_DFL), \
                patch.object(maintenance.signal, 'signal'), patch.object(maintenance.signal, 'setitimer') as timer, \
                patch.object(port, 'command') as command, patch.object(port, 'start_node') as nodes:
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'LXD_READINESS_TIMEOUT'):
                port.wait_ready()
        ready.assert_called_once()
        command.assert_not_called()
        nodes.assert_not_called()
        self.assertEqual(timer.call_args_list[-1].args, (maintenance.signal.ITIMER_REAL, 0))



class SharedSnapshotIntentBindingTests(unittest.TestCase):
    def test_native_static_intent_pins_the_same_asset_and_preserves_existing_pin_indices(self) -> None:
        self.assertEqual(maintenance.FILES[4], 'tools/linux/qualification/incus_profile_listener_fixture.py')
        self.assertEqual(maintenance.FILES[5], 'tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py')
        self.assertEqual(maintenance.FILES[6], 'documentation/handbook/05-development/workflow/issues/issue-449/workflow.md')
        self.assertEqual(maintenance.FILES[12], str(maintenance.fixture.WINDOWS_SNAPSHOT_REL))
        self.assertEqual(maintenance.FILES[13], str(maintenance.fixture.WINDOWS_CERTIFICATE_REL))
        source = 'a' * 40
        run = 'b' * 32
        profile, base_profile, instance = (f'tsw-q449-{run}-{suffix}' for suffix in ('profile', 'base', 'fixture'))
        static: dict[str, Any] = {
            'source_commit': source,
            'workflow_sha256': maintenance.digest((maintenance.ROOT / maintenance.FILES[6]).read_bytes()),
            'runner_sha256': maintenance.digest((maintenance.ROOT / maintenance.FILES[4]).read_bytes()),
            'test_sha256': maintenance.digest((maintenance.ROOT / maintenance.FILES[5]).read_bytes()),
            'windows_snapshot_sha256': maintenance.digest((maintenance.ROOT / maintenance.fixture.WINDOWS_SNAPSHOT_REL).read_bytes()),
            'windows_certificate_sha256': maintenance.digest((maintenance.ROOT / maintenance.fixture.WINDOWS_CERTIFICATE_REL).read_bytes()),
            'issue447_inventory_sha256': 'c' * 64,
            'target': {'host': maintenance.HOST, 'endpoint': 'unix://', 'project': 'default', 'server_version': '6.0.5',
                       'run_id': run, 'profile': profile, 'base_profile': base_profile, 'instance': instance,
                       'image_fingerprint': 'd' * 64},
            'proxy': {'listen': 'tcp:127.0.0.1:61000', 'connect': 'tcp:127.0.0.1:8080', 'bind': 'host'},
            'cleanup': [instance, profile, base_profile],
            'reviews': dict.fromkeys(maintenance.fixture.REVIEW_KEYS, 'APPROVED'),
            'windows_rules_unchanged': True, 'external_routes_enabled': False,
            'default_profile_sha256': 'e' * 64, 'fixture_base_profile_sha256': 'f' * 64,
            'default_profile_used_by': [],
        }
        intent: dict[str, Any] = {'schema_version': 1, 'decision': 'INTENT_ONLY', 'fixture': static,
                  'provider_config_sha256': '0' * 64}
        self.assertEqual(maintenance.validate_fixture_intent(intent, source), intent)
        for field in ('windows_snapshot_sha256', 'windows_certificate_sha256'):
            for field_value in (None, '0' * 64):
                forged = copy.deepcopy(intent)
                if field_value is None:
                    del forged['fixture'][field]
                else:
                    forged['fixture'][field] = field_value
                with self.subTest(field=field, field_value=field_value), self.assertRaises((maintenance.MaintenanceError, maintenance.fixture.FixtureError)):
                    maintenance.validate_fixture_intent(forged, source)



class OwnedTransitionObservationTests(unittest.TestCase):
    def port(self) -> maintenance.NativePort:
        port = maintenance.NativePort('a' * 40, 'b' * 64, time.monotonic() + 600)
        port.baseline = baseline()
        return port

    @staticmethod
    def row(active: str, sub: str, pid: str = '0') -> bytes:
        return (f'LoadState=loaded\nActiveState={active}\nSubState={sub}\n'
                f'UnitFileState=enabled\nMainPID={pid}\n').encode()

    def test_own_shutdown_real_runner_parser_waits_for_strict_inactive_and_full_binding(self) -> None:
        port = self.port()
        port._shutdown_attempted = True
        rows = [self.row('deactivating', 'stop-sigterm', '17'), self.row('inactive', 'dead')]
        processes: list[subprocess.Popen[bytes]] = []
        original_popen = subprocess.Popen
        original_runner = maintenance.inventory.Runner
        def popen(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
            self.assertEqual(argv[:3], ['/usr/bin/systemctl', 'show', maintenance.DAEMON])
            raw = rows.pop(0)
            process = original_popen([sys.executable, '-c', 'import os; os.write(1, ' + repr(raw) + ')'], **kwargs)
            processes.append(process)
            assert process.stdout is not None and process.stderr is not None
            self.addCleanup(process.stdout.close)
            self.addCleanup(process.stderr.close)
            return process
        with (patch.object(port, '_stable_environment') as environment,
              patch.object(port, 'check_binding') as binding,
              patch.object(maintenance.inventory, 'Runner', side_effect=lambda: original_runner(popen=popen)),
              patch.object(port, 'command') as effects):
            port.wait_inactive()
        self.assertEqual(environment.call_count, 2)
        binding.assert_called_once_with(port.baseline, active=False)
        effects.assert_not_called()
        self.assertEqual(len(processes), 2)
        self.assertTrue(all(process.poll() is not None for process in processes))
        self.assertIsNone(port._read_deadline)

    def test_no_shutdown_attempt_or_malformed_stable_state_is_never_pending_authority(self) -> None:
        port = self.port()
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'SHUTDOWN_WAIT_NOT_ADMITTED'):
            port.wait_inactive()
        port._shutdown_attempted = True
        for error in (maintenance.inventory.InventoryError('UNIT_SCHEMA_INVALID'),
                      maintenance.inventory.InventoryError('UNIT_VALUE_INVALID'),
                      maintenance.MaintenanceError('UNIT_LOAD_DRIFT'),
                      maintenance.MaintenanceError('UNIT_TRANSITION_UNCERTAIN')):
            with (self.subTest(reason=str(error)), patch.object(port, '_stable_environment'),
                  patch.object(port, 'unit', side_effect=error) as unit,
                  patch.object(port, 'check_binding') as binding, patch.object(port, 'command') as effects):
                with self.assertRaises(type(error)):
                    port.wait_inactive()
                unit.assert_called_once_with(maintenance.DAEMON)
                binding.assert_not_called()
                effects.assert_not_called()

    def test_forever_unknown_shutdown_times_out_without_classifying_inactive_or_effect(self) -> None:
        port = self.port()
        port.deadline = 600
        port._shutdown_attempted = True
        clock = {'now': 10.0}
        def sleep(_seconds: float) -> None:
            clock['now'] += 10
        with (patch.object(maintenance.time, 'monotonic', side_effect=lambda: clock['now']),
              patch.object(maintenance.time, 'sleep', side_effect=sleep),
              patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)),
              patch.object(maintenance.signal, 'signal'), patch.object(maintenance.signal, 'setitimer') as timer,
              patch.object(port, '_stable_environment') as environment,
              patch.object(port, 'unit', side_effect=maintenance.inventory.InventoryError('UNIT_STATE_BLOCKED')),
              patch.object(port, 'check_binding') as binding, patch.object(port, 'command') as effects):
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'SHUTDOWN_OUTCOME_UNCERTAIN'):
                port.wait_inactive()
        self.assertEqual(environment.call_count, 3)
        binding.assert_not_called()
        effects.assert_not_called()
        self.assertEqual(timer.call_args_list[0].args, (maintenance.signal.ITIMER_REAL, 25))
        self.assertEqual(timer.call_args_list[-1].args, (maintenance.signal.ITIMER_REAL, 0))
        self.assertIsNone(port._read_deadline)

    def test_recovery_first_state_reconciles_pending_shutdown_without_starting_anything(self) -> None:
        port = self.port()
        port.recovering = True
        with (patch.object(port, '_stable_environment'),
              patch.object(port, 'unit', side_effect=[maintenance.inventory.InventoryError('UNIT_STATE_BLOCKED'), 'inactive']),
              patch.object(port, 'check_binding') as binding,
              patch.object(port, 'ready_binding') as ready, patch.object(port, 'command') as effects):
            self.assertEqual(port.recovery_state(transition_owned=True, start_owned=False), 'inactive')
        binding.assert_called_once_with(port.baseline, active=False)
        ready.assert_not_called()
        effects.assert_not_called()
        with (patch.object(port, '_stable_environment'),
              patch.object(port, 'unit', side_effect=maintenance.inventory.InventoryError('UNIT_STATE_BLOCKED')) as unit):
            with self.assertRaisesRegex(maintenance.inventory.InventoryError, 'UNIT_STATE_BLOCKED'):
                port.recovery_state(transition_owned=False, start_owned=False)
            unit.assert_called_once()

    def test_own_start_provenance_classes_require_subsequent_full_proof_not_a_successful_exception(self) -> None:
        for reason in ('SNAP_WRAPPER_FILE_UNVERIFIED', 'SNAP_WRAPPER_PROC_INVALID', 'SNAP_WRAPPER_CHILD_ABSENT'):
            port = self.port()
            port.recovering = True
            with (self.subTest(reason=reason), patch.object(port, '_stable_environment'),
                  patch.object(port, 'unit', return_value='active'),
                  patch.object(port, 'ready_binding', side_effect=[maintenance.provenance.ProvenanceError(reason), None]) as ready,
                  patch.object(port, 'command') as effects):
                self.assertEqual(port.recovery_state(transition_owned=True, start_owned=True), 'active')
                self.assertEqual(ready.call_count, 2)
                effects.assert_not_called()
            port = self.port()
            port.recovering = True
            with (patch.object(port, 'ready_binding', side_effect=maintenance.provenance.ProvenanceError(reason)) as ready,
                  patch.object(port, 'command') as effects):
                with self.assertRaises(maintenance.provenance.ProvenanceError):
                    port.wait_ready()
                ready.assert_called_once()
                effects.assert_not_called()

    def test_known_binding_mismatch_and_other_provenance_codes_are_fatal_even_after_own_start(self) -> None:
        failures = (maintenance.MaintenanceError('INSTALLED_BINDING_DRIFT'),
                    maintenance.MaintenanceError('INCUS_SOCKET_DRIFT'), maintenance.MaintenanceError('LXD_API_AUTHORITY_DRIFT'),
                    maintenance.provenance.ProvenanceError('SNAP_WRAPPER_DRIFT'),
                    maintenance.provenance.ProvenanceError('SNAP_WRAPPER_CONTEXT_BLOCKED'))
        for failure in failures:
            port = self.port()
            port.recovering = port._owned_start = True
            with (self.subTest(reason=str(failure)), patch.object(port, 'ready_binding', side_effect=failure) as ready,
                  patch.object(port, 'command') as effects):
                with self.assertRaises(type(failure)):
                    port.wait_ready()
                ready.assert_called_once()
                effects.assert_not_called()

    def test_persistent_file_unknown_cannot_pass_or_start_nodes_and_timer_restores(self) -> None:
        port = self.port()
        port.deadline = 600
        port.recovering = port._owned_start = True
        clock = {'now': 10.0}
        def sleep(_seconds: float) -> None:
            clock['now'] += 10
        with (patch.object(maintenance.time, 'monotonic', side_effect=lambda: clock['now']),
              patch.object(maintenance.time, 'sleep', side_effect=sleep),
              patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)),
              patch.object(maintenance.signal, 'signal') as handler, patch.object(maintenance.signal, 'setitimer') as timer,
              patch.object(port, 'ready_binding', side_effect=maintenance.provenance.ProvenanceError('SNAP_WRAPPER_FILE_UNVERIFIED')),
              patch.object(port, 'start_node') as nodes):
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'LXD_READINESS_TIMEOUT'):
                port.wait_ready()
        nodes.assert_not_called()
        self.assertEqual(timer.call_args_list[-1].args, (maintenance.signal.ITIMER_REAL, 0))
        self.assertEqual(handler.call_args_list[-1].args[0], maintenance.signal.SIGALRM)
        self.assertIsNone(port._read_deadline)

    def test_actual_runner_hanging_unit_reader_is_reaped_before_shutdown_wait_returns(self) -> None:
        port = self.port()
        port._shutdown_attempted = True
        original_popen = subprocess.Popen
        original_runner = maintenance.inventory.Runner
        original_selector = maintenance.inventory.selectors.DefaultSelector
        processes: list[subprocess.Popen[bytes]] = []
        handlers: list[Any] = []
        test = self
        class InterruptingSelector:
            def __init__(self) -> None:
                self.selector = original_selector()
                test.addCleanup(self.selector.close)
            def register(self, *args: Any, **kwargs: Any) -> Any:
                return self.selector.register(*args, **kwargs)
            def unregister(self, *args: Any, **kwargs: Any) -> Any:
                return self.selector.unregister(*args, **kwargs)
            def get_map(self) -> Any:
                return self.selector.get_map()
            def close(self) -> None:
                self.selector.close()
            def select(self, timeout: float | None = None) -> Any:
                handlers[0](maintenance.signal.SIGALRM, None)
                return []
        def popen(_argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
            process = original_popen([sys.executable, '-c', 'import time; time.sleep(60)'], **kwargs)
            processes.append(process)
            assert process.stdout is not None and process.stderr is not None
            self.addCleanup(process.stdout.close)
            self.addCleanup(process.stderr.close)
            return process
        started = time.monotonic()
        with (patch.object(port, '_stable_environment'),
              patch.object(maintenance.inventory, 'Runner', side_effect=lambda: original_runner(popen=popen)),
              patch.object(maintenance.inventory.selectors, 'DefaultSelector', InterruptingSelector),
              patch.object(maintenance.signal, 'getitimer', return_value=(0.0, 0.0)),
              patch.object(maintenance.signal, 'signal', side_effect=lambda _s, handler: handlers.append(handler)),
              patch.object(maintenance.signal, 'setitimer') as timer,
              patch.object(port, 'command') as effects):
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'SHUTDOWN_OUTCOME_UNCERTAIN'):
                port.wait_inactive()
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(timer.call_args_list[0].args, (maintenance.signal.ITIMER_REAL, 25))
        self.assertEqual(timer.call_args_list[-1].args, (maintenance.signal.ITIMER_REAL, 0))
        self.assertIsNone(port._read_deadline)
        effects.assert_not_called()

    def test_read_window_clips_only_fixed_read_command_and_cannot_reduce_effect_timeouts(self) -> None:
        port = self.port()
        port.deadline = 1000
        port._read_deadline = 10.75
        with patch.object(maintenance.time, 'monotonic', return_value=10), patch.object(maintenance, 'bounded', return_value=b'') as bounded:
            port.command(list(maintenance.READ_STOP_METADATA), 10)
            self.assertEqual(bounded.call_args.args[1], .75)
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'READ_WINDOW_EFFECT_BLOCKED'):
                port.command(['/usr/bin/systemctl', 'start', maintenance.DAEMON], 90)
            self.assertEqual(bounded.call_count, 1)
            port._read_deadline = None
            port.command(['/usr/bin/systemctl', 'start', maintenance.DAEMON], 90)
            self.assertEqual(bounded.call_args.args[1], 90)

    def test_transaction_waits_for_full_reconciliation_before_one_owned_start(self) -> None:
        saved = baseline()
        fake = FakePort(saved)
        fake.daemon = 'inactive'
        events = Events(fake)
        events.event('shutdown')
        observed = self.port()
        observed.recovering = True
        def reconcile(*, transition_owned: bool, start_owned: bool) -> str:
            self.assertEqual(fake.calls, [])
            self.assertTrue(transition_owned)
            self.assertFalse(start_owned)
            return observed.recovery_state(transition_owned=transition_owned, start_owned=start_owned)
        with (patch.object(fake, 'recovery_state', side_effect=reconcile),
              patch.object(observed, '_stable_environment'),
              patch.object(observed, 'unit', side_effect=[maintenance.inventory.InventoryError('UNIT_STATE_BLOCKED'), 'inactive']),
              patch.object(observed, 'check_binding') as binding):
            maintenance.Transaction(fake, events, saved).recover()
        binding.assert_called_once_with(observed.baseline, active=False)
        self.assertEqual(fake.calls, [('start-daemon', '')])
        self.assertEqual(events.transition_intents(), {'shutdown', 'start-daemon'})

    def test_private_journal_derives_only_valid_owned_transition_intents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            with patch.object(maintenance, 'private_directory'):
                journal = maintenance.Journal(root)
            journal.event('stop-node', maintenance.NODES[0])
            journal.event('shutdown')
            journal.event('start-daemon')
            self.assertEqual(journal.stopped_nodes(), {maintenance.NODES[0]})
            self.assertEqual(journal.transition_intents(), {'shutdown', 'start-daemon'})
            journal.save('event-foreign.json', {'intent': 'start-daemon', 'node': maintenance.NODES[0], 'utc': 'fixed'})
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'JOURNAL_EVENT_INVALID'):
                journal.transition_intents()
        self.assertEqual(maintenance.failure_reason(maintenance.provenance.ProvenanceError('SNAP_WRAPPER_FILE_UNVERIFIED')),
                         'SNAP_WRAPPER_FILE_UNVERIFIED')
        normalized = maintenance.provenance.ProvenanceError('private value/address')
        self.assertEqual(maintenance.failure_reason(normalized), 'SNAP_WRAPPER_FILE_UNVERIFIED')
        normalized.args = ('private value/address',)
        self.assertEqual(maintenance.failure_reason(normalized), 'UNCLASSIFIED_FAILURE_REDACTED')



class CausalWrapperReadinessTests(unittest.TestCase):
    def test_real_inventory_wrapper_must_be_followed_by_full_original_binding(self) -> None:
        for reason in ('SNAP_WRAPPER_FILE_UNVERIFIED', 'SNAP_WRAPPER_PROC_INVALID', 'SNAP_WRAPPER_CHILD_ABSENT'):
            port = maintenance.NativePort('a' * 40, 'b' * 64, time.monotonic() + 600)
            saved = baseline()
            expected = {'server_version': '5.21.9', 'server_lts': False}
            saved['preserve']['lxd_admission'] = {'initial': expected}
            port.baseline = saved
            port.recovering = port._owned_start = True
            calls = [0]
            def binding(_baseline, *, active):
                self.assertTrue(active)
                calls[0] += 1
                if calls[0] == 1:
                    maintenance.inventory._resolve_executable(Mock(), {'unit': maintenance.DAEMON, 'main_pid': 17})
            with self.subTest(reason=reason), patch.object(port, 'check_binding', side_effect=binding), \
                    patch.object(maintenance.inventory, '_read_executable_path', return_value='/usr/bin/snap'), \
                    patch.object(maintenance.provenance, 'prove_snap_wrapper', side_effect=maintenance.provenance.ProvenanceError(reason)), \
                    patch.object(maintenance.inventory, '_read_server_root', return_value=expected) as root, \
                    patch.object(port, 'command') as effects, patch.object(maintenance.time, 'sleep'):
                port.wait_ready()
            self.assertEqual(calls[0], 3)
            root.assert_called_once()
            effects.assert_not_called()

    def test_same_text_without_exact_direct_cause_and_own_start_is_never_retryable(self) -> None:
        for reason in ('SNAP_WRAPPER_FILE_UNVERIFIED', 'SNAP_WRAPPER_PROC_INVALID', 'SNAP_WRAPPER_CHILD_ABSENT'):
            for owner, cause in ((False, maintenance.provenance.ProvenanceError(reason)),
                                 (True, None), (True, RuntimeError(reason)),
                                 (True, maintenance.provenance.ProvenanceError('SNAP_WRAPPER_CONTEXT_BLOCKED'))):
                port = maintenance.NativePort('a' * 40, 'b' * 64, time.monotonic() + 600)
                port.baseline = baseline()
                port.recovering = True
                port._owned_start = owner
                error = maintenance.inventory.InventoryError(reason)
                error.__cause__ = cause
                with self.subTest(reason=reason, owner=owner, cause=type(cause).__name__), \
                        patch.object(port, 'ready_binding', side_effect=error) as ready, \
                        patch.object(port, 'command') as effects:
                    with self.assertRaises(maintenance.inventory.InventoryError):
                        port.wait_ready()
                ready.assert_called_once()
                effects.assert_not_called()

    def test_recovery_state_retries_only_the_same_causal_provenance_proof(self) -> None:
        port = maintenance.NativePort('a' * 40, 'b' * 64, time.monotonic() + 600)
        port.baseline = baseline()
        port.recovering = True
        with patch.object(port, '_stable_environment'), patch.object(port, 'unit', return_value='active'), \
                patch.object(port, 'ready_binding', side_effect=[wrapped_provenance('SNAP_WRAPPER_FILE_UNVERIFIED'), None]) as ready, \
                patch.object(maintenance.time, 'sleep'), patch.object(port, 'command') as effects:
            self.assertEqual(port.recovery_state(transition_owned=True, start_owned=True), 'active')
        self.assertEqual(ready.call_count, 2)
        effects.assert_not_called()

if __name__ == '__main__':
    unittest.main()

"""Exact association of protected public CLI receipts without running a workload."""
from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import io
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from modules.tsw_core.tests.e2e.classic import run_lcm_acceptance as report

upgrades = report.upgrades
wsl = report.wsl

RUN = 'a' * 32
SOURCE = 'b' * 40
CASE = 'minimal'
T0 = datetime(2026, 11, 10, tzinfo=timezone.utc)
DIGEST = 'c' * 64


class Campaign:
    def __init__(self):
        self.intent = wsl.Intent(
            RUN, CASE, SOURCE, DIGEST, DIGEST, '{11111111-1111-1111-1111-111111111111}',
            DIGEST, 'windows-pc', 'A' * 64, DIGEST, DIGEST, DIGEST, DIGEST, DIGEST,
        )
        self.home = wsl.BASE / RUN / 'cases' / CASE
        self.journal = self.home / 'journal'
        self.key = 'child-' + 'e' * 32
        self.data: dict[Path, dict] = {}
        self.data[self.home / 'intent.json'] = asdict(self.intent)
        self.proposal = {'intent_sha256': upgrades.digest(asdict(self.intent)),
                         'identity': {'host': 'private-host'}, 'baseline': {'routes': []},
                         'pins': {report.ACTIVE_WORKFLOW: '1' * 64, upgrades.CLI_MAIN: '2' * 64,
                                  upgrades.CLI_RELEASE: '3' * 64}}
        self.put('proposal.json', self.proposal)
        budgets = upgrades.budgets(CASE, 'wsl')
        reserved = sum(budgets[key] for key in ('admit', 'case', 'disposal', 'final'))
        go = {'decision': 'GO', 'schema_version': 1, 'phase': 'wsl-case-run',
              'source_commit': SOURCE, 'proposal_sha256': upgrades.digest(self.proposal),
              'intent_sha256': self.proposal['intent_sha256'], 'pins': self.proposal['pins'],
              'budgets': budgets, 'expires_at_utc': self.at(reserved + 60),
              'reviews': dict.fromkeys(wsl.REVIEWS, 'APPROVED')}
        self.data[self.home / 'run-go.json'] = go
        self.go_sha = upgrades.digest(go)
        args = report.suite.CASE_RECIPES[CASE].args()
        executable = str(self.intent.checkout / '.venv/bin/python')
        argv = [executable, '-E', '-s', '-B', '-c', upgrades.CLI_BOOTSTRAP, *args]
        identity = {'pid': 200, 'start_time': 220}
        self.start = {'schema_version': 1, 'platform': 'wsl', 'case': CASE, 'run_id': RUN,
                      'source_commit': SOURCE, 'workflow_sha256': '1' * 64, 'entrypoint_sha256': '2' * 64,
                      'release_sha256': '3' * 64, 'proposal_sha256': upgrades.digest(self.proposal),
                      'before_sha256': upgrades.digest(self.proposal['baseline']),
                      'host_sha256': upgrades.digest(self.proposal['identity']),
                      'approval': {'phase': go['phase'], 'sha256': self.go_sha, 'accepted_at': self.at(0)},
                      'activation': None, 'incus_client': '6.0.5', 'incus_server': '6.0.5',
                      'package_version': '0.2.0',
                      'argv_sha256': upgrades.digest(argv), 'args': args, 'effect': True,
                      'executable': executable, 'executable_sha256': DIGEST,
                      'parent': {'pid': 190, 'start_time': 120}, 'child': identity,
                      'started_at': self.at(5), 'started_monotonic_ns': 100}
        self.child('cli-start', self.start)
        self.child('pid', identity.copy())
        self.child('intent', {'argv_sha256': self.start['argv_sha256'], 'timeout': 20, 'public': True})
        self.child('cli-released', {'released_at': self.at(6), 'released_monotonic_ns': 200})
        outcome = {'return_code': 0, 'stdout_sha256': DIGEST, 'stderr_sha256': DIGEST}
        self.child('outcome', outcome)
        self.child('settled', {'pid': 200, 'released': True, 'group_absent': True})
        self.settled = outcome | {'pid': 200, 'released': True, 'group_absent': True,
                                  'output_complete': True, 'fault': None,
                                  'settled_at': self.at(7), 'settled_monotonic_ns': 300}
        self.child('cli-settled', self.settled)
        result = {'status': 'CASE_PASS_DISPOSED', 'run_id': RUN, 'case': CASE, 'source_commit': SOURCE}
        self.put('outcome-' + 'f' * 32 + '.json', result)
        self.finished = {'schema_version': 1, 'case': CASE, 'run_id': RUN, 'source_commit': SOURCE,
                         'approval_sha256': self.go_sha, 'before_sha256': self.start['before_sha256'],
                         'after_sha256': upgrades.digest(self.proposal['baseline']), 'result_sha256': upgrades.digest(result),
                         'selection': {'requested': [], 'resolved': ['incus'], 'product_release': '0.2.0',
                                       'product_revision': SOURCE, 'manifest_sha256': DIGEST},
                         'finished_at': self.at(8), 'finished_monotonic_ns': 400}
        self.put('cli-result-' + self.go_sha + '.json', self.finished)
        self.put('cli-after-' + self.go_sha + '.json', self.proposal['baseline'].copy())

    @staticmethod
    def at(seconds: int) -> str:
        return (T0 + timedelta(seconds=seconds)).isoformat()

    def put(self, name: str, value: dict) -> None:
        self.data[self.journal / name] = value

    def child(self, suffix: str, value: dict) -> None:
        self.put(self.key + '-' + suffix + '.json', value)

    def read(self, path: Path):
        if path not in self.data:
            raise FileNotFoundError
        value = self.data[path]
        return value, upgrades.digest(value)

    def records(self, directory, pattern):
        for path in self.data:
            if path.parent == directory and (match := pattern.fullmatch(path.name)) is not None:
                yield match, self.read(path)

    def invoke(self):
        out = io.StringIO()
        with redirect_stdout(out), patch.object(report, 'private_directory'), patch.object(report, 'record', self.read), \
                patch.object(report, 'records', self.records), patch.object(subprocess, 'Popen', side_effect=AssertionError):
            result = report.main(['report', '--platform', 'wsl', '--case', CASE, '--run-id', RUN,
                                  '--expected-go-sha256', self.go_sha])
        return result, out.getvalue()


class AttributionTests(unittest.TestCase):
    def test_historical_valid_go_uses_acceptance_time_and_reports_digests_only(self):
        result, out = Campaign().invoke()
        self.assertEqual(result, 0)
        self.assertIn('"status":"ATTRIBUTED"', out)
        self.assertIn('"effects":1', out)
        self.assertIn('"package_version":"0.2.0"', out)
        self.assertIn('"resolved":["incus"]', out)
        self.assertNotIn('private-host', out)
        self.assertNotIn('bin/python', out)

    def test_refuses_unattributed_legacy_missing_release_and_changed_child_pid(self):
        for suffix in ('cli-start', 'cli-released', 'pid', 'cli-settled', 'settled', 'outcome'):
            campaign = Campaign()
            with self.subTest(suffix=suffix):
                del campaign.data[campaign.journal / (campaign.key + '-' + suffix + '.json')]
                self.assertEqual(campaign.invoke(), (2, '{"status":"INCOMPLETE","epic_complete":false}\n'))
        campaign = Campaign()
        campaign.child('pid', {'pid': 201, 'start_time': 220})
        self.assertEqual(campaign.invoke()[0], 2)

    def test_changed_source_command_or_go_is_incomplete(self):
        for field, value in (('workflow_sha256', DIGEST), ('source_commit', 'f' * 40),
                             ('executable', '/tmp/private-canary'), ('args', ['setup', 'run'])):
            campaign = Campaign()
            campaign.start[field] = value
            with self.subTest(field=field):
                result, output = campaign.invoke()
                self.assertEqual(result, 2)
                self.assertNotIn('private-canary', output)
        campaign = Campaign()
        campaign.data[campaign.home / 'run-go.json']['decision'] = 'DENY'
        self.assertEqual(campaign.invoke()[0], 2)

    def test_lost_acknowledgement_does_not_become_a_completed_effect(self):
        campaign = Campaign()
        campaign.settled['output_complete'] = False
        self.assertEqual(campaign.invoke()[0], 2)

    def test_report_rechecks_durable_after_observation(self):
        campaign = Campaign()
        after = {'routes': ['unexpected']}
        campaign.put('cli-after-' + campaign.go_sha + '.json', after)
        campaign.finished['after_sha256'] = upgrades.digest(after)
        self.assertEqual(campaign.invoke()[0], 2)

    def test_live_argv_needs_the_phase_specific_approval_before_release(self):
        campaign = Campaign()
        binding = {'platform': 'native', 'proposal_sha256': DIGEST,
                   'approval': {'phase': 'native-product-maintenance'}, 'activation': None}
        receipt = upgrades.CliReceipt(Mock(), campaign.key, binding, [], campaign.start['args'])
        with self.assertRaisesRegex(upgrades.UpgradeError, 'CASE_CLI_GO_REQUIRED'):
            receipt.require_approval()
        binding['activation'] = {'phase': 'paused-product-case'}
        receipt.require_approval()
        binding['platform'] = 'wsl'
        with self.assertRaisesRegex(upgrades.UpgradeError, 'CASE_CLI_GO_REQUIRED'):
            receipt.require_approval()
        binding.update(approval={'phase': 'wsl-case-run'}, activation=None)
        receipt.require_approval()

    def test_fault_requires_the_owned_child_and_protected_checkpoint_receipt(self):
        campaign = Campaign()
        campaign.settled.update(return_code=-15, output_complete=False, fault={
            'checkpoint_sha256': DIGEST, 'predicate': 'PARTIAL_BATCH', 'process_group': 200, 'signal': 15,
            'sent_at': campaign.at(6), 'sent_monotonic_ns': 250,
        })
        campaign.put('upgrade-fault-intent-' + 'f' * 32 + '.json', {'checkpoint_sha256': DIGEST,
            'predicate': 'PARTIAL_BATCH', 'run_id': RUN, 'case': CASE, 'source_commit': SOURCE})
        campaign.child('cli-fault-intent', {'checkpoint_sha256': DIGEST, 'predicate': 'PARTIAL_BATCH',
            'process_group': 200, 'signal': 15, 'process': campaign.start['child'],
            'prepared_at': campaign.at(6), 'prepared_monotonic_ns': 230})
        with patch.object(report, 'record', campaign.read), patch.object(report, 'records', campaign.records):
            self.assertIs(report.validate_child(campaign.journal, campaign.key, campaign.start,
                campaign.start['args'], 'PARTIAL_BATCH', T0, T0 + timedelta(minutes=2), campaign.finished), campaign.settled)
            for wrong_code in (0, 1, -9):
                campaign.settled['return_code'] = wrong_code
                with self.subTest(return_code=wrong_code), self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
                    report.validate_child(campaign.journal, campaign.key, campaign.start, campaign.start['args'],
                        'PARTIAL_BATCH', T0, T0 + timedelta(minutes=2), campaign.finished)
            campaign.settled['return_code'] = -15
            campaign.settled['fault']['process_group'] = 201
            with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
                report.validate_child(campaign.journal, campaign.key, campaign.start, campaign.start['args'],
                    'PARTIAL_BATCH', T0, T0 + timedelta(minutes=2), campaign.finished)

    def test_argument_refusal_redacts_invalid_values(self):
        out = io.StringIO()
        with redirect_stdout(out):
            result = report.main(['report', '--platform', 'private-canary'])
        self.assertEqual(result, 2)
        self.assertNotIn('private-canary', out.getvalue())

    def test_exact_pair_does_not_infer_client_from_server(self):
        self.assertEqual(upgrades.cli_incus_versions(b'Client version: 6.0.4\nServer version: 6.0.5\n'), ('6.0.4', '6.0.5'))
        with self.assertRaisesRegex(upgrades.UpgradeError, 'CASE_CLI_INCUS_VERSION_INVALID'):
            upgrades.cli_incus_versions(b'Server version: 6.0.5\n')

    def test_failed_signal_has_no_observed_fault_receipt(self):
        port = SimpleNamespace(intent=SimpleNamespace(case='recover-portainer'), upgrade_fault_armed=True,
                               upgrade_fault_observed=False, upgrade_before={'installation_id': 'owned'},
                               event=Mock())
        checkpoint = SimpleNamespace(installation_id='owned', stage='backed_up', backup_digest=DIGEST,
                                     model_dump=Mock(return_value={'stage': 'backed_up'}))
        child = SimpleNamespace(pid=200, poll=lambda: None)
        with patch.object(upgrades, 'checkpoint', return_value=checkpoint), \
                patch.object(upgrades.os, 'killpg', side_effect=ProcessLookupError):
            with self.assertRaises(ProcessLookupError):
                upgrades.poll_fault(port, child)
        self.assertFalse(port.upgrade_fault_observed)

    def test_native_recovered_engine_uses_successful_supervisor_exit(self):
        self.assertEqual(report.suite.case_exit_status('ENGINE_RECOVERED_DISPOSED'), 0)
        self.assertEqual(report.suite.case_exit_status('QUALIFICATION_FAILED_RECOVERED'), 2)

    def test_native_bound_read_uses_the_exact_inventory_environment(self):
        socket = {'unit': 'incus.socket', 'load_state': 'loaded', 'active_state': 'active',
                  'sub_state': 'listening', 'unit_file_state': 'enabled', 'main_pid': 0, 'listen': 'incus_run'}
        baseline = {'preserve': {'incus_units': [socket]}}
        env = report.suite.SuiteNativePort.incus_env(baseline)
        launch = Mock(side_effect=OSError)
        runner = report.native.inventory.Runner(popen=launch)
        with self.assertRaises(report.native.inventory.InventoryError):
            runner.run(['/usr/bin/incus', '--force-local', 'version'], env=env,
                       command_id='suite_cli_incus_version', safe_args=[])
        launch.assert_called_once()
        self.assertEqual(launch.call_args.kwargs['env'],
                         {'LC_ALL': 'C', 'PATH': '/usr/bin:/bin', 'INCUS_SOCKET': '/run/incus/unix.socket'})


class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.campaign = Campaign()
        self.campaign.data.clear()
        self.journal = SimpleNamespace(directory=self.campaign.journal, save=self.campaign.put)
        self.proposal = self.campaign.proposal | {'host_id_sha256': DIGEST}
        self.args = self.campaign.start['args']
        self.body = "print('harmless-worker')"
        self.executable = '/usr/bin/python3'
        self.argv = [self.executable, '-E', '-s', '-B', '-c', self.body, *self.args]

    def verify_receipts(self):
        [(match, (start, _))] = self.campaign.records(self.campaign.journal, report.START_FILE)
        finish = {'finished_at': upgrades.utc_stamp(), 'finished_monotonic_ns': time.monotonic_ns()}
        accepted = datetime.now(timezone.utc) - timedelta(minutes=1)
        with patch.object(report, 'record', self.campaign.read):
            result = report.validate_child(self.campaign.journal, match.group(1), start, self.args, None,
                                           accepted, accepted + timedelta(minutes=2), finish)
        self.assertEqual(result['return_code'], 0)
        self.assertTrue(result['output_complete'])

    def test_native_producer_and_reader_for_real_harmless_child(self):
        intent = report.suite.SuiteIntent(RUN, SOURCE, CASE, DIGEST, DIGEST, DIGEST, DIGEST, DIGEST)
        port = report.suite.SuiteNativePort(intent, self.journal, self.proposal)
        port.cli_approval = {'phase': 'native-product-maintenance'}
        port.cli_activation = {'phase': 'paused-product-case'}
        port.cli_versions = ('6.0.5', '6.0.5')
        with patch.object(upgrades, 'CLI_BOOTSTRAP', self.body), patch.object(port, 'interpreter', return_value=self.executable), \
                patch.object(report.suite, 'operator_values', return_value={}), \
                patch.object(report.suite, 'case_tls_root', return_value='/tmp'):
            self.assertEqual(port.child(self.argv, 3), b'harmless-worker\n')
            self.verify_receipts()

    def test_wsl_producer_and_reader_for_real_harmless_child(self):
        port = wsl.WslCasePort(self.campaign.intent, self.journal)
        port.proposal = self.proposal
        port.cli_approval = {'phase': 'wsl-case-run'}
        port.cli_versions = ('6.0.5', '6.0.5')
        with patch.object(upgrades, 'CLI_BOOTSTRAP', self.body), patch.object(port, 'interpreter', return_value=self.executable), \
                patch.object(port, 'operator_values', return_value={}), patch.object(port, 'tls_root', return_value='/tmp'), \
                patch.dict(os.environ, {}, clear=True):
            self.assertEqual(port.command(self.argv, 3, public=True), b'harmless-worker\n')
            self.verify_receipts()

    def test_armed_wsl_probe_cannot_signal_internal_child(self):
        port = wsl.WslCasePort(replace(self.campaign.intent, case='recover-batch-swarm'), self.journal)
        port.upgrade_fault_armed = True
        with patch.object(port, 'interpreter', return_value=self.executable), \
                patch.object(port, 'tls_root', return_value='/tmp'), patch.object(upgrades, 'poll_fault') as poll, \
                patch.dict(os.environ, {}, clear=True):
            self.assertEqual(port.command([self.executable, '-c', 'pass'], 3), b'')
        poll.assert_not_called()


if __name__ == '__main__':
    unittest.main()

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
from typing import Any, cast
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


def synthetic_refusal_inputs(root: Path, infra: Path) -> dict[str, Any]:
    """Explicitly synthetic private tree identities; no credential contents."""
    import copy
    regular = [1, 3, 0, 0o100644, 1, 1, 1, 1]
    directory = [1, 2, 0, 0o40700, 0, 1, 1, 2]
    operator = [1, 4, 0, 0o100600, 1, 1, 1, 1]
    official: dict[str, Any] = {'path': str(root / 'modules/tsw_core/infra'), 'metadata': {'root': directory,
        'members': {'config': directory, 'config/provider.yaml': regular}}, 'files': {'config/provider.yaml': 'a' * 64}}
    campaign = copy.deepcopy(official)
    campaign['path'] = str(infra)
    campaign['metadata']['members']['operator.env'] = operator
    campaign['files']['operator.env'] = 'f' * 64
    return {'schema_version': 1, 'official': official, 'campaign': campaign,
            'operator': {'path': str(infra / 'operator.env'), 'identity': operator, 'sha256': 'f' * 64}}


class Campaign:
    def __init__(self, case=CASE, configuration_sha=DIGEST):
        self.intent = wsl.Intent(
            RUN, case, SOURCE, DIGEST, DIGEST, '{11111111-1111-1111-1111-111111111111}',
            DIGEST, 'windows-pc', 'A' * 64, DIGEST, configuration_sha, DIGEST, DIGEST, DIGEST,
        )
        self.home = wsl.BASE / RUN / 'cases' / case
        self.journal = self.home / 'journal'
        self.key = 'child-' + 'e' * 32
        self.data: dict[Path, dict] = {}
        self.data[self.home / 'intent.json'] = asdict(self.intent)
        self.proposal = {'intent_sha256': upgrades.digest(asdict(self.intent)),
                         'identity': {'host': 'private-host'}, 'baseline': {'routes': []},
                         'pins': {report.ACTIVE_WORKFLOW: '1' * 64, upgrades.CLI_MAIN: '2' * 64,
                                  upgrades.CLI_RELEASE: '3' * 64}}
        self.put('proposal.json', self.proposal)
        budgets = upgrades.budgets(case, 'wsl')
        reserved = sum(budgets[key] for key in ('admit', 'case', 'disposal', 'final'))
        go = {'decision': 'GO', 'schema_version': 1, 'phase': 'wsl-case-run',
              'source_commit': SOURCE, 'proposal_sha256': upgrades.digest(self.proposal),
              'intent_sha256': self.proposal['intent_sha256'], 'pins': self.proposal['pins'],
              'budgets': budgets, 'expires_at_utc': self.at(reserved + 60),
              'reviews': dict.fromkeys(wsl.REVIEWS, 'APPROVED')}
        self.data[self.home / 'run-go.json'] = go
        self.go_sha = upgrades.digest(go)
        args = report.suite.CASE_RECIPES[case].args()
        executable = str(self.intent.checkout / '.venv/bin/python')
        argv = [executable, '-E', '-s', '-B', '-c', upgrades.CLI_BOOTSTRAP, *args]
        identity = {'pid': 200, 'start_time': 220}
        self.start = {'schema_version': 1, 'platform': 'wsl', 'case': case, 'run_id': RUN,
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
        result = {'status': 'CASE_PASS_DISPOSED', 'run_id': RUN, 'case': case, 'source_commit': SOURCE}
        self.put('outcome-' + 'f' * 32 + '.json', result)
        self.finished = {'schema_version': 1, 'case': case, 'run_id': RUN, 'source_commit': SOURCE,
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
            result = report.main(['report', '--platform', 'wsl', '--case', self.intent.case, '--run-id', RUN,
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





class NegativeCampaign(Campaign):
    def __init__(self, case='refuse-product-consent-n'):
        import base64
        import copy
        import json
        from modules.tsw_native_linux.tests.tools.test_product_upgrade_cases import proof
        input_state = synthetic_refusal_inputs(wsl.BASE / RUN / 'cases' / case / 'checkout', wsl.BASE / RUN / 'infra')
        configuration_sha = upgrades.digest(sorted(input_state['campaign']['files'].items()))
        super().__init__(case, configuration_sha=configuration_sha)
        self.refusal_key = 'child-' + 'd' * 32
        spec = upgrades.REFUSALS[case]
        start = copy.deepcopy(self.start)
        args = list(spec.args)
        start.update(args=args, effect=False, child={'pid': 201, 'start_time': 221},
            started_at=self.at(9), started_monotonic_ns=500,
            argv_sha256=upgrades.digest([start['executable'], '-E', '-s', '-B', '-c', upgrades.CLI_BOOTSTRAP, *args]))
        self.put(self.refusal_key + '-cli-start.json', start)
        self.put(self.refusal_key + '-pid.json', start['child'])
        self.put(self.refusal_key + '-intent.json', {'argv_sha256': start['argv_sha256'], 'timeout': 120, 'public': True})
        self.put(self.refusal_key + '-cli-released.json', {'released_at': self.at(10), 'released_monotonic_ns': 600})
        if spec.cause == 'CONSENT':
            from tiny_swarm_world.domain.preflight import LIVE_CONSENT_PROMPT
            output = (LIVE_CONSENT_PROMPT + ' ').encode() + json.dumps(
                {'status': 'refused', 'diagnostics': ['missing live confirmation']}, sort_keys=True).encode() + b'\n'
            error = b''
        elif spec.cause == 'TARGET_SYNTAX':
            output, error = b'', upgrades.parser_refusal(args)
        else:
            message = ('No matching product checkpoint; inspect the original target.' if spec.cause == 'CHECKPOINT_ABSENT'
                       else 'Installation inventory differs from actual source revision/lock/release; inspect explicit adoption.')
            output = json.dumps({'status': 'blocked', 'diagnostics': [message],
                'recovery': 'preserve source/checkpoint; use product upgrade --to 0.5.0 --recover --preview from management checkout'},
                sort_keys=True).encode() + b'\n'
            error = b''
        outcome = {'return_code': spec.exit_code, 'stdout_sha256': report.native.digest(output), 'stderr_sha256': report.native.digest(error)}
        settled = outcome | {'pid': 201, 'released': True, 'group_absent': True, 'output_complete': True,
                             'fault': None, 'settled_at': self.at(11), 'settled_monotonic_ns': 700}
        self.put(self.refusal_key + '-outcome.json', outcome)
        self.put(self.refusal_key + '-cli-settled.json', settled)
        self.put(self.refusal_key + '-settled.json', {'pid': 201, 'released': True, 'group_absent': True})
        extras = {'schema_version', 'argv_sha256', 'args', 'effect', 'executable', 'executable_sha256',
                  'parent', 'child', 'started_at', 'started_monotonic_ns'}
        binding = {name: start[name] for name in report.START_KEYS - extras}
        common = {'schema_version': 1, 'case': case, 'binding_sha256': upgrades.digest(binding),
                  'args_sha256': upgrades.digest(args), 'child': start['child']}
        self.put(self.refusal_key + '-cli-stdin.json', common | {'mode': spec.stdin_mode,
            'delivered_bytes': 2 if spec.stdin_mode == 'DECLINE_N' else 0, 'writer_closed': True, 'released': True,
            'delivered_monotonic_ns': 610, 'closed_monotonic_ns': 620,
            'environment': upgrades.expected_refusal_environment(case, self.intent.checkout, self.intent.home / 'infra', self.intent.home / 'infra/operator.env'),
            'inputs_sha256': upgrades.digest(input_state)})
        self.put(self.refusal_key + '-cli-refusal.json', common | outcome | {
            'stdout_base64': base64.b64encode(output).decode(), 'stderr_base64': base64.b64encode(error).decode(),
            'product_result': upgrades.validate_refusal(case, args, spec.exit_code, output, error),
            'command_executed': True, 'positive_upgrade': False})
        protected: dict[str, Any] = {'schema_version': 1, 'paths': {name: {'kind': 'absent'} for name in upgrades.PROTECTED_PATHS}}
        protected['paths']['installation/manifest.json'] = {'kind': 'regular',
            'identity': [1, 2, 0o100600, 0, 1, 1, 10, 10], 'sha256': DIGEST}
        runtime = proof() | {'manifest_schema': 2, 'manifest_sha256': DIGEST, 'manifest_token': DIGEST,
                             'selection': self.finished['selection'].copy()}
        binding = {'schema_version': 1, 'case': case, 'run_id': RUN, 'source_commit': SOURCE, 'root': str(self.intent.checkout)}
        self.put('product-refusal-before.json', binding | {'protected': protected, 'runtime': runtime, 'inputs': input_state, 'captured_monotonic_ns': 450})
        self.put('product-refusal-after.json', binding | {'protected': copy.deepcopy(protected), 'runtime': copy.deepcopy(runtime), 'inputs': copy.deepcopy(input_state), 'captured_monotonic_ns': 800})
        self.finished.update(finished_at=self.at(12), finished_monotonic_ns=900)


class NegativeAttributionTests(unittest.TestCase):
    def test_whole_report_attributes_all_closed_negative_cells_without_product_success(self):
        import json
        for case in upgrades.REFUSALS:
            with self.subTest(case=case):
                code, raw = NegativeCampaign(case).invoke()
                self.assertEqual(code, 0, raw)
                value = json.loads(raw)
                self.assertEqual(value['verification_kind'], 'PUBLIC_REFUSAL_PRESERVED')
                self.assertFalse(value['positive_upgrade'])
                self.assertFalse(value['recovery_performed'])
                self.assertEqual(value['effects'], 1)
                self.assertEqual(value['commands'], 2)
                self.assertEqual(value['stdin_mode'], upgrades.REFUSALS[case].stdin_mode)
                self.assertNotIn('protected', raw)

    def test_standalone_refusal_never_counts_without_settlement_input_and_preservation(self):
        for suffix in ('cli-settled', 'settled', 'pid', 'cli-released', 'cli-stdin', 'cli-refusal', 'outcome'):
            campaign = NegativeCampaign()
            del campaign.data[campaign.journal / (campaign.refusal_key + '-' + suffix + '.json')]
            with self.subTest(suffix=suffix):
                self.assertEqual(campaign.invoke()[0], 2)
        for name in ('product-refusal-before.json', 'product-refusal-after.json'):
            campaign = NegativeCampaign()
            del campaign.data[campaign.journal / name]
            with self.subTest(missing=name):
                self.assertEqual(campaign.invoke()[0], 2)

    def test_changed_input_child_source_status_or_protected_state_is_incomplete(self):
        for suffix, field, wrong in (
            ('cli-stdin', 'mode', 'EOF'), ('cli-stdin', 'delivered_bytes', 0), ('cli-stdin', 'writer_closed', False),
            ('cli-stdin', 'child', {'pid': 999, 'start_time': 1}), ('cli-refusal', 'binding_sha256', 'f' * 64),
            ('cli-refusal', 'product_result', {'status': 'completed', 'cause': 'CONSENT_DECLINED_N'}),
            ('cli-settled', 'output_complete', False), ('cli-settled', 'return_code', 0), ('settled', 'group_absent', False),
        ):
            campaign = NegativeCampaign()
            campaign.data[campaign.journal / (campaign.refusal_key + '-' + suffix + '.json')][field] = wrong
            with self.subTest(suffix=suffix, field=field):
                self.assertEqual(campaign.invoke()[0], 2)
        campaign = NegativeCampaign()
        campaign.data[campaign.journal / 'product-refusal-after.json']['protected']['paths']['product/inputs'] = {'kind': 'unreadable'}
        self.assertEqual(campaign.invoke()[0], 2)
        campaign = NegativeCampaign()
        campaign.data[campaign.journal / 'product-refusal-after.json']['root'] = '/other-source'
        self.assertEqual(campaign.invoke()[0], 2)
        for field in ('infra_mode', 'repository_root', 'infra_root', 'operator_file', 'campaign_infra_root'):
            campaign = NegativeCampaign('refuse-product-source')
            campaign.data[campaign.journal / (campaign.refusal_key + '-cli-stdin.json')]['environment'][field] = 'foreign'
            with self.subTest(environment=field):
                self.assertEqual(campaign.invoke()[0], 2)
        campaign = NegativeCampaign('refuse-product-source')
        campaign.data[campaign.journal / 'product-refusal-after.json']['inputs']['official']['files']['config/provider.yaml'] = '0' * 64
        self.assertEqual(campaign.invoke()[0], 2)

    def test_unavailable_product_helpers_cannot_be_reported_as_executed_negative_or_pass(self):
        for case in ('upgrade-product-v1', 'recover-product-v1'):
            campaign = Campaign()
            campaign.intent = replace(campaign.intent, case=case)
            self.assertEqual(campaign.invoke()[0], 2)


class FixtureExecutableOwner:
    """Inject only ownership for this explicitly synthetic executable boundary."""
    def __init__(self, info: os.stat_result):
        self._info = info

    @property
    def st_uid(self) -> int:
        return 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._info, name)


class ActualRefusalTransportTests(unittest.TestCase):
    def test_real_owned_public_children_bind_eof_and_n_on_both_transports(self):
        import sys
        from contextlib import ExitStack
        for platform in ('native', 'wsl'):
            for case in (name for name, spec in upgrades.REFUSALS.items() if spec.cause in {'CONSENT', 'TARGET_SYNTAX'}):
                with self.subTest(platform=platform, case=case), ExitStack() as stack:
                    campaign = Campaign(case)
                    campaign.data.clear()
                    journal = SimpleNamespace(directory=campaign.journal, save=campaign.put)
                    proposal = campaign.proposal | {'host_id_sha256': DIGEST}
                    if platform == 'native':
                        native_intent = report.suite.SuiteIntent(RUN, SOURCE, case, DIGEST, DIGEST, DIGEST, DIGEST, DIGEST)
                        port = cast(Any, report.suite.SuiteNativePort(native_intent, journal, proposal))
                        port.cli_approval = {'phase': 'native-product-maintenance', 'sha256': DIGEST, 'accepted_at': upgrades.utc_stamp()}
                        port.cli_activation = {'phase': 'paused-product-case'}
                        stack.enter_context(patch.object(report.suite, 'operator_values', return_value={}))
                        stack.enter_context(patch.object(report.suite, 'case_tls_root', return_value='/tmp'))
                        stack.enter_context(patch.object(report.suite, 'tree_digest', return_value=DIGEST))
                    else:
                        port = cast(Any, wsl.WslCasePort(campaign.intent, journal))
                        port.proposal = proposal
                        port.cli_approval = {'phase': 'wsl-case-run', 'sha256': DIGEST, 'accepted_at': upgrades.utc_stamp()}
                        stack.enter_context(patch.object(port, 'operator_values', return_value={}))
                        stack.enter_context(patch.object(port, 'tls_root', return_value='/tmp'))
                    port.cli_versions = ('6.0.5', '6.0.5')
                    stack.enter_context(patch.object(port, 'interpreter', return_value=sys.executable))
                    executable_info = Path(sys.executable).resolve(strict=True).stat()
                    actual_fstat = os.fstat
                    def fixture_executable_owner(fd):
                        info = actual_fstat(fd)
                        if (info.st_dev, info.st_ino) == (executable_info.st_dev, executable_info.st_ino):
                            return FixtureExecutableOwner(info)
                        return info
                    stack.enter_context(patch.object(upgrades.os, 'fstat', side_effect=fixture_executable_owner))
                    infra = report.suite.INFRA if platform == 'native' else campaign.intent.home / 'infra'
                    stack.enter_context(patch.object(port, 'refusal_inputs', return_value=synthetic_refusal_inputs(report.suite.ROOT, infra)))
                    stack.enter_context(patch.dict(os.environ, {}, clear=True))
                    args = list(upgrades.REFUSALS[case].args)
                    argv = [sys.executable, '-E', '-s', '-B', '-c', upgrades.CLI_BOOTSTRAP, *args]
                    if platform == 'native':
                        output = port.child(argv, 10, refusal_case=case)
                    else:
                        output = port.command(argv, 10, public=True, refusal_case=case)
                    self.assertTrue(port.worker_settled)
                    [(match, (start, _))] = campaign.records(campaign.journal, report.START_FILE)
                    release, _ = campaign.read(campaign.journal / (match.group(1) + '-cli-released.json'))
                    settled, _ = campaign.read(campaign.journal / (match.group(1) + '-cli-settled.json'))
                    with patch.object(report, 'record', campaign.read):
                        verified = report.verify_refusal_child(campaign.journal, match.group(1), start, release, settled)
                    self.assertEqual(verified['stdin_mode'], upgrades.REFUSALS[case].stdin_mode)
                    self.assertEqual(verified['cause'], 'TARGET_SYNTAX' if upgrades.REFUSALS[case].cause == 'TARGET_SYNTAX' else
                                     'CONSENT_DECLINED_N' if upgrades.REFUSALS[case].stdin_mode == 'DECLINE_N' else 'CONSENT_EOF')
                    self.assertEqual(report.native.digest(output), settled['stdout_sha256'])


if __name__ == '__main__':
    unittest.main()

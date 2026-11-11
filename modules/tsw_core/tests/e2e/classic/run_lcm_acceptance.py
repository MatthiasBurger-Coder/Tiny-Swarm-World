#!/usr/bin/env python3
"""Read protected lifecycle acceptance receipts. Product-v1 recipes are unavailable."""
from __future__ import annotations

import argparse
import base64
from dataclasses import asdict
from datetime import datetime
import os
from pathlib import Path
import re
import stat
from typing import Any, NoReturn

from modules.tsw_core.tools.linux.qualification import native_lxd_maintenance as native
from modules.tsw_core.tools.linux.qualification import preserving_product_acceptance as suite
from modules.tsw_core.tools.linux.qualification import product_upgrade_cases as upgrades
from modules.tsw_core.tools.linux.qualification import wsl_product_acceptance as wsl

ACTIVE_WORKFLOW = native.fixture.ACTIVE_WORKFLOW
START_FILE = re.compile(r'(child-[0-9a-f]{32})-cli-start\.json')
SERVICE_ID = re.compile(r'[a-z0-9][a-z0-9_.-]{0,99}\Z')
RESULT_FILE = {'native': re.compile(r'result-[0-9a-f]{32}\.json'),
               'wsl': re.compile(r'outcome-[0-9a-f]{32}\.json')}
START_KEYS = {'schema_version', 'platform', 'run_id', 'case', 'source_commit',
              'workflow_sha256', 'entrypoint_sha256', 'release_sha256', 'proposal_sha256',
              'before_sha256', 'host_sha256', 'approval', 'activation', 'incus_client', 'incus_server', 'package_version',
              'argv_sha256', 'args', 'effect', 'executable', 'executable_sha256', 'parent', 'child',
              'started_at', 'started_monotonic_ns'}
SETTLED_KEYS = {'pid', 'return_code', 'released', 'group_absent', 'output_complete',
                'stdout_sha256', 'stderr_sha256', 'fault', 'settled_at', 'settled_monotonic_ns'}
FINAL_KEYS = {'schema_version', 'case', 'run_id', 'source_commit', 'approval_sha256',
              'before_sha256', 'after_sha256', 'result_sha256', 'selection', 'finished_at', 'finished_monotonic_ns'}


def require(condition: Any) -> None:
    if not condition:
        raise ValueError('INCOMPLETE')


def fields(row: Any, keys: set[str]) -> dict[str, Any]:
    require(type(row) is dict and set(row) == keys)
    return row


def sha(value: Any) -> str:
    require(type(value) is str and native.HEX.fullmatch(value))
    return value


def time_value(value: Any) -> datetime:
    require(type(value) is str and len(value) <= 40)
    result = datetime.fromisoformat(value)
    offset = result.utcoffset()
    require(offset is not None and offset.total_seconds() == 0)
    return result


def monotonic(row: dict[str, Any], name: str) -> int:
    value = row[name]
    require(type(value) is int and 0 < value < 2**63)
    return value


def process(value: Any) -> dict[str, int]:
    row = fields(value, {'pid', 'start_time'})
    require(type(row['pid']) is int and 1 < row['pid'] < 4_194_304)
    require(type(row['start_time']) is int and 0 < row['start_time'] < 2**63)
    return row


def private_directory(path: Path) -> None:
    require(path.is_absolute())
    for parent in (path, *path.parents):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022)
    require(stat.S_IMODE(path.lstat().st_mode) == 0o700)
    native.fixture._require_private_ext4(path)


def record(path: Path) -> tuple[dict[str, Any], str]:
    raw = upgrades.private_bytes(path)
    row = native.inventory.strict_json(raw)
    require(type(row) is dict)
    return row, native.digest(raw)


def records(directory: Path, pattern: re.Pattern[str]):
    with os.scandir(directory) as rows:
        for index, row in enumerate(rows):
            require(index < 8192)
            match = pattern.fullmatch(row.name)
            if match is not None:
                yield match, record(directory / row.name)


def expected_effects(case: str, *, engine: bool) -> list[tuple[list[str], str | None]]:
    recipe = suite.CASE_RECIPES[case]
    if case not in upgrades.RECIPES:
        require(not engine)
        result: list[tuple[list[str], str | None]] = [(recipe.args(), None)]
        if recipe.add_traefik:
            result.append((recipe.args(add=True), None))
        return result
    upgrade = upgrades.recipe(case)
    if case in upgrades.REFUSALS:
        require(not engine)
        return [(upgrade.args(), None), (list(upgrades.REFUSALS[case].args), 'EXPECTED_REFUSAL')]
    require(upgrade.kind != 'product')
    if engine:
        return [(upgrade.update(recover=True), None)]
    result = [(upgrade.args(), None)]
    if case == 'upgrade-batch-default-swarm-internal':
        single = upgrades.UpgradeRecipe(('swagger',), upgrade.preset, upgrade.owner, upgrade.exposure)
        result.extend(((single.update(), None), (single.update(recover=True), None)))
    if upgrade.fault:
        predicate = 'CHECKED_BACKUP' if upgrade.kind == 'portainer' else 'PARTIAL_BATCH'
        return result + [(upgrade.update(), predicate), (upgrade.update(recover=True), None),
                         (upgrade.update(recover=True), None)]
    result.extend(((upgrade.update(), None), (upgrade.update(), None)))
    if upgrade.kind == 'component' and len(upgrade.services) == 2:
        result.append((upgrade.args(), None))
    return result


def validate_child(directory: Path, key: str, start: dict[str, Any], expected: list[str],
                   predicate: str | None, accepted_at: datetime, expires: datetime,
                   finished: dict[str, Any]) -> dict[str, Any]:
    child = process(start['child'])
    require(child != process(start['parent']))
    require(start['args'] == expected and (start['effect'] is False if predicate == 'EXPECTED_REFUSAL' else start['effect'] is True))
    executable = start['executable']
    require(type(executable) is str and 0 < len(executable) < 4096 and Path(executable).is_absolute())
    sha(start['executable_sha256'])
    require(start['argv_sha256'] == upgrades.digest([executable, '-E', '-s', '-B', '-c',
                                                    upgrades.CLI_BOOTSTRAP, *expected]))
    intent, _ = record(directory / (key + '-intent.json'))
    intent_keys = {'argv_sha256', 'timeout'} | ({'public'} if start['platform'] == 'wsl' else set())
    fields(intent, intent_keys)
    require(intent['argv_sha256'] == start['argv_sha256'] and type(intent['timeout']) is int
            and 0 < intent['timeout'] <= 5400 and intent.get('public', True) is True)
    pid, _ = record(directory / (key + '-pid.json'))
    require(process(pid) == child)
    release, _ = record(directory / (key + '-cli-released.json'))
    fields(release, {'released_at', 'released_monotonic_ns'})
    settled, _ = record(directory / (key + '-cli-settled.json'))
    fields(settled, SETTLED_KEYS)
    legacy_settled, _ = record(directory / (key + '-settled.json'))
    expected_settled = {'pid': child['pid'], 'group_absent': True}
    if start['platform'] == 'wsl':
        expected_settled['released'] = True
    require(legacy_settled == expected_settled and legacy_settled['group_absent'] is True
            and legacy_settled.get('released', True) is True and type(legacy_settled['pid']) is int)
    require(settled['pid'] == child['pid'] and type(settled['pid']) is int
            and settled['released'] is True and settled['group_absent'] is True
            and type(settled['return_code']) is int and -255 <= settled['return_code'] <= 255)
    sha(settled['stdout_sha256'])
    sha(settled['stderr_sha256'])
    launched = monotonic(start, 'started_monotonic_ns')
    released = monotonic(release, 'released_monotonic_ns')
    reaped = monotonic(settled, 'settled_monotonic_ns')
    require(launched <= released <= reaped <= monotonic(finished, 'finished_monotonic_ns'))
    require(accepted_at <= time_value(start['started_at']) <= time_value(release['released_at'])
            < expires and time_value(release['released_at']) <= time_value(settled['settled_at'])
            <= time_value(finished['finished_at']))
    verify_outcome(directory, key, start, release, settled, predicate)
    return settled


def verify_refusal_child(directory: Path, key: str, start: dict[str, Any], release: dict[str, Any],
                         settled: dict[str, Any]) -> dict[str, Any]:
    case = start['case']
    spec = upgrades.refusal_spec(case, start['args'])
    require(settled['fault'] is None and settled['output_complete'] is True and settled['return_code'] == spec.exit_code)
    outcome, _ = record(directory / (key + '-outcome.json'))
    require(outcome == {name: settled[name] for name in ('return_code', 'stdout_sha256', 'stderr_sha256')})
    metadata = {'schema_version', 'argv_sha256', 'args', 'effect', 'executable', 'executable_sha256',
                'parent', 'child', 'started_at', 'started_monotonic_ns'}
    binding = {name: start[name] for name in START_KEYS - metadata}
    row, _ = record(directory / (key + '-cli-refusal.json'))
    fields(row, {'schema_version', 'case', 'binding_sha256', 'args_sha256', 'child', 'return_code',
                 'stdout_base64', 'stderr_base64', 'stdout_sha256', 'stderr_sha256', 'product_result',
                 'command_executed', 'positive_upgrade'})
    require(type(row['schema_version']) is int and row['schema_version'] == 1 and row['case'] == case
            and row['binding_sha256'] == upgrades.digest(binding) and row['args_sha256'] == upgrades.digest(start['args'])
            and row['child'] == start['child'] and row['return_code'] == settled['return_code']
            and row['command_executed'] is True and row['positive_upgrade'] is False)
    require(type(row['stdout_base64']) is str and type(row['stderr_base64']) is str
            and len(row['stdout_base64']) + len(row['stderr_base64']) <= 90000)
    output = base64.b64decode(row['stdout_base64'], validate=True)
    error = base64.b64decode(row['stderr_base64'], validate=True)
    require(native.digest(output) == row['stdout_sha256'] == settled['stdout_sha256']
            and native.digest(error) == row['stderr_sha256'] == settled['stderr_sha256'])
    actual = upgrades.validate_refusal(case, start['args'], row['return_code'], output, error)
    require(row['product_result'] == actual)
    stdin, _ = record(directory / (key + '-cli-stdin.json'))
    fields(stdin, {'schema_version', 'case', 'binding_sha256', 'args_sha256', 'child', 'mode',
                   'delivered_bytes', 'writer_closed', 'released', 'delivered_monotonic_ns', 'closed_monotonic_ns', 'environment', 'inputs_sha256'})
    require(type(stdin['schema_version']) is int and stdin['schema_version'] == 1 and stdin['case'] == case
            and stdin['binding_sha256'] == row['binding_sha256'] and stdin['args_sha256'] == row['args_sha256']
            and stdin['child'] == start['child'] and stdin['mode'] == spec.stdin_mode
            and type(stdin['delivered_bytes']) is int and stdin['delivered_bytes'] == (2 if spec.stdin_mode == 'DECLINE_N' else 0)
            and stdin['writer_closed'] is True and stdin['released'] is True
            and monotonic(release, 'released_monotonic_ns') <= monotonic(stdin, 'delivered_monotonic_ns')
            <= monotonic(stdin, 'closed_monotonic_ns') <= monotonic(settled, 'settled_monotonic_ns'))
    environment = fields(stdin['environment'], {'infra_mode', 'repository_root', 'campaign_infra_root', 'operator_file', 'infra_root'})
    require(all(type(value) is str and 0 < len(value) <= 4096 for value in environment.values()))
    require(environment == upgrades.expected_refusal_environment(case, Path(environment['repository_root']),
        Path(environment['campaign_infra_root']), Path(environment['operator_file'])))
    sha(stdin['inputs_sha256'])
    return actual | {'stdin_mode': spec.stdin_mode, 'infra_mode': environment['infra_mode'],
                     'command_executed': True, 'positive_upgrade': False}


def verify_refusal_preservation(directory: Path, start: dict[str, Any], settled: dict[str, Any], platform: str, intent: Any, selection: dict[str, Any], key: str) -> None:
    before, _ = record(directory / 'product-refusal-before.json')
    after, _ = record(directory / 'product-refusal-after.json')
    keys = {'schema_version', 'case', 'run_id', 'source_commit', 'root', 'protected', 'runtime', 'inputs', 'captured_monotonic_ns'}
    fields(before, keys)
    fields(after, keys)
    root = str(suite.ROOT) if platform == 'native' else str(intent.checkout)
    infra = suite.INFRA if platform == 'native' else intent.home / 'infra'
    operator = infra / 'operator.env'
    pinned_infra = intent.infra_sha256 if platform == 'native' else intent.configuration_sha256
    pinned_operator = intent.operator_config_sha256 if platform == 'native' else None
    for row in (before, after):
        require(type(row['schema_version']) is int and row['schema_version'] == 1
                and row['case'] == intent.case and row['run_id'] == intent.run_id
                and row['source_commit'] == intent.source_commit and row['root'] == root)
        fields(row['protected'], {'schema_version', 'paths'})
        require(type(row['protected']['schema_version']) is int and row['protected']['schema_version'] == 1
                and type(row['protected']['paths']) is dict and len(row['protected']['paths']) <= 1024
                and set(upgrades.PROTECTED_PATHS) <= set(row['protected']['paths']))
        upgrades.validate_protected(row['protected'])
        upgrades.validate_refusal_inputs(row['inputs'], Path(root), infra, operator, pinned_infra, pinned_operator)
        runtime = row['runtime']
        require(type(runtime) is dict and runtime.get('status') == 'UPGRADE_RUNTIME_VERIFIED'
                and type(runtime.get('manifest_schema')) is int and runtime['manifest_schema'] == 2
                and runtime.get('selection') == selection)
        manifest = row['protected']['paths']['installation/manifest.json']
        require(manifest['kind'] == 'regular' and manifest['sha256'] == runtime.get('manifest_sha256')
                == runtime.get('manifest_token') == selection['manifest_sha256'])
    require(before['protected'] == after['protected']
            and monotonic(before, 'captured_monotonic_ns') < monotonic(start, 'started_monotonic_ns')
            < monotonic(settled, 'settled_monotonic_ns') < monotonic(after, 'captured_monotonic_ns'))
    upgrades.preserve(before['runtime'], after['runtime'], no_op=True)
    require(before['inputs'] == after['inputs'])
    stdin, _ = record(directory / (key + '-cli-stdin.json'))
    require(stdin['environment'] == upgrades.expected_refusal_environment(intent.case, Path(root), infra, operator)
            and stdin['inputs_sha256'] == upgrades.digest(before['inputs']))
    if upgrades.REFUSALS[intent.case].cause == 'CHECKPOINT_ABSENT':
        require(before['protected']['paths']['installation/product-upgrade.json'] == {'kind': 'absent'})


def verify_outcome(directory: Path, key: str, start: dict[str, Any], release: dict[str, Any],
                   settled: dict[str, Any], predicate: str | None) -> None:
    if predicate == 'EXPECTED_REFUSAL':
        verify_refusal_child(directory, key, start, release, settled)
        return
    if predicate is None:
        require(settled['fault'] is None and settled['return_code'] == 0 and settled['output_complete'] is True)
        outcome, _ = record(directory / (key + '-outcome.json'))
        require(type(outcome.get('return_code')) is int and outcome == {
            name: settled[name] for name in ('return_code', 'stdout_sha256', 'stderr_sha256')})
        return
    fault = fields(settled['fault'], {'checkpoint_sha256', 'predicate', 'process_group', 'signal',
                                      'sent_at', 'sent_monotonic_ns'})
    require(fault['predicate'] == predicate and fault['process_group'] == start['child']['pid']
            and type(fault['process_group']) is int and type(fault['signal']) is int and fault['signal'] == 15
            and settled['return_code'] == -fault['signal'] and settled['output_complete'] is False)
    sha(fault['checkpoint_sha256'])
    prepared, _ = record(directory / (key + '-cli-fault-intent.json'))
    keys = {'checkpoint_sha256', 'predicate', 'process_group', 'signal'}
    fields(prepared, keys | {'process', 'prepared_at', 'prepared_monotonic_ns'})
    require(process(prepared['process']) == start['child'] and all(prepared[k] == fault[k] for k in keys))
    require(monotonic(release, 'released_monotonic_ns') <= monotonic(prepared, 'prepared_monotonic_ns')
            <= monotonic(fault, 'sent_monotonic_ns')
            <= monotonic(settled, 'settled_monotonic_ns'))
    require(time_value(release['released_at']) <= time_value(prepared['prepared_at'])
            <= time_value(fault['sent_at']) <= time_value(settled['settled_at']))
    require(any(row.get('checkpoint_sha256') == fault['checkpoint_sha256'] and row.get('predicate') == predicate
                and all(row.get(name) == start[name] for name in ('run_id', 'case', 'source_commit'))
                for _, (row, _) in records(directory, re.compile(r'upgrade-fault-intent-[0-9a-f]{32}\.json'))))


def approval_time(row: Any, digest: str, phase: str) -> datetime:
    value = fields(row, {'phase', 'sha256', 'accepted_at'})
    require(value['sha256'] == digest and value['phase'] == phase)
    return time_value(value['accepted_at'])


def native_activation(directory: Path, proposal: dict[str, Any], proposal_sha: str, case: str,
                      row: Any) -> tuple[datetime, datetime]:
    go, digest = record(directory / 'activation.json')
    accepted_at = approval_time(row, digest, 'paused-product-case')
    expiry = suite.validate_go(go, proposal, proposal_sha, accepted_at, paused=True, case=case)
    accepted, _ = record(directory / 'activation-accepted.json')
    require(accepted == {'activation_sha256': digest})
    for field in ('resource', 'route', 'preview'):
        _, observed = record(directory / ('paused-' + field + '.json'))
        require(go[field + '_sha256'] == observed)
    return accepted_at, expiry


def validate_selection(selection: Any, case: str, source: str) -> dict[str, Any]:
    row = fields(selection, {'requested', 'resolved', 'product_release', 'product_revision', 'manifest_sha256'})
    recipe = suite.CASE_RECIPES[case]
    expected = set(recipe.services) | ({'traefik'} if recipe.add_traefik else set())
    for key in ('requested', 'resolved'):
        services = row[key]
        require(type(services) is list and len(services) <= 128
                and all(type(value) is str and SERVICE_ID.fullmatch(value) for value in services)
                and services == sorted(set(services)))
    require(set(row['requested']) == expected and expected <= set(row['resolved']))
    require(type(row['product_release']) is str and upgrades.VERSION_TEXT.fullmatch(row['product_release'])
            and row['product_revision'] == source)
    sha(row['manifest_sha256'])
    return row


def report(platform: str, run_id: str, case: str, expected_go: str) -> dict[str, Any]:
    require(platform in ('native', 'wsl') and native.RUN_ID.fullmatch(run_id)
            and case in suite.CASE_RECIPES and native.HEX.fullmatch(expected_go))
    require(case not in upgrades.RECIPES or upgrades.RECIPES[case].kind != 'product')
    home = suite.PRIVATE if platform == 'native' else wsl.BASE / run_id / 'cases' / case
    directory = home / ('product-case-' + run_id if platform == 'native' else 'journal')
    private_directory(home)
    private_directory(directory)
    intent_file = home / ('product-intent-' + run_id + '.json' if platform == 'native' else 'intent.json')
    proposal, proposal_sha = record(directory / 'proposal.json')
    intent_data, _ = record(intent_file)
    intent = (suite.SuiteIntent.parse(intent_data, proposal['source_commit']) if platform == 'native'
              else wsl.Intent.parse(intent_data))
    require(intent.run_id == run_id and intent.case == case
            and proposal['intent_sha256'] == upgrades.digest(asdict(intent)))
    binding = {'platform': platform, 'case': case, 'run_id': run_id, 'source_commit': intent.source_commit}
    finished, _ = record(directory / ('cli-result-' + expected_go + '.json'))
    fields(finished, FINAL_KEYS)
    require(type(finished['schema_version']) is int and finished['schema_version'] == 1
            and finished['approval_sha256'] == expected_go
            and all(finished[key] == binding[key] for key in ('case', 'run_id', 'source_commit'))
            and finished['before_sha256'] == upgrades.digest(proposal['baseline']))
    after, after_sha = record(directory / ('cli-after-' + expected_go + '.json'))
    require(finished['after_sha256'] == after_sha)
    if platform == 'native':
        require(native.preserved_snapshot(proposal['baseline'], native.validate_snapshot(after)))
    else:
        require(after == proposal['baseline'])
    selection = validate_selection(finished['selection'], case, intent.source_commit)
    result_sha = sha(finished['result_sha256'])
    effects = []
    for match, (start, _) in records(directory, START_FILE):
        fields(start, START_KEYS)
        approval = start['approval']
        if (start['effect'] is True or case in upgrades.REFUSALS and start['args'] == list(upgrades.REFUSALS[case].args)) and type(approval) is dict and approval.get('sha256') == expected_go:
            effects.append((match.group(1), start))
    require(bool(effects))
    effects.sort(key=lambda item: monotonic(item[1], 'started_monotonic_ns'))
    first = effects[0][1]
    engine_phase = 'native-product-engine-recovery' if platform == 'native' else 'wsl-engine-recovery'
    engine = first['approval']['phase'] == engine_phase
    normal_phase = 'native-product-maintenance' if platform == 'native' else 'wsl-case-run'
    phase = engine_phase if engine else normal_phase
    go_home = directory if platform == 'native' else home
    go_name = 'engine-recovery-go.json' if engine else 'approval.json' if platform == 'native' else 'run-go.json'
    go, go_sha = record(go_home / go_name)
    require(go_sha == expected_go)
    accepted_at = approval_time(first['approval'], go_sha, phase)
    if platform == 'native':
        expiry = suite.validate_go(go, proposal, proposal_sha, accepted_at, paused=False, case=case, engine_recovery=engine)
    else:
        if not isinstance(intent, wsl.Intent):
            raise ValueError('INCOMPLETE')
        expiry = wsl.approval(go, intent, proposal, proposal_sha, engine_recovery=engine, now=accepted_at)
    if platform == 'native' and not engine:
        activated_at, activation_expiry = native_activation(directory, proposal, proposal_sha, case, first['activation'])
        require(accepted_at <= activated_at < expiry)
        accepted_at, expiry = activated_at, activation_expiry
    else:
        require(first['activation'] is None)
    if engine:
        started, _ = record(directory / 'engine-recovery-started.json')
        pending, _ = record(directory / 'engine-recovery-proposal.json')
        require(started == {'go_sha256': expected_go, 'binding': pending} and pending == go['engine_binding'])
    expected = expected_effects(case, engine=engine)
    require(len(effects) == len(expected))
    pins = proposal['pins']
    package_version = first['package_version']
    require(type(package_version) is str and upgrades.VERSION_TEXT.fullmatch(package_version))
    binding |= {'workflow_sha256': sha(pins[ACTIVE_WORKFLOW]), 'entrypoint_sha256': sha(pins[upgrades.CLI_MAIN]),
                'release_sha256': sha(pins[upgrades.CLI_RELEASE]), 'proposal_sha256': proposal_sha,
                'before_sha256': finished['before_sha256'],
                'host_sha256': sha(proposal['host_id_sha256']) if platform == 'native' else upgrades.digest(proposal['identity']),
                'incus_client': '6.0.5', 'incus_server': '6.0.5',
                'approval': first['approval'], 'activation': first['activation'], 'parent': first['parent'],
                'package_version': package_version}
    previous = 0
    proof = []
    refusal_summary = None
    for (key, start), (args, predicate) in zip(effects, expected, strict=True):
        require(type(start['schema_version']) is int and start['schema_version'] == 1
                and all(start[k] == value for k, value in binding.items())
                and monotonic(start, 'started_monotonic_ns') >= previous)
        if platform == 'wsl':
            require(isinstance(intent, wsl.Intent) and start['executable'] == str(intent.checkout / '.venv/bin/python'))
        settled = validate_child(directory, key, start, args, predicate, accepted_at, expiry, finished)
        previous = settled['settled_monotonic_ns']
        proof.append({'start': start, 'settled': settled})
        if predicate == 'EXPECTED_REFUSAL':
            verify_refusal_preservation(directory, start, settled, platform, intent, selection, key)
            release, _ = record(directory / (key + '-cli-released.json'))
            refusal_summary = verify_refusal_child(directory, key, start, release, settled)
    status = ('ENGINE_RECOVERED_DISPOSED' if engine else 'PASS') if platform == 'native' else (
        'CASE_RECOVERED' if engine else 'CASE_PASS_DISPOSED')
    require(any(digest == result_sha and row.get('status') == status
                and (platform == 'native' or all(row.get(k) == binding[k] for k in ('run_id', 'case', 'source_commit')))
                for _, (row, digest) in records(directory, RESULT_FILE[platform])))
    result = {'status': 'ATTRIBUTED', 'platform': platform, 'case': case, 'run_id': run_id,
            'source_commit': intent.source_commit, 'workflow_sha256': binding['workflow_sha256'],
            'result_sha256': result_sha, 'execution_sha256': upgrades.digest(proof),
            'before_sha256': finished['before_sha256'], 'after_sha256': finished['after_sha256'],
            'package_version': package_version, 'selection': selection, 'effects': sum(start['effect'] is True for _, start in effects), 'epic_complete': False}
    if case in upgrades.REFUSALS:
        result.update(verification_kind='PUBLIC_REFUSAL_PRESERVED', command_executed=True, positive_upgrade=False,
                      recovery_performed=False, refusal_case=case, stdin_mode=upgrades.REFUSALS[case].stdin_mode,
                      product_result=refusal_summary, commands=len(proof))
    return result


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ValueError('INCOMPLETE')


def main(argv: list[str] | None = None) -> int:
    parser = Parser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True, parser_class=Parser)
    read = modes.add_parser('report', help='read fixed protected evidence for one accepted case')
    read.add_argument('--platform', required=True, choices=('native', 'wsl'))
    read.add_argument('--run-id', required=True, metavar='HEX32')
    read.add_argument('--case', required=True, choices=tuple(suite.CASE_RECIPES))
    read.add_argument('--expected-go-sha256', required=True, metavar='HEX64')
    try:
        args = parser.parse_args(argv)
        result = report(args.platform, args.run_id, args.case, args.expected_go_sha256)
    except (AttributeError, KeyError, OSError, RecursionError, TypeError, ValueError,
            native.MaintenanceError, native.fixture.FixtureError, native.inventory.InventoryError,
            upgrades.UpgradeError, wsl.CaseError):
        print('{"status":"INCOMPLETE","epic_complete":false}')
        return 2
    print(native.canonical(result).decode('ascii'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Closed, unpublished upgrade qualification recipes using the actual public CLI.

This module never promotes compatibility, creates a catalog, or accepts commands
from JSON. Host adapters retain the maintenance/identity/lease authority. Historical schema1 product cases retain their original supported scope; the
legacy live helpers remain unavailable. Current negatives prove only their actual
public refusal and preservation contract.
"""
from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import time
from typing import Any
from uuid import uuid4

SCRIPT = 'modules/tsw_core/tools/linux/qualification/product_upgrade_cases.py'
CATALOG = 'modules/tsw_core/src/infrastructure/adapters/lifecycle/component_transitions.py'
CLI_MAIN = 'modules/tsw_core/src/__main__.py'
CLI_RELEASE = 'pyproject.toml'
CLI_BOOTSTRAP = (
    "import importlib.metadata, importlib.util, pathlib, runpy, tomllib\n"
    "spec = importlib.util.find_spec('tiny_swarm_world')\n"
    "expected = pathlib.Path('modules/tsw_core/src/__init__.py').resolve(strict=True)\n"
    "if not spec or not spec.origin or pathlib.Path(spec.origin).resolve(strict=True) != expected:\n"
    "    raise SystemExit('CASE_CLI_ORIGIN')\n"
    "main = importlib.util.find_spec('tiny_swarm_world.__main__')\n"
    "if not main or not main.origin or pathlib.Path(main.origin).resolve(strict=True) != expected.with_name('__main__.py'):\n"
    "    raise SystemExit('CASE_CLI_ENTRYPOINT')\n"
    "release = tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['version']\n"
    "if importlib.metadata.version('tiny-swarm-world') != release:\n"
    "    raise SystemExit('CASE_CLI_PACKAGE_VERSION')\n"
    "runpy.run_module('tiny_swarm_world', run_name='__main__')"
)
VERSION_TEXT = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.+-]{0,99}\Z')
ROOT = Path(__file__).resolve().parents[5]
FRESH_NAMES = ('minimal', 'swagger-internal', 'swagger-published', 'swagger-traefik-swarm',
               'swagger-traefik-portainer', 'swagger-add-traefik', 'full-swarm', 'full-portainer')


class UpgradeError(Exception):
    """Bounded refusal; not a product engine result."""


class FaultObserved(UpgradeError):
    """A real durable checkpoint was observed before signaling our own child."""

    def __init__(self, reason: str, receipt: dict[str, Any] | None = None):
        super().__init__(reason)
        self.receipt = receipt


def require(value: Any, code: str) -> None:
    if not value:
        raise UpgradeError(code)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def outcome(failure: str | None, *, recovered: bool = False) -> str:
    if recovered:
        return 'CASE_RECOVERED'
    return {'UPGRADE_NOT_EXERCISED': 'CASE_NOT_EXERCISED', 'UPGRADE_PRODUCT_NOT_IMPLEMENTED': 'CASE_NOT_IMPLEMENTED'}.get(
        failure or '', 'CASE_FAILED_DISPOSED' if failure else 'CASE_PASS_DISPOSED')


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def cli_args(argv: list[str]) -> list[str] | None:
    return argv[6:] if argv[1:6] == ['-E', '-s', '-B', '-c', CLI_BOOTSTRAP] else None


def cli_is_effect(args: list[str]) -> bool:
    return '--live' in args and '--approve-live' in args


def approval_receipt(raw: bytes, value: dict[str, Any], accepted_at: str) -> dict[str, str]:
    return {'phase': value['phase'], 'sha256': hashlib.sha256(raw).hexdigest(), 'accepted_at': accepted_at}


def cli_incus_versions(raw: bytes) -> tuple[str, str]:
    value = raw.decode('ascii')
    client = re.findall(r'^Client version: ([0-9.]+)$', value, re.M)
    server = re.findall(r'^Server version: ([0-9.]+)$', value, re.M)
    require(len(client) == len(server) == 1, 'CASE_CLI_INCUS_VERSION_INVALID')
    return client[0], server[0]


def cli_binding(port: Any, platform: str, workflow: str) -> dict[str, Any]:
    proposal = port.proposal
    pins = proposal['pins'] if proposal is not None else port.cli_pins
    host = None if proposal is None else proposal['host_id_sha256'] if platform == 'native' else digest(proposal['identity'])
    client, server = port.cli_versions
    package_version = version('tiny-swarm-world')
    require(VERSION_TEXT.fullmatch(package_version), 'CASE_CLI_PACKAGE_VERSION')
    return {'platform': platform, 'run_id': port.intent.run_id, 'case': port.intent.case,
            'source_commit': port.intent.source_commit, 'workflow_sha256': pins[workflow],
            'entrypoint_sha256': pins[CLI_MAIN], 'release_sha256': pins[CLI_RELEASE],
            'proposal_sha256': digest(proposal) if proposal is not None else None,
            'before_sha256': digest(proposal['baseline']) if proposal is not None else None,
            'host_sha256': host, 'approval': port.cli_approval, 'activation': port.cli_activation,
            'incus_client': client, 'incus_server': server, 'package_version': package_version}


def selection_evidence(manifest: Any, manifest_sha: str) -> dict[str, Any]:
    return {'requested': sorted(manifest.requested_services), 'resolved': sorted(manifest.resolved_services),
            'product_release': manifest.product.release, 'product_revision': manifest.product.revision,
            'manifest_sha256': manifest_sha}


def save_cli_case_result(port: Any, result: dict[str, Any]) -> None:
    require(port.cli_approval is not None and port.cli_final is not None and port.cli_selection is not None,
            'CASE_CLI_FINAL_UNAVAILABLE')
    go_sha = port.cli_approval['sha256']
    port.journal.save('cli-after-' + go_sha + '.json', port.cli_final)
    port.journal.save('cli-result-' + go_sha + '.json', {
        'schema_version': 1, 'case': port.intent.case, 'run_id': port.intent.run_id,
        'source_commit': port.intent.source_commit, 'approval_sha256': go_sha,
        'before_sha256': digest(port.proposal['baseline']), 'after_sha256': digest(port.cli_final),
        'result_sha256': digest(result), 'selection': port.cli_selection, 'finished_at': utc_stamp(),
        'finished_monotonic_ns': time.monotonic_ns(),
    })


@dataclass(frozen=True)
class RefusalSpec:
    """Closed public commands; never an operator-provided expected-error policy."""
    args: tuple[str, ...]
    exit_code: int
    cause: str
    stdin_mode: str = 'EOF'


_PRODUCT = ('product', 'upgrade', '--to', '0.5.0')
REFUSALS = {
    'refuse-product-target': RefusalSpec(('product', 'upgrade', '--to', '0.4.0', '--preview', '--json'), 2, 'TARGET_SYNTAX'),
    'refuse-product-syntax': RefusalSpec((*_PRODUCT, '--preview', '--live', '--json'), 2, 'TARGET_SYNTAX'),
    'refuse-product-source': RefusalSpec((*_PRODUCT, '--preview', '--json'), 1, 'SOURCE'),
    'refuse-product-checkpoint': RefusalSpec((*_PRODUCT, '--recover', '--preview', '--json'), 1, 'CHECKPOINT_ABSENT'),
    'refuse-product-consent-eof': RefusalSpec((*_PRODUCT, '--live', '--json'), 2, 'CONSENT'),
    'refuse-product-consent-n': RefusalSpec((*_PRODUCT, '--live', '--json'), 2, 'CONSENT', 'DECLINE_N'),
    'refuse-product-recovery-consent-eof': RefusalSpec((*_PRODUCT, '--recover', '--live', '--json'), 2, 'CONSENT'),
    'refuse-product-recovery-consent-n': RefusalSpec((*_PRODUCT, '--recover', '--live', '--json'), 2, 'CONSENT', 'DECLINE_N'),
}
SOURCE_REFUSALS = {
    'Dirty checkout or unrelated untracked files; preserve operator work and commit or move it before upgrading.': 'SOURCE_DIRTY',
    'Product anchor must be the actual prepared checkout root.': 'SOURCE_ROOT',
    'Source checkout must identify the official product repository without embedded credentials.': 'SOURCE_ORIGIN',
    'Installation inventory differs from actual source revision/lock/release; inspect explicit adoption.': 'SOURCE_INVENTORY',
}
PROTECTED_PATHS = ('installation/manifest.json', 'installation/product-upgrade.json', 'product',
                   'product/active', 'product/.active-next', 'product/tiny-swarm-world',
                   'product/activations', 'product/staging', 'product/inputs', 'product/releases', 'product/infra')


def unavailable_product(case: str) -> dict[str, Any]:
    require(case in RECIPES and RECIPES[case].kind == 'product', 'UPGRADE_CASE_UNKNOWN')
    return {'status': 'QUALIFICATION_HELPER_UNAVAILABLE', 'case': case, 'requires': 'S-U2',
            'command_executed': False, 'product_result': None, 'epic_complete': False,
            'historical_scope': 'OFFICIAL_SCHEMA1_0.4.0_TO_0.5.0_UNCHANGED'}


def validate_unexecuted(value: Any, case: str, run: str, source: str) -> None:
    old = {'status', 'case', 'run_id', 'source_commit', 'epic_complete'}
    new = old | {'command_executed', 'product_result'}
    require(type(value) is dict and set(value) in (old, new) and value['case'] == case
            and value['run_id'] == run and value['source_commit'] == source and value['epic_complete'] is False,
            'UPGRADE_UNEXECUTED_UNPROVEN')
    if set(value) == new:
        require(value['command_executed'] is False and value['product_result'] is None, 'UPGRADE_UNEXECUTED_UNPROVEN')
    if value['status'] == 'QUALIFICATION_HELPER_UNAVAILABLE':
        require(case in {'upgrade-product-v1', 'recover-product-v1'} and set(value) == new, 'UPGRADE_UNEXECUTED_UNPROVEN')
    elif value['status'] == 'CASE_NOT_IMPLEMENTED':
        require(case in ALL_NAMES, 'UPGRADE_UNEXECUTED_UNPROVEN')
    else:
        require(value['status'] == 'CASE_NOT_EXECUTED' and case in ALL_NAMES, 'UPGRADE_UNEXECUTED_UNPROVEN')


def refusal_spec(case: str, args: list[str]) -> RefusalSpec:
    require(case in REFUSALS and tuple(args) == REFUSALS[case].args and '--approve-live' not in args,
            'REFUSAL_COMMAND_NOT_ADMITTED')
    return REFUSALS[case]


def parser_refusal(args: list[str]) -> bytes:
    """Exact current public parser output, with the actual -c CLI program name."""
    from contextlib import redirect_stderr
    import io
    import sys
    from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
    stream = io.StringIO()
    previous = sys.argv
    try:
        sys.argv = ['-c']
        with redirect_stderr(stream):
            try:
                parse_args(args)
            except SystemExit as exc:
                require(exc.code == 2, 'REFUSAL_PARSER_CONTRACT')
            else:
                raise UpgradeError('REFUSAL_PARSER_CONTRACT')
    finally:
        sys.argv = previous
    raw = stream.getvalue().encode()
    require(raw.startswith(b'usage: -c ') and raw.endswith(
        b'-c: error: product upgrade requires --to 0.5.0 and exactly one of --preview or --live\n'),
        'REFUSAL_PARSER_CONTRACT')
    return raw


def validate_refusal(case: str, args: list[str], code: int, output: bytes, error: bytes) -> dict[str, Any]:
    spec = refusal_spec(case, args)
    require(type(code) is int and code == spec.exit_code and len(output) + len(error) <= 65536,
            'REFUSAL_RESULT_UNPROVEN')
    if spec.cause == 'TARGET_SYNTAX':
        require(output == b'' and error == parser_refusal(args), 'REFUSAL_PARSER_OUTPUT')
        return {'status': 'parser_refused', 'cause': spec.cause}
    require(not error, 'REFUSAL_UNEXPECTED_STDERR')
    body = output
    if spec.cause == 'CONSENT':
        from tiny_swarm_world.domain.preflight import LIVE_CONSENT_PROMPT
        prefix = (LIVE_CONSENT_PROMPT + ' ').encode()
        require(body.startswith(prefix), 'REFUSAL_PROMPT_UNPROVEN')
        body = body[len(prefix):]
    try:
        value = json.loads(body)
        require(type(value) is dict and body == json.dumps(value, sort_keys=True).encode() + b'\n',
                'REFUSAL_OUTPUT_FRAMING')
    except (ValueError, UnicodeError):
        raise UpgradeError('REFUSAL_OUTPUT_FRAMING') from None
    if spec.cause == 'CONSENT':
        require(value == {'status': 'refused', 'diagnostics': ['missing live confirmation']}, 'REFUSAL_CONSENT_UNPROVEN')
        cause = 'CONSENT_DECLINED_N' if spec.stdin_mode == 'DECLINE_N' else 'CONSENT_EOF'
    else:
        require(set(value) == {'status', 'diagnostics', 'recovery'} and value['status'] == 'blocked'
                and value['recovery'] == 'preserve source/checkpoint; use product upgrade --to 0.5.0 --recover --preview from management checkout'
                and type(value['diagnostics']) is list and len(value['diagnostics']) == 1,
                'REFUSAL_CAUSE_UNPROVEN')
        diagnostic = value['diagnostics'][0]
        if spec.cause == 'CHECKPOINT_ABSENT':
            require(diagnostic == 'No matching product checkpoint; inspect the original target.', 'REFUSAL_CHECKPOINT_UNPROVEN')
            cause = 'CHECKPOINT_ABSENT'
        else:
            require(type(diagnostic) is str and diagnostic in SOURCE_REFUSALS, 'REFUSAL_SOURCE_UNPROVEN')
            cause = SOURCE_REFUSALS[diagnostic]
    return {'status': value['status'], 'cause': cause}


def require_refusal_binding(receipt: Any, case: str) -> None:
    binding = receipt.binding
    require(binding['case'] == case and binding['proposal_sha256'] is not None
            and type(binding['approval']) is dict, 'REFUSAL_GO_REQUIRED')
    if binding['platform'] == 'native':
        require(binding['approval']['phase'] == 'native-product-maintenance'
                and type(binding['activation']) is dict and binding['activation']['phase'] == 'paused-product-case',
                'REFUSAL_GO_REQUIRED')
    else:
        require(binding['platform'] == 'wsl' and binding['approval']['phase'] == 'wsl-case-run'
                and binding['activation'] is None, 'REFUSAL_GO_REQUIRED')


def expected_refusal_environment(case: str, root: Path, infra: Path, operator: Path) -> dict[str, str]:
    require(case in REFUSALS and root.is_absolute() and infra.is_absolute() and operator == infra / 'operator.env',
            'REFUSAL_ENVIRONMENT_UNPROVEN')
    official = case == 'refuse-product-source'
    return {'infra_mode': 'OFFICIAL_INFRA_READ_ONLY' if official else 'CAMPAIGN_INFRA',
            'repository_root': str(root), 'campaign_infra_root': str(infra), 'operator_file': str(operator),
            'infra_root': str(root / 'modules/tsw_core/infra') if official else str(infra)}


def select_refusal_environment(case: str, args: list[str], env: dict[str, str], root: Path,
                               infra: Path, operator: Path) -> dict[str, str]:
    refusal_spec(case, args)
    require(env.get('TSW_REPOSITORY_ROOT') == str(root) and env.get('TSW_INFRA_ROOT') == str(infra)
            and env.get('TSW_INSTALL_ENV_FILE') == str(operator), 'REFUSAL_ENVIRONMENT_SUBSTITUTED')
    expected = expected_refusal_environment(case, root, infra, operator)
    # This dictionary belongs to one validated public child. The parent,
    # operator source, baseline and observer environments remain unchanged.
    env['TSW_INFRA_ROOT'] = expected['infra_root']
    return expected


def capture_refusal_inputs(root: Path, infra: Path, operator: Path, pinned_infra: str,
                           pinned_operator: str) -> dict[str, Any]:
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_validation import read_tree
    require(operator == infra / 'operator.env', 'REFUSAL_OPERATOR_REFERENCE')
    def capture(path: Path, *, private: bool) -> dict[str, Any]:
        tree = read_tree(path, private=private)
        return {'path': str(path), 'metadata': tree.metadata(),
                'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(tree.files.items())}}
    official = capture(root / 'modules/tsw_core/infra', private=False)
    campaign = capture(infra, private=True)
    files = campaign['files']
    require(digest(list(files.items())) == pinned_infra and files.get('operator.env') == pinned_operator,
            'REFUSAL_PRIVATE_INPUT_DRIFT')
    operator_identity = campaign['metadata']['members'].get('operator.env')
    require(type(operator_identity) is list and len(operator_identity) == 8
            and stat.S_IMODE(operator_identity[3]) == 0o600, 'REFUSAL_OPERATOR_UNSAFE')
    return {'schema_version': 1, 'official': official, 'campaign': campaign,
            'operator': {'path': str(operator), 'identity': operator_identity, 'sha256': pinned_operator}}


def validate_refusal_inputs(value: Any, root: Path, infra: Path, operator: Path,
                            pinned_infra: str, pinned_operator: str | None = None) -> None:
    require(type(value) is dict and set(value) == {'schema_version', 'official', 'campaign', 'operator'}
            and type(value['schema_version']) is int and value['schema_version'] == 1, 'REFUSAL_INPUT_RECEIPT')
    for name, path in (('official', root / 'modules/tsw_core/infra'), ('campaign', infra)):
        row = value[name]
        require(type(row) is dict and set(row) == {'path', 'metadata', 'files'} and row['path'] == str(path)
                and type(row['metadata']) is dict and set(row['metadata']) == {'root', 'members'}
                and type(row['files']) is dict and type(row['metadata']['members']) is dict
                and 0 < len(row['metadata']['members']) <= 4096, 'REFUSAL_INPUT_RECEIPT')
        entries = row['metadata']['members']
        for member, identity in [('', row['metadata']['root']), *entries.items()]:
            require(type(member) is str and not Path(member).is_absolute() and '..' not in Path(member).parts
                    and len(Path(member).parts) <= 16 and type(identity) is list and len(identity) == 8
                    and all(type(item) is int and item >= 0 for item in identity) and identity[1] > 0
                    and identity[2] == 0 and not identity[3] & 0o022
                    and (stat.S_ISREG(identity[3]) or stat.S_ISDIR(identity[3])), 'REFUSAL_INPUT_RECEIPT')
        require(stat.S_ISDIR(row['metadata']['root'][3]), 'REFUSAL_INPUT_RECEIPT')
        require(all(identity[7] == 1 and identity[4] <= 16 * 1024 * 1024 for identity in entries.values() if stat.S_ISREG(identity[3]))
                and sum(identity[4] for identity in entries.values() if stat.S_ISREG(identity[3])) <= 64 * 1024 * 1024, 'REFUSAL_INPUT_RECEIPT')
        files = {member for member, identity in entries.items() if stat.S_ISREG(identity[3])}
        require(set(row['files']) == files and all(type(sha) is str and re.fullmatch('[0-9a-f]{64}', sha)
                for sha in row['files'].values()), 'REFUSAL_INPUT_RECEIPT')
    campaign = value['campaign']
    require(digest(sorted(campaign['files'].items())) == pinned_infra, 'REFUSAL_PRIVATE_INPUT_DRIFT')
    row = value['operator']
    require(type(row) is dict and set(row) == {'path', 'identity', 'sha256'} and row['path'] == str(operator)
            and operator == infra / 'operator.env' and row['identity'] == campaign['metadata']['members'].get('operator.env')
            and row['sha256'] == campaign['files'].get('operator.env') and (pinned_operator is None or row['sha256'] == pinned_operator)
            and type(row['identity']) is list and stat.S_IMODE(row['identity'][3]) == 0o600,
            'REFUSAL_OPERATOR_UNSAFE')


def fixed_stdin(case: str, args: list[str], child: Any, receipt: Any) -> None:
    """Deliver only the reviewed literal decline, after releasing our own child."""
    spec = refusal_spec(case, args)
    require(receipt is not None and receipt.released and receipt.process is not None
            and child.pid == receipt.process['pid'] and receipt.args == args
            and receipt.binding['case'] == case and type(receipt.environment) is dict
            and type(receipt.inputs_sha256) is str and re.fullmatch('[0-9a-f]{64}', receipt.inputs_sha256), 'REFUSAL_INPUT_NOT_RELEASED')
    delivered = 0
    if spec.stdin_mode == 'DECLINE_N':
        require(child.stdin is not None, 'REFUSAL_INPUT_PIPE_MISSING')
        delivered = child.stdin.write(b'n\n')
        require(delivered == 2, 'REFUSAL_INPUT_INCOMPLETE')
        delivered_at = time.monotonic_ns()
        child.stdin.flush()
        child.stdin.close()
    else:
        require(spec.stdin_mode == 'EOF' and child.stdin is None, 'REFUSAL_INPUT_MODE')
        delivered_at = time.monotonic_ns()
    closed_at = time.monotonic_ns()
    receipt.journal.save(receipt.key + '-cli-stdin.json', {
        'schema_version': 1, 'case': case, 'binding_sha256': digest(receipt.binding),
        'args_sha256': digest(args), 'child': receipt.process, 'mode': spec.stdin_mode,
        'delivered_bytes': delivered, 'writer_closed': True, 'released': True,
        'delivered_monotonic_ns': delivered_at, 'closed_monotonic_ns': closed_at,
        'environment': receipt.environment, 'inputs_sha256': receipt.inputs_sha256,
    })


def save_refusal(receipt: Any, case: str, code: int, output: bytes, error: bytes) -> None:
    import base64
    require(receipt is not None and receipt.released and receipt.process is not None, 'REFUSAL_CHILD_MISSING')
    result = validate_refusal(case, receipt.args, code, output, error)
    receipt.journal.save(receipt.key + '-cli-refusal.json', {
        'schema_version': 1, 'case': case, 'binding_sha256': digest(receipt.binding),
        'args_sha256': digest(receipt.args), 'child': receipt.process, 'return_code': code,
        'stdout_base64': base64.b64encode(output).decode(), 'stderr_base64': base64.b64encode(error).decode(),
        'stdout_sha256': hashlib.sha256(output).hexdigest(), 'stderr_sha256': hashlib.sha256(error).hexdigest(),
        'product_result': result, 'command_executed': True, 'positive_upgrade': False,
    })


def protected_state(root: Path) -> dict[str, Any]:
    """Private, bounded, no-follow byte comparison; never exported as public input hashes."""
    root = root / '.tiny-swarm-world'
    rows: dict[str, Any] = {}
    total = 0
    def identity(info: os.stat_result) -> tuple[int, ...]:
        return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_nlink,
                info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    def visit(path: Path, *, recursive: bool) -> None:
        nonlocal total
        name = path.relative_to(root).as_posix()
        require(len(rows) < 1024, 'REFUSAL_STATE_ENTRY_BOUND')
        # Prove every existing ancestor rather than treating an escaping or
        # unreadable parent as an absent leaf.
        for parent in reversed((path.parent, *path.parent.parents)):
            if parent == root or root in parent.parents:
                try:
                    parent_info = parent.lstat()
                except FileNotFoundError:
                    continue
                require(stat.S_ISDIR(parent_info.st_mode) and parent_info.st_uid == 0
                        and not parent_info.st_mode & 0o022, 'REFUSAL_STATE_PARENT')
        try:
            before = path.lstat()
        except FileNotFoundError:
            rows[name] = {'kind': 'absent'}
            return
        require(before.st_uid == 0 and (stat.S_ISLNK(before.st_mode) or not before.st_mode & 0o022), 'REFUSAL_STATE_TYPE')
        if name in {'installation/manifest.json', 'installation/product-upgrade.json'}:
            require(not before.st_mode & 0o077, 'REFUSAL_STATE_PRIVATE')
        if stat.S_ISLNK(before.st_mode):
            target = Path(os.readlink(path))
            allowed = name in {'product/active', 'product/.active-next'} or (name.startswith('product/activations/') and path.name in {'code', 'infra'})
            require(allowed and target.is_absolute() and '..' not in target.parts and target.is_relative_to(root / 'product'), 'REFUSAL_STATE_LINK')
            rows[name] = {'kind': 'symlink', 'identity': list(identity(before)), 'target_sha256': hashlib.sha256(os.fsencode(target)).hexdigest()}
        elif stat.S_ISDIR(before.st_mode):
            rows[name] = {'kind': 'directory', 'identity': list(identity(before))}
            if recursive:
                children = []
                with os.scandir(path) as entries:
                    for child in entries:
                        require(len(children) < 1024 - len(rows), 'REFUSAL_STATE_ENTRY_BOUND')
                        children.append(child)
                children.sort(key=lambda item: item.name)
                for child in children:
                    visit(path / child.name, recursive=True)
        else:
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 1024 * 1024,
                    'REFUSAL_STATE_TYPE')
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            try:
                require(identity(os.fstat(fd)) == identity(before), 'REFUSAL_STATE_CAS')
                raw = os.read(fd, before.st_size + 1)
                total += len(raw)
                require(total <= 8 * 1024 * 1024 and len(raw) == before.st_size
                        and identity(os.fstat(fd)) == identity(before), 'REFUSAL_STATE_CAS')
            finally:
                os.close(fd)
            rows[name] = {'kind': 'regular', 'identity': list(identity(before)), 'sha256': hashlib.sha256(raw).hexdigest()}
        require(identity(path.lstat()) == identity(before), 'REFUSAL_STATE_CAS')
    try:
        for name in PROTECTED_PATHS:
            visit(root / name, recursive=name in {'product/activations', 'product/staging', 'product/inputs', 'product/releases', 'product/infra'})
    except OSError:
        raise UpgradeError('REFUSAL_STATE_UNREADABLE') from None
    value = {'schema_version': 1, 'paths': rows}
    validate_protected(value)
    return value


def validate_protected(value: Any) -> None:
    require(type(value) is dict and set(value) == {'schema_version', 'paths'} and type(value['schema_version']) is int
            and value['schema_version'] == 1 and type(value['paths']) is dict
            and set(PROTECTED_PATHS) <= set(value['paths']) and len(value['paths']) <= 1024, 'REFUSAL_STATE_RECEIPT')
    recursive = ('product/activations/', 'product/staging/', 'product/inputs/', 'product/releases/', 'product/infra/')
    for name, row in value['paths'].items():
        require(type(name) is str and len(name) <= 2048 and not Path(name).is_absolute() and '..' not in Path(name).parts
                and (name in PROTECTED_PATHS or name.startswith(recursive)) and type(row) is dict, 'REFUSAL_STATE_RECEIPT')
        kind = row.get('kind')
        if kind == 'absent':
            require(name in PROTECTED_PATHS and row == {'kind': 'absent'}, 'REFUSAL_STATE_RECEIPT')
            continue
        keys = {'kind', 'identity'} | ({'sha256'} if kind == 'regular' else {'target_sha256'} if kind == 'symlink' else set())
        require(kind in {'regular', 'directory', 'symlink'} and set(row) == keys, 'REFUSAL_STATE_RECEIPT')
        info = row['identity']
        require(type(info) is list and len(info) == 8 and all(type(item) is int and item >= 0 for item in info)
                and info[1] > 0 and info[3] == 0 and info[4] > 0, 'REFUSAL_STATE_RECEIPT')
        if kind == 'symlink':
            require(stat.S_ISLNK(info[2]) and (name in {'product/active', 'product/.active-next'}
                or name.startswith('product/activations/') and Path(name).name in {'code', 'infra'}), 'REFUSAL_STATE_RECEIPT')
        else:
            require(not info[2] & 0o022 and (stat.S_ISREG(info[2]) if kind == 'regular' else stat.S_ISDIR(info[2])),
                    'REFUSAL_STATE_RECEIPT')
        if kind == 'regular':
            require(info[4] == 1 and info[5] <= 1024 * 1024, 'REFUSAL_STATE_RECEIPT')
        for key in keys - {'kind', 'identity'}:
            require(type(row[key]) is str and re.fullmatch('[0-9a-f]{64}', row[key]), 'REFUSAL_STATE_RECEIPT')


def run_refusal(port: Any, value: Any) -> None:
    require(not getattr(port, 'engine_recovery', False), 'REFUSAL_NOT_ENGINE_RECOVERY')
    port.upgrade_validate_inputs()
    # Current schema2 baseline only; historical schema1 acceptance is untouched.
    port.public(value.args(), timeout=5250)
    before = observe(port, 'source')
    protected = protected_state(ROOT)
    inputs = port.refusal_inputs()
    if REFUSALS[port.intent.case].cause == 'CHECKPOINT_ABSENT':
        require(protected['paths']['installation/product-upgrade.json'] == {'kind': 'absent'}, 'REFUSAL_CHECKPOINT_PRESENT')
    binding = {'schema_version': 1, 'case': port.intent.case, 'run_id': port.intent.run_id,
               'source_commit': port.intent.source_commit, 'root': str(ROOT)}
    port.journal.save('product-refusal-before.json', binding | {'protected': protected,
        'runtime': before, 'inputs': inputs, 'captured_monotonic_ns': time.monotonic_ns()})
    port.public_refusal(list(REFUSALS[port.intent.case].args), timeout=120)
    require(port.worker_settled, 'REFUSAL_CHILD_UNSETTLED')
    after = observe(port, 'noop')
    preserve(before, after, no_op=True)
    current = protected_state(ROOT)
    require(current == protected, 'REFUSAL_PROTECTED_STATE_CHANGED')
    current_inputs = port.refusal_inputs()
    require(current_inputs == inputs, 'REFUSAL_INPUTS_CHANGED')
    port.journal.save('product-refusal-after.json', binding | {'protected': current,
        'runtime': after, 'inputs': current_inputs, 'captured_monotonic_ns': time.monotonic_ns()})
    event(port, 'product-refusal-verified', {'status': 'REFUSAL_PRESERVED', 'case': port.intent.case,
        'command_executed': True, 'positive_upgrade': False, 'historical_scope': 'UNCHANGED',
        'recovery_performed': False, 'epic_complete': False})


@dataclass
class CliReceipt:
    journal: Any
    key: str
    binding: dict[str, Any]
    argv: list[str]
    args: list[str]
    released: bool = False
    fault: dict[str, Any] | None = None
    process: dict[str, int] | None = None
    environment: dict[str, str] | None = None
    inputs_sha256: str | None = None

    def require_approval(self) -> None:
        if not cli_is_effect(self.args):
            return
        approval = self.binding['approval']
        activation = self.binding['activation']
        require(self.binding['proposal_sha256'] is not None and approval is not None, 'CASE_CLI_GO_REQUIRED')
        if self.binding['platform'] == 'native':
            require((approval['phase'] == 'native-product-maintenance' and activation is not None
                     and activation['phase'] == 'paused-product-case')
                    or (approval['phase'] == 'native-product-engine-recovery' and activation is None),
                    'CASE_CLI_GO_REQUIRED')
        else:
            require(approval['phase'] in {'wsl-case-run', 'wsl-engine-recovery'} and activation is None,
                    'CASE_CLI_GO_REQUIRED')

    def start(self, process: dict[str, int], parent_start: int) -> None:
        executable = Path(self.argv[0]).resolve(strict=True)
        with executable.open('rb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022
                    and 0 < info.st_size <= 64 * 1024 * 1024, 'CASE_CLI_EXECUTABLE_BOUND')
            raw = stream.read(info.st_size + 1)
            after = os.fstat(stream.fileno())
            require(len(raw) == info.st_size and (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns)
                    == (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_ctime_ns), 'CASE_CLI_EXECUTABLE_DRIFT')
            executable_sha = hashlib.sha256(raw).hexdigest()
        self.journal.save(self.key + '-cli-start.json', self.binding | {
            'schema_version': 1, 'argv_sha256': digest(self.argv), 'args': self.args,
            'effect': cli_is_effect(self.args), 'executable': self.argv[0], 'executable_sha256': executable_sha,
            'parent': {'pid': os.getpid(), 'start_time': parent_start}, 'child': process,
            'started_at': utc_stamp(), 'started_monotonic_ns': time.monotonic_ns(),
        })
        self.process = process

    def release(self) -> None:
        self.released = True
        self.journal.save(self.key + '-cli-released.json', {
            'released_at': utc_stamp(), 'released_monotonic_ns': time.monotonic_ns(),
        })

    def prepare_fault(self, intent: dict[str, Any]) -> None:
        self.journal.save(self.key + '-cli-fault-intent.json', intent | {'process': self.process})

    def settle(self, pid: int, return_code: int, output_complete: bool, output_sha: str, error_sha: str) -> None:
        self.journal.save(self.key + '-cli-settled.json', {
            'pid': pid, 'return_code': return_code, 'released': self.released, 'group_absent': True,
            'output_complete': output_complete, 'stdout_sha256': output_sha, 'stderr_sha256': error_sha,
            'fault': self.fault, 'settled_at': utc_stamp(), 'settled_monotonic_ns': time.monotonic_ns(),
        })


def cli_fault_candidate(port: Any, receipt: CliReceipt | None) -> bool:
    if receipt is None or not port.upgrade_fault_armed:
        return False
    selected = RECIPES.get(port.intent.case)
    return selected is not None and selected.kind != 'product' and selected.fault and receipt.args == selected.update()

@dataclass(frozen=True)
class UpgradeRecipe:
    services: tuple[str, ...]
    preset: str = 'default'
    owner: str = 'swarm'
    exposure: str = 'published'
    kind: str = 'component'
    fault: bool = False
    add_traefik: bool = False

    def args(self, *, preview: bool = False, add: bool = False) -> list[str]:
        require(not add and self.kind != 'product', 'UPGRADE_PRODUCT_NOT_IMPLEMENTED')
        if self.kind == 'refusal':
            return ['setup', 'run', '--minimal', *(('--preview', '--json') if preview else ('--live', '--approve-live', '--json')),
                    '--node-provider', 'lxc_native', '--lxc-backend', 'incus']
        return ['setup', 'run', '--services', ','.join(self.services), '--service-profile', self.preset,
                '--stack-owner', self.owner, *(['--swagger-exposure', self.exposure] if 'swagger' in self.services else []),
                *(('--preview', '--json') if preview else ('--live', '--approve-live', '--json')),
                '--node-provider', 'lxc_native', '--lxc-backend', 'incus']

    def update(self, *, preview: bool = False, recover: bool = False) -> list[str]:
        require(self.kind != 'refusal', 'REFUSAL_COMMAND_NOT_ADMITTED')
        services = ('portainer',) if self.kind == 'portainer' else self.services
        args = ['services', 'update', '--services', ','.join(services)]
        if recover:
            args.append('--recover')
        elif len(services) == 1:
            args += ['--to', {'swagger': 'swagger-ui-5-32-7', 'traefik': 'traefik-3-7-5',
                             'portainer': 'portainer-ce-2.45.1'}[services[0]]]
        return args + (['--preview', '--json'] if preview else ['--live', '--approve-live', '--json'])


RECIPES: dict[str, UpgradeRecipe] = {
    'upgrade-swagger-swarm': UpgradeRecipe(('swagger',)),
    'upgrade-traefik-swarm': UpgradeRecipe(('traefik',)),
}
for _preset in ('default', 'service-access'):
    for _owner in ('swarm', 'portainer'):
        for _exposure in ('published', 'internal'):
            RECIPES[f'upgrade-batch-{_preset}-{_owner}-{_exposure}'] = UpgradeRecipe(
                ('swagger', 'traefik'), _preset, _owner, _exposure)
RECIPES |= {
    'recover-batch-swarm': UpgradeRecipe(('swagger', 'traefik'), exposure='internal', fault=True),
    'recover-batch-portainer': UpgradeRecipe(('swagger', 'traefik'), owner='portainer', fault=True),
    'upgrade-portainer': UpgradeRecipe(('swagger',), owner='portainer', kind='portainer'),
    'recover-portainer': UpgradeRecipe(('swagger',), owner='portainer', kind='portainer', fault=True),
    'upgrade-product-v1': UpgradeRecipe((), preset='service-access', kind='product'),
    'recover-product-v1': UpgradeRecipe((), preset='service-access', kind='product', fault=True),
}
RECIPES |= {name: UpgradeRecipe((), kind='refusal') for name in REFUSALS}
ALL_NAMES = (*FRESH_NAMES, *RECIPES)


def recipe(case: str) -> UpgradeRecipe:
    require(case in RECIPES, 'UPGRADE_CASE_UNKNOWN')
    value = RECIPES[case]
    require(value.kind != 'product', 'UPGRADE_PRODUCT_NOT_IMPLEMENTED')
    return value


def budgets(case: str, host: str, *, engine_recovery: bool = False) -> dict[str, int]:
    require(not engine_recovery or case not in REFUSALS, 'REFUSAL_NOT_ENGINE_RECOVERY')
    if case not in RECIPES:
        require(not engine_recovery, 'UPGRADE_ENGINE_RECOVERY_CASE')
        return ({'prepare': 1200, 'pause': 600, 'approval': 180, 'case': 5400, 'teardown': 900, 'restore': 600}
                if host == 'native' else {'prepare': 1200, 'admit': 300, 'case': 5400, 'disposal': 900, 'final': 300, 'recover': 900})
    value = RECIPES[case]
    case_seconds = (10800 if value.kind == 'product' else 3300) if engine_recovery else (18000 if value.kind == 'product' else 9000)
    require(host in {'native', 'wsl'}, 'UPGRADE_HOST_UNKNOWN')
    return ({'prepare': 1200, 'pause': 600, 'approval': 180, 'case': case_seconds, 'teardown': 900, 'restore': 600}
            if host == 'native' else {'prepare': 1200, 'admit': 300, 'case': case_seconds, 'disposal': 900, 'final': 300, 'recover': 900})


def baseline_environment(case: str) -> dict[str, str]:
    value = recipe(case)
    if value.kind == 'refusal':
        return {}
    module = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.catalog')
    catalog = module.NativeComponentCatalog(ROOT).load()
    names = importlib.import_module('tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml').IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT
    result: dict[str, str] = {}
    for service in catalog.services:
        if service.service_id not in value.services:
            continue
        transition = next((item for item in service.update_transitions if service.service_id in {'swagger', 'traefik'}), None)
        if transition is None:
            raise UpgradeError('UPGRADE_SOURCE_POLICY_MISSING')
        for name, identity in transition.source_versions.items():
            if identity.image_repository is None or identity.image_digest is None:
                raise UpgradeError('UPGRADE_SOURCE_UNPINNED')
            result[names[name]] = identity.image_repository + '@' + identity.image_digest
    if value.kind == 'portainer':
        policy = importlib.import_module('tiny_swarm_world.domain.lifecycle.portainer_upgrade')
        pins = policy.images(policy.SOURCE_VERSION)
        result |= {'TSW_PORTAINER_IMAGE': pins['portainer'], 'TSW_PORTAINER_AGENT_IMAGE': pins['portainer-agent']}
    return result


def event(port: Any, stage: str, value: dict[str, Any]) -> None:
    if hasattr(port, 'event'):
        port.event(stage, value)
    else:
        port.journal.save(stage + '-' + uuid4().hex + '.json', value | {'case': port.intent.case,
            'run_id': port.intent.run_id, 'source_commit': port.intent.source_commit})


def private_bytes(path: Path, *, limit: int = 8 * 1024 * 1024) -> bytes:
    for parent in path.parents:
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022, 'UPGRADE_JOURNAL_PARENT')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == 0 and before.st_nlink == 1
                and stat.S_IMODE(before.st_mode) == 0o600 and before.st_size <= limit, 'UPGRADE_JOURNAL_UNSAFE')
        raw = stream.read(limit + 1); after = os.fstat(stream.fileno())
    require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and len(raw) == before.st_size, 'UPGRADE_JOURNAL_DRIFT')
    return raw


def private_json(path: Path, *, limit: int = 8 * 1024 * 1024) -> Any:
    raw = private_bytes(path, limit=limit)
    def pairs(items):
        result = {}
        for name, content in items:
            require(name not in result, 'UPGRADE_DUPLICATE_JSON'); result[name] = content
        return result
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(UpgradeError('UPGRADE_NONFINITE_JSON')))


def private_file_hash(path: Path, *, optional: bool = False) -> str | None:
    if optional:
        try:
            path.lstat()
        except FileNotFoundError:
            for parent in path.parents:
                info = parent.lstat()
                require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022, 'UPGRADE_JOURNAL_PARENT')
            return None
    return hashlib.sha256(private_bytes(path)).hexdigest()


def proof_credentials(case: str, infra: Path, operator: dict[str, str]) -> tuple[str, str] | None:
    if 'traefik' not in recipe(case).services:
        return None
    value = private_json(infra / 'proof-credentials.json', limit=1024)
    require(isinstance(value, dict) and set(value) == {'schema_version', 'traefik_username', 'traefik_password'}
        and type(value['schema_version']) is int and value['schema_version'] == 1
        and type(value['traefik_username']) is str and bool(re.fullmatch('[A-Za-z0-9_.-]{1,64}', value['traefik_username']))
        and type(value['traefik_password']) is str and 1 <= len(value['traefik_password']) <= 512
        and not any(ord(c) < 32 or ord(c) == 127 for c in value['traefik_password']), 'UPGRADE_PROOF_CREDENTIAL_SCHEMA')
    from tiny_swarm_world.domain.configuration.configuration_contract import validate_traefik_htpasswd
    material = operator.get('TSW_TRAEFIK_GUI_USERS_HTPASSWD', '')
    try:
        validate_traefik_htpasswd(material)
    except ValueError:
        raise UpgradeError('UPGRADE_PROOF_HTPASSWD_INVALID') from None
    entries = material.splitlines()
    require(sum(line.partition(':')[0] == value['traefik_username'] for line in entries) == 1, 'UPGRADE_PROOF_USER_NOT_BOUND')
    return value['traefik_username'], value['traefik_password']


def authenticated_traefik(credentials: tuple[str, str], tls: Path, *, swagger_exposure: str | None = None) -> None:
    """Fixed local authority, verified TLS, bounded bodies; secrets stay in RAM."""
    import requests
    ca = tls / 'ca-bundle.pem'
    info = ca.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
        and not info.st_mode & 0o022 and info.st_size <= 65536, 'UPGRADE_CA_UNSAFE')
    for parent in ca.parents:
        row = parent.lstat()
        require(stat.S_ISDIR(row.st_mode) and row.st_uid == 0 and not row.st_mode & 0o022, 'UPGRADE_CA_PARENT_UNSAFE')
    with requests.Session() as session:
        session.trust_env = False
        def get(path: str, *, authenticated: bool) -> tuple[int, bytes]:
            with session.get('https://traefik.tsw.local' + path, auth=credentials if authenticated else None,
                    verify=str(ca), allow_redirects=False, timeout=(10, 10), stream=True) as response:
                content = bytearray()
                for chunk in response.iter_content(4096):
                    content.extend(chunk)
                    require(len(content) <= 65536, 'UPGRADE_AUTH_BODY_BOUND')
                return response.status_code, bytes(content)
        require(get('/api/rawdata', authenticated=False)[0] == 401, 'UPGRADE_AUTH_CHALLENGE_MISSING')
        status, body = get('/api/rawdata', authenticated=True)
        require(status == 200, 'UPGRADE_TRAEFIK_AUTH_FAILED')
        overview = json.loads(body)
        require(isinstance(overview, dict)
            and all(isinstance(overview.get(key), dict) for key in ('routers', 'services', 'middlewares')),
            'UPGRADE_TRAEFIK_API_SCHEMA')
        routers = list(overview['routers'].values())
        require(all(isinstance(row, dict) and isinstance(row.get('rule'), str) for row in routers), 'UPGRADE_TRAEFIK_ROUTER_SCHEMA')
        dashboard = [row for row in routers if 'traefik.tsw.local' in row['rule']]
        require(len(dashboard) == 1 and dashboard[0].get('service') == 'api@internal'
            and dashboard[0].get('status') == 'enabled', 'UPGRADE_TRAEFIK_DASHBOARD_ROUTE')
        swagger = [row for row in routers if 'swagger.tsw.local' in row['rule']]
        require(bool(swagger) == (swagger_exposure == 'published'), 'UPGRADE_SWAGGER_ROUTE_EXPOSURE')
        status, body = get('/dashboard/', authenticated=True)
        require(status == 200 and b'Traefik' in body, 'UPGRADE_TRAEFIK_DASHBOARD')


def checkpoint(port: Any) -> Any:
    value = recipe(port.intent.case)
    path = ROOT / '.tiny-swarm-world/installation' / ('portainer-upgrade.json' if value.kind == 'portainer' else 'component-update.json')
    if not path.exists():
        raise FileNotFoundError(path)
    raw = private_json(path)
    module = importlib.import_module('tiny_swarm_world.domain.lifecycle.' + ('portainer_upgrade' if value.kind == 'portainer' else 'update_execution'))
    return (module.PortainerCheckpoint if value.kind == 'portainer' else module.UpdateBatch).model_validate(raw)


def original_proof(port: Any) -> dict[str, Any]:
    files = list(port.journal.directory.glob('upgrade-proof-source-*.json'))
    require(len(files) == 1, 'UPGRADE_ORIGINAL_PROOF_AMBIGUOUS')
    value = private_json(files[0])
    require(value['case'] == port.intent.case and value['run_id'] == port.intent.run_id
        and value['source_commit'] == port.intent.source_commit, 'UPGRADE_ORIGINAL_PROOF_DRIFT')
    return value


def engine_binding(port: Any) -> dict[str, Any]:
    """Fresh full ownership/foreign proof for a separate recovery authorization."""
    value = recipe(port.intent.case)
    require(port.worker_settled, 'UPGRADE_CHILD_UNSETTLED')
    require(port.upgrade_children_settled(), 'UPGRADE_CHILD_UNSETTLED')
    if hasattr(port, 'fresh_source'):
        port.fresh_source()
        require(port.unit('snap.lxd.daemon.service') == 'inactive', 'UPGRADE_ORIGINAL_NOT_QUIESCED')
        for name, prior in port.prestate()['nodes'].items():
            actual = port.node(name)
            require(actual == prior | {'status': 'Stopped'}, 'UPGRADE_ORIGINAL_NODE_DRIFT')
    else:
        require(port.settled(), 'UPGRADE_CHILD_UNSETTLED')
        require(port.proposal is not None and port.source() == port.proposal['pins']
                and port.identity() == port.proposal['identity'], 'UPGRADE_RECOVERY_SOURCE_DRIFT')
    current = checkpoint(port)
    require(not current.settled, 'UPGRADE_NO_PENDING_OPERATION')
    original = original_proof(port)
    module = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.manifest')
    manifest = module.decode_manifest(private_json_bytes(ROOT / '.tiny-swarm-world/installation/manifest.json'))
    require(str(manifest.installation_id) == original['installation_id'] and manifest.service_preset == value.preset,
            'UPGRADE_RECOVERY_INSTALLATION_DRIFT')
    if value.kind == 'portainer':
        service = importlib.import_module('tiny_swarm_world.application.services.portainer_upgrade')
        service.PortainerUpgradeService._validate_manifest(current, manifest)
    else:
        service = importlib.import_module('tiny_swarm_world.application.services.component_execution')
        service._validate_manifest(current, manifest)
    port.prepare_disposal()
    require(port.owned is not None and port.owned.installation_id == original['installation_id'], 'UPGRADE_RECOVERY_UUID_UNPROVEN')
    graph = port.case_graph(port.owned)
    require(len(graph['instances']) == 3 and all(row['status'] == 'Running' for row in graph['instances'].values()),
            'UPGRADE_RECOVERY_RUNTIME_NOT_RUNNING')
    return {'installation_id': original['installation_id'], 'source_proof_sha256': digest(original),
            'pending_journal_sha256': digest(current.model_dump(mode='json')),
            'profile_sha256': port.owned.profile_sha256, 'owned_graph_sha256': digest(graph)}


def private_json_bytes(path: Path) -> bytes:
    # Reuse the exact nofollow/owner/mode/stability read, preserving JSON semantics.
    return canonical(private_json(path))


def poll_fault(port: Any, child: subprocess.Popen, *, before_signal: Callable[[dict[str, Any]], None] | None = None) -> None:
    """Called only by the existing owning supervisor, before its next wait."""
    if not getattr(port, 'upgrade_fault_armed', False) or child.poll() is not None:
        return
    try:
        current = checkpoint(port)
    except FileNotFoundError:
        return
    value = recipe(port.intent.case)
    baseline = getattr(port, 'upgrade_before', None)
    if baseline is None:
        raise UpgradeError('UPGRADE_FAULT_BASELINE_MISSING')
    installation = current.installation_id if value.kind == 'portainer' else current.original.installation_id
    require(str(installation) == baseline['installation_id'], 'UPGRADE_FAULT_INSTALLATION_DRIFT')
    ready = (current.backup_digest is not None and current.stage in {'backed_up', 'upgrading'} if value.kind == 'portainer'
             else current.direction == 'apply' and any(stage.outcome == 'committed' and stage.source != stage.target for stage in current.stages)
             and any(stage.outcome == 'applying' and stage.source != stage.target for stage in current.stages))
    if ready:
        checkpoint_sha = digest(current.model_dump(mode='json'))
        predicate = 'CHECKED_BACKUP' if value.kind == 'portainer' else 'PARTIAL_BATCH'
        event(port, 'upgrade-fault-intent', {'checkpoint_sha256': checkpoint_sha,
             'installation_id': baseline['installation_id'], 'predicate': predicate})
        identity = {'checkpoint_sha256': checkpoint_sha, 'predicate': predicate, 'process_group': child.pid,
                    'signal': int(signal.SIGTERM)}
        if before_signal is not None:
            before_signal(identity | {'prepared_at': utc_stamp(), 'prepared_monotonic_ns': time.monotonic_ns()})
        port.upgrade_fault_armed = False
        os.killpg(child.pid, signal.SIGTERM)
        port.upgrade_fault_observed = True
        raise FaultObserved('UPGRADE_ACTUAL_FAULT_OBSERVED', identity | {
            'sent_at': utc_stamp(), 'sent_monotonic_ns': time.monotonic_ns()})


def observe(port: Any, stage: str) -> dict[str, Any]:
    value = port.upgrade_helper(stage)
    require(isinstance(value, dict) and value.get('status') == 'UPGRADE_RUNTIME_VERIFIED', 'UPGRADE_PROOF_UNAVAILABLE')
    port.cli_selection = value.get('selection')
    event(port, 'upgrade-proof-' + stage, value)
    return value


def preserve(before: dict[str, Any], after: dict[str, Any], *, no_op: bool = False) -> None:
    for name in ('installation_id', 'node_ids', 'swarm_id', 'service_ids', 'mounts', 'data', 'owner_ids', 'preset', 'exposure'):
        require(before[name] == after[name], 'UPGRADE_PRESERVATION_' + name.upper())
    if no_op:
        for name in ('service_versions', 'tasks', 'managed_journals', 'backup_journal', 'stack_updates', 'manifest_sha256', 'manifest_token', 'component_journal_sha256'):
            require(before[name] == after[name], 'UPGRADE_NOOP_MUTATION_' + name.upper())


def cache_contracts():
    """Exactly four real policy references; no operator or catalog substitution."""
    from tiny_swarm_world.domain.artifacts import ContainerImageContract
    from tiny_swarm_world.domain.lifecycle.portainer_upgrade import SOURCE_VERSION, TARGET_VERSION, versions
    result = []
    for version in (SOURCE_VERSION, TARGET_VERSION):
        for name, identity in versions(version).items():
            if identity.image_repository is None or identity.image_digest is None:
                raise UpgradeError('UPGRADE_CACHE_POLICY_UNPINNED')
            result.append(ContainerImageContract(identity.image_repository, '@' + identity.image_digest, name, source='pull'))
    return tuple(result)


def cache_inventory(row: Any, reference: str) -> dict[str, Any]:
    require(isinstance(row, list) and len(row) == 1 and isinstance(row[0], dict), 'UPGRADE_CACHE_IMAGE_SCHEMA')
    image = row[0]
    require(isinstance(image.get('Id'), str) and re.fullmatch('sha256:[0-9a-f]{64}', image['Id'])
        and image.get('Architecture') == 'amd64' and image.get('Os') == 'linux'
        and isinstance(image.get('RepoDigests'), list) and 1 <= len(image['RepoDigests']) <= 32
        and all(type(item) is str for item in image['RepoDigests'])
        and len(set(image['RepoDigests'])) == len(image['RepoDigests']) and reference in image['RepoDigests'], 'UPGRADE_CACHE_IDENTITY')
    return {'id': image['Id'], 'repo_digests': sorted(image['RepoDigests']), 'reference': reference}


def verify_cache_nodes(after: dict[str, Any], nodes, references) -> None:
    require(set(after) == {node + ':' + ref for node in nodes for ref in references}, 'UPGRADE_CACHE_NODE_SET')
    for reference in references:
        rows = [after[node + ':' + reference] for node in nodes]
        require(all(isinstance(row, dict) and set(row) == {'id', 'repo_digests', 'reference'}
            and type(row['id']) is str and re.fullmatch('sha256:[0-9a-f]{64}', row['id'])
            and isinstance(row['repo_digests'], list) and 1 <= len(row['repo_digests']) <= 32
            and all(type(item) is str for item in row['repo_digests'])
            and row.get('reference') == reference and reference in row['repo_digests']
            for row in rows) and len({row['id'] for row in rows}) == 1, 'UPGRADE_CACHE_NODE_IMAGE_DRIFT')


class CacheRunner:
    """Only the actual publisher's four pinned inspect/pull commands, own nodes.

    Child clients stay in the fixture helper's process group. A parent timeout
    therefore reaches them; only our own Popen is terminated by a local timeout.
    No command supplied by a CLI/JSON input reaches this process port.
    """
    def __init__(self, operation, template, manager_uuid, worker_uuids, end: float):
        self.operation, self.template, self.manager_uuid, self.worker_uuids = operation, template, manager_uuid, worker_uuids
        self.end = end
        self.nodes = ('swarm-manager', 'swarm-worker-1', 'swarm-worker-2')
        self.references = tuple(contract.image_ref for contract in cache_contracts())
        self.pulled: set[tuple[str, str]] = set()
        self.unknown = False
        self.total_bytes = 0
        prefix = __package__ + '.' if __package__ else ''
        self.inventory = importlib.import_module(prefix + 'native_runtime_inventory')
        socket = {'incus_run': '/run/incus/unix.socket', 'incus_var_lib': '/var/lib/incus/unix.socket'}[template.endpoint_kind]
        self.env = self.inventory.ENV_BASE | {'INCUS_SOCKET': socket}

    def remaining(self) -> float:
        seconds = self.end - time.monotonic() - 10
        require(seconds > 0, 'UPGRADE_CACHE_DEADLINE')
        return min(60.0, seconds)

    def guard(self, node: str) -> None:
        self.remaining()
        self.operation.lease.require_active()
        self.operation.require_current_manifest()
        n = self.inventory
        runner = n.Runner()
        runner.started = min(runner.started, self.end - 10 - n.MAX_WALL_SECONDS)
        unit = n._systemctl_show(runner, 'incus.service')
        require(n._resolve_executable(runner, unit) == ('incus_system', 'system:incus'), 'UPGRADE_CACHE_DAEMON')
        require(n._endpoint(runner, self.env['INCUS_SOCKET'], unit='incus.service') == (self.template.endpoint_kind, True), 'UPGRADE_CACHE_ENDPOINT')
        n._require_full_local_access(self.env['INCUS_SOCKET'], incus=True)
        root = n._detail(runner, ['/usr/bin/incus', '--force-local'], 'server-root', (), 'default',
            command_id='cache_server_root', env=self.env, safe_args=[])
        n._validate_server_root(root, incus=True, cli_version='6.0.5')
        require(root['environment']['server_pid'] == unit['main_pid'], 'UPGRADE_CACHE_PEER_PID')
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.observations import instance_rows, owned_instance, worker_intent, worker_state
        raw = n._detail(runner, ['/usr/bin/incus', '--force-local'], 'instances', (node,), 'default',
            command_id='cache_owned_node', env=self.env, safe_args=[])
        # Scoped proxy devices contain the product's explicit nat/proxy_protocol
        # fields. Use its complete strict DTO, then exact owned specification;
        # never strip fields to fit the unrelated generic collector whitelist.
        rows = instance_rows([raw], 'default')
        require(set(rows) == {node}, 'UPGRADE_CACHE_NODE_IDENTITY')
        row = rows[node]
        if node == 'swarm-manager':
            state, identifier, exact = owned_instance(row, self.template)
            require(state == 'running' and identifier == self.manager_uuid and exact, 'UPGRADE_CACHE_MANAGER_UUID')
        else:
            observed = worker_state(row, self.template, worker_intent(self.template, node))
            require(observed.state == 'running' and observed.instance_uuid == self.worker_uuids[node]
                and observed.no_proxy, 'UPGRADE_CACHE_WORKER_UUID')
        require(n._systemctl_show(runner, 'incus.service') == unit, 'UPGRADE_CACHE_UNIT_DRIFT')
        self.operation.lease.require_active()
        self.operation.require_current_manifest()

    def run_bytes(self, args, **kwargs):
        raise UpgradeError('UPGRADE_CACHE_BYTES_DENIED')

    def run_text(self, args, **kwargs):
        import shlex
        from tiny_swarm_world.infrastructure.process import ProcessLaunchError
        # The shipped publisher treats this exact denied host probe as an
        # unavailable host cache; it may then perform the one permitted own pull.
        if list(args[:3]) == ['docker', 'image', 'inspect'] and len(args) == 4 and args[3] in self.references:
            raise ProcessLaunchError()
        require(len(args) == 7 and args[0] == 'incus' and args[1] == 'exec' and args[2] in self.nodes
            and list(args[3:6]) == ['--', 'sh', '-lc'] and kwargs.get('input') is None
            and kwargs.get('shell') is False, 'UPGRADE_CACHE_COMMAND_DENIED')
        node, script = args[2], args[6]
        pair = next(((action, reference) for action in ('inspect', 'pull') for reference in self.references
            if script == ('docker image inspect ' if action == 'inspect' else 'docker pull ') + shlex.quote(reference)), None)
        if pair is None:
            raise UpgradeError('UPGRADE_CACHE_COMMAND_DENIED')
        action, reference = pair
        self.guard(node)
        if action == 'pull':
            require((node, reference) not in self.pulled, 'UPGRADE_CACHE_REPLAY_DENIED')
            self.pulled.add((node, reference))
        # Bind the container's own Unix Docker endpoint and clear contexts/env;
        # a node login shell must not redirect this prerequisite elsewhere.
        docker_args = ['image', 'inspect', reference] if action == 'inspect' else ['pull', reference]
        argv = ['/usr/bin/incus', '--force-local', 'exec', node, '--project', 'default', '--',
                '/usr/bin/env', '-i', 'LC_ALL=C', 'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
                'DOCKER_CONFIG=/run/tsw440-image-cache-client', '/usr/bin/docker', '--host', 'unix:///var/run/docker.sock', *docker_args]
        result = self.process(argv, min(self.remaining(), float(kwargs.get('timeout') or 60)))
        self.guard(node)
        return result

    def process(self, argv: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        import selectors
        child = None
        selector = selectors.DefaultSelector()
        streams = [bytearray(), bytearray()]
        try:
            child = subprocess.Popen(argv, env=self.env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, shell=False, close_fds=True, start_new_session=False)
            if child.stdout is None or child.stderr is None:
                raise UpgradeError('UPGRADE_CACHE_PIPE')
            selector.register(child.stdout, selectors.EVENT_READ, 0)
            selector.register(child.stderr, selectors.EVENT_READ, 1)
            deadline = min(self.end - 10, time.monotonic() + timeout)
            while selector.get_map():
                require(time.monotonic() < deadline, 'UPGRADE_CACHE_EXEC_UNKNOWN')
                for key, _ in selector.select(min(.2, max(.001, deadline - time.monotonic()))):
                    data = os.read(key.fd, 65536)
                    streams[key.data].extend(data); self.total_bytes += len(data)
                    require(len(streams[key.data]) <= 2 * 1024 * 1024 and self.total_bytes <= 32 * 1024 * 1024, 'UPGRADE_CACHE_OUTPUT_UNKNOWN')
                    if not data:
                        selector.unregister(key.fileobj)
            status = child.wait(timeout=max(.01, deadline - time.monotonic()))
            return subprocess.CompletedProcess(argv, status, streams[0].decode('utf-8', 'strict'), streams[1].decode('utf-8', 'strict'))
        except BaseException:
            self.unknown = True
            raise
        finally:
            selector.close()
            if child is not None:
                if child.poll() is None:
                    child.kill(); child.wait(timeout=5)
                for pipe in (child.stdout, child.stderr):
                    if pipe is not None:
                        pipe.close()

    def image(self, node: str, reference: str, *, absent: bool = False) -> dict[str, Any] | None:
        import shlex
        result = self.run_text(['incus', 'exec', node, '--', 'sh', '-lc', 'docker image inspect ' + shlex.quote(reference)],
            input=None, shell=False, timeout=self.remaining())
        if result.returncode == 1 and absent and result.stderr.strip() == 'Error response from daemon: No such image: ' + reference:
            return None
        require(result.returncode == 0 and not result.stderr, 'UPGRADE_CACHE_INSPECTION_UNKNOWN')
        return cache_inventory(json.loads(result.stdout), reference)

    def clients_absent(self, node: str) -> None:
        require(node in self.nodes, 'UPGRADE_CACHE_NODE_DENIED')
        self.guard(node)
        script = ("set -eu; n=0; for f in /proc/[0-9]*/cmdline; do "
            "n=$((n+1)); test $n -le 4096 || exit 2; test \"$f\" != /proc/$$/cmdline || continue; "
            "if c=$(tr '\\000' ' ' < \"$f\" 2>/dev/null); then :; else test ! -e \"$f\" && continue; exit 2; fi; "
            "case \"$c\" in docker\\ *|/usr/bin/docker\\ *|/bin/docker\\ *) exit 1;; esac; "
            "done; printf CACHE_CLIENTS_ABSENT")
        result = self.process(['/usr/bin/incus', '--force-local', 'exec', node, '--project', 'default', '--',
            '/usr/bin/env', '-i', 'LC_ALL=C', 'PATH=/usr/sbin:/usr/bin:/sbin:/bin', '/bin/sh', '-c', script], self.remaining())
        self.guard(node)
        require(result.returncode == 0 and result.stdout == 'CACHE_CLIENTS_ABSENT' and not result.stderr,
                'UPGRADE_CACHE_CLIENTS_UNKNOWN')


def cache_steps(operation, runner):
    from tiny_swarm_world.application.services.artifacts.ensure_container_image import EnsureContainerImage
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.images.lxc_container_image_publisher import LxcContainerImagePublisher
    from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
    def ensure(node, contract):
        publisher = LxcContainerImagePublisher(backend=ManagedLxcBackend.INCUS, registry_username='', registry_password='',
            manager_node=node, timeout_seconds=60, process_runner=runner)
        real = EnsureContainerImage(publisher, contract)
        class ScopedStep:
            artifact_target_id = real.artifact_target_id
            verification_target_id = real.verification_target_id
            async def run(self):
                await operation.admit_runtime(); await operation.verify_effective_routes()
                await real.run()
            async def verify(self):
                await operation.admit_runtime(); await operation.verify_effective_routes()
                return await real.verify()
        return ScopedStep()
    return tuple(ensure(node, contract) for node in runner.nodes for contract in cache_contracts())


def prepare_target_cache(case: str, *, read_only: bool = False) -> dict[str, Any]:
    """One closed prerequisite; never a scoped public artifacts CLI substitute."""
    end = time.monotonic() + (170 if read_only else 900)
    value = recipe(case)
    require(value.kind == 'portainer', 'UPGRADE_CACHE_CASE_DENIED')
    from tiny_swarm_world.application.services.artifacts.workflows import ArtifactPrepareWorkflow, ArtifactWorkflowStatus
    from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import for_runtime
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import current_evidence
    from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service
    from tiny_swarm_world.domain.preflight import LiveConsent
    lifecycle = build_installation_lifecycle_service(ROOT)
    manifest = lifecycle.manifests.load().manifest
    if manifest is None or manifest.installation_profile is None:
        raise UpgradeError('UPGRADE_CACHE_SCOPED_REQUIRED')
    directory = Path(os.environ['TSW_LIVE_EVIDENCE_ROOT'])
    paths = list(directory.glob('upgrade-proof-source-*.json'))
    require(len(paths) == 1, 'UPGRADE_CACHE_SOURCE_PROOF_AMBIGUOUS')
    original = private_json(paths[0])
    require(original['installation_id'] == str(manifest.installation_id) and original['case'] == case
        and original['status'] == 'UPGRADE_RUNTIME_VERIFIED' and bool(re.fullmatch('[0-9a-f]{32}', original['run_id']))
        and manifest.service_preset == value.preset and set(manifest.requested_services) == set(value.services)
        and all(owner.owner == 'portainer' for owner in manifest.effective_stack_ownership().values()), 'UPGRADE_CACHE_SOURCE_PROOF_DRIFT')
    intent = private_json(directory / 'image-cache-intent.json')
    require(set(intent) == {'installation_id', 'graph_sha256', 'source_proof_sha256', 'contracts',
                           'deadline_monotonic_ns', 'boot_id_sha256'}
        and intent['installation_id'] == original['installation_id']
        and intent['source_proof_sha256'] == digest({key: item for key, item in original.items() if key not in {'case', 'run_id', 'source_commit'}})
        and intent['contracts'] == [contract.image_ref for contract in cache_contracts()], 'UPGRADE_CACHE_INTENT_DRIFT')
    require(intent['boot_id_sha256'] == hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes().strip()).hexdigest(),
            'UPGRADE_CACHE_BOOT_DRIFT')
    if not read_only:
        require(type(intent['deadline_monotonic_ns']) is int
            and 0 < intent['deadline_monotonic_ns'] - time.monotonic_ns() <= 900_000_000_000, 'UPGRADE_CACHE_INTENT_DEADLINE')
        end = min(end, intent['deadline_monotonic_ns'] / 1_000_000_000)
    prefix = __package__ + '.' if __package__ else ''
    journals = importlib.import_module(prefix + 'wsl_product_acceptance')
    if not read_only:
        journals.Journal(directory).save('image-cache-helper-started.json', {'case': case,
            'source_commit': original['source_commit'], 'installation_id': original['installation_id'], 'intent_sha256': digest(intent)})
    async def execute():
        with JsonInstallationOperationLock(ROOT).exclusive('portainer-upgrade') as lease:
            operation = await for_runtime(ROOT, lifecycle, lease, 'portainer-upgrade', LiveConsent(True, confirmed=True))
            require(original['source_commit'] == operation.intent.profile.controller_revision, 'UPGRADE_CACHE_SOURCE_REVISION')
            await operation.admit_runtime(); await operation.verify_effective_routes()
            template, manager_uuid, worker_uuids = current_evidence(ROOT, manifest)
            runner = CacheRunner(operation, template, manager_uuid, worker_uuids, end)
            if read_only:
                for node in runner.nodes:
                    runner.clients_absent(node)
                after = {node + ':' + ref: runner.image(node, ref) for node in runner.nodes for ref in runner.references}
                verify_cache_nodes(after, runner.nodes, runner.references)
                await operation.admit_runtime(); await operation.verify_effective_routes()
                require(lifecycle.manifests.load().manifest == manifest and time.monotonic() < end, 'UPGRADE_CACHE_MANIFEST_DRIFT')
                return {'status': 'UPGRADE_CACHE_OBSERVED_SETTLED', 'after': after,
                    'installation_id': str(manifest.installation_id), 'clients_absent': True, 'read_only': True}
            before = {node + ':' + ref: runner.image(node, ref, absent=True) for node in runner.nodes for ref in runner.references}
            steps = cache_steps(operation, runner)
            result = await ArtifactPrepareWorkflow(steps, requires_bootstrap=False).run()
            require(result.status == ArtifactWorkflowStatus.COMPLETED and not runner.unknown, 'UPGRADE_CACHE_EXEC_UNKNOWN')
            after = {node + ':' + ref: runner.image(node, ref) for node in runner.nodes for ref in runner.references}
            verify_cache_nodes(after, runner.nodes, runner.references)
            await operation.admit_runtime(); await operation.verify_effective_routes()
            require(lifecycle.manifests.load().manifest == manifest and time.monotonic() < end, 'UPGRADE_CACHE_MANIFEST_DRIFT')
            return {'status': 'UPGRADE_CACHE_VERIFIED', 'before': before, 'after': after,
                'actual_pulls': sorted(runner.pulled), 'installation_id': str(manifest.installation_id)}
    return asyncio.run(execute())


def cache_stage(port: Any, before: dict[str, Any]) -> None:
    """The owning case retains full graph and source-runtime equality authority."""
    outer_deadline = port.deadline
    port.deadline = min(outer_deadline, time.monotonic() + 900)
    try:
        _cache_stage(port, before)
    finally:
        # Restore the ORIGINAL absolute exercise deadline; elapsed time is never
        # restored and this cannot extend either case or containing authorization.
        port.deadline = outer_deadline


def _cache_stage(port: Any, before: dict[str, Any]) -> None:
    require(port.upgrade_children_settled(), 'UPGRADE_CACHE_CHILD_UNSETTLED')
    port.prepare_disposal()
    require(port.owned is not None, 'UPGRADE_CACHE_OWNERSHIP_MISSING')
    graph = port.case_graph(port.owned)
    port.journal.save('image-cache-intent.json', {'installation_id': before['installation_id'],
        'graph_sha256': digest(graph), 'source_proof_sha256': digest(before),
        'contracts': [contract.image_ref for contract in cache_contracts()],
        'deadline_monotonic_ns': int(port.deadline * 1_000_000_000),
        'boot_id_sha256': hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes().strip()).hexdigest()})
    port.cache_unknown = True
    result = port.upgrade_helper('cache-targets')
    require(result.get('status') == 'UPGRADE_CACHE_VERIFIED' and result.get('installation_id') == before['installation_id']
        and len(result.get('after', {})) == 12 and port.upgrade_children_settled(), 'UPGRADE_CACHE_OUTCOME_UNKNOWN')
    verify_cache_nodes(result['after'], ('swarm-manager', 'swarm-worker-1', 'swarm-worker-2'),
        tuple(contract.image_ref for contract in cache_contracts()))
    require(port.case_graph(port.owned) == graph, 'UPGRADE_CACHE_GRAPH_CHANGED')
    after = observe(port, 'cache-source')
    preserve(before, after, no_op=True)
    port.journal.save('image-cache-complete.json', {'status': 'CACHE_VERIFIED', 'proof': result,
        'graph_sha256': digest(graph), 'runtime_sha256': digest(after)})
    port.cache_unknown = False


def require_cache_settled(port: Any) -> None:
    """Unknown cache clients never authorize an incidental disposal attempt."""
    intent = port.journal.directory / 'image-cache-intent.json'
    complete = port.journal.directory / 'image-cache-complete.json'
    if not complete.exists():
        complete = port.journal.directory / 'image-cache-observed-settled.json'
    require(not getattr(port, 'cache_unknown', False) and (not intent.exists() or complete.exists()), 'UPGRADE_CACHE_RECOVERY_REQUIRED')
    if intent.exists():
        prior, settled = private_json(intent), private_json(complete)
        require(settled.get('status') == 'CACHE_VERIFIED' and settled.get('graph_sha256') == prior['graph_sha256']
            and settled.get('proof', {}).get('status') in {'UPGRADE_CACHE_VERIFIED', 'UPGRADE_CACHE_OBSERVED_SETTLED'}
            and settled['proof'].get('installation_id') == prior['installation_id']
            and len(settled['proof'].get('after', {})) == 12, 'UPGRADE_CACHE_SETTLEMENT_UNVERIFIED')
        verify_cache_nodes(settled['proof']['after'], ('swarm-manager', 'swarm-worker-1', 'swarm-worker-2'),
            tuple(contract.image_ref for contract in cache_contracts()))


def reconcile_cache(port: Any) -> None:
    """New read-only recovery proof, not a retry or a renewed writer grant."""
    directory = port.journal.directory
    if not (directory / 'image-cache-intent.json').exists() or (directory / 'image-cache-complete.json').exists():
        return
    if (directory / 'image-cache-observed-settled.json').exists():
        require_cache_settled(port)
        return
    require(port.upgrade_children_settled(), 'UPGRADE_CACHE_CHILD_UNSETTLED')
    prefix = __package__ + '.' if __package__ else ''
    old = importlib.import_module(prefix + 'preserving_product_acceptance')
    if port.owned is None:
        port.owned = old.decode_disposal(private_json(directory / 'disposal-intent.json'))
    original = original_proof(port)
    graph = port.case_graph(port.owned)
    prior = private_json(directory / 'image-cache-intent.json')
    require(digest(graph) == prior['graph_sha256'], 'UPGRADE_CACHE_RECONCILE_GRAPH')
    result = port.upgrade_helper('cache-reconcile')
    require(result.get('status') == 'UPGRADE_CACHE_OBSERVED_SETTLED' and result.get('read_only') is True
        and result.get('clients_absent') is True and port.upgrade_children_settled(), 'UPGRADE_CACHE_SETTLEMENT_UNKNOWN')
    require(port.case_graph(port.owned) == graph, 'UPGRADE_CACHE_RECONCILE_GRAPH')
    after = observe(port, 'cache-source')
    preserve(original, after, no_op=True)
    port.journal.save('image-cache-observed-settled.json', {'status': 'CACHE_VERIFIED', 'proof': result,
        'graph_sha256': digest(graph), 'runtime_sha256': digest(after)})
    port.cache_unknown = False


def run(port: Any, *, engine_recovery: bool = False) -> None:
    value = recipe(port.intent.case)
    if value.kind == 'refusal':
        require(not engine_recovery, 'REFUSAL_NOT_ENGINE_RECOVERY')
        run_refusal(port, value)
        return
    port.upgrade_validate_inputs()
    if engine_recovery:
        require(port.worker_settled, 'UPGRADE_CHILD_UNSETTLED')
        original = port.upgrade_original_proof()
        pending = checkpoint(port)
        require(not pending.settled, 'UPGRADE_NO_PENDING_OPERATION')
        port.public(value.update(preview=True, recover=True), timeout=120)
        result = json.loads(port.public(value.update(recover=True), timeout=3000))
        require(result.get('status') == 'recovered', 'UPGRADE_ENGINE_RECOVERY_FAILED')
        preserve(original, observe(port, 'recovered'))
        event(port, 'upgrade-engine-recovered', {'status': 'ENGINE_RECOVERED'})
        return
    port.upgrade_baseline = True
    outer_deadline = getattr(port, 'deadline', time.monotonic() + 9000)
    port.deadline = min(outer_deadline, time.monotonic() + 5400)
    try:
        port.public(value.args(), timeout=5250)
    finally:
        port.upgrade_baseline = False
    port.deadline = min(outer_deadline, time.monotonic() + 3600)
    before = observe(port, 'source')
    port.upgrade_before = before
    if port.intent.case == 'upgrade-batch-default-swarm-internal':
        single = UpgradeRecipe(('swagger',), value.preset, value.owner, value.exposure)
        port.public(['services', 'list', '--json'], timeout=120)
        preview = json.loads(port.public(single.update(preview=True), timeout=120))
        require(preview.get('status') == 'preview', 'UPGRADE_SINGLE_PREVIEW_BLOCKED')
        result = json.loads(port.public(single.update(), timeout=900))
        require(result.get('status') == 'completed', 'UPGRADE_SINGLE_APPLY_FAILED')
        preserve(before, observe(port, 'single-target'))
        preview = json.loads(port.public(single.update(preview=True, recover=True), timeout=120))
        require(preview.get('status') == 'preview', 'UPGRADE_SINGLE_RECOVERY_PREVIEW_BLOCKED')
        result = json.loads(port.public(single.update(recover=True), timeout=900))
        require(result.get('status') == 'recovered', 'UPGRADE_SINGLE_RECOVERY_FAILED')
        preserve(before, observe(port, 'recovered'))
    if value.kind == 'portainer':
        cache_stage(port, before)
    port.public(['services', 'updates', '--services', 'portainer' if value.kind == 'portainer' else ','.join(value.services), '--json'], timeout=120)
    plan = json.loads(port.public(value.update(preview=True), timeout=120))
    require(plan.get('status') not in {'blocked', 'unsupported'}, 'UPGRADE_PREVIEW_BLOCKED')
    if value.fault:
        port.upgrade_fault_armed = True
        port.upgrade_fault_observed = False
        try:
            port.public(value.update(), timeout=900)
        except FaultObserved:
            pass
        finally:
            port.upgrade_fault_armed = False
        require(port.upgrade_fault_observed and port.worker_settled, 'UPGRADE_NOT_EXERCISED')
        port.public(value.update(preview=True, recover=True), timeout=120)
        result = json.loads(port.public(value.update(recover=True), timeout=900))
        require(result.get('status') == 'recovered', 'UPGRADE_RECOVERY_FAILED')
        after = observe(port, 'recovered'); preserve(before, after)
        repeated = json.loads(port.public(value.update(recover=True), timeout=300))
        require(repeated.get('status') == ('no_op' if value.kind == 'portainer' else 'recovered'), 'UPGRADE_RECOVERY_REPEAT_FAILED')
        preserve(after, observe(port, 'noop'), no_op=True)
    else:
        result = json.loads(port.public(value.update(), timeout=900))
        require(result.get('status') == 'completed', 'UPGRADE_APPLY_FAILED')
        after = observe(port, 'target'); preserve(before, after)
        repeated = json.loads(port.public(value.update(), timeout=300))
        # The dedicated gateway emits literal no_op; the actual component
        # executor revalidates its settled batch and emits completed.
        require(repeated.get('status') == ('no_op' if value.kind == 'portainer' else 'completed'), 'UPGRADE_NOOP_FAILED')
        preserve(after, observe(port, 'noop'), no_op=True)
        if value.kind == 'component' and len(value.services) == 2:
            port.public(value.args(), timeout=900)
            preserve(before, observe(port, 'persistent'))
    event(port, 'upgrade-accepted', {'status': 'UPGRADE_CASE_VERIFIED', 'recipe': port.intent.case,
                                    'publication_qualified': False, 'epic_complete': False})


def _expected_component_versions(value: UpgradeRecipe, name: str, definition: Any, stage: str) -> Any:
    policy = definition.update_transitions[0]
    source = (stage in {'source', 'cache-source', 'recovered'} or value.kind == 'portainer'
              or stage == 'single-target' and name != 'swagger'
              or stage in {'noop', 'persistent'} and value.fault)
    return policy.source_versions if source else next(
        target.versions for target in definition.update_targets if target.target_id == policy.target_id)


def read_runtime(case: str, stage: str) -> dict[str, Any]:
    """Use production read-only observers; stdout contains no credentials or Env."""
    value = recipe(case)
    require(stage in {'source', 'cache-source', 'single-target', 'target', 'recovered', 'noop', 'persistent'}
        and (stage != 'single-target' or case == 'upgrade-batch-default-swarm-internal'), 'UPGRADE_PROOF_STAGE')
    import logging
    import shlex
    from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client import LxcPortainerHttpClient
    from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import for_runtime
    from tiny_swarm_world.infrastructure.adapters.lifecycle.completion_runtime import verify_selected_runtime, node_inventory
    from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi
    from tiny_swarm_world.infrastructure.composition_configuration import _required_operator_secret_value
    from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
    from tiny_swarm_world.domain.preflight import LiveConsent
    from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership

    lifecycle = build_installation_lifecycle_service(ROOT)
    snapshot = lifecycle.manifests.load()
    manifest = snapshot.manifest
    if manifest is None:
        raise UpgradeError('UPGRADE_MANIFEST_MISSING')
    require(not snapshot.diagnostics and manifest.schema_version == 2
        and manifest.service_preset == value.preset and set(manifest.requested_services) == set(value.services)
        and manifest.effective_exposure().get('swagger') == (value.exposure if 'swagger' in value.services else None)
        and all(owner.owner == value.owner for owner in manifest.effective_stack_ownership().values()), 'UPGRADE_MANIFEST_SCOPE')
    shell = LxcManagerShellGateway(backend=ManagedLxcBackend.INCUS, manager_node='swarm-manager',
        timeout_seconds=15, logger=logging.getLogger('upgrade_qualification_observer'))
    client = LxcPortainerHttpClient(backend=ManagedLxcBackend.INCUS, username='admin',
        password=_required_operator_secret_value('TSW_PORTAINER_ADMIN_PASSWORD'))._client()
    prefix = __package__ + '.' if __package__ else ''
    existing = importlib.import_module(prefix + 'preserving_product_acceptance')
    # The owning supervisor immediately rehashes the complete approved infra
    # before this child. Re-read the same fixed private bytes, without exporting.
    infra = Path(os.environ['TSW_INFRA_ROOT'])
    operator_path = infra / 'operator.env'
    fd = os.open(operator_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
            and stat.S_IMODE(info.st_mode) == 0o600 and info.st_size <= 65536, 'UPGRADE_OPERATOR_UNSAFE')
        raw_operator = stream.read(65537)
        after = os.fstat(stream.fileno())
        require((info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            and len(raw_operator) == info.st_size, 'UPGRADE_OPERATOR_DRIFT')
        operator = existing.operator_credentials(raw_operator)
    credentials = proof_credentials(case, infra, operator)
    def read(command: str) -> str:
        result = shell.run_manager_shell(command, check=False)
        require(result.returncode == 0 and len(result.stdout.encode()) <= 2 * 1024 * 1024, 'UPGRADE_READ_FAILED')
        return result.stdout.strip()
    swarm = read("docker info --format '{{.Swarm.Cluster.ID}}'")
    api = GuardedPortainerStackApi(client, lambda: swarm)
    node_names = ('swarm-manager', 'swarm-worker-1', 'swarm-worker-2')
    async def verify() -> dict[str, Any]:
        with JsonInstallationOperationLock(ROOT).exclusive('recovery') as lease:
            operation = await for_runtime(ROOT, lifecycle, lease, 'recovery', LiveConsent(True, confirmed=True))
            await operation.verify_effective_routes()
            await asyncio.to_thread(verify_selected_runtime, shell, client, ROOT, manifest, node_names)
            return await asyncio.to_thread(capture)
    def capture() -> dict[str, Any]:
        if credentials is not None:
            authenticated_traefik(credentials, Path(os.environ['TSW_LOCAL_TLS_STATE_ROOT']),
                swagger_exposure=value.exposure if 'swagger' in value.services else None)
        definitions = {service.service_id: service for service in lifecycle.catalog.load().services}
        selected = {item.component_id: item for item in manifest.components}
        for name in value.services:
            expected = _expected_component_versions(value, name, definitions[name], stage)
            for component, identity in expected.items():
                require(selected[component].desired.image_repository == identity.image_repository
                    and selected[component].desired.image_digest == identity.image_digest, 'UPGRADE_BUNDLE_PIN_DRIFT')
        if value.kind == 'portainer':
            policy = importlib.import_module('tiny_swarm_world.domain.lifecycle.portainer_upgrade')
            version = policy.SOURCE_VERSION if stage in {'source', 'cache-source', 'recovered'} or value.fault else policy.TARGET_VERSION
            for name, identity in policy.versions(version).items():
                require(selected[name].desired.image_repository == identity.image_repository
                    and selected[name].desired.image_digest == identity.image_digest, 'UPGRADE_GATEWAY_PIN_DRIFT')
        endpoint = api.local_endpoint()
        owners, stack_updates = {}, {}
        for name, owner in manifest.effective_stack_ownership().items():
            if isinstance(owner, PortainerOwnership):
                actual = api.inspect(name, owner.endpoint_id, owner.stack_id)
                require(actual.ownership == owner, 'UPGRADE_OWNER_DRIFT')
                owners[name] = {'endpoint': endpoint, 'stack': owner.stack_id,
                    'resource_control': owner.resource_control_id, 'ownership': owner.ownership_fingerprint}
                metadata = api._get('/api/stacks/' + str(owner.stack_id))
                require(isinstance(metadata, dict) and type(metadata.get('UpdateDate')) is int
                    and metadata['UpdateDate'] >= 0 and type(metadata.get('CreationDate')) is int
                    and metadata['CreationDate'] > 0, 'UPGRADE_STACK_COUNTERS_UNAVAILABLE')
                stack_updates[name] = {'updated': metadata.get('UpdateDate'), 'created': metadata.get('CreationDate')}
        import yaml
        names = sorted(service.service_id + '_' + member for service in definitions.values()
            if service.service_id in manifest.resolved_services and service.native_asset
            for member in yaml.safe_load((ROOT / service.native_asset).read_text())['services'])
        service_ids, service_versions, mounts, tasks = {}, {}, {}, {}
        template = '{"id":{{json .ID}},"version":{{json .Version.Index}},"mounts":{{json .Spec.TaskTemplate.ContainerSpec.Mounts}},"configs":{{json .Spec.TaskTemplate.ContainerSpec.Configs}},"secrets":{{json .Spec.TaskTemplate.ContainerSpec.Secrets}},"ports":{{json .Endpoint.Spec.Ports}}}'
        for name in names:
            row = json.loads(read('docker service inspect --format ' + shlex.quote(template) + ' -- ' + shlex.quote(name)))
            require(set(row) == {'id', 'version', 'mounts', 'configs', 'secrets', 'ports'}
                and isinstance(row['id'], str) and type(row['version']) is int, 'UPGRADE_SERVICE_READBACK')
            service_ids[name], service_versions[name] = row.pop('id'), row.pop('version')
            mounts[name] = row
            tasks[name] = read("docker service ps --no-trunc --filter desired-state=running --format '{{.ID}}' -- " + shlex.quote(name)).splitlines()
            require(tasks[name] and len(tasks[name]) <= 1024, 'UPGRADE_TASK_READBACK')
        data = {}
        if 'swagger' in value.services:
            data['swagger'] = read('sha256sum /var/lib/tiny-swarm-world/stacks/swagger/swagger/openapi.json /var/lib/tiny-swarm-world/stacks/swagger/nginx/default.conf')
            # Actual inside-container HTTP works for internal and published exposure.
            container = read("docker ps --filter label=com.docker.swarm.service.name=swagger_swagger-nginx --format '{{.ID}}'")
            require(bool(re.fullmatch('[0-9a-f]{12,64}', container)), 'UPGRADE_SWAGGER_CONTAINER')
            require(read('docker exec ' + container + " wget -q -O /dev/null http://127.0.0.1:8084/status && printf HTTP_OK") == 'HTTP_OK',
                    'UPGRADE_SWAGGER_API_HTTP')
            response = read('docker exec ' + container + " wget -q -O - http://tasks.swagger-ui:8080/")
            require('Swagger UI' in response, 'UPGRADE_SWAGGER_UI_HTTP')
        state = ROOT / '.tiny-swarm-world/installation'
        managed = {path.name: digest(private_json(path)) for path in state.glob('managed-stack-*.json')}
        backup = state / 'portainer-upgrade.json'
        manifest_hash = private_file_hash(state / 'manifest.json')
        if manifest_hash is None or manifest_hash != snapshot.token:
            raise UpgradeError('UPGRADE_MANIFEST_CHANGED_DURING_PROOF')
        component_hash = private_file_hash(state / 'component-update.json', optional=True)
        return {'status': 'UPGRADE_RUNTIME_VERIFIED', 'installation_id': str(manifest.installation_id),
            'preset': manifest.service_preset, 'exposure': manifest.effective_exposure(),
            'node_ids': node_inventory(shell, node_names), 'swarm_id': swarm, 'service_ids': service_ids,
            'service_versions': service_versions, 'mounts': mounts, 'tasks': tasks, 'data': data,
            'owner_ids': owners, 'stack_updates': stack_updates, 'managed_journals': managed,
            'backup_journal': digest(private_json(backup)) if backup.exists() else None,
            'manifest_sha256': manifest_hash, 'manifest_token': snapshot.token, 'manifest_schema': manifest.schema_version, 'component_journal_sha256': component_hash,
            'selection': selection_evidence(manifest, manifest_hash)}
    return asyncio.run(verify())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=tuple(RECIPES), required=True)
    parser.add_argument('--stage', choices=('source', 'cache-source', 'cache-targets', 'cache-reconcile', 'single-target', 'target', 'recovered', 'noop', 'persistent'), required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, 'UPGRADE_ROOT_REQUIRED')
    import sys
    sys.path.insert(0, str(ROOT / 'modules/tsw_core/src'))
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    print(json.dumps(prepare_target_cache(args.case, read_only=args.stage == 'cache-reconcile')
        if args.stage in {'cache-targets', 'cache-reconcile'} else read_runtime(args.case, args.stage)))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""One closed native product case between preserving LXD pause and recovery.

The old listener fixture and its approval remain untouched. Suite approvals
cover distinct, explicit budgets. ``binding.fixture_image`` is the inherited
maintenance snapshot compatibility field for this suite's Ubuntu fingerprint,
not an assertion that the Alpine listener fixture has run.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any, Iterator
from uuid import uuid4

if TYPE_CHECKING:
    from . import native_lxd_maintenance as native
    from . import owned_case_disposal as disposal
else:
    prefix = __package__ + '.' if __package__ else ''
    native = importlib.import_module(prefix + 'native_lxd_maintenance')
    disposal = importlib.import_module(prefix + 'owned_case_disposal')

ROOT = native.ROOT
PRIVATE = native.PRIVATE
BUDGETS = {'prepare': 1200, 'pause': 600, 'approval': 180, 'case': 5400, 'teardown': 900, 'restore': 600}
START_COVERAGE = sum(BUDGETS.values())
ACTIVATION_COVERAGE = BUDGETS['case'] + BUDGETS['teardown'] + BUDGETS['restore']
BOOTSTRAP = "import runpy,sys;sys.path.insert(0,'src');runpy.run_module('tiny_swarm_world',run_name='__main__')"
GATED_CHILD = "import os,sys;fd=int(sys.argv[1]);permit=os.read(fd,1);os.close(fd);os.execvpe(sys.argv[2],sys.argv[2:],os.environ) if permit==b'G' else sys.exit(125)"
PROFILE_STATE = ROOT / '.tiny-swarm-world/installation/profile-operation.json'
MANIFEST = ROOT / '.tiny-swarm-world/installation/manifest.json'
INFRA = PRIVATE / 'native-infra-override'
OPERATOR = INFRA / 'operator.env'
CAPABILITY = ROOT / 'infra/config/incus-profile-capabilities.json'
SUITE_FILES = ('tools/linux/qualification/preserving_product_acceptance.py',
    'tools/linux/qualification/owned_case_disposal.py', 'tests/tools/test_preserving_product_acceptance.py',
    'tests/tools/test_owned_case_disposal.py', 'infra/config/incus-profile-capabilities.json')


@dataclass(frozen=True)
class Recipe:
    services: tuple[str, ...]
    exposure: str = 'published'
    owner: str = 'swarm'
    add_traefik: bool = False

    def args(self, *, preview: bool = False, add: bool = False) -> list[str]:
        args = ['services', 'add', '--services', 'traefik'] if add else ['setup', 'run']
        if not add:
            args += ['--services', ','.join(self.services)] if self.services else ['--minimal']
        if self.services:
            args += ['--swagger-exposure', self.exposure, '--stack-owner', self.owner]
        return args + (['--preview', '--json'] if preview else ['--live', '--approve-live', '--json']) + [
            '--node-provider', 'lxc_native', '--lxc-backend', 'incus']


# Different requested/resolved ServiceID sets are separate cases. An owner or
# exposure change alone is never counted as the second optional selection.
RECIPES = {
    'minimal': Recipe(()),
    'swagger-internal': Recipe(('swagger',), 'internal'),
    'swagger-published': Recipe(('swagger',)),
    'swagger-traefik-swarm': Recipe(('swagger', 'traefik')),
    'swagger-traefik-portainer': Recipe(('swagger', 'traefik'), owner='portainer'),
    'swagger-add-traefik': Recipe(('swagger',), add_traefik=True),
    'full-swarm': Recipe(('swagger', 'traefik', 'nexus', 'jenkins', 'pulsar', 'sonarqube', 'infisical', 'service-access')),
    'full-portainer': Recipe(('swagger', 'traefik', 'nexus', 'jenkins', 'pulsar', 'sonarqube', 'infisical', 'service-access'), owner='portainer'),
}


@dataclass(frozen=True)
class SuiteIntent:
    run_id: str
    source_commit: str
    case: str
    ubuntu_fingerprint: str
    provider_config_sha256: str
    operator_config_sha256: str
    infra_sha256: str
    capability_sha256: str

    @classmethod
    def parse(cls, value: Any, source: str) -> 'SuiteIntent':
        native.require(isinstance(value, dict) and set(value) == {'run_id', 'source_commit', 'case',
            'ubuntu_fingerprint', 'provider_config_sha256', 'operator_config_sha256', 'infra_sha256', 'capability_sha256'}
            and all(type(item) is str for item in value.values()), 'SUITE_INTENT_SCHEMA_INVALID')
        native.require(bool(native.RUN_ID.fullmatch(value['run_id'])) and value['source_commit'] == source
            and bool(native.inventory.HEX40.fullmatch(source)) and value['case'] in RECIPES, 'SUITE_INTENT_IDENTITY_INVALID')
        native.require(all(native.HEX.fullmatch(value[key]) for key in ('ubuntu_fingerprint', 'provider_config_sha256',
            'operator_config_sha256', 'infra_sha256', 'capability_sha256')), 'SUITE_INTENT_DIGEST_INVALID')
        return cls(**value)


def validate_go(value: Any, proposal: dict[str, Any], proposal_sha: str, now: datetime, *, paused: bool,
                recovery: bool = False) -> datetime:
    keys = {'decision', 'schema_version', 'phase', 'proposal_sha256', 'source_commit', 'intent_sha256',
            'host_id_sha256', 'pins', 'budgets', 'expires_at_utc', 'reviews'}
    if paused:
        keys |= {'resource_sha256', 'route_sha256', 'preview_sha256'}
    native.require(isinstance(value, dict) and set(value) == keys and type(value['schema_version']) is int
        and value['schema_version'] == 1 and value['decision'] == 'GO'
        and not (paused and recovery) and value['phase'] == ('paused-product-case' if paused else
            'native-product-recovery' if recovery else 'native-product-maintenance'), 'SUITE_GO_SCHEMA_INVALID')
    native.require(isinstance(value['budgets'], dict) and all(type(item) is int for item in value['budgets'].values())
        and value['proposal_sha256'] == proposal_sha and value['budgets'] == BUDGETS
        and all(value[key] == proposal[key] for key in ('source_commit', 'intent_sha256', 'host_id_sha256', 'pins')),
        'SUITE_GO_BINDING_DRIFT')
    native.require(isinstance(value['reviews'], dict) and set(value['reviews']) == native.fixture.REVIEW_KEYS
        and all(item == 'APPROVED' for item in value['reviews'].values()), 'SUITE_GO_REVIEWS_MISSING')
    try:
        expiry = datetime.fromisoformat(value['expires_at_utc'])
        remaining = (expiry - now).total_seconds()
    except (ValueError, TypeError) as exc:
        raise native.MaintenanceError('SUITE_GO_EXPIRY_INVALID') from exc
    minimum = (BUDGETS['teardown'] + BUDGETS['restore']) if recovery else (ACTIVATION_COVERAGE if paused else START_COVERAGE)
    native.require(expiry.tzinfo is not None and minimum <= remaining <= minimum + 300, 'SUITE_GO_EXPIRED')
    if paused:
        native.require(all(type(value[key]) is str and native.HEX.fullmatch(value[key]) for key in (
            'resource_sha256', 'route_sha256', 'preview_sha256')), 'SUITE_GO_CAPTURE_INVALID')
    return expiry


def source_pins() -> tuple[str, dict[str, str]]:
    source, pins = native.source_pins()
    for relative in SUITE_FILES:
        path = ROOT / relative
        for parent in path.parents:
            info = parent.lstat()
            native.require(info.st_uid == 0 and not info.st_mode & 0o022 and parent.is_dir(), 'SOURCE_ANCESTOR_UNSAFE')
            if parent == ROOT:
                break
        info = path.lstat()
        native.require(path.is_file() and not path.is_symlink() and info.st_uid == 0 and not info.st_mode & 0o022,
                       'SOURCE_FILE_UNSAFE')
        raw = native.bounded(['/usr/bin/git', '--no-optional-locks', 'show', source + ':' + relative], 10)
        native.require(raw == path.read_bytes(), 'SOURCE_BLOB_DRIFT')
        pins[relative] = native.digest(raw)
    return source, pins


def tree_digest(root: Path) -> str:
    rows: list[tuple[str, str]] = []
    paths: list[Path] = []
    for path in root.rglob('*'):
        native.require(len(paths) < 4096, 'SUITE_INFRA_BOUND')
        paths.append(path)
    for path in sorted(paths):
        info = path.lstat()
        native.require(not path.is_symlink() and info.st_uid == 0 and not info.st_mode & 0o022, 'SUITE_INFRA_UNSAFE')
        if path.is_file():
            native.require(info.st_size <= native.LIMIT and len(rows) < 2048, 'SUITE_INFRA_BOUND')
            rows.append((str(path.relative_to(root)), native.digest(path.read_bytes())))
        else:
            native.require(path.is_dir(), 'SUITE_INFRA_UNSAFE')
    native.require(bool(rows), 'SUITE_INFRA_EMPTY')
    return native.digest(native.canonical(rows))


def operator_values(intent: SuiteIntent) -> dict[str, str]:
    native.require(native.digest(native.read_private(OPERATOR)) == intent.operator_config_sha256,
                   'SUITE_CONFIGURATION_DRIFT')
    module = importlib.import_module('tiny_swarm_world.infrastructure.adapters.configuration.configuration_sources')
    values = dict(module.ShellEnvFileConfigurationSource(OPERATOR).load())
    native.require(all(type(key) is str and key.startswith('TSW_') and type(value) is str for key, value in values.items()),
                   'SUITE_OPERATOR_VALUES_INVALID')
    return values


def check_prerequisites(intent: SuiteIntent) -> None:
    """No import, alias change, matrix promotion or data mutation here."""
    info = CAPABILITY.lstat()
    native.require(CAPABILITY.is_file() and not CAPABILITY.is_symlink() and info.st_uid == 0
                   and not info.st_mode & 0o022 and info.st_size <= 65536, 'SUITE_CAPABILITY_UNSAFE')
    native.require(native.digest(CAPABILITY.read_bytes())
                   == intent.capability_sha256, 'SUITE_CAPABILITY_DRIFT')
    matrix = importlib.import_module('tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository')
    admission = matrix.IncusProfileCapabilityRepository(ROOT).load()
    native.require(admission.admits('6.0.5', '6.0.5'), 'BOTH_HOST_CAPABILITY_NOT_ADMITTED')
    entry = next(row for row in admission.admitted_versions if (row.client_version, row.server_version) == ('6.0.5', '6.0.5'))
    reference = native.bounded(['/usr/bin/git', '--no-optional-locks', 'show', entry.fixture_source_revision + ':' + native.FILES[4]], 10)
    native.require(native.digest(reference) == entry.fixture_sha256, 'SUITE_CAPABILITY_SOURCE_MISMATCH')
    # The immutable promotion record is required in addition to its public matrix
    # entry: both actual host listener observations must identify this admission.
    proof = native.inventory.strict_json(native.read_private(PRIVATE / 'both-host-profile-capability.json'))
    native.require(isinstance(proof, dict) and set(proof) == {'capability_sha256', 'client', 'server', 'hosts'}
        and proof['capability_sha256'] == intent.capability_sha256 and proof['client'] == proof['server'] == '6.0.5'
        and isinstance(proof['hosts'], dict) and set(proof['hosts']) == {'native_linux', 'wsl2'}
        and all(isinstance(row, dict) and set(row) == {'decision', 'artifact_sha256', 'source_commit'}
            and row['decision'] == 'PASS' and type(row['artifact_sha256']) is str and native.HEX.fullmatch(row['artifact_sha256'])
            and type(row['source_commit']) is str and native.inventory.HEX40.fullmatch(row['source_commit'])
            for row in proof['hosts'].values()), 'BOTH_HOST_CAPABILITY_NOT_PROVEN')
    for host, receipt in proof['hosts'].items():
        raw = native.read_private(PRIVATE / ('profile-capability-' + host + '.json'))
        actual = native.inventory.strict_json(raw)
        native.require(native.digest(raw) == receipt['artifact_sha256'] and isinstance(actual, dict)
            and actual.get('status') == 'PASS' and actual.get('source_commit') == receipt['source_commit']
            and actual.get('runner_sha256') == entry.fixture_sha256
            and actual.get('server_version') == '6.0.5' and type(actual.get('go_sha256')) is str
            and native.HEX.fullmatch(actual['go_sha256']), 'BOTH_HOST_CAPABILITY_ARTIFACT_MISMATCH')
        actual_blob = native.bounded(['/usr/bin/git', '--no-optional-locks', 'show', receipt['source_commit'] + ':' + native.FILES[4]], 10)
        native.require(native.digest(actual_blob) == entry.fixture_sha256, 'BOTH_HOST_CAPABILITY_SOURCE_MISMATCH')
    native.require(tree_digest(INFRA) == intent.infra_sha256
        and native.digest(native.read_private(OPERATOR)) == intent.operator_config_sha256, 'SUITE_CONFIGURATION_DRIFT')
    resource = importlib.import_module((__package__ + '.' if __package__ else '') + 'native_resource_admission')
    resource.selection(resource.read_config(intent.provider_config_sha256))


class DetailsRunner(native.ConfigRunner):
    """Keep raw metadata in RAM for UUID/spec checks; never export raw streams."""
    def __init__(self) -> None:
        super().__init__()
        self.details: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}

    def run(self, argv: list[str], **kwargs: Any) -> tuple[int, bytes, bytes]:
        result = super().run(argv, **kwargs)
        command = kwargs['command_id']
        if (command.endswith(('_show', '_config_show', '_config_show_expanded')) or '_server_root_' in command) and result[0] == 0:
            envelope = native.inventory.strict_json(result[1])
            row = envelope.get('metadata') if isinstance(envelope, dict) else None
            if isinstance(row, dict):
                self.details[(command, tuple(kwargs.get('safe_args', [])))] = row
        return result


class SuiteNativePort(native.NativePort):
    def __init__(self, intent: SuiteIntent, journal: native.Journal, proposal: dict[str, Any] | None = None):
        super().__init__(intent.source_commit, native.digest(native.canonical(asdict(intent))), time.monotonic() + BUDGETS['prepare'])
        self.intent, self.journal, self.proposal = intent, journal, proposal
        self.last_artifact: dict[str, Any] = {}
        self.details: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        self.owned: disposal.DisposalIntent | None = None
        self.worker_settled = True
        self.restore_safe = True
        self.pause_started = False
        self.in_case_window = False
        self.approval_recheck = False
        self.disposal_lease: Any | None = None

    def prestate(self) -> dict[str, Any]:
        if self.baseline is None:
            raise native.MaintenanceError('SUITE_PRESTATE_MISSING')
        return self.baseline

    def current_proposal(self) -> dict[str, Any]:
        if self.proposal is None:
            raise native.MaintenanceError('SUITE_PROPOSAL_MISSING')
        return self.proposal

    def begin_recovery(self) -> None:
        self.in_case_window = False
        super().begin_recovery()
        if not self.restore_safe and self.worker_settled:
            self.restore_safe = self.fast_stopped_remainder()

    def fast_stopped_remainder(self) -> bool:
        """A fixed read-only safety gate, charged to the existing restore reserve."""
        try:
            route = native.inventory.strict_json(native.read_private(self.journal.directory / 'paused-route.json'))
            # Call the unchanged binding proof directly: the new safety decision
            # is what this read-only probe is establishing, not an inherited GO.
            super().check_binding(self.prestate(), active=False)
            if self.unit(native.SOCKET) != 'inactive':
                return False
            self.wait_operations()
            runner = native.inventory.Runner()
            remaining = min(60.0, self.deadline - time.monotonic() - 5)
            if remaining <= 0:
                return False
            runner.started = runner.clock() - (native.inventory.MAX_WALL_SECONDS - remaining)
            rows = native.inventory._detail(runner, ['/usr/bin/incus', '--force-local'], 'instance-list', (), 'default',
                command_id='suite_recovery_instance_list', env=self.incus_env(self.prestate()), safe_args=['default'])
            known = {} if self.owned is None else {node.name: node for node in self.owned.nodes}
            seen: set[str] = set()
            for row in rows:
                row = native.inventory._validate_instance_config(row, row.get('name'), 'default')
                name = row['name']
                if name in seen or name not in known or self.owned is None:
                    return False
                seen.add(name)
                config = row['config']
                if ((row['status'], row['status_code']) != ('Stopped', 102)
                    or config.get('volatile.uuid') != known[name].uuid
                    or config.get(disposal.INSTALLATION) != self.owned.installation_id
                    or config.get(disposal.OPERATION) != self.owned.operation_id
                    or disposal.specification(row) != known[name].specification_sha256):
                    return False
            super().check_binding(self.prestate(), active=False)
            raw = self.command(['/usr/bin/ss', '-H', '-ltnp'], 15)
            return listener_digest(raw) == route['listeners_sha256']
        except (native.MaintenanceError, native.inventory.InventoryError, OSError, ValueError, TypeError):
            return False

    def start_pause_budget(self) -> None:
        if not self.pause_started:
            self.phase('pause')
            self.pause_started = True

    def stop_node(self, name: str) -> None:
        self.start_pause_budget()
        super().stop_node(name)

    def shutdown(self) -> None:
        self.start_pause_budget()
        super().shutdown()

    def fresh_source(self) -> None:
        source, _pins = source_pins()
        native.require(source == self.source, 'SOURCE_HEAD_DRIFT')
        check_prerequisites(self.intent)

    def capture(self) -> tuple[dict[str, Any], DetailsRunner]:
        self.budget()
        native.require(self.deadline - time.monotonic() >= (6 if self.approval_recheck else 300), 'INVENTORY_RESERVE_MISSING')
        self.fresh_source()
        if self.in_case_window:
            native.require(self.baseline is not None, 'SUITE_PRESTATE_MISSING')
            self.check_binding(self.prestate(), active=False)
            native.require(self.unit(native.SOCKET) == 'inactive', 'DAEMON_REACTIVATED')
        runner = DetailsRunner()
        if self.approval_recheck:
            # Explicit read-only final route recheck shares the 180-second
            # approval phase, rather than resetting a fresh 300-second phase.
            remaining = self.deadline - time.monotonic() - 5
            native.require(remaining > 0, 'SUITE_APPROVAL_RECHECK_EXPIRED')
            runner.started = runner.clock() - (native.inventory.MAX_WALL_SECONDS - min(native.inventory.MAX_WALL_SECONDS, remaining))
        artifact = native.inventory.capture(self.source, runner=runner, image_aware=True)
        native.inventory._validate_artifact(artifact)
        native.require(type(artifact['schema_version']) is int and artifact['schema_version'] == 6, 'SUITE_INVENTORY_SCHEMA_INVALID')
        self.last_artifact, self.details = artifact, runner.details
        return artifact, runner

    def snapshot(self) -> dict[str, Any]:
        artifact, runner = self.capture()
        native.require([row['project'] for row in artifact['lxd_projects']] == ['default']
            and {row['name'] for row in artifact['lxd_projects'][0]['instances']} == set(native.NODES), 'LXD_NODE_SET_DRIFT')
        native.require(len(artifact['lxd_executables']) == 1 and artifact['lxd_executables'][0]['identity_id'] == 'lxd_snap'
            and len(artifact['incus_executables']) == 1, 'SUITE_RUNTIME_IDENTITY_DRIFT')
        preserve = {key: artifact[key] for key in ('lxd_projects', 'incus_projects', 'lxd_pools', 'incus_pools',
            'lxd_admission', 'incus_admission', 'sockets')}
        preserve.update(configuration_digests=runner.configs, incus_units=artifact['incus_units'],
            lxd_units=[{key: value for key, value in row.items() if key != 'main_pid'} for row in artifact['lxd_units']])
        binding = {'installed': self.installed_binding(),
            'incus_unit': next(row for row in artifact['incus_units'] if row['unit'] == 'incus.service'),
            'lxd_initial_pid': (self.baseline['binding']['lxd_initial_pid'] if self.baseline is not None else artifact['lxd_executables'][0]['main_pid']),
            'fixture_image': self.intent.ubuntu_fingerprint}
        return native.validate_snapshot({'nodes': {name: self.node(name) for name in native.NODES},
            'socket': self.unit(native.SOCKET), 'preserve': preserve, 'binding': binding})

    def check_binding(self, baseline: dict[str, Any], *, active: bool) -> None:
        if self.recovering and not active:
            native.require(self.worker_settled and self.restore_safe, 'CASE_LISTENER_RECOVERY_UNSAFE')
        super().check_binding(baseline, active=active)

    def admit_empty(self, baseline: dict[str, Any]) -> None:
        default = next(row for row in baseline['preserve']['incus_projects'] if row['project'] == 'default')
        native.require(not default['instances'] and not any(path.exists() or path.is_symlink() for path in (MANIFEST, PROFILE_STATE)),
                       'SUITE_FRESH_INSTALLATION_REQUIRED')
        anchor = MANIFEST.parent
        native.require(not anchor.exists() or not anchor.is_symlink() and all(
            path.name == 'operation.lock' and not path.is_symlink() for path in anchor.iterdir()), 'SUITE_STALE_INSTALLATION_STATE')
        native.require(not any(row['name'].startswith('tsw-manager-') for row in default['profiles']), 'SUITE_PROFILE_COLLISION')
        preparation = importlib.import_module('tiny_swarm_world.infrastructure.adapters.incus_preparation.configuration')
        resources = importlib.import_module('tiny_swarm_world.infrastructure.adapters.incus_preparation.resources')
        requirements = preparation.load_requirements(INFRA / 'config/node-providers/provider_config.yaml')
        profiles = [row for (command, args), row in self.details.items()
                    if command == 'incus_profile_show' and len(args) == 2 and args[1] == 'default']
        native.require(not resources.profile_actions(requirements, {'profiles': profiles}), 'SUITE_BASE_PROFILE_PREPARATION_REQUIRED')
        images = [row for row in default['images'] if row['fingerprint'] == self.intent.ubuntu_fingerprint]
        native.require(len(images) == 1, 'SUITE_IMAGE_NOT_PRESTAGED')
        image = self.details.get(('incus_image_show', (self.intent.ubuntu_fingerprint, 'default')))
        native.require(isinstance(image, dict) and image.get('architecture') == 'x86_64'
            and isinstance(image.get('properties'), dict) and image['properties'].get('os', '').casefold() == 'ubuntu'
            and image['properties'].get('release') in {'24.04', 'noble'}, 'SUITE_UBUNTU_IMAGE_METADATA_MISMATCH')
        runner = native.inventory.Runner()
        self.check_binding(baseline, active=True)
        response = native.inventory._parse_json_command(runner, ['/usr/bin/incus', '--force-local', 'query', '--request', 'GET', '--raw',
            '/1.0/images/aliases/ubuntu-24.04?project=default'], command_id='suite_ubuntu_alias_show',
            env=self.incus_env(baseline), safe_args=[])
        native.require(isinstance(response, dict) and set(response) == {'type', 'status', 'status_code', 'operation', 'error_code', 'error', 'metadata'}
            and response['type'] == 'sync' and response['status'] == 'Success' and type(response['status_code']) is int
            and response['status_code'] == 200 and response['operation'] == '' and type(response['error_code']) is int
            and response['error_code'] == 0 and response['error'] == '' and isinstance(response['metadata'], dict)
            and response['metadata'] == {
                'name': 'ubuntu-24.04', 'target': self.intent.ubuntu_fingerprint, 'type': 'container',
                'description': response['metadata'].get('description')}, 'SUITE_IMAGE_ALIAS_DRIFT')
        native.require(type(response['metadata']['description']) is str, 'SUITE_IMAGE_ALIAS_DRIFT')
        self.check_binding(baseline, active=True)

    @staticmethod
    def incus_env(baseline: dict[str, Any]) -> dict[str, str]:
        kind = native.incus_socket(baseline)['listen']
        return native.ENV | {'INCUS_SOCKET': '/run/incus/unix.socket' if kind == 'incus_run' else '/var/lib/incus/unix.socket',
                             'INCUS_CONF': '/proc/self'}

    def incus_effect(self, args: list[str], timeout: int) -> None:
        native.require(self.baseline is not None and self.worker_settled, 'CASE_WORKER_NOT_SETTLED')
        native.require(self.owned is not None and self.disposal_lease is not None, 'CASE_DISPOSAL_LEASE_REQUIRED')
        lease = self.disposal_lease
        if lease is None:
            raise native.MaintenanceError('CASE_DISPOSAL_LEASE_REQUIRED')
        lease.require_active()
        self.check_binding(self.prestate(), active=False)
        self.fresh_source()
        names = set() if self.owned is None else {node.name for node in self.owned.nodes}
        allowed = (args[:3] == ['--project', 'default', 'stop'] and len(args) == 6 and args[3] in names and args[4:] == ['--timeout', '60']
            or args[:3] == ['--project', 'default', 'delete'] and len(args) == 4 and args[3] in names
            or args[:4] == ['--project', 'default', 'profile', 'delete'] and len(args) == 5
                and self.owned is not None and args[4] == self.owned.profile_name)
        native.require(allowed, 'CASE_COMMAND_NOT_ALLOWED')
        env = self.incus_env(self.prestate())
        self.command(['/usr/bin/env', '-i', *(key + '=' + value for key, value in sorted(env.items())),
                      '/usr/bin/incus', '--force-local', *args], timeout)

    def phase(self, name: str) -> None:
        native.require(name in BUDGETS, 'SUITE_PHASE_INVALID')
        self.deadline = time.monotonic() + BUDGETS[name]

    def run_fixture(self) -> None:
        """The inherited protocol name dispatches exactly one compiled product recipe."""
        native.require(self.proposal is not None and self.baseline is not None, 'SUITE_PROPOSAL_MISSING')
        self.start_pause_budget()
        self.in_case_window = True
        self.check_binding(self.prestate(), active=False)
        resource_raw = self.command([self.interpreter(), '-E', '-s', '-B', str(ROOT / native.RESOURCE_SCRIPT),
            '--source', self.source, '--config-sha256', self.intent.provider_config_sha256], 60)
        resource = native.inventory.strict_json(resource_raw)
        native.require(isinstance(resource, dict) and set(resource.get('checks', {})) >= {'incus_version'}, 'SUITE_RESOURCE_INVALID')
        # The unchanged resource inspector intentionally leaves version to the
        # trusted collector admission; this fills it only from actual paired API.
        artifact, _runner = self.capture()
        admission = artifact['incus_admission']
        native.require(admission['initial'] == admission['final'] and admission['initial']['server_version'] == '6.0.5', 'SUITE_VERSION_DRIFT')
        self.check_binding(self.prestate(), active=False)
        _code, version_raw, _error = native.inventory.Runner().run(['/usr/bin/incus', '--force-local', 'version'],
            command_id='suite_incus_version', env=self.incus_env(self.prestate()), safe_args=[])
        version = version_raw.decode('utf-8', 'strict')
        clients = re.findall(r'^Client version: ([0-9.]+)$', version, re.M)
        servers = re.findall(r'^Server version: ([0-9.]+)$', version, re.M)
        self.check_binding(self.prestate(), active=False)
        resource['observed'].update(incus_client_version=clients, incus_server_version=servers)
        resource['checks']['incus_version'] = clients == servers == ['6.0.5']
        native.require(all(type(item) is bool and item for item in resource['checks'].values()), 'SUITE_RESOURCE_NOT_PASS')
        resource['decision'] = 'PASS'
        self.journal.save('paused-resource.json', resource)
        route = self.route_capture()
        self.journal.save('paused-route.json', route)
        ready = self.child([self.interpreter(), '-E', '-s', '-B', str(Path(__file__)), 'prerequisites'], 180)
        native.require(native.inventory.strict_json(ready) == {'status': 'SHARED_PREREQUISITES_READY'}, 'SUITE_SHARED_PREPARATION_REQUIRED')
        recipe = RECIPES[self.intent.case]
        preview = validate_preview(self.public(recipe.args(preview=True), 120), recipe)
        previews = {'initial': preview}
        if recipe.add_traefik:
            final_recipe = Recipe(('swagger', 'traefik'), recipe.exposure, recipe.owner)
            previews['final'] = validate_preview(self.public(final_recipe.args(preview=True), 120), final_recipe)
        self.journal.save('paused-preview.json', previews)
        self.await_activation(resource, route, native.digest(native.canonical(previews)))
        self.phase('case')
        self.restore_safe = False
        failure: BaseException | None = None
        try:
            self.journal.save('case-started.json', {'case': self.intent.case, 'source_commit': self.source})
            self.public(RECIPES[self.intent.case].args(), 4500)
            if RECIPES[self.intent.case].add_traefik:
                self.public(RECIPES[self.intent.case].args(add=True), 600)
            self.observe_completion()
            self.journal.save('case-verified.json', {'case': self.intent.case, 'source_commit': self.source})
        except BaseException as exc:
            failure = exc
            self.journal.save('case-failure.json', {'case': self.intent.case, 'reason': native.failure_reason(exc)})
        finally:
            self.phase('teardown')
            try:
                self.prepare_disposal()
                if self.owned is not None:
                    with self.installation_lease():
                        disposal.dispose(disposal.IncusDisposalPort(self, self.owned, self.journal), self.owned)
                self.restore_safe = self.listeners_clear(route)
                native.require(self.restore_safe, 'CASE_LISTENERS_REMAIN')
            except BaseException:
                # Deletion failure may still leave the exact owned nodes safely
                # stopped. Never stop/adopt an unknown replacement to restore LXD.
                self.restore_safe = self.safe_stopped_remainder(route)
                raise
        if failure is not None:
            raise failure

    def await_activation(self, resource: dict[str, Any], route: dict[str, Any], preview_sha: str) -> None:
        self.phase('approval')
        expected = {'resource_sha256': native.digest(native.canonical(resource)),
                    'route_sha256': native.digest(native.canonical(route)), 'preview_sha256': preview_sha}
        self.journal.save('paused-admission-pending.json', expected | {'status': 'PAUSED_ADMISSION_PENDING'})
        path = self.journal.directory / 'activation.json'
        while time.monotonic() < self.deadline:
            if path.exists() or path.is_symlink():
                raw = native.read_private(path)
                value = native.inventory.strict_json(raw)
                native.require(self.proposal is not None, 'SUITE_PROPOSAL_MISSING')
                proposal = self.current_proposal()
                validate_go(value, proposal, native.digest(native.canonical(proposal)), datetime.now(timezone.utc), paused=True)
                native.require(all(value[key] == item for key, item in expected.items()), 'SUITE_PAUSED_CAPTURE_DRIFT')
                self.approval_recheck = True
                try:
                    native.require(self.route_capture() == route, 'SUITE_ROUTE_DRIFT')
                finally:
                    self.approval_recheck = False
                self.fresh_source()
                self.journal.save('activation-accepted.json', {'activation_sha256': native.digest(raw)})
                return
            time.sleep(.25)
        raise native.MaintenanceError('SUITE_ACTIVATION_TIMEOUT')

    def route_capture(self) -> dict[str, Any]:
        native.require(self.baseline is not None, 'SUITE_PRESTATE_MISSING')
        self.check_binding(self.prestate(), active=False)
        raw = self.command(['/usr/bin/ss', '-H', '-ltnp'], 15)
        return {'schema_version': 1, 'listeners_sha256': listener_digest(raw),
                'host_sha256': native.digest(native.canonical(self.host_projection())),
                'incus_routes_sha256': native.digest(native.canonical(self.proxy_rows()))}

    def host_projection(self) -> dict[str, Any]:
        paths = ('/etc/hosts', '/etc/sysctl.d/90-tiny-swarm-world.conf',
            '/etc/modules-load.d/tiny-swarm-world.conf', '/usr/local/bin/tsw-apply-incus-forwarding.sh',
            '/etc/systemd/system/tsw-incus-forwarding.service')
        files: dict[str, Any] = {}
        for name in paths:
            path = Path(name)
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            except FileNotFoundError:
                files[name] = None
                continue
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                native.require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022
                    and info.st_nlink == 1 and info.st_size <= 1024 * 1024, 'SUITE_HOST_FILE_UNSAFE')
                raw = stream.read(1024 * 1024 + 1)
                after = os.fstat(stream.fileno())
                native.require(len(raw) <= 1024 * 1024 and (info.st_ino, info.st_dev, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                    == (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'SUITE_HOST_FILE_DRIFT')
                files[name] = {'sha256': native.digest(raw), 'uid': info.st_uid, 'gid': info.st_gid, 'mode': stat.S_IMODE(info.st_mode)}
        nft = native.inventory.strict_json(self.command(['/usr/sbin/nft', '-j', 'list', 'ruleset'], 20))
        firewall = importlib.import_module('tiny_swarm_world.infrastructure.adapters.network_preparation.firewall_inventory')
        controls = {name: Path('/proc/sys/' + name.replace('.', '/')).read_text().strip() for name in (
            'net.ipv4.ip_forward', 'net.bridge.bridge-nf-call-iptables', 'net.bridge.bridge-nf-call-ip6tables')}
        unit = self.command(['/usr/bin/systemctl', 'show', 'tsw-incus-forwarding.service', '--no-pager',
            '--property=LoadState,ActiveState,SubState,UnitFileState'], 15)
        return {'files': files, 'nft': firewall.stable_nft(nft), 'controls': controls,
                'forwarding_unit_sha256': native.digest(unit)}

    def proxy_rows(self) -> list[Any]:
        _artifact, _runner = self.capture()
        result: list[Any] = []
        for (command, args), row in self.details.items():
            if command in {'incus_profile_show', 'incus_instance_config_show'}:
                field = 'devices' if command == 'incus_profile_show' else 'expanded_devices'
                for name, device in row.get(field, {}).items():
                    if device.get('type') == 'proxy':
                        result.append((command, args, name, device))
        return sorted(result, key=lambda row: (row[0], row[1], row[2]))

    def listeners_clear(self, before: dict[str, Any]) -> bool:
        return self.worker_settled and self.route_capture() == before

    def public(self, args: list[str], timeout: int) -> bytes:
        self.fresh_source()
        native.require(self.baseline is not None, 'SUITE_PRESTATE_MISSING')
        self.check_binding(self.prestate(), active=False)
        native.require(self.unit(native.SOCKET) == 'inactive', 'DAEMON_REACTIVATED')
        return self.child([self.interpreter(), '-E', '-s', '-B', '-c', BOOTSTRAP, *args], timeout)

    def child(self, argv: list[str], timeout: int) -> bytes:
        self.budget()
        native.require(self.deadline - time.monotonic() >= timeout + 10 and self.worker_settled, 'CASE_BUDGET_INSUFFICIENT')
        env = native.ENV | operator_values(self.intent) | {'TSW_REPOSITORY_ROOT': str(ROOT), 'TSW_INFRA_ROOT': str(INFRA),
            'TSW_INSTALL_ENV_FILE': str(OPERATOR), 'TSW_LIVE_EVIDENCE_ROOT': str(self.journal.directory)}
        self.worker_settled = False
        child_key = 'child-' + uuid4().hex
        self.journal.save(child_key + '-intent.json', {'argv_sha256': native.digest(native.canonical(argv)), 'timeout': timeout})
        gate_read, gate_write = os.pipe()
        try:
            child = subprocess.Popen([self.interpreter(), '-E', '-s', '-B', '-c', GATED_CHILD,
                str(gate_read), *argv], cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, pass_fds=(gate_read,))
        except OSError:
            os.close(gate_write)
            self.worker_settled = True
            self.journal.save(child_key + '-launch-refused.json', {'released': False})
            raise
        finally:
            os.close(gate_read)
        selector = selectors.DefaultSelector()
        output = bytearray()
        error_digest = hashlib.sha256()
        total = 0
        deadline = time.monotonic() + timeout
        try:
            self.journal.save(child_key + '-pid.json', {'pid': child.pid, 'start_time': process_start(child.pid)})
            os.write(gate_write, b'G')
            os.close(gate_write)
            gate_write = -1
            if child.stdout is None or child.stderr is None:
                raise native.MaintenanceError('CASE_PIPE_UNAVAILABLE')
            selector.register(child.stdout, selectors.EVENT_READ)
            selector.register(child.stderr, selectors.EVENT_READ)
            while selector.get_map():
                native.require(time.monotonic() < deadline, 'CASE_WORKER_TIMEOUT')
                for selected, _event in selector.select(.2):
                    chunk = os.read(selected.fd, 65536)
                    total += len(chunk)
                    native.require(total <= native.LIMIT, 'CASE_OUTPUT_BOUND')
                    if not chunk:
                        selector.unregister(selected.fileobj)
                    elif selected.fileobj is child.stdout:
                        output.extend(chunk)
                    else:
                        error_digest.update(chunk)
            status = child.wait(timeout=max(.01, deadline - time.monotonic()))
            self.journal.save(child_key + '-outcome.json', {'return_code': status,
                'stdout_sha256': native.digest(bytes(output)), 'stderr_sha256': error_digest.hexdigest()})
            native.require(status == 0, 'CASE_CLI_FAILED')
            return bytes(output)
        finally:
            selector.close()
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
            self.worker_settled = child.poll() is not None and settle_group(child.pid)
            if self.worker_settled:
                self.journal.save(child_key + '-settled.json', {'pid': child.pid, 'group_absent': True})
            if gate_write >= 0:
                os.close(gate_write)
            if child.stdout is not None:
                child.stdout.close()
            if child.stderr is not None:
                child.stderr.close()

    def observe_completion(self) -> None:
        raw = self.child([self.interpreter(), '-E', '-s', '-B', str(Path(__file__)), 'observe'], 180)
        native.require(native.inventory.strict_json(raw) == {'status': 'SELECTED_RUNTIME_VERIFIED'}, 'CASE_COMPLETION_NOT_PROVEN')
        model = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.manifest')
        actual = model.decode_manifest(native.read_private(MANIFEST))
        recipe = RECIPES[self.intent.case]
        wanted = set(recipe.services) | ({'traefik'} if recipe.add_traefik else set())
        native.require(set(actual.requested_services) == wanted and actual.schema_version == 2
            and actual.effective_exposure().get('swagger') == (recipe.exposure if 'swagger' in wanted else None)
            and all(owner.owner == recipe.owner for owner in actual.effective_stack_ownership().values()), 'CASE_SAVED_SELECTION_DRIFT')

    @contextmanager
    def installation_lease(self) -> Iterator[Any]:
        lock = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock')
        native.require(self.disposal_lease is None, 'CASE_DISPOSAL_LEASE_ALREADY_HELD')
        with lock.JsonInstallationOperationLock(ROOT).exclusive('cleanup') as lease:
            self.disposal_lease = lease
            try:
                yield lease
            finally:
                self.disposal_lease = None

    def prepare_disposal(self) -> None:
        native.require(self.worker_settled, 'CASE_WORKER_NOT_SETTLED')
        self.wait_operations()
        if not PROFILE_STATE.exists():
            native.require(not MANIFEST.exists(), 'CASE_RECEIPT_MISSING')
            self.owned = None
            return
        saved = self.journal.directory / 'disposal-intent.json'
        if saved.exists():
            self.owned = decode_disposal(native.inventory.strict_json(native.read_private(saved)))
            return
        raw, creation = disposal.read_creation(ROOT)
        intent = creation['intent']
        if MANIFEST.exists():
            module = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.manifest')
            manifest = module.decode_manifest(native.read_private(MANIFEST))
            evidence = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change')
            template, manager_uuid, worker_uuids = evidence.current_evidence(ROOT, manifest)
            intent = template.model_dump(mode='json')
            native.require(manager_uuid == creation['instance_uuid'] and worker_uuids == creation['worker_uuids'], 'CASE_CREATION_HISTORY_DRIFT')
        self.capture()
        uuids = creation['worker_uuids'] | ({'swarm-manager': creation['instance_uuid']} if creation['instance_uuid'] is not None else {})
        instances = {args[0]: row for (command, args), row in self.details.items()
                     if command == 'incus_instance_config_show' and len(args) == 2 and args[1] == 'default'}
        native.require(set(instances) == set(uuids), 'CASE_CREATE_RECEIPT_UNCERTAIN')
        profile_name = intent['profile']['profile']['profile_name']
        profile = self.details.get(('incus_profile_show', (profile_name, 'default')))
        models = importlib.import_module('tiny_swarm_world.domain.lifecycle.profile_lifecycle')
        template = models.ManagerCreateIntent.model_validate_json(native.canonical(intent))
        observations = importlib.import_module('tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.observations')
        for name, row in instances.items():
            if name == 'swarm-manager':
                state, uuid, exact = observations.owned_instance(row, template)
                native.require(state in {'running', 'stopped'} and uuid == uuids[name] and exact,
                               'CASE_ORIGINAL_SPEC_UNPROVEN')
            else:
                worker = observations.worker_intent(template, name)
                observed = observations.worker_state(row, template, worker)
                native.require(observed.state in {'running', 'stopped'} and observed.instance_uuid == uuids[name]
                               and observed.no_proxy, 'CASE_ORIGINAL_SPEC_UNPROVEN')
        expected_profile = {'name': profile_name, 'project': 'default', 'description': 'Tiny Swarm World installation profile',
                            'config': template.markers(), 'devices': template.devices()}
        if profile is not None:
            native.require(profile['config'] == template.markers() and profile['devices'] == template.devices()
                and profile['description'] == expected_profile['description'], 'CASE_ORIGINAL_PROFILE_UNPROVEN')
        else:
            native.require(not instances, 'CASE_PROFILE_RECEIPT_UNCERTAIN')
        self.owned = disposal.DisposalIntent(installation_id=intent['profile']['installation_id'],
            operation_id=intent['profile']['operation_id'], checkpoint_sha256=native.digest(raw),
            profile_name=profile_name, profile_sha256=disposal.profile_identity(profile if profile is not None else expected_profile), pool=intent['storage_pool'],
            nodes=tuple(disposal.OwnedNode(name, uuids[name], disposal.specification(instances[name]))
                        for name in native.NODES if name in uuids))
        disposal.validate_case_graph(self.graph_from_capture(self.owned), self.owned)
        self.journal.save('disposal-intent.json', asdict(self.owned))

    def graph_from_capture(self, intent: disposal.DisposalIntent) -> dict[str, Any]:
        default = next(row for row in self.last_artifact['incus_projects'] if row['project'] == 'default')
        instances = {args[0]: row for (command, args), row in self.details.items()
            if command == 'incus_instance_config_show' and len(args) == 2 and args[1] == 'default'}
        pool = next(row for row in default['pools'] if row['name'] == intent.pool)
        profile = self.details.get(('incus_profile_show', (intent.profile_name, 'default')))
        return {'instances': instances, 'profile': profile,
            'volumes': [row for row in pool['volumes'] if row['name'] in {node.name for node in intent.nodes}],
            'snapshots': [row for row in pool['snapshots'] if row['parent'] in {node.name for node in intent.nodes}],
            'checkpoint_sha256': native.digest(native.read_private(PROFILE_STATE))}

    def case_graph(self, intent: disposal.DisposalIntent) -> dict[str, Any]:
        self.wait_operations()
        self.capture()
        result = self.graph_from_capture(intent)
        disposal.validate_case_graph(result, intent)
        native.require(self.baseline is not None, 'SUITE_PRESTATE_MISSING')
        native.require(preserved_case(self.prestate(), self.last_artifact, self.details, intent), 'CASE_FOREIGN_GRAPH_DRIFT')
        return result

    def wait_operations(self) -> None:
        """Read-only settle includes the daemon's five-second completed retention."""
        deadline = min(self.deadline - 5, time.monotonic() + 25)
        native.require(time.monotonic() < deadline, 'CASE_OPERATION_SETTLE_EXPIRED')
        runner = native.inventory.Runner()
        runner.started = runner.clock() - (native.inventory.MAX_WALL_SECONDS - (deadline - time.monotonic()))
        while time.monotonic() < deadline:
            super().check_binding(self.prestate(), active=False)
            value = native.inventory._parse_json_command(runner, ['/usr/bin/incus', '--force-local', 'query',
                '--request', 'GET', '--raw', '/1.0/operations?all-projects=true'], command_id='suite_operations_settle',
                env=self.incus_env(self.prestate()), safe_args=[])
            if operations_empty(value):
                super().check_binding(self.prestate(), active=False)
                return
            time.sleep(.25)
        raise native.MaintenanceError('CASE_OPERATION_SETTLE_EXPIRED')

    def safe_stopped_remainder(self, route: dict[str, Any]) -> bool:
        try:
            if not self.worker_settled:
                return False
            if self.owned is not None:
                rows = disposal.validate_case_graph(self.case_graph(self.owned), self.owned)
                if any(row['status'] != 'Stopped' for row in rows.values()):
                    return False
            raw = self.command(['/usr/bin/ss', '-H', '-ltnp'], 15)
            return listener_digest(raw) == route['listeners_sha256']
        except (native.MaintenanceError, native.inventory.InventoryError, OSError, ValueError):
            return False


def decode_disposal(value: Any) -> disposal.DisposalIntent:
    native.require(isinstance(value, dict) and set(value) == {'installation_id', 'operation_id', 'checkpoint_sha256',
        'profile_name', 'profile_sha256', 'pool', 'nodes'} and isinstance(value['nodes'], list), 'CASE_INTENT_INVALID')
    native.require(all(type(item) is str for key, item in value.items() if key != 'nodes'), 'CASE_INTENT_INVALID')
    nodes = []
    for row in value['nodes']:
        native.require(isinstance(row, dict) and set(row) == {'name', 'uuid', 'specification_sha256'}
            and all(type(item) is str for item in row.values()), 'CASE_NODE_INVALID')
        nodes.append(disposal.OwnedNode(**row))
    return disposal.DisposalIntent(**(value | {'nodes': tuple(nodes)}))


def listener_digest(raw: bytes) -> str:
    return native.digest(b'\n'.join(sorted(raw.splitlines())))


def operations_empty(value: Any) -> bool:
    keys = {'type', 'status', 'status_code', 'operation', 'error_code', 'error', 'metadata'}
    native.require(isinstance(value, dict) and set(value) == keys and value['type'] == 'sync'
        and value['status'] == 'Success' and type(value['status_code']) is int and value['status_code'] == 200
        and value['operation'] == '' and type(value['error_code']) is int and value['error_code'] == 0 and value['error'] == '',
        'CASE_OPERATION_ENVELOPE_INVALID')
    rows = value['metadata']
    states = {'operation created', 'started', 'stopped', 'running', 'cancelling', 'pending', 'success', 'failure',
              'cancelled', 'starting', 'stopping', 'aborting', 'freezing', 'frozen', 'thawed', 'error', 'ready'}
    native.require(isinstance(rows, dict) and set(rows) <= states and len(rows) <= 17, 'CASE_OPERATION_SCHEMA_INVALID')
    for entries in rows.values():
        native.require(isinstance(entries, list) and len(entries) <= 1024 and all(type(entry) is str and re.fullmatch(
            r'/1\.0/operations/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', entry) for entry in entries),
            'CASE_OPERATION_SCHEMA_INVALID')
    return not any(rows.values())


def validate_preview(raw: bytes, recipe: Recipe) -> dict[str, Any]:
    value = native.inventory.strict_json(raw)
    native.require(isinstance(value, dict) and set(value) == {'status', 'plan', 'routes', 'execution', 'data_policy'}
        and value['status'] == 'selection_preview', 'CASE_PREVIEW_INVALID')
    models = importlib.import_module('tiny_swarm_world.domain.lifecycle.selection')
    plan = models.SelectionPlan.model_validate_json(native.canonical(value['plan']))
    native.require(set(plan.requested_services) == set(recipe.services)
        and plan.service_exposure.get('swagger') == (recipe.exposure if 'swagger' in recipe.services else None)
        and all(mode == recipe.owner for mode in plan.stack_owners.values()), 'CASE_PREVIEW_SELECTION_DRIFT')
    manifests = importlib.import_module('tiny_swarm_world.domain.preflight.setup_manifest')
    profiles = importlib.import_module('tiny_swarm_world.application.services.profile_setup')
    routes = value['routes']
    native.require(isinstance(routes, dict) and routes.get('before') == [] and routes.get('runtime_observed') is False
        and routes.get('listen_address') in {'127.0.0.1', '0.0.0.0'}, 'CASE_PREVIEW_ROUTE_INVALID')
    manifest = manifests.default_setup_manifest(service_profile=plan.service_preset,
        resolved_services=plan.resolved_services, service_exposure=plan.service_exposure)
    expected = [row.model_dump(mode='json') for row in profiles.proxy_routes_from_setup_manifest(manifest, routes['listen_address'])]
    native.require(routes.get('after') == expected, 'CASE_PREVIEW_ROUTE_INVALID')
    return value


def settle_group(pid: int) -> bool:
    """A reaped CLI leader is not proof that its mutation descendants exited."""
    def alive() -> bool:
        try:
            os.killpg(pid, 0)
            return True
        except ProcessLookupError:
            return False
    if not alive():
        return True
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and alive():
        time.sleep(.05)
    if not alive():
        return True
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and alive():
        time.sleep(.05)
    return not alive()


def process_start(pid: int) -> int:
    raw = Path(f'/proc/{pid}/stat').read_text()
    fields = raw.rsplit(')', 1)[1].split()
    native.require(len(fields) > 19 and fields[19].isdigit(), 'CASE_CHILD_IDENTITY_INVALID')
    return int(fields[19])


def previous_children_settled(journal: native.Journal) -> bool:
    intents = list(journal.directory.glob('child-*-intent.json'))
    native.require(len(intents) <= 32, 'CASE_CHILD_EVENT_BOUND')
    for path in intents:
        key = path.name.removesuffix('-intent.json')
        # A settled receipt is informational; verify absence independently even
        # after interruption. Never signal a PID supplied by retained JSON.
        receipt = journal.directory / (key + '-pid.json')
        if not receipt.exists():
            refused = journal.directory / (key + '-launch-refused.json')
            if refused.exists() and native.inventory.strict_json(native.read_private(refused)) == {'released': False}:
                continue
            return False
        value = native.inventory.strict_json(native.read_private(receipt))
        native.require(isinstance(value, dict) and set(value) == {'pid', 'start_time'}
            and type(value['pid']) is int and value['pid'] > 1 and type(value['start_time']) is int,
            'CASE_CHILD_RECEIPT_INVALID')
        try:
            os.killpg(value['pid'], 0)
            return False
        except ProcessLookupError:
            pass
    return True


def preserved_case(baseline: dict[str, Any], artifact: dict[str, Any], details: dict[Any, Any],
                   intent: disposal.DisposalIntent) -> bool:
    """Subtract only independently proved case nodes/links; preserve all others."""
    observed = copy.deepcopy(baseline)
    preserve = observed['preserve']
    projects = copy.deepcopy(artifact['incus_projects'])
    names = {node.name for node in intent.nodes}
    for project in projects:
        if project['project'] == 'default':
            project['instances'] = [row for row in project['instances'] if row['name'] not in names]
        project['profiles'] = [row for row in project['profiles'] if not (
            row['name'] == intent.profile_name and row['owner_project'] == 'default')]
        for pool in project['pools']:
            if pool['name'] == intent.pool:
                pool['volumes'] = [row for row in pool['volumes'] if not (
                    row['name'] in names and row['type'] == 'container' and row['owner_project'] == 'default')]
        def remove_links(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == 'used_by' and isinstance(child, list):
                        value[key] = [ref for ref in child if not disposal.own_reference(ref, intent)]
                    else:
                        remove_links(child)
            elif isinstance(value, list):
                for child in value:
                    remove_links(child)
        remove_links(project)
    preserve['incus_projects'] = projects
    pools = copy.deepcopy(artifact['incus_pools'])
    for pool in pools:
        pool['used_by'] = [ref for ref in pool['used_by'] if not disposal.own_reference(ref, intent)]
    preserve['incus_pools'] = pools
    configs = {}
    for (command, args), row in details.items():
        if 'config' not in row or not command.startswith('incus_'):
            continue
        own = (command in {'incus_instance_config_show', 'incus_instance_config_show_expanded'} and len(args) == 2 and args == (args[0], 'default') and args[0] in names
            or command == 'incus_profile_show' and len(args) == 2 and args[0] == intent.profile_name
            or command == 'incus_storage_volume_show' and len(args) == 4 and args[:2] == (intent.pool, 'container') and args[2] in names and args[3] == 'default')
        if not own:
            projection = {'config': row['config']} if '_server_root_' in command else native.config_projection(row, instance='instance' in command)
            configs[command + ':' + ':'.join(args)] = native.digest(native.canonical(projection))
    # Existing raw metadata digests must all remain; new owner-view profile rows
    # are accounted above, not silently accepted through a digest omission.
    expected_configs = {key: value for key, value in baseline['preserve']['configuration_digests'].items()
                        if key.startswith('incus_')}
    for key, value in expected_configs.items():
        if configs.get(key) != value:
            return False
    preserve['configuration_digests'] = {key: value for key, value in baseline['preserve']['configuration_digests'].items()
                                      if not key.startswith('incus_')} | configs
    for key in ('incus_admission', 'incus_units'):
        preserve[key] = artifact[key]
    return native.preserved_snapshot(baseline, observed)


def observe_selected() -> None:
    """Real merged read-only profile and whole selected task/API verification."""
    lifecycle_module = importlib.import_module('tiny_swarm_world.infrastructure.composition_lifecycle')
    lifecycle = lifecycle_module.build_installation_lifecycle_service(ROOT)
    manifest = lifecycle.manifests.load().manifest
    native.require(manifest is not None, 'CASE_MANIFEST_MISSING')
    lock_module = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock')
    consent_module = importlib.import_module('tiny_swarm_world.domain.preflight')
    profile = importlib.import_module('tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup')
    backend = importlib.import_module('tiny_swarm_world.domain.node_provider').ManagedLxcBackend.INCUS
    management = importlib.import_module('tiny_swarm_world.infrastructure.composition_management')
    async def verify() -> None:
        with lock_module.JsonInstallationOperationLock(ROOT).exclusive('recovery') as lease:
            operation = await profile.for_runtime(ROOT, lifecycle, lease, 'recovery',
                consent_module.LiveConsent(live_flag=True, confirmed=True))
            await operation.verify_effective_routes()
            await management.verify_completed_stacks(ROOT, manifest, backend, node_names=tuple(reversed(native.NODES)))
    asyncio.run(verify())
    print('{"status":"SELECTED_RUNTIME_VERIFIED"}')


def observe_prerequisites() -> None:
    """Read actual production plans; this helper never calls apply/execute."""
    module = importlib.import_module('tiny_swarm_world.infrastructure.composition_native_preparation')
    async def verify() -> None:
        incus = await module.build_incus_preparation_service(service_profile='service-access').plan()
        network = await module.build_network_preparation_service(service_profile='service-access').plan()
        native.require(incus.verified and not incus.actions and not incus.blockers
            and network.verified and not network.actions and not network.blockers, 'SUITE_SHARED_PREPARATION_REQUIRED')
    asyncio.run(verify())
    print('{"status":"SHARED_PREREQUISITES_READY"}')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'execute', 'recover', 'observe', 'prerequisites'))
    parser.add_argument('--run-id')
    parser.add_argument('--intent-sha256')
    parser.add_argument('--expected-go-sha256')
    args = parser.parse_args(argv)
    try:
        native.require(os.geteuid() == 0, 'ROOT_REQUIRED')
        def interrupted(_number: int, _frame: Any) -> None:
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, interrupted)
        sys.path.insert(0, str(ROOT / 'src'))
        if args.mode in {'observe', 'prerequisites'}:
            native.require(args.run_id is None and args.intent_sha256 is None and args.expected_go_sha256 is None,
                           'SUITE_ARGUMENT_INVALID')
            if args.mode == 'observe':
                observe_selected()
            else:
                observe_prerequisites()
            return 0
        native.require(type(args.run_id) is str and bool(native.RUN_ID.fullmatch(args.run_id))
            and type(args.intent_sha256) is str and bool(native.HEX.fullmatch(args.intent_sha256)), 'SUITE_ARGUMENT_INVALID')
        native.private_directory(PRIVATE)
        source, pins = source_pins()
        raw = native.read_private(PRIVATE / ('product-intent-' + args.run_id + '.json'))
        native.require(native.digest(raw) == args.intent_sha256, 'SUITE_INTENT_DRIFT')
        intent = SuiteIntent.parse(native.inventory.strict_json(raw), source)
        native.require(intent.run_id == args.run_id, 'SUITE_RUN_ID_DRIFT')
        check_prerequisites(intent)
        native.fixture._assert_host_identity(native.HOST)
        host_id = native.digest(Path('/etc/machine-id').read_bytes())
        directory = PRIVATE / ('product-case-' + args.run_id)
        if args.mode == 'prepare':
            native.require(args.expected_go_sha256 is None, 'SUITE_ARGUMENT_INVALID')
            directory.mkdir(mode=0o700)
            journal = native.Journal(directory)
            port = SuiteNativePort(intent, journal)
            baseline = port.snapshot()
            port.admit_empty(baseline)
            proposal: dict[str, Any] = {'source_commit': source, 'pins': pins, 'host_id_sha256': host_id,
                'intent_sha256': native.digest(native.canonical(asdict(intent))), 'baseline': baseline}
            journal.save('proposal.json', proposal)
            print(native.canonical({'status': 'PREPARED_READ_ONLY', 'proposal_sha256': native.digest(native.canonical(proposal))}).decode())
            return 0
        native.private_directory(directory)
        journal = native.Journal(directory)
        proposal_raw = native.read_private(directory / 'proposal.json')
        proposal = native.inventory.strict_json(proposal_raw)
        native.require(isinstance(proposal, dict) and set(proposal) == {'source_commit', 'pins', 'host_id_sha256', 'intent_sha256', 'baseline'}
            and proposal['host_id_sha256'] == host_id and proposal['pins'] == pins and proposal['source_commit'] == source
            and proposal['intent_sha256'] == native.digest(native.canonical(asdict(intent))), 'SUITE_PROPOSAL_DRIFT')
        native.validate_snapshot(proposal['baseline'])
        native.require(type(args.expected_go_sha256) is str and native.HEX.fullmatch(args.expected_go_sha256), 'SUITE_GO_REQUIRED')
        go_raw = native.read_private(directory / 'approval.json')
        native.require(native.digest(go_raw) == args.expected_go_sha256, 'SUITE_GO_HASH_DRIFT')
        go = native.inventory.strict_json(go_raw)
        validate_go(go, proposal, native.digest(proposal_raw), datetime.now(timezone.utc), paused=False, recovery=args.mode == 'recover')
        with native.host_lock():
            validate_go(go, proposal, native.digest(proposal_raw), datetime.now(timezone.utc), paused=False, recovery=args.mode == 'recover')
            port = SuiteNativePort(intent, journal, proposal)
            port.baseline = proposal['baseline']
            transaction = native.Transaction(port, journal, proposal['baseline'])
            if args.mode == 'execute':
                current = port.snapshot()
                native.require(current == proposal['baseline'], 'PRESTATE_DRIFT')
                port.admit_empty(current)
                journal.save('started.json', {'proposal_sha256': native.digest(proposal_raw)})
                result = transaction.execute()
            else:
                native.require((directory / 'started.json').exists(), 'SUITE_NOT_STARTED')
                port.phase('teardown')
                port.worker_settled = previous_children_settled(journal)
                native.require(port.worker_settled, 'CASE_WORKER_NOT_SETTLED')
                if port.unit(native.DAEMON) == 'active' and native.preserved_snapshot(proposal['baseline'], port.snapshot()):
                    transaction.recover()
                    result = {'status': 'RECOVERED'}
                    journal.save('result-' + uuid4().hex + '.json', result)
                    print(native.canonical(result).decode())
                    return 0
                route = native.inventory.strict_json(native.read_private(directory / 'paused-route.json'))
                cleanup_failure: BaseException | None = None
                port.restore_safe = False
                try:
                    port.prepare_disposal()
                    if port.owned is not None:
                        with port.installation_lease():
                            disposal.dispose(disposal.IncusDisposalPort(port, port.owned, journal), port.owned)
                    port.restore_safe = port.listeners_clear(route)
                except BaseException as exc:
                    cleanup_failure = exc
                    port.restore_safe = port.safe_stopped_remainder(route)
                finally:
                    transaction.recover()
                if cleanup_failure is not None:
                    raise cleanup_failure
                result = {'status': 'RECOVERED'}
            journal.save('result-' + uuid4().hex + '.json', result)
            print(native.canonical(result).decode())
            return 0 if result['status'] in {'PASS', 'RECOVERED'} else 2
    except BaseException as exc:
        reason = native.failure_reason(exc)
        print(native.canonical({'status': reason}).decode(), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

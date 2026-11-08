"""Closed, unpublished upgrade qualification recipes using the actual public CLI.

This module never promotes compatibility, creates a catalog, or accepts commands
from JSON. Host adapters retain the maintenance/identity/lease authority. Official
legacy product cases are deliberately unavailable until the separate S-U2 slice.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import hashlib
import importlib
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

SCRIPT = 'tools/linux/qualification/product_upgrade_cases.py'
CATALOG = 'src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py'
ROOT = Path(__file__).resolve().parents[3]
FRESH_NAMES = ('minimal', 'swagger-internal', 'swagger-published', 'swagger-traefik-swarm',
               'swagger-traefik-portainer', 'swagger-add-traefik', 'full-swarm', 'full-portainer')


class UpgradeError(Exception):
    """Bounded refusal; not a product engine result."""


class FaultObserved(UpgradeError):
    """A real durable checkpoint was observed before signaling our own child."""


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
        return ['setup', 'run', '--services', ','.join(self.services), '--service-profile', self.preset,
                '--stack-owner', self.owner, *(['--swagger-exposure', self.exposure] if 'swagger' in self.services else []),
                *(('--preview', '--json') if preview else ('--live', '--approve-live', '--json')),
                '--node-provider', 'lxc_native', '--lxc-backend', 'incus']

    def update(self, *, preview: bool = False, recover: bool = False) -> list[str]:
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
ALL_NAMES = (*FRESH_NAMES, *RECIPES)


def recipe(case: str) -> UpgradeRecipe:
    require(case in RECIPES, 'UPGRADE_CASE_UNKNOWN')
    value = RECIPES[case]
    require(value.kind != 'product', 'UPGRADE_PRODUCT_NOT_IMPLEMENTED')
    return value


def budgets(case: str, host: str, *, engine_recovery: bool = False) -> dict[str, int]:
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


def poll_fault(port: Any, child: subprocess.Popen) -> None:
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
        event(port, 'upgrade-fault-intent', {'checkpoint_sha256': digest(current.model_dump(mode='json')),
             'installation_id': baseline['installation_id'], 'predicate': 'CHECKED_BACKUP' if value.kind == 'portainer' else 'PARTIAL_BATCH'})
        port.upgrade_fault_armed = False
        port.upgrade_fault_observed = True
        os.killpg(child.pid, signal.SIGTERM)
        raise FaultObserved('UPGRADE_ACTUAL_FAULT_OBSERVED')


def observe(port: Any, stage: str) -> dict[str, Any]:
    value = port.upgrade_helper(stage)
    require(isinstance(value, dict) and value.get('status') == 'UPGRADE_RUNTIME_VERIFIED', 'UPGRADE_PROOF_UNAVAILABLE')
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


def read_runtime(case: str, stage: str) -> dict[str, Any]:
    """Use production read-only observers; stdout contains no credentials or Env."""
    value = recipe(case)
    require(stage in {'source', 'cache-source', 'target', 'recovered', 'noop', 'persistent'}, 'UPGRADE_PROOF_STAGE')
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
            policy = definitions[name].update_transitions[0]
            expected = policy.source_versions if stage in {'source', 'cache-source', 'recovered'} or value.kind == 'portainer' else next(
                target.versions for target in definitions[name].update_targets if target.target_id == policy.target_id)
            if stage in {'noop', 'persistent'}:
                expected = policy.source_versions if value.fault or value.kind == 'portainer' else expected
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
        require(manifest_hash == snapshot.token, 'UPGRADE_MANIFEST_CHANGED_DURING_PROOF')
        component_hash = private_file_hash(state / 'component-update.json', optional=True)
        return {'status': 'UPGRADE_RUNTIME_VERIFIED', 'installation_id': str(manifest.installation_id),
            'preset': manifest.service_preset, 'exposure': manifest.effective_exposure(),
            'node_ids': node_inventory(shell, node_names), 'swarm_id': swarm, 'service_ids': service_ids,
            'service_versions': service_versions, 'mounts': mounts, 'tasks': tasks, 'data': data,
            'owner_ids': owners, 'stack_updates': stack_updates, 'managed_journals': managed,
            'backup_journal': digest(private_json(backup)) if backup.exists() else None,
            'manifest_sha256': manifest_hash, 'manifest_token': snapshot.token, 'component_journal_sha256': component_hash}
    return asyncio.run(verify())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=tuple(RECIPES), required=True)
    parser.add_argument('--stage', choices=('source', 'cache-source', 'cache-targets', 'cache-reconcile', 'target', 'recovered', 'noop', 'persistent'), required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, 'UPGRADE_ROOT_REQUIRED')
    import sys
    sys.path.insert(0, str(ROOT / 'src'))
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    print(json.dumps(prepare_target_cache(args.case, read_only=args.stage == 'cache-reconcile')
        if args.stage in {'cache-targets', 'cache-reconcile'} else read_runtime(args.case, args.stage)))


if __name__ == '__main__':
    main()

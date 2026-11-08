"""Finite Incus6.0.5 DTO, inherited-profile and effective-route observations."""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import parse_qsl, quote, urlsplit
from uuid import UUID

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import ProfileObservation, WorkerObservation
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.args import scoped_node_config
from tiny_swarm_world.infrastructure.adapters.network_preparation.trusted_process import PROBE, _complete_proof

_ERROR = 'Scoped Incus observation or effect is unknown; preserve the checkpoint for explicit recovery.'
_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}')
_ENVELOPE = {'type', 'status', 'status_code', 'operation', 'error_code', 'error', 'metadata'}
_OWNER_ARGS = ('/usr/bin/systemctl', 'show', 'incus.service',
               '--property=LoadState,ActiveState,UnitFileState,MainPID', '--no-pager')
_ENV = ('/usr/bin/env', '-i', 'LC_ALL=C', 'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
        'INCUS_CONF=/proc/self', '/usr/bin/incus', '--force-local')

def instance_config(intent):
    return scoped_node_config(intent, intent)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LifecycleStateError(_ERROR)
        result[key] = value
    return result


def metadata(raw):
    try:
        row = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, TypeError, RecursionError):
        raise LifecycleStateError(_ERROR) from None
    if (not isinstance(row, dict) or set(row) != _ENVELOPE or row['type'] != 'sync'
            or row['status'] != 'Success' or type(row['status_code']) is not int or row['status_code'] != 200
            or row['operation'] != '' or type(row['error_code']) is not int or row['error_code'] != 0
            or row['error'] != '' or not isinstance(row['metadata'], (dict, list))):
        raise LifecycleStateError(_ERROR)
    bounded(row['metadata'])
    return row['metadata']


def bounded(value, depth=0):
    if depth > 16:
        raise LifecycleStateError(_ERROR)
    if isinstance(value, (dict, list)):
        if len(value) > 2048:
            raise LifecycleStateError(_ERROR)
        for entry in value.values() if isinstance(value, dict) else value:
            bounded(entry, depth + 1)
    elif isinstance(value, str) and len(value.encode('utf-8', 'strict')) > 65536:
        raise LifecycleStateError(_ERROR)


def name(value):
    if type(value) is not str or _NAME.fullmatch(value) is None:
        raise LifecycleStateError(_ERROR)
    return value


def allowed_read_uri(uri):
    patterns = (r'/1\.0/profiles/tsw-manager-[0-9a-f]{24}\?project=default', r'/1\.0/images/aliases/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\?project=default', r'/1\.0', r'/1\.0/projects\?recursion=1',
        r'/1\.0/(profiles|instances)\?recursion=1&project=[A-Za-z0-9][A-Za-z0-9_.-]{0,99}',
        r'/1\.0/(networks|storage-pools)/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\?project=default',
        r'/1\.0/instances/swarm-manager(?:/state)?\?project=default')
    if type(uri) is not str or not any(re.fullmatch(pattern, uri) for pattern in patterns):
        raise LifecycleStateError(_ERROR)


def string_map(value):
    if (not isinstance(value, dict) or len(value) > 256
            or any(type(k) is not str or len(k) > 256 or type(v) is not str
                   or len(v.encode('utf-8', 'strict')) > 65536 for k, v in value.items())):
        raise LifecycleStateError(_ERROR)
    return value


def devices(value):
    if not isinstance(value, dict) or len(value) > 256:
        raise LifecycleStateError(_ERROR)
    for key, entry in value.items():
        name(key)
        string_map(entry)
        if not entry.get('type'):
            raise LifecycleStateError(_ERROR)
    return value


def rows(value, fields, limit):
    if not isinstance(value, list) or len(value) > limit:
        raise LifecycleStateError(_ERROR)
    result = {}
    for row in value:
        if not isinstance(row, dict) or set(row) - fields:
            raise LifecycleStateError(_ERROR)
        key = name(row.get('name'))
        if key in result:
            raise LifecycleStateError(_ERROR)
        result[key] = row
    return result


def owner_identity(raw):
    pairs = [line.split('=', 1) for line in raw.splitlines()]
    if any(len(pair) != 2 for pair in pairs):
        raise LifecycleStateError(_ERROR)
    row = dict(pairs)
    if (len(row) != len(pairs) or set(row) != {'LoadState', 'ActiveState', 'UnitFileState', 'MainPID'}
            or row['LoadState'] != 'loaded' or row['ActiveState'] != 'active'
            or not re.fullmatch(r'[1-9][0-9]{0,9}', row['MainPID'])
            or row['UnitFileState'] in {'', 'masked', 'masked-runtime', 'not-found'}):
        raise LifecycleStateError(_ERROR)
    return row


def client_versions(raw):
    match = re.fullmatch(r'Client version: ([0-9]+\.[0-9]+\.[0-9]+)\r?\nServer version: ([0-9]+\.[0-9]+\.[0-9]+)\r?\n?', raw)
    if match is None:
        raise LifecycleStateError(_ERROR)
    return match.group(1), match.group(2)

_ROOT_STRINGS = {'api_status', 'api_version', 'auth', 'auth_user_name', 'auth_user_method'}
_ENV_STRINGS = {'certificate', 'certificate_fingerprint', 'driver', 'driver_version', 'firewall',
    'kernel', 'kernel_architecture', 'kernel_version', 'os_name', 'os_version', 'project',
    'server', 'server_event_mode', 'server_name', 'server_version', 'storage', 'storage_version'}


def text(value):
    if type(value) is not str or len(value.encode('utf-8', 'strict')) > 65536:
        raise LifecycleStateError(_ERROR)


def string_array(value, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, list) or len(value) > 2048:
        raise LifecycleStateError(_ERROR)
    for item in value:
        text(item)


def server_environment(environment):
    fields = _ENV_STRINGS | {'server_clustered', 'server_pid', 'addresses', 'architectures',
                             'kernel_features', 'lxc_features', 'storage_supported_drivers'}
    if not isinstance(environment, dict) or set(environment) != fields:
        raise LifecycleStateError(_ERROR)
    for key in _ENV_STRINGS:
        text(environment[key])
    if (type(environment['server_clustered']) is not bool or type(environment['server_pid']) is not int
            or environment['server_pid'] < 0):
        raise LifecycleStateError(_ERROR)
    for key in ('addresses', 'architectures'):
        string_array(environment[key], nullable=True)
    for key in ('kernel_features', 'lxc_features'):
        if environment[key] is not None:
            string_map(environment[key])
    drivers = environment['storage_supported_drivers']
    if drivers is not None:
        if not isinstance(drivers, list):
            raise LifecycleStateError(_ERROR)
        for driver in drivers:
            if not isinstance(driver, dict) or set(driver) != {'Name', 'Version', 'Remote'} or type(driver['Remote']) is not bool:
                raise LifecycleStateError(_ERROR)
            text(driver['Name'])
            text(driver['Version'])


def server_admission(row, server_version):
    fields = _ROOT_STRINGS | {'public', 'api_extensions', 'auth_methods', 'config', 'environment'}
    if not isinstance(row, dict) or set(row) != fields:
        raise LifecycleStateError(_ERROR)
    for key in _ROOT_STRINGS:
        text(row[key])
    for key in ('api_extensions', 'auth_methods'):
        string_array(row[key], nullable=True)
    string_map(row['config'])
    server_environment(row['environment'])
    environment = row['environment']
    if (row['auth'] != 'trusted' or row['public'] is not False or row['api_status'] != 'stable'
            or row['api_version'] != '1.0' or environment['server'] != 'incus'
            or environment['project'] != 'default' or environment['server_clustered'] is not False
            or environment['server_version'] != server_version):
        raise LifecycleStateError(_ERROR)
    return {key: row[key] for key in ('auth', 'public', 'api_status', 'api_version')} | {
        key: environment[key] for key in ('server', 'project', 'server_clustered', 'server_version')}


def project_rows(value):
    result = rows(value, {'name', 'description', 'config', 'used_by'}, 64)
    if 'default' not in result:
        raise LifecycleStateError(_ERROR)
    for row in result.values():
        string_map(row.get('config'))
        text(row.get('description'))
        string_array(row.get('used_by'))
        if row['config'].get('features.profiles') not in {None, 'true', 'false'}:
            raise LifecycleStateError(_ERROR)
    return result


def profile_owner(project, projects):
    return project if project == 'default' or projects[project]['config'].get('features.profiles') == 'true' else 'default'


def instance_reference(value):
    if type(value) is not str:
        raise LifecycleStateError(_ERROR)
    parsed = urlsplit(value)
    parts = parsed.path.split('/')
    query = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    if (parsed.scheme or parsed.netloc or parsed.fragment or len(parts) != 4 or parts[:3] != ['', '1.0', 'instances']
            or (query and (len(query) != 1 or query[0][0] != 'project'))):
        raise LifecycleStateError(_ERROR)
    return name(query[0][1]) if query else 'default', name(parts[3])


def consumers(value):
    string_array(value)
    parsed = [instance_reference(item) for item in value]
    if len(set(parsed)) != len(parsed):
        raise LifecycleStateError(_ERROR)
    return tuple(sorted(parsed))


def profile_rows(value, owner):
    result = rows(value, {'name', 'project', 'description', 'config', 'devices', 'used_by'}, 512)
    for row in result.values():
        if row.get('project') != owner:
            raise LifecycleStateError(_ERROR)
        text(row.get('description'))
        string_map(row.get('config'))
        devices(row.get('devices'))
        consumers(row.get('used_by'))
    return result


def instance_rows(value, project):
    fields = {'name', 'project', 'description', 'architecture', 'config', 'devices', 'profiles',
              'expanded_config', 'expanded_devices', 'ephemeral', 'stateful', 'location', 'type',
              'status', 'status_code', 'created_at', 'last_used_at'}
    result = rows(value, fields, 1024)
    for row in result.values():
        if row.get('project', project) != project:
            raise LifecycleStateError(_ERROR)
        string_map(row.get('config'))
        devices(row.get('devices'))
        string_map(row.get('expanded_config', {}))
        devices(row.get('expanded_devices', {}))
        string_array(row.get('profiles'))
        if len(set(row['profiles'])) != len(row['profiles']):
            raise LifecycleStateError(_ERROR)
        for profile in row['profiles']:
            name(profile)
        validate_instance_metadata(row)
    return result


def validate_instance_metadata(row):
    if (type(row.get('ephemeral')) is not bool or type(row.get('stateful')) is not bool
            or type(row.get('status_code')) is not int or row.get('type') not in {'container', 'virtual-machine'}):
        raise LifecycleStateError(_ERROR)
    for key in ('description', 'architecture', 'created_at', 'last_used_at', 'status', 'location'):
        if key in row:
            text(row[key])
    if row.get('location', '') not in {'', 'none'}:
        raise LifecycleStateError(_ERROR)


async def resource_observations(runtime, intent):
    network = await runtime.query('/1.0/networks/' + quote(intent.network, safe='') + '?project=default')
    pool = await runtime.query('/1.0/storage-pools/' + quote(intent.storage_pool, safe='') + '?project=default')
    network_fields = {'name', 'project', 'description', 'managed', 'type', 'status', 'config', 'used_by', 'locations'}
    pool_fields = {'name', 'project', 'description', 'driver', 'status', 'config', 'used_by', 'locations'}
    for row, fields, expected in ((network, network_fields, intent.network), (pool, pool_fields, intent.storage_pool)):
        if not isinstance(row, dict) or set(row) - fields or row.get('name') != expected or row.get('project', 'default') != 'default':
            raise LifecycleStateError(_ERROR)
        string_map(row.get('config'))
        string_array(row.get('used_by'))
        text(row.get('description'))
        text(row.get('status'))
        if 'locations' in row:
            string_array(row['locations'], nullable=True)
    if (network.get('managed') is not True or network.get('type') != 'bridge' or network.get('status') != 'Created'
            or network['config'].get('ipv4.nat') != 'true' or network['config'].get('ipv6.address') != 'none'
            or pool.get('status') != 'Created' or type(pool.get('driver')) is not str):
        raise LifecycleStateError(_ERROR)
    return network, pool


async def profile_inventory(runtime, projects):
    profiles, instances = {}, {}
    for project in projects:
        suffix = '&project=' + quote(project, safe='')
        owner = profile_owner(project, projects)
        profiles[project] = profile_rows(await runtime.query('/1.0/profiles?recursion=1' + suffix), owner)
        instances[project] = instance_rows(await runtime.query('/1.0/instances?recursion=1' + suffix), project)
    if sum(len(items) for items in profiles.values()) > 2048 or sum(len(items) for items in instances.values()) > 1024:
        raise LifecycleStateError(_ERROR)
    validate_profile_graph(projects, profiles, instances)
    return profiles, instances


def profile_metadata(row):
    return {**row, 'used_by': consumers(row['used_by'])}


def validate_profile_graph(projects, profiles, instances):
    expected = {}
    for project, entries in profiles.items():
        owner = profile_owner(project, projects)
        if set(entries) != set(profiles[owner]):
            raise LifecycleStateError(_ERROR)
        for profile, row in entries.items():
            if profile_metadata(row) != profile_metadata(profiles[owner][profile]):
                raise LifecycleStateError(_ERROR)
            expected.setdefault((owner, profile), set())
    for project, entries in instances.items():
        for instance, row in entries.items():
            owner = profile_owner(project, projects)
            for profile in row['profiles']:
                if (owner, profile) not in expected:
                    raise LifecycleStateError(_ERROR)
                expected[(owner, profile)].add((project, instance))
    for (owner, profile), actual in expected.items():
        if set(consumers(profiles[owner][profile]['used_by'])) != actual:
            raise LifecycleStateError(_ERROR)


def own_reference(value, intent):
    binding = intent.profile.profile
    if binding is None or type(value) is not str:
        return False
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        return False
    if parsed.query not in {'', 'project=default'}:
        return False
    return parsed.path in {'/1.0/instances/' + node for node in (intent.node_name, *(worker.node_name for worker in intent.workers))} | {'/1.0/profiles/' + binding.profile_name}


def preserved_row(row, intent):
    result = dict(row)
    if 'used_by' in result:
        result['used_by'] = sorted(value for value in result['used_by'] if not own_reference(value, intent))
    return result


def preservation_projection(projects, profiles, instances, resources, admission, intent):
    binding = intent.profile.profile
    if binding is None:
        raise LifecycleStateError(_ERROR)
    return {
        'projects': {key: preserved_row(value, intent) for key, value in projects.items()},
        'profiles': {project: {key: preserved_row(value, intent) for key, value in entries.items()
                              if not (key == binding.profile_name and value['project'] == 'default')}
                     for project, entries in profiles.items()},
        'instances': {project: {key: value for key, value in entries.items()
                               if not (project == 'default' and key in {intent.node_name, *(worker.node_name for worker in intent.workers)})}
                      for project, entries in instances.items()},
        'resources': [preserved_row(row, intent) for row in resources],
        'admission': admission,
    }


def safe_base_profile(row, intent):
    allowed = {'security.nesting', 'security.syscalls.intercept.mknod', 'security.syscalls.intercept.setxattr',
               'security.privileged', 'limits.cpu', 'limits.memory', 'boot.autostart'}
    config = row['config']
    if (set(config) - allowed or config.get('security.privileged', 'false') != 'false'
            or any(config.get(key) != 'true' for key in ('security.nesting',
                   'security.syscalls.intercept.mknod', 'security.syscalls.intercept.setxattr'))):
        raise LifecycleStateError(_ERROR)
    for key, device in row['devices'].items():
        if device['type'] == 'disk':
            if (key != 'root' or set(device) - {'type', 'path', 'pool', 'size'}
                    or device.get('path') != '/' or device.get('pool') != intent.storage_pool):
                raise LifecycleStateError(_ERROR)
        elif device['type'] == 'nic':
            if (key != 'eth0' or set(device) - {'type', 'name', 'network'}
                    or device.get('name') != 'eth0' or device.get('network') != intent.network):
                raise LifecycleStateError(_ERROR)
        else:
            raise LifecycleStateError(_ERROR)


def base_projection(profiles, intent):
    result = {}
    for key in intent.base_profiles:
        row = profiles['default'].get(key)
        if row is None or row['project'] != 'default':
            raise LifecycleStateError(_ERROR)
        safe_base_profile(row, intent)
        result[key] = preserved_row(row, intent)
    return result


def profile_state(profiles, instances, intent):
    binding = intent.profile.profile
    if binding is None:
        raise LifecycleStateError(_ERROR)
    row = profiles['default'].get(binding.profile_name)
    if row is None:
        return 'absent'
    wanted = {('default', intent.node_name)} if intent.node_name in instances['default'] else set()
    if (row['project'] == 'default' and row['description'] == 'Tiny Swarm World installation profile'
            and row['config'] == intent.markers() and row['devices'] == intent.devices()
            and set(consumers(row['used_by'])) == wanted):
        return 'exact'
    return 'foreign'


def local_devices(intent):
    return {'eth0': {'type': 'nic', 'name': 'eth0', 'network': intent.network},
            'root': {'type': 'disk', 'path': '/', 'pool': intent.storage_pool, 'size': intent.disk}}


def owned_instance(row, intent):
    if row is None:
        return 'absent', None, False
    config = row['config']
    expanded_config = row.get('expanded_config', {})
    required = instance_config(intent)
    uuid = config.get('volatile.uuid')
    try:
        canonical_uuid = str(UUID(uuid)) if type(uuid) is str else None
    except ValueError:
        canonical_uuid = None
    if (canonical_uuid is None or canonical_uuid != uuid or row['type'] != 'container'
            or row['ephemeral'] or row['stateful'] or tuple(row['profiles']) != intent.attachments()
            or any(config.get(key) != value or expanded_config.get(key) != value for key, value in required.items())
            or config.get('volatile.base_image') != intent.image_fingerprint
            or config.get('security.privileged', 'false') != 'false'
            or expanded_config.get('security.privileged', 'false') != 'false'
            or any(key.startswith('raw.') for key in (*config, *expanded_config))):
        return 'foreign', None, False
    wanted = local_devices(intent)
    expanded = {**wanted, **intent.devices()}
    effective = row['devices'] == wanted and row.get('expanded_devices', {}) == expanded
    states = {('Stopped', 102): 'stopped', ('Running', 103): 'running'}
    state = states.get((row['status'], row['status_code']), 'foreign')
    return state, uuid, effective


async def owned_runtime_read(runtime, intent, expected_uuid):
    row = await runtime.query('/1.0/instances/swarm-manager?project=default')
    instance_rows([row], 'default')
    state, uuid, effective = owned_instance(row, intent)
    if state != 'running' or uuid != expected_uuid or not effective:
        raise LifecycleStateError(_ERROR)
    runtime_state = await runtime.query('/1.0/instances/swarm-manager/state?project=default')
    return row, state_pid(runtime_state)


async def listener_proof(runtime, pid, daemon_pid, intent, expected_uuid):
    before, manager_pid = await owned_runtime_read(runtime, intent, expected_uuid)
    raw = await runtime.run(('/usr/bin/sudo', '-n', '--', '/usr/bin/python3', '-I', '-B', '-c',
                             PROBE, str(pid), str(daemon_pid), str(manager_pid)))
    proof = json.loads(raw, object_pairs_hook=unique)
    if not _complete_proof(proof, {'listener': pid, 'daemon': daemon_pid, 'manager': manager_pid}):
        raise LifecycleStateError(_ERROR)
    after, after_pid = await owned_runtime_read(runtime, intent, expected_uuid)
    if after != before or after_pid != manager_pid:
        raise LifecycleStateError(_ERROR)
    return digest(proof)


def listener_rows(raw, intent):
    output = []
    ports = set(intent.catalog_ports)
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) < 4:
            raise LifecycleStateError(_ERROR)
        endpoint = fields[3]
        address, separator, port_text = endpoint.rpartition(':')
        if not separator or not port_text.isdigit():
            raise LifecycleStateError(_ERROR)
        port = int(port_text)
        if port not in ports:
            continue
        pids = set(re.findall(r'pid=([0-9]+)', line))
        if len(pids) != 1:
            raise LifecycleStateError(_ERROR)
        output.append((address, port, int(next(iter(pids)))))
    return output


async def listeners(runtime, intent, daemon_pid, running, effective, uuid):
    observed = listener_rows(await runtime.run(('/usr/bin/ss', '-H', '-O', '-ltnpe')), intent)
    binding = intent.profile.profile
    if binding is None:
        raise LifecycleStateError(_ERROR)
    expected = {(route.listen_address, route.listen_port): route for route in binding.routes}
    tuples = [(row[0], row[1]) for row in observed]
    forbidden = any(endpoint not in expected for endpoint in tuples)
    matches = running and effective and not forbidden and len(tuples) == len(set(tuples)) and set(tuples) == set(expected)
    proofs = []
    if matches:
        for address, port, pid in observed:
            proofs.append(await listener_proof(runtime, pid, daemon_pid, intent, uuid))
    return forbidden, matches, not observed, tuple(proofs)


async def inspect_runtime(runtime, intent):
    before = owner_identity(await runtime.run(_OWNER_ARGS))
    client, server = client_versions(await runtime.run((*_ENV, 'version')))
    admission = server_admission(await runtime.query('/1.0'), server)
    projects = project_rows(await runtime.query('/1.0/projects?recursion=1'))
    profiles, instances = await profile_inventory(runtime, projects)
    resources = await resource_observations(runtime, intent)
    preserved = preservation_projection(projects, profiles, instances, resources, admission, intent)
    bases = base_projection(profiles, intent)
    profile = profile_state(profiles, instances, intent)
    row = instances['default'].get(intent.node_name)
    instance, uuid, effective = owned_instance(row, intent)
    workers = worker_observations(instances, intent)
    forbidden, matched, clear, proofs = await listeners(runtime, intent, int(before['MainPID']), instance == 'running', effective, uuid)
    final = server_admission(await runtime.query('/1.0'), server)
    if owner_identity(await runtime.run(_OWNER_ARGS)) != before or final != admission:
        raise LifecycleStateError(_ERROR)
    binding = intent.profile.profile
    if binding is None:
        raise LifecycleStateError(_ERROR)
    current = {'preserved': preserved, 'base': bases,
               'profile': profile_metadata(profiles['default'][binding.profile_name]) if binding.profile_name in profiles['default'] else None,
               'instance': row,
               'workers': [(worker.node_name, worker.state, worker.instance_uuid, worker.no_proxy) for worker in workers],
               'listeners': proofs, 'forbidden': forbidden, 'clear': clear}
    return ProfileObservation(client_version=client, server_version=server,
        preservation_sha256=digest(preserved), base_profiles_sha256=digest(bases),
        profile_state=profile, instance_state=instance, effective_routes_match=effective,
        forbidden_listener=forbidden, listeners_match=matched, listeners_clear=clear,
        observation_sha256=digest(current), instance_uuid=uuid, workers=workers)


def integer_fields(value, fields):
    if not isinstance(value, dict) or set(value) != fields or any(type(item) is not int or item < 0 for item in value.values()):
        raise LifecycleStateError(_ERROR)


def state_network(value):
    fields = {'addresses', 'counters', 'hwaddr', 'host_name', 'mtu', 'state', 'type'}
    counters = {'bytes_received', 'bytes_sent', 'packets_received', 'packets_sent', 'errors_received',
                'errors_sent', 'packets_dropped_outbound', 'packets_dropped_inbound'}
    if not isinstance(value, dict) or set(value) != fields or type(value['mtu']) is not int or value['mtu'] < 0:
        raise LifecycleStateError(_ERROR)
    for key in ('hwaddr', 'host_name', 'state', 'type'):
        text(value[key])
    integer_fields(value['counters'], counters)
    addresses = value['addresses']
    if addresses is not None:
        if not isinstance(addresses, list):
            raise LifecycleStateError(_ERROR)
        for address in addresses:
            if not isinstance(address, dict) or set(address) != {'family', 'address', 'netmask', 'scope'}:
                raise LifecycleStateError(_ERROR)
            for item in address.values():
                text(item)


def state_pid(row):
    fields = {'status', 'status_code', 'disk', 'memory', 'network', 'pid', 'processes', 'cpu', 'started_at', 'os_info'}
    if (not isinstance(row, dict) or set(row) != fields or row['status'] != 'Running'
            or type(row['status_code']) is not int or row['status_code'] != 103
            or type(row['pid']) is not int or row['pid'] <= 0
            or type(row['processes']) is not int or row['processes'] < 0):
        raise LifecycleStateError(_ERROR)
    text(row['started_at'])
    integer_fields(row['memory'], {'usage', 'usage_peak', 'total', 'swap_usage', 'swap_usage_peak'})
    integer_fields(row['cpu'], {'usage', 'allocated_time'})
    for key, validator in (('disk', lambda entry: integer_fields(entry, {'usage', 'total'})), ('network', state_network)):
        if row[key] is not None:
            if not isinstance(row[key], dict):
                raise LifecycleStateError(_ERROR)
            for field, value in row[key].items():
                text(field)
                validator(value)
    if row['os_info'] is not None:
        if not isinstance(row['os_info'], dict) or set(row['os_info']) != {'os', 'os_version', 'kernel_version', 'hostname', 'fqdn'}:
            raise LifecycleStateError(_ERROR)
        for value in row['os_info'].values():
            text(value)
    return row['pid']


def worker_intent(intent, node_name):
    worker = next((item for item in intent.workers if item.node_name == node_name), None)
    if worker is None:
        raise LifecycleStateError(_ERROR)
    return worker


def worker_config(intent, worker):
    return scoped_node_config(intent, worker)


def worker_state(row, intent, worker):
    if row is None:
        return WorkerObservation(worker.node_name, 'absent', None, True)
    config, expanded = row['config'], row.get('expanded_config', {})
    expected = worker_config(intent, worker)
    uuid = config.get('volatile.uuid')
    try:
        canonical_uuid = str(UUID(uuid)) if type(uuid) is str else None
    except ValueError:
        canonical_uuid = None
    desired_devices = local_devices(worker)
    safe = (row['type'] == 'container' and not row['ephemeral'] and not row['stateful']
        and tuple(row['profiles']) == worker.base_profiles and canonical_uuid is not None and uuid == canonical_uuid
        and all(config.get(key) == value and expanded.get(key) == value for key, value in expected.items())
        and config.get('volatile.base_image') == worker.image_fingerprint
        and config.get('security.privileged', 'false') == 'false' and expanded.get('security.privileged', 'false') == 'false'
        and not any(key.startswith('raw.') for key in (*config, *expanded))
        and row['devices'] == desired_devices and row.get('expanded_devices', {}) == desired_devices)
    state = {('Stopped', 102): 'stopped', ('Running', 103): 'running'}.get((row['status'], row['status_code']), 'foreign')
    return WorkerObservation(worker.node_name, state if safe else 'foreign', uuid if safe else None, safe)


def worker_observations(instances, intent):
    result = tuple(worker_state(instances['default'].get(worker.node_name), intent, worker) for worker in intent.workers)
    if any(worker.state == 'foreign' or not worker.no_proxy for worker in result):
        raise LifecycleStateError(_ERROR)
    return result


ENDPOINTS = {'incus_run': '/run/incus/unix.socket', 'incus_var_lib': '/var/lib/incus/unix.socket'}


def socket_binding(raw):
    pairs = [line.split('=', 1) for line in raw.splitlines()]
    if any(len(pair) != 2 for pair in pairs):
        raise LifecycleStateError(_ERROR)
    row = dict(pairs)
    fields = {'LoadState', 'ActiveState', 'SubState', 'UnitFileState', 'Listen'}
    if 'MainPID' in row:
        fields.add('MainPID')
    if (len(row) != len(pairs) or set(row) != fields or row.get('MainPID', '0') != '0'
            or row['LoadState'] != 'loaded' or row['ActiveState'] != 'active'
            or row['SubState'] not in {'listening', 'running'}
            or row['UnitFileState'] in {'', 'masked', 'masked-runtime', 'not-found'}):
        raise LifecycleStateError(_ERROR)
    candidates = {path: kind for kind, path in ENDPOINTS.items()}
    for path, kind in candidates.items():
        if row['Listen'] in {path, path + ' (Stream)', 'Stream:' + path}:
            return kind
    raise LifecycleStateError(_ERROR)

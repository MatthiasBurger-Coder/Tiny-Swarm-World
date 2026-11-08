"""Read-only, root-anchored Incus listener and manager process provenance."""
from __future__ import annotations

import json

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.incus_preparation import runtime as incus
from tiny_swarm_world.infrastructure.adapters.network_preparation import runtime


PROBE = r'''
import json, os, pathlib, stat, sys

def mapped_root(rows):
    if not rows: raise RuntimeError('Empty identity map')
    for row in rows:
        if len(row) != 3 or any(type(n) is not int or n < 0 for n in row):
            raise RuntimeError('Invalid identity map')
        if row[2] <= 0 or any(row[i] + row[2] > 2**32 - 1 for i in (0, 1)):
            raise RuntimeError('Invalid identity range')
    for axis in (0, 1):
        ordered = sorted(rows, key=lambda row: row[axis])
        if any(a[axis] + a[2] > b[axis] for a, b in zip(ordered, ordered[1:])):
            raise RuntimeError('Overlapping identity map')
    roots = [row[1] for row in rows if row[0] == 0]
    if len(roots) != 1: raise RuntimeError('Missing mapped root')
    return roots[0]

def safe_executable(path, info):
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise RuntimeError('Executable unsafe')
    for parent in path.parents:
        metadata = parent.stat()
        if metadata.st_uid != 0 or metadata.st_mode & 0o022:
            raise RuntimeError('Executable ancestor unsafe')

def snapshot(pid, trusted=False):
    root = pathlib.Path('/proc') / str(pid)
    owner = root.stat().st_uid
    status = {}
    for line in (root / 'status').read_text().splitlines():
        key, _, value = line.partition(':')
        if key in ('Uid', 'Gid'):
            if key in status: raise RuntimeError('Duplicate credentials')
            status[key] = [int(n) for n in value.split()]
    if set(status) != {'Uid', 'Gid'} or any(len(v) != 4 for v in status.values()):
        raise RuntimeError('Incomplete credentials')
    maps = {name: [[int(n) for n in row.split()] for row in (root / name).read_text().splitlines()]
            for name in ('uid_map', 'gid_map')}
    for rows in maps.values(): mapped_root(rows)
    namespaces = {name: os.readlink(root / 'ns' / name) for name in ('user', 'net')}
    executable = ((root / 'exe').resolve(strict=True) if trusted
                  else pathlib.Path(os.readlink(root / 'exe')))
    fd = os.open(root / 'exe', os.O_RDONLY)
    try:
        info = os.fstat(fd)
        if trusted:
            safe_executable(executable, info)
            path_info = executable.stat()
            if (info.st_dev, info.st_ino) != (path_info.st_dev, path_info.st_ino):
                raise RuntimeError('Executable path changed')
        identity = [str(executable), info.st_dev, info.st_ino, info.st_uid, info.st_mode]
    finally: os.close(fd)
    start = (root / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    return dict(pid=pid, owner=owner, credentials=status, maps=maps,
                namespaces=namespaces, executable=identity, start=start)

def root_credentials(process, host=False):
    uid = mapped_root(process['maps']['uid_map'])
    gid = mapped_root(process['maps']['gid_map'])
    if host and (uid != 0 or gid != 0): raise RuntimeError('Daemon is not host root')
    if process['owner'] != uid or process['credentials'] != {'Uid': [uid]*4, 'Gid': [gid]*4}:
        raise RuntimeError('Process is not namespace root')

def host_user_namespace():
    return os.readlink('/proc/1/ns/user')

def prove(listener_pid, daemon_pid, manager_pid):
    host_namespace = host_user_namespace()
    listener = snapshot(listener_pid, True)
    daemon = snapshot(daemon_pid, True)
    manager = snapshot(manager_pid)
    root_credentials(daemon, True)
    if daemon['namespaces']['user'] != host_namespace:
        raise RuntimeError('Daemon is outside host user namespace')
    root_credentials(listener)
    if listener['executable'][1:3] != daemon['executable'][1:3]:
        raise RuntimeError('Listener executable differs from Incus')
    if listener['owner'] != 0:
        root_credentials(manager)
        if mapped_root(listener['maps']['gid_map']) == 0:
            raise RuntimeError('Mixed host and mapped root credentials')
        if listener['namespaces']['user'] == daemon['namespaces']['user']:
            raise RuntimeError('Mapped listener shares host user namespace')
        if listener['maps'] != manager['maps'] or listener['namespaces'] != manager['namespaces']:
            raise RuntimeError('Listener is outside canonical manager namespaces')
    elif (mapped_root(listener['maps']['gid_map']) != 0
          or listener['namespaces']['user'] != daemon['namespaces']['user']):
        raise RuntimeError('Listener is not host root')
    if (listener != snapshot(listener_pid, True) or daemon != snapshot(daemon_pid, True)
            or manager != snapshot(manager_pid) or host_namespace != host_user_namespace()):
        raise RuntimeError('Process changed')
    return dict(listener=listener, daemon=daemon, manager=manager)

if __name__ == '__main__':
    print(json.dumps(prove(*(int(value) for value in sys.argv[1:]))))
'''


def _validate_device(device: dict[str, str]) -> None:
    if (device.get("type") != "proxy" or "security.uid" in device or "security.gid" in device
            or device.get("bind", "host") != "host" or device.get("nat", "false") != "false"):
        raise NetworkPreparationFailure("Proxy credentials or binding cannot be trusted.")


async def _manager(expected_device: dict[str, str]) -> int:
    state = await incus.query("/1.0/instances/swarm-manager/state?project=default")
    instance = await incus.query("/1.0/instances/swarm-manager?project=default")
    pid = state.get("pid") if isinstance(state, dict) else None
    devices = instance.get("expanded_devices") if isinstance(instance, dict) else None
    if type(pid) is not int or pid <= 0 or not isinstance(devices, dict):
        raise NetworkPreparationFailure("Canonical manager process identity is incomplete.")
    matching = [device for device in devices.values() if isinstance(device, dict)
                and device.get("listen") == expected_device.get("listen")]
    if matching != [expected_device]:
        raise NetworkPreparationFailure("Canonical manager proxy configuration changed.")
    return pid


def _complete_proof(proof: object, identities: dict[str, int]) -> bool:
    fields = {"pid", "owner", "credentials", "maps", "namespaces", "executable", "start"}
    if not isinstance(proof, dict) or set(proof) != set(identities):
        return False
    return all(isinstance(proof[name], dict) and set(proof[name]) == fields
               and proof[name]["pid"] == pid and all(proof[name][key]
                   for key in ("credentials", "maps", "namespaces", "executable", "start"))
               for name, pid in identities.items())


async def verify(pid: int, expected_device: dict[str, str]) -> tuple[object, ...]:
    _validate_device(expected_device)
    manager = await _manager(expected_device)
    main = await runtime.command(("systemctl", "show", "incus.service", "--property=MainPID", "--value"))
    if type(pid) is not int or pid <= 0 or not main.strip().isdigit() or int(main.strip()) <= 0:
        raise NetworkPreparationFailure("Incus daemon process ownership cannot be observed.")
    output = await runtime.privileged(("python3", "-I", "-B", "-c", PROBE, str(pid), main.strip(), str(manager)))
    if manager != await _manager(expected_device):
        raise NetworkPreparationFailure("Canonical manager process changed.")
    after = await runtime.command(("systemctl", "show", "incus.service", "--property=MainPID", "--value"))
    if main.strip() != after.strip():
        raise NetworkPreparationFailure("Incus daemon process changed.")
    try:
        proof = json.loads(output)
    except (ValueError, TypeError):
        raise NetworkPreparationFailure("Listener provenance is incomplete.") from None
    if not _complete_proof(proof, {"listener": pid, "daemon": int(main.strip()), "manager": manager}):
        raise NetworkPreparationFailure("Listener provenance is incomplete.")
    # Canonical JSON keeps every identity observation in the inventory fingerprint.
    return (pid, json.dumps(proof, sort_keys=True, separators=(",", ":")))

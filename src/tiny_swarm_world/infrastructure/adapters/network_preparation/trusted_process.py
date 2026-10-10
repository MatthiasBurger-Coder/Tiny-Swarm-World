"""Read-only root process provenance matched to the observed Incus executable."""
from __future__ import annotations

import json

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation import runtime


PROBE = r'''
import json, os, pathlib, stat, sys
def snapshot(pid):
    root = pathlib.Path('/proc') / str(pid)
    if root.stat().st_uid != 0: raise RuntimeError('Process owner differs')
    executable = (root / 'exe').resolve(strict=True)
    for parent in executable.parents:
        info = parent.stat()
        if info.st_uid != 0 or info.st_mode & 0o022: raise RuntimeError('Executable ancestor unsafe')
    fd = os.open(root / 'exe', os.O_RDONLY)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise RuntimeError('Executable unsafe')
        identity = (info.st_dev, info.st_ino)
    finally: os.close(fd)
    start = (root / 'stat').read_text().rsplit(')',1)[1].split()[19]
    return [str(executable), *identity, start]
listener, daemon = int(sys.argv[1]), int(sys.argv[2])
before, trusted = snapshot(listener), snapshot(daemon)
if before[1:3] != trusted[1:3]: raise RuntimeError('Listener executable differs from Incus')
if before != snapshot(listener) or trusted != snapshot(daemon): raise RuntimeError('Process changed')
print(json.dumps(before))
'''


async def verify(pid: int) -> tuple[object, ...]:
    main = await runtime.command(("systemctl", "show", "incus.service", "--property=MainPID", "--value"))
    if not main.strip().isdigit() or int(main.strip()) <= 0:
        raise NetworkPreparationFailure("Incus daemon process ownership cannot be observed.")
    output = await runtime.privileged(("python3", "-I", "-B", "-c", PROBE, str(pid), main.strip()))
    proof = json.loads(output)
    if not isinstance(proof, list) or len(proof) != 4:
        raise NetworkPreparationFailure("Listener provenance is incomplete.")
    return (pid, *proof)

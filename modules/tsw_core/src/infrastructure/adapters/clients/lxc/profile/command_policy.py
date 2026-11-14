"""Finite observation commands and the trusted clean-source read sequence."""
from collections.abc import Awaitable, Callable
from pathlib import Path
import re

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile import observations
from tiny_swarm_world.infrastructure.adapters.network_preparation.trusted_process import PROBE

_ENV = observations._ENV
SOCKET_ARGS = ('/usr/bin/systemctl', 'show', 'incus.socket',
               '--property=LoadState,ActiveState,SubState,UnitFileState,MainPID,Listen', '--no-pager')
_FIXED_READS = {(*_ENV, 'version'), SOCKET_ARGS, observations._OWNER_ARGS,
                ('/usr/bin/sudo', '-n', '--', '/usr/bin/ss', '-H', '-O', '-ltnp')}
_PROBE_PREFIX = ('/usr/bin/sudo', '-n', '--', '/usr/bin/python3', '-I', '-B', '-c', PROBE)
_MAX_LINUX_PID = 4_194_304
_GIT_ENV = ('/usr/bin/env', '-i', 'LC_ALL=C', 'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
            'GIT_CONFIG_NOSYSTEM=1', 'GIT_CONFIG_GLOBAL=/dev/null', '/usr/bin/git', '--no-optional-locks')
SOURCE_ERROR = 'Scoped setup requires the original clean source, admitted local image and exact original profile operation.'


def require_read_command(args: tuple[str, ...]) -> None:
    if type(args) is not tuple or any(type(part) is not str for part in args):
        raise LifecycleStateError(observations._ERROR)
    if args in _FIXED_READS:
        return
    query_prefix = (*_ENV, 'query', '--request', 'GET', '--raw')
    if args[:-1] == query_prefix:
        observations.allowed_read_uri(args[-1])
        return
    if args[:-3] == _PROBE_PREFIX and all(
            re.fullmatch(r'[1-9][0-9]{0,6}', pid) and int(pid) < _MAX_LINUX_PID for pid in args[-3:]):
        return
    raise LifecycleStateError(observations._ERROR)


def filter_suppressions(config: str) -> tuple[str, ...]:
    suppress: list[str] = []
    for record in config.split('\0'):
        key = record.partition('\n')[0]
        if key.startswith('filter.'):
            if re.fullmatch(r'filter\.[A-Za-z0-9_.-]{1,128}\.(clean|smudge|process|required)', key) is None:
                raise LifecycleStateError(SOURCE_ERROR)
            suppress.extend(('-c', key + ('=false' if key.endswith('.required') else '=')))
    return tuple(suppress)


async def read_clean_source_revision(root: Path, run: Callable[[tuple[str, ...]], Awaitable[str]]) -> str:
    if not root.is_absolute() or '..' in root.parts:
        raise LifecycleStateError(SOURCE_ERROR)
    prefix = (*_GIT_ENV, '-C', str(root), '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null')
    raw = await run((*prefix, 'config', '--list', '--null', '--includes'))
    suppress = filter_suppressions(raw)
    top = (await run((*prefix, 'rev-parse', '--show-toplevel'))).strip()
    tracked = await run((*prefix, 'ls-files', '-v', '--stage', '-z'))
    if top != str(root) or not tracked or any(record and not record.startswith(('H 100644 ', 'H 100755 ', 'H 120000 '))
                                               for record in tracked.split('\0')):
        raise LifecycleStateError(SOURCE_ERROR)
    revision = (await run((*prefix, 'rev-parse', '--verify', 'HEAD'))).strip()
    if re.fullmatch('[0-9a-f]{40}', revision) is None:
        raise LifecycleStateError(SOURCE_ERROR)
    if await run((*prefix, *suppress, 'status', '--porcelain=v1', '--untracked-files=normal', '--ignore-submodules=all')):
        raise LifecycleStateError(SOURCE_ERROR)
    return revision

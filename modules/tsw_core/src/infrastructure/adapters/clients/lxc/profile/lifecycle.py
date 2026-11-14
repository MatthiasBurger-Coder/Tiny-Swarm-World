"""Bounded local Incus observations and exact installation-owned primitives."""
from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from functools import partial
import json
import math
import time
from pathlib import Path
import stat
import socket
import struct
from typing import Any

from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile import observations
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.command_policy import (
    _ENV, SOCKET_ARGS, read_clean_source_revision, require_read_command,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.args import scoped_init_args
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import LxcNodeCommandResult, LxcNodeCommandRunner

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import (
    InstallationLease, ProfileCapabilityRepository, ProfileObservation,
)
from tiny_swarm_world.domain.lifecycle.models import InstallationProfileBinding
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, ProfileCapabilityMatrix

_ERROR = 'Scoped Incus observation or effect is unknown; preserve the checkpoint for explicit recovery.'


@dataclass
class Budget:
    remaining: float = 300.0
    busy: bool = False
    commands: int = 0
    output: int = 0


class IncusProfileLifecycleRuntime:
    def __init__(self, runner: LxcNodeCommandRunner, *, capabilities: ProfileCapabilityRepository | None = None):
        self.runner = runner
        self.capabilities = capabilities
        self.lease: InstallationLease | None = None
        self.intent: ManagerCreateIntent | None = None
        self.endpoint_kind: str | None = None
        self.budget = Budget()

    def for_observation(self, intent: ManagerCreateIntent) -> 'IncusProfileLifecycleRuntime':
        private = copy(self)
        private.lease = None
        private.capabilities = None
        private.intent = ManagerCreateIntent.model_validate_json(intent.model_dump_json())
        private.endpoint_kind = None
        private.budget = Budget()
        return private

    def for_preparation(self, lease: InstallationLease) -> 'IncusProfileLifecycleRuntime':
        lease.require_active()
        private = copy(self)
        private.lease, private.intent, private.endpoint_kind = lease, None, None
        private.budget = Budget()
        return private

    def for_operation(self, lease: InstallationLease, intent: ManagerCreateIntent) -> 'IncusProfileLifecycleRuntime':
        lease.require_active()
        private = copy(self)
        private.lease = lease
        private.intent = ManagerCreateIntent.model_validate_json(intent.model_dump_json())
        if self.lease is not lease:
            private.budget = Budget()
        return private

    async def run(self, args: tuple[str, ...], *, mutation: bool = False, timeout: int = 30) -> str:
        if mutation is not False:
            raise LifecycleStateError(_ERROR)
        require_read_command(args)
        return await _dispatch_profile_command(self, args, timeout=timeout)

    async def clean_source_revision(self, root: Path) -> str:
        return await read_clean_source_revision(root, partial(_dispatch_profile_command, self))

    async def _run_effect(self, intent: ManagerCreateIntent, args: tuple[str, ...], *, timeout: int = 30) -> str:
        await require_live_version(self, intent)
        return await _dispatch_profile_command(self, args, intent=intent, timeout=timeout)

    async def query(self, path: str) -> Any:
        observations.allowed_read_uri(path)
        raw = await self.run((*_ENV, 'query', '--request', 'GET', '--raw', path))
        return observations.metadata(raw)

    async def inspect(self, intent: ManagerCreateIntent) -> ProfileObservation:
        if self.lease is None:
            private = copy(self)
            private.capabilities = None
            if self.intent != intent:
                private.budget = Budget()
            private.intent = ManagerCreateIntent.model_validate_json(intent.model_dump_json())
            return await observations.inspect_runtime(private, intent)
        self.lease.require_active()
        if self.intent is not None and self.intent != intent:
            raise LifecycleStateError(_ERROR)
        return await observations.inspect_runtime(self, intent)

    async def create_profile(self, intent: ManagerCreateIntent) -> None:
        binding = require_bound(self, intent)
        payload = {'name': binding.profile_name, 'description': 'Tiny Swarm World installation profile',
                   'config': intent.markers(), 'devices': intent.devices()}
        raw = await self._run_effect(intent, (*_ENV, 'query', '--request', 'POST', '--data',
            json.dumps(payload, sort_keys=True, separators=(',', ':')), '--raw', '--wait',
            '/1.0/profiles?project=default'))
        observations.metadata(raw)

    async def update_profile(self, intent: ManagerCreateIntent, before: ManagerCreateIntent) -> None:
        await _update_profile(self, intent, before)

    async def init_instance(self, intent: ManagerCreateIntent) -> None:
        await self._run_effect(intent, (*_ENV, *scoped_init_args(intent, intent.node_name)), timeout=120)

    async def start_instance(self, intent: ManagerCreateIntent) -> None:
        await self._run_effect(intent, (*_ENV, '--project', 'default', 'start', intent.node_name), timeout=120)

    async def delete_instance(self, intent: ManagerCreateIntent) -> None:
        await self._run_effect(intent, (*_ENV, '--project', 'default', 'delete', intent.node_name), timeout=120)

    async def delete_profile(self, intent: ManagerCreateIntent) -> None:
        binding = require_bound(self, intent)
        await self._run_effect(intent, (*_ENV, '--project', 'default', 'profile', 'delete', binding.profile_name))


    async def init_worker(self, intent: ManagerCreateIntent, node_name: str) -> None:
        observations.worker_intent(intent, node_name)
        await self._run_effect(intent, (*_ENV, *scoped_init_args(intent, node_name)), timeout=120)

    async def start_worker(self, intent: ManagerCreateIntent, node_name: str) -> None:
        worker = observations.worker_intent(intent, node_name)
        await self._run_effect(intent, (*_ENV, '--project', 'default', 'start', worker.node_name), timeout=120)


async def _update_profile(self: IncusProfileLifecycleRuntime, intent: ManagerCreateIntent,
                          before: ManagerCreateIntent) -> None:
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.cas import PROFILE_CAS

    binding = require_bound(self, intent)
    previous = before.profile.profile
    if previous is None or previous.profile_name != binding.profile_name or before.markers() != intent.markers():
        raise LifecycleStateError(_ERROR)
    await require_live_version(self, intent)
    uri = '/1.0/profiles/' + binding.profile_name + '?project=default'
    row = await self.query(uri)
    observations.profile_rows([row], 'default')
    if (row['config'] != before.markers() or row['devices'] != before.devices()
            or row['description'] != 'Tiny Swarm World installation profile'
            or observations.consumers(row['used_by']) != (('default', before.node_name),)):
        raise LifecycleStateError(_ERROR)
    payload = {'endpoint_kind': intent.endpoint_kind, 'path': uri, 'before': row, 'target': {'description': row['description'],
               'config': intent.markers(), 'devices': intent.devices()}}
    if self.budget.commands + 3 > 2048 or self.budget.output + 3 * 1024 * 1024 > 16 * 1024 * 1024:
        raise LifecycleStateError(_ERROR)
    self.budget.commands += 2
    self.budget.output += 3 * 1024 * 1024  # Bound both HTTP bodies and finite headers, including discarded metadata.
    result = await self._run_effect(intent, ('/usr/bin/env', '-i', 'LC_ALL=C', 'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
        '/usr/bin/python3', '-I', '-B', '-c', PROFILE_CAS,
        json.dumps(payload, sort_keys=True, separators=(',', ':'))))
    if result != 'PROFILE_CAS_APPLIED\n':
        raise LifecycleStateError(_ERROR)


def require_bound(runtime: IncusProfileLifecycleRuntime, intent: ManagerCreateIntent) -> InstallationProfileBinding:
    binding = intent.profile.profile
    if runtime.lease is None or runtime.intent != intent or binding is None or runtime.capabilities is None:
        raise LifecycleStateError(_ERROR)
    runtime.lease.require_active()
    try:
        matrix = ProfileCapabilityMatrix.model_validate_json(runtime.capabilities.load().model_dump_json())
    except (AttributeError, OSError, RecursionError, TypeError, ValueError):
        raise LifecycleStateError(_ERROR) from None
    if not matrix.admits(intent.profile.incus_version, intent.profile.incus_version):
        raise LifecycleStateError(_ERROR)
    return binding


async def require_live_version(runtime: IncusProfileLifecycleRuntime, intent: ManagerCreateIntent) -> None:
    require_bound(runtime, intent)
    versions = observations.client_versions(await runtime.run((*_ENV, 'version')))
    if versions != (intent.profile.incus_version, intent.profile.incus_version):
        raise LifecycleStateError(_ERROR)



def assert_local_socket(endpoint_kind: str | None, *, timeout: float) -> None:
    if endpoint_kind is None or endpoint_kind not in observations.ENDPOINTS:
        raise LifecycleStateError(_ERROR)
    path = Path(observations.ENDPOINTS[endpoint_kind])
    try:
        info = path.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != 0:
            raise ValueError('Untrusted socket.')
        for parent in path.parents:
            row = parent.lstat()
            if not stat.S_ISDIR(row.st_mode) or row.st_uid != 0 or row.st_mode & 0o022:
                raise ValueError('Untrusted socket parent.')
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout)
            connection.connect(str(path))
            _, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if uid != 0:
                raise ValueError('Untrusted socket peer.')
    except (OSError, ValueError):
        raise LifecycleStateError(_ERROR) from None


async def _bind_socket(runtime: IncusProfileLifecycleRuntime, args: tuple[str, ...]) -> tuple[str, ...]:
    observed = observations.socket_binding(await runtime.run(SOCKET_ARGS))
    expected = runtime.intent.endpoint_kind if runtime.intent is not None else runtime.endpoint_kind
    if expected is not None and observed != expected:
        raise LifecycleStateError(_ERROR)
    runtime.endpoint_kind = observed
    if args[:len(_ENV)] == _ENV:
        return (*_ENV[:5], 'INCUS_SOCKET=' + observations.ENDPOINTS[observed], *_ENV[5:], *args[len(_ENV):])
    return args


async def _dispatch_profile_command(self: IncusProfileLifecycleRuntime, args: tuple[str, ...], *,
                                    intent: ManagerCreateIntent | None = None, timeout: int = 30) -> str:
    if self.lease is not None:
        self.lease.require_active()
    local = args[:len(_ENV)] == _ENV or intent is not None
    if local:
        args = await _bind_socket(self, args)
    budget = self.budget
    if (budget.busy or not math.isfinite(budget.remaining) or budget.remaining <= 0
            or budget.commands >= 2048 or type(timeout) is not int or not 1 <= timeout <= 120):
        raise LifecycleStateError(_ERROR)
    budget.busy = True
    started = time.monotonic()
    budget.commands += 1
    try:
        available = budget.remaining
        if local:
            assert_local_socket(self.endpoint_kind, timeout=min(5.0, available))
        if intent is not None:
            require_bound(self, intent)
        if local:
            available -= time.monotonic() - started
            if available <= 0:
                raise LifecycleStateError(_ERROR)
        result = await self.runner.run(args, min(timeout, available))
    except (OSError, ValueError, RuntimeError, TimeoutError):
        raise LifecycleStateError(_ERROR) from None
    finally:
        duration = time.monotonic() - started
        budget.busy = False
        if not math.isfinite(duration) or duration < 0:
            budget.remaining = -1
            raise LifecycleStateError(_ERROR)
        budget.remaining -= duration
    if budget.remaining < 0:
        raise LifecycleStateError(_ERROR)
    return _checked_stdout(result, budget)


def _checked_stdout(result: LxcNodeCommandResult, budget: Budget) -> str:
    if (type(result.returncode) is not int or result.returncode != 0 or result.timed_out is not False
            or result.failure_hint is not None or type(result.stdout) is not str
            or type(result.stderr) is not str or result.stderr):
        raise LifecycleStateError(_ERROR)
    count = len(result.stdout.encode('utf-8', 'strict'))
    budget.output += count
    if count > 8388608 or budget.output > 16777216:
        raise LifecycleStateError(_ERROR)
    return result.stdout

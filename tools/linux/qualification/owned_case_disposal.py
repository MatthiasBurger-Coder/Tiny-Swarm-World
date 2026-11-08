"""Qualification-only disposal of UUID-bound new default-project case nodes.

This is deliberately not a product reset command. The caller owns the host
maintenance lock; this adapter separately acquires the actual installation
lease after the product child has exited. No command, project or callback is
accepted from a CLI argument.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import re
import time
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import quote
from uuid import UUID

if TYPE_CHECKING:
    from . import native_lxd_maintenance as native
else:
    native = importlib.import_module((__package__ + '.' if __package__ else '') + 'native_lxd_maintenance')

NAMES = ('swarm-worker-2', 'swarm-worker-1', 'swarm-manager')
INSTALLATION = 'user.tiny_swarm_world.installation_id'
OPERATION = 'user.tiny_swarm_world.operation_id'


@dataclass(frozen=True)
class OwnedNode:
    name: str
    uuid: str
    specification_sha256: str


@dataclass(frozen=True)
class DisposalIntent:
    installation_id: str
    operation_id: str
    checkpoint_sha256: str
    profile_name: str
    profile_sha256: str
    pool: str
    nodes: tuple[OwnedNode, ...]

    def __post_init__(self) -> None:
        try:
            installation_uuid = str(UUID(self.installation_id)) == self.installation_id
        except (ValueError, AttributeError):
            installation_uuid = False
        native.require(installation_uuid
                       and bool(native.RUN_ID.fullmatch(self.operation_id)), 'CASE_IDENTITY_INVALID')
        native.require(bool(re.fullmatch(r'tsw-manager-[0-9a-f]{24}', self.profile_name))
                       and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', self.pool)), 'CASE_RESOURCE_INVALID')
        native.require(bool(native.HEX.fullmatch(self.checkpoint_sha256))
                       and bool(native.HEX.fullmatch(self.profile_sha256)), 'CASE_DIGEST_INVALID')
        native.require(tuple(node.name for node in self.nodes) == tuple(name for name in NAMES if any(
            row.name == name for row in self.nodes)), 'CASE_NODE_SET_INVALID')
        for node in self.nodes:
            try:
                valid_uuid = str(UUID(node.uuid)) == node.uuid
            except (ValueError, AttributeError):
                valid_uuid = False
            native.require(valid_uuid and bool(native.HEX.fullmatch(node.specification_sha256)), 'CASE_UUID_INVALID')


class DisposalPort(Protocol):
    def inspect(self) -> dict[str, Any]: ...
    def stop(self, node: OwnedNode) -> None: ...
    def delete(self, node: OwnedNode) -> None: ...
    def delete_profile(self, intent: DisposalIntent) -> None: ...
    def event(self, action: str, name: str) -> None: ...
    def pending(self, action: str, name: str) -> bool: ...


class SuiteDisposalPort(Protocol):
    def case_graph(self, intent: DisposalIntent) -> dict[str, Any]: ...
    def incus_effect(self, args: list[str], timeout: int) -> None: ...


def specification(row: dict[str, Any]) -> str:
    """Current spec identity, including UUID, with only status/volatile ignored."""
    return native.digest(native.canonical(native.config_projection(row, instance=True)))


def profile_identity(row: dict[str, Any]) -> str:
    return native.digest(native.canonical(native.config_projection(row)))


def own_reference(value: Any, intent: DisposalIntent) -> bool:
    if not isinstance(value, dict) or value.get('project') != 'default':
        return False
    names = {node.name for node in intent.nodes}
    if value.get('kind') == 'instances':
        return value.get('name') in names
    if value.get('kind') == 'profiles':
        return value.get('name') == intent.profile_name
    return value.get('kind') == 'storage-volumes' and value.get('name') in {
        f'{intent.pool}/container/{name}' for name in names}


def default_manager_consumers(value: Any) -> set[tuple[str, str]]:
    """Incus6.0.5 URL.Project omits the default project query parameter.

    Accept only the two literal spellings of this one known-scope consumer.
    Additional queries, fragments, escaping and semantic duplicates are denied.
    """
    native.require(isinstance(value, list) and len(value) <= 1, 'CASE_PROFILE_FOREIGN_CONSUMER')
    allowed = {'/1.0/instances/swarm-manager', '/1.0/instances/swarm-manager?project=default'}
    native.require(all(type(item) is str and item in allowed for item in value), 'CASE_PROFILE_FOREIGN_CONSUMER')
    return {('default', 'swarm-manager')} if value else set()


def validate_case_graph(graph: dict[str, Any], intent: DisposalIntent) -> dict[str, dict[str, Any]]:
    """Raw rows come from the unchanged full, independently validated collector."""
    native.require(set(graph) == {'instances', 'profile', 'volumes', 'snapshots', 'checkpoint_sha256'},
                   'CASE_GRAPH_INVALID')
    native.require(graph['checkpoint_sha256'] == intent.checkpoint_sha256, 'CASE_CHECKPOINT_DRIFT')
    native.require(isinstance(graph['instances'], dict) and set(graph['instances']) <= {node.name for node in intent.nodes},
                   'CASE_INSTANCE_SET_DRIFT')
    nodes = {node.name: node for node in intent.nodes}
    for name, row in graph['instances'].items():
        native.require(isinstance(row, dict) and row.get('name') == name and row.get('type') == 'container'
            and row.get('ephemeral') is False and row.get('stateful') is False, 'CASE_INSTANCE_KIND_DRIFT')
        config = row.get('config', {})
        native.require(config.get(INSTALLATION) == intent.installation_id
            and config.get(OPERATION) == intent.operation_id and config.get('volatile.uuid') == nodes[name].uuid
            and specification(row) == nodes[name].specification_sha256, 'CASE_INSTANCE_IDENTITY_DRIFT')
        native.require((row.get('status'), row.get('status_code')) in {('Running', 103), ('Stopped', 102)},
                       'CASE_INSTANCE_STATE_UNKNOWN')
        disks = [device for device in row.get('expanded_devices', {}).values() if device.get('type') == 'disk']
        native.require(len(disks) == 1 and disks[0].get('path') == '/' and disks[0].get('pool') == intent.pool
                       and not disks[0].get('source'), 'CASE_EXTERNAL_DISK_REFUSED')
    native.require(isinstance(graph['snapshots'], list) and not graph['snapshots'], 'CASE_SNAPSHOTS_REQUIRE_REVIEW')
    volumes = graph['volumes']
    native.require(isinstance(volumes, list) and len(volumes) == len(graph['instances']), 'CASE_ROOT_VOLUME_SET_DRIFT')
    native.require({row.get('name') for row in volumes} == set(graph['instances']), 'CASE_ROOT_VOLUME_SET_DRIFT')
    for row in volumes:
        native.require(row.get('type') == 'container' and row.get('owner_project') == 'default'
            and row.get('content_type') == 'filesystem' and row.get('used_by') == [
                {'kind': 'instances', 'name': row['name'], 'project': 'default'}], 'CASE_ROOT_VOLUME_FOREIGN_CONSUMER')
    profile = graph['profile']
    if profile is not None:
        native.require(isinstance(profile, dict) and profile.get('name') == intent.profile_name
            and profile.get('project') == 'default' and profile_identity(profile) == intent.profile_sha256,
            'CASE_PROFILE_DRIFT')
        native.require(profile.get('config') == {INSTALLATION: intent.installation_id, OPERATION: intent.operation_id},
                       'CASE_PROFILE_MARKER_DRIFT')
        allowed = {('default', 'swarm-manager')} if 'swarm-manager' in graph['instances'] else set()
        native.require(default_manager_consumers(profile.get('used_by')) == allowed, 'CASE_PROFILE_FOREIGN_CONSUMER')
    else:
        native.require(not graph['instances'], 'CASE_PROFILE_MISSING')
    return graph['instances']


def dispose(port: DisposalPort, intent: DisposalIntent) -> None:
    """Unknown mutation outcomes are re-observed, never automatically replayed."""
    for node in intent.nodes:
        observed = validate_case_graph(port.inspect(), intent)
        if node.name not in observed:
            continue
        if observed[node.name]['status'] == 'Running':
            native.require(not port.pending('stop', node.name), 'CASE_STOP_OUTCOME_UNCERTAIN')
            port.event('stop', node.name)
            port.stop(node)
            observed = validate_case_graph(port.inspect(), intent)
        native.require(node.name in observed and observed[node.name]['status'] == 'Stopped', 'CASE_STOP_NOT_PROVEN')
    for node in intent.nodes:
        observed = validate_case_graph(port.inspect(), intent)
        native.require(all(row['status'] == 'Stopped' for row in observed.values()), 'CASE_STOP_NOT_PROVEN')
        if node.name not in observed:
            continue
        native.require(not port.pending('delete', node.name), 'CASE_DELETE_OUTCOME_UNCERTAIN')
        port.event('delete', node.name)
        port.delete(node)
        native.require(node.name not in validate_case_graph(port.inspect(), intent), 'CASE_DELETE_NOT_PROVEN')
    graph = port.inspect()
    native.require(not validate_case_graph(graph, intent), 'CASE_NODES_REMAIN')
    if graph['profile'] is not None:
        native.require(not port.pending('profile-delete', intent.profile_name), 'CASE_PROFILE_DELETE_UNCERTAIN')
        port.event('profile-delete', intent.profile_name)
        port.delete_profile(intent)
    final = port.inspect()
    native.require(not validate_case_graph(final, intent) and final['profile'] is None, 'CASE_DISPOSAL_NOT_PROVEN')


class IncusDisposalPort:
    """Fixed adapter; parent supplies the full-provenance suite port, not argv."""
    def __init__(self, suite: SuiteDisposalPort, intent: DisposalIntent, journal: native.Journal):
        self.suite, self.intent, self.journal = suite, intent, journal

    def inspect(self) -> dict[str, Any]:
        return dict(self.suite.case_graph(self.intent))

    def event(self, action: str, name: str) -> None:
        native.require(action in {'stop', 'delete', 'profile-delete'} and name in (*NAMES, self.intent.profile_name),
                       'CASE_EFFECT_INVALID')
        self.journal.save(f'case-{action}-{name}.json', {'action': action, 'name': name,
            'intent_sha256': native.digest(native.canonical(self.intent_dict())), 'utc': time.time()})

    def intent_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self.intent)

    def pending(self, action: str, name: str) -> bool:
        return (self.journal.directory / f'case-{action}-{name}.json').exists()

    def stop(self, node: OwnedNode) -> None:
        self.suite.incus_effect(['--project', 'default', 'stop', node.name, '--timeout', '60'], 75)

    def delete(self, node: OwnedNode) -> None:
        self.suite.incus_effect(['--project', 'default', 'delete', node.name], 120)

    def delete_profile(self, intent: DisposalIntent) -> None:
        self.suite.incus_effect(['--project', 'default', 'profile', 'delete', intent.profile_name], 30)


def read_creation(root: Any) -> tuple[bytes, dict[str, Any]]:
    """Use the real merged strict model; an unmerged S04 is a hard prerequisite."""
    model = importlib.import_module('tiny_swarm_world.domain.lifecycle.profile_lifecycle').ProfileLifecycleCheckpoint
    raw = native.read_private(root / '.tiny-swarm-world/installation/profile-operation.json')
    native.inventory.strict_json(raw)
    row = model.model_validate_json(raw)
    return raw, dict(row.model_dump(mode='json'))


def query_uri(name: str) -> str:
    native.require(name in NAMES, 'CASE_NODE_NOT_ALLOWED')
    return '/1.0/instances/' + quote(name, safe='') + '?project=default'

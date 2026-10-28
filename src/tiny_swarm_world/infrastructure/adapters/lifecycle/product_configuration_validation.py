"""Finite no-follow inspection of an explicitly owned infrastructure input."""
from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from pathlib import Path
import stat

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError

MAX_MEMBERS = 4096
MAX_DEPTH = 16
MAX_BYTES = 64 * 1024 * 1024
MAX_FILE_BYTES = 16 * 1024 * 1024
PROVIDER = 'config/node-providers/provider_config.yaml'


def refused():
    return LifecycleStateError('Effective infrastructure is unsafe, changed or outside the admitted policy; preserve inputs for review.')


def identity(info):
    return [info.st_dev, info.st_ino, info.st_uid, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns, info.st_nlink]


@dataclass
class ConfigurationTree:
    root: list[int]
    files: dict[str, bytes] = field(repr=False)
    members: dict[str, list[int]] = field(repr=False)

    @property
    def size(self):
        return sum(map(len, self.files.values()))

    def metadata(self):
        return {'root': self.root, 'members': self.members}


def _safe_directory(info, *, root=False):
    if not stat.S_ISDIR(info.st_mode):
        raise refused()
    if root:
        if info.st_uid != os.getuid() or info.st_mode & 0o7077:
            raise refused()
    elif info.st_uid not in (0, os.getuid()) or info.st_mode & 0o022:
        # A root-owned sticky ancestor (e.g. /tmp) cannot replace owned children.
        if not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX):
            raise refused()


@contextmanager
def open_directory(path):
    """Traverse canonical absolute ancestry using held directory descriptors."""
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise refused()
    descriptors = [os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)]
    try:
        _safe_directory(os.fstat(descriptors[0]))
        for part in path.parts[1:]:
            descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                 dir_fd=descriptors[-1])
            descriptors.append(descriptor)
            _safe_directory(os.fstat(descriptor))
        yield descriptors[-1]
        # Check links between held parents after traversal/capture as well.
        for index, part in enumerate(path.parts[1:]):
            if identity(os.stat(part, dir_fd=descriptors[index], follow_symlinks=False)) != identity(os.fstat(descriptors[index + 1])):
                raise refused()
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _read_file(parent, name, before):
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or before.st_uid != os.getuid() or before.st_mode & 0o022
            or before.st_mode & 0o7000
            or before.st_size > MAX_FILE_BYTES):
        raise refused()
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        if identity(before) != identity(os.fstat(descriptor)):
            raise refused()
        with os.fdopen(os.dup(descriptor), 'rb') as stream:
            content = stream.read(MAX_FILE_BYTES + 1)
        if len(content) != before.st_size or identity(before) != identity(os.fstat(descriptor)):
            raise refused()
        return content
    finally:
        os.close(descriptor)


def _read_members(descriptor, prefix, files, members, budget):
    before = identity(os.fstat(descriptor))
    names = []
    with os.scandir(descriptor) as entries:
        for entry in entries:
            if len(members) + len(names) >= MAX_MEMBERS:
                raise refused()
            names.append(entry.name)
    for name in sorted(names):
        relative = prefix + name
        if len(members) >= MAX_MEMBERS or len(Path(relative).parts) > MAX_DEPTH:
            raise refused()
        info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        members[relative] = identity(info)
        if stat.S_ISDIR(info.st_mode):
            _safe_directory(info)
            if info.st_uid != os.getuid() or info.st_mode & 0o7000:
                raise refused()
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            try:
                if identity(info) != identity(os.fstat(child)):
                    raise refused()
                _read_members(child, relative + '/', files, members, budget)
            finally:
                os.close(child)
        else:
            budget[0] += info.st_size
            if budget[0] > MAX_BYTES:
                raise refused()
            files[relative] = _read_file(descriptor, name, info)
        if identity(info) != identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False)):
            raise refused()
    if before != identity(os.fstat(descriptor)):
        raise refused()


def read_tree(path, *, private=True):
    try:
        with open_directory(path) as descriptor:
            if private:
                _safe_directory(os.fstat(descriptor), root=True)
            files, members = {}, {}
            _read_members(descriptor, '', files, members, [0])
            return ConfigurationTree(identity(os.fstat(descriptor)), files, members)
    except (OSError, ValueError):
        raise refused() from None


def _provider_mapping(content):
    from tiny_swarm_world.infrastructure.adapters.configuration.configuration_sources import validate_configuration_tree
    from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import _config_from_mapping

    parser = YAML(typ='safe')
    parser.allow_duplicate_keys = False
    data = parser.load(content.decode('utf-8'))
    validate_configuration_tree(data)
    _config_from_mapping(data)
    return data


def memory_only(source, effective):
    """Use the existing typed provider parser; compare every other field exactly."""
    try:
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.resource.resolution import resources_supported

        source_data, effective_data = _provider_mapping(source), _provider_mapping(effective)
        for data in (source_data, effective_data):
            for node in data['nodes']:
                if not resources_supported(node['resources']) or not node['resources'].get('memory'):
                    raise refused()
                node['resources']['memory'] = '<admitted-memory>'
        if source_data != effective_data:
            raise refused()
    except Exception:
        # Parser diagnostics may contain operator input; report no raw values.
        raise refused() from None


def validate_policy(official, effective):
    if set(official.files) != set(effective.files) or set(official.members) != set(effective.members):
        raise refused()
    for name, source in official.files.items():
        if bool(official.members[name][3] & 0o111) != bool(effective.members[name][3] & 0o111):
            raise refused()
        if source != effective.files[name]:
            if name != PROVIDER:
                raise refused()
            memory_only(source, effective.files[name])


def require_capacity(tree, disk_path):
    """Apply the unchanged provider planning guard to actual effective host limits."""
    from tiny_swarm_world.domain.preflight.resources import HostResources, PlannedContainerLimit, validate_planned_container_limits
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.resource.resolution import resource_cpu, resource_memory_bytes, resources_supported
    from tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector import WslResourceInspector
    from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import _config_from_mapping

    try:
        config = _config_from_mapping(_provider_mapping(tree.files[PROVIDER]))
        if not all(resources_supported(node.resources) for node in config.nodes):
            raise refused()
        planned = tuple(PlannedContainerLimit(node.spec.name, resource_cpu(node.resources.get('cpu')),
                        resource_memory_bytes(node.resources.get('memory'))) for node in config.nodes)
        resources = WslResourceInspector().inspect(disk_path)
        if not isinstance(resources, HostResources) or not validate_planned_container_limits(resources, planned):
            raise refused()
    except Exception:
        raise refused() from None

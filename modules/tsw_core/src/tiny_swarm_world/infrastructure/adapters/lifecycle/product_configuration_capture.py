"""Private descriptor-bound binding persistence and operation-owned capture."""
import json
import os
import ctypes
from contextlib import contextmanager
from pathlib import Path
import stat
from uuid import uuid4

from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_validation import (
    MAX_FILE_BYTES, identity, open_directory, read_tree, refused,
)


def atomic_record(directory, record):
    """Publish only under held private ancestry; never follow a record symlink."""
    name = '.binding-' + uuid4().hex
    with open_directory(directory) as parent:
        if identity(os.fstat(parent))[:4] != record['directory_identity']:
            raise refused()
        if record['capture_state'] == 'captured':
            snapshot = os.stat('snapshot', dir_fd=parent, follow_symlinks=False)
            if identity(snapshot) != record['snapshot_metadata']['root']:
                raise refused()
        if 'binding.json' in os.listdir(parent):
            previous = os.stat('binding.json', dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(previous.st_mode) or previous.st_nlink != 1 or previous.st_uid != os.getuid():
                raise refused()
        descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(json.dumps(record, sort_keys=True).encode() + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, 'binding.json', src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)


def load_record(directory):
    try:
        with open_directory(directory) as parent:
            names = set(os.listdir(parent))
            descriptor = os.open('binding.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(descriptor, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                        or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > MAX_FILE_BYTES):
                    raise refused()
                raw = stream.read(MAX_FILE_BYTES + 1)
                if identity(info) != identity(os.fstat(stream.fileno())):
                    raise refused()
            if identity(info) != identity(os.stat('binding.json', dir_fd=parent, follow_symlinks=False)):
                raise refused()
        record = json.loads(raw)
        if (set(record) != {'version', 'reference', 'source_revision', 'target_revision', 'source_path',
                            'source_metadata', 'capture_state', 'snapshot_metadata', 'directory_identity', 'pending_roots'}
                or type(record['version']) is not int or record['version'] != 1
                or record['capture_state'] not in ('admitted', 'capturing', 'captured')):
            raise refused()
        metadata = record['snapshot_metadata']
        if record['capture_state'] == 'captured':
            if (not isinstance(metadata, dict) or set(metadata) != {'root', 'members'}
                    or not _identity_record(metadata['root']) or not isinstance(metadata['members'], dict)
                    or any(not isinstance(name, str) or not _identity_record(member)
                           for name, member in metadata['members'].items())):
                raise refused()
            stage_name = None
        else:
            stage_name = metadata.get('stage_name') if isinstance(metadata, dict) else None
            if metadata is not None and (not isinstance(metadata, dict)
                                         or set(metadata) - {'stage_name', 'root_identity'}):
                raise refused()
        if stage_name is not None and (not isinstance(stage_name, str)
                                       or len(stage_name) != 48
                                       or not stage_name.startswith('.snapshot-stage-')
                                       or any(character not in '0123456789abcdef' for character in stage_name[16:])):
            raise refused()
        allowed = {'binding.json', 'snapshot'} | ({stage_name} if stage_name is not None else set())
        if not names.issubset(allowed):
            raise refused()
        if not isinstance(record['source_path'], str) or not isinstance(record['source_metadata'], dict):
            raise refused()
        if not isinstance(record['pending_roots'], dict) or set(record['pending_roots']) - {'code', 'migration'}:
            raise refused()
        with open_directory(directory) as parent:
            if record['directory_identity'] != identity(os.fstat(parent))[:4]:
                raise refused()
        return record
    except (OSError, ValueError, TypeError, KeyError):
        raise refused() from None


def _identity_record(value):
    return (isinstance(value, list) and len(value) == 8
            and all(type(part) is int for part in value))


def create_binding(directory, record):
    try:
        directory.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        with open_directory(directory.parent) as parent:
            os.mkdir(directory.name, 0o700, dir_fd=parent)
        with open_directory(directory) as descriptor:
            record['directory_identity'] = identity(os.fstat(descriptor))[:4]
        atomic_record(directory, record)
    except OSError:
        # A foreign/orphan binding is evidence, never a disposable staging slot.
        raise refused() from None


@contextmanager
def _member_parent(root, parts):
    """Keep every write relative to the originally verified snapshot descriptor."""
    descriptors = [root]
    try:
        for part in parts:
            before = os.stat(part, dir_fd=descriptors[-1], follow_symlinks=False)
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptors[-1])
            descriptors.append(child)
            if identity(before) != identity(os.fstat(child)):
                raise refused()
        yield descriptors[-1]
        for index, part in enumerate(parts):
            if identity(os.stat(part, dir_fd=descriptors[index], follow_symlinks=False)) != identity(os.fstat(descriptors[index + 1])):
                raise refused()
    finally:
        for descriptor in reversed(descriptors[1:]):
            os.close(descriptor)


def _write_tree(directory, tree, expected_root):
    with open_directory(directory) as descriptor:
        if identity(os.fstat(descriptor))[:4] != expected_root:
            raise refused()
        for member in sorted(tree.members, key=lambda name: (len(Path(name).parts), name)):
            path = Path(member)
            with _member_parent(descriptor, path.parent.parts) as parent:
                if member not in tree.files:
                    if path.name not in os.listdir(parent):
                        os.mkdir(path.name, 0o700, dir_fd=parent)
                    continue
                mode = 0o700 if tree.members[member][3] & 0o111 else 0o600
                before = os.stat(path.name, dir_fd=parent, follow_symlinks=False) if path.name in os.listdir(parent) else None
                flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
                output = os.open(path.name, flags | (os.O_EXCL if before is None else 0), mode, dir_fd=parent)
                info = os.fstat(output)
                if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                        or info.st_mode & 0o077 or (before is not None and identity(before) != identity(info))):
                    os.close(output)
                    raise refused()
                with os.fdopen(output, 'wb') as stream:
                    stream.write(tree.files[member])
                    stream.truncate()
                    stream.flush()
                    os.fsync(stream.fileno())
                os.fsync(parent)
        os.fsync(descriptor)


def _check_source(record, tree):
    current = read_tree(record['source_path'])
    if current.metadata() != record['source_metadata'] or current.files != tree.files:
        raise refused()


def capture(directory, record, tree):
    try:
        return _capture(directory, record, tree)
    except OSError:
        raise refused() from None


def _capture(directory, record, tree):
    snapshot = directory / 'snapshot'
    if record['capture_state'] == 'captured':
        actual = read_tree(snapshot)
        if actual.metadata() != record['snapshot_metadata'] or actual.files != tree.files:
            raise refused()
        return snapshot
    _check_source(record, tree)
    record = _prepare_snapshot(directory, record, tree)
    expected_root = record['snapshot_metadata']['root_identity']
    _write_tree(snapshot, tree, expected_root)
    _check_source(record, tree)
    captured = read_tree(snapshot)
    if captured.root[:4] != expected_root or captured.files != tree.files:
        raise refused()
    atomic_record(directory, dict(record, capture_state='captured', snapshot_metadata=captured.metadata()))
    return snapshot


def _prepare_snapshot(directory, record, tree):
    snapshot = directory / 'snapshot'
    if record['capture_state'] == 'admitted':
        if snapshot.exists() or snapshot.is_symlink():
            raise refused()
        record = dict(record, capture_state='capturing')
        atomic_record(directory, record)
    metadata = record['snapshot_metadata']
    if metadata is None:
        if snapshot.exists() or snapshot.is_symlink():
            # A pre-existing canonical directory has no durable ownership token.
            raise refused()
        metadata = {'stage_name': '.snapshot-stage-' + uuid4().hex}
        record = dict(record, snapshot_metadata=metadata)
        atomic_record(directory, record)
    stage_name = metadata.get('stage_name')
    if stage_name is not None:
        record = _promote_snapshot_stage(directory, record, stage_name, metadata)
    elif snapshot.exists() or snapshot.is_symlink():
        validate_partial(directory, record, tree)
    else:
        raise refused()
    validate_partial(directory, record, tree)
    return record


def _promote_snapshot_stage(directory, record, stage_name, metadata):
    with open_directory(directory) as parent:
        if identity(os.fstat(parent))[:4] != record['directory_identity']:
            raise refused()
        names = os.listdir(parent)
        stage_present = stage_name in names
        snapshot_present = 'snapshot' in names
        if stage_present and snapshot_present:
            raise refused()
        if snapshot_present:
            info = os.stat('snapshot', dir_fd=parent, follow_symlinks=False)
            if (not stat.S_ISDIR(info.st_mode) or metadata.get('root_identity') != identity(info)[:4]):
                raise refused()
        else:
            if not stage_present:
                if metadata.get('root_identity') is not None:
                    raise refused()
                os.mkdir(stage_name, 0o700, dir_fd=parent)
            info = os.stat(stage_name, dir_fd=parent, follow_symlinks=False)
            descriptor = os.open(stage_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            try:
                if (identity(info) != identity(os.fstat(descriptor))
                        or info.st_uid != os.getuid() or info.st_mode & 0o077
                        or (metadata.get('root_identity') is None and os.listdir(descriptor))):
                    raise refused()
                root_identity = identity(info)[:4]
            finally:
                os.close(descriptor)
            if metadata.get('root_identity') not in (None, root_identity):
                raise refused()
            if metadata.get('root_identity') is None:
                metadata = {'stage_name': stage_name, 'root_identity': root_identity}
                record = dict(record, snapshot_metadata=metadata)
                atomic_record(directory, record)
            _rename_new(parent, stage_name, parent, 'snapshot')
            if identity(os.stat('snapshot', dir_fd=parent, follow_symlinks=False))[:4] != root_identity:
                raise refused()
            os.fsync(parent)
        record = dict(record, snapshot_metadata={'root_identity': metadata['root_identity']})
        atomic_record(directory, record)
    return record


def validate_partial(directory, record, tree):
    snapshot = directory / 'snapshot'
    if not snapshot.exists() and not snapshot.is_symlink() and record['snapshot_metadata'] is None:
        return
    partial = read_tree(snapshot)
    if record['snapshot_metadata'] != {'root_identity': partial.root[:4]}:
        raise refused()
    if not set(partial.members).issubset(tree.members):
        raise refused()
    for name, content in partial.files.items():
        if (name not in tree.files or not tree.files[name].startswith(content)
                or bool(partial.members[name][3] & 0o111) != bool(tree.members[name][3] & 0o111)):
            raise refused()


def prepare_pending(directory, record, pending, kind):
    """Rebuild only this binding's proven root; preserve all interrupted bytes."""
    expected = record['pending_roots'].get(kind)
    roots = dict(record['pending_roots'])
    with open_directory(pending.parent) as parent:
        if pending.name in os.listdir(parent):
            actual = os.stat(pending.name, dir_fd=parent, follow_symlinks=False)
            if expected is None or not stat.S_ISDIR(actual.st_mode) or identity(actual)[:4] != expected:
                raise refused()
            retained = pending.name + '.interrupted-' + uuid4().hex
            _rename_new(parent, pending.name, parent, retained)
            if identity(os.stat(retained, dir_fd=parent, follow_symlinks=False))[:4] != expected:
                raise refused()
            roots.pop(kind)
            record = dict(record, pending_roots=roots)
            atomic_record(directory, record)
        elif expected is not None:
            raise refused()
        os.mkdir(pending.name, 0o700, dir_fd=parent)
        descriptor = os.open(pending.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            created = identity(os.fstat(descriptor))[:4]
            if created != identity(os.stat(pending.name, dir_fd=parent, follow_symlinks=False))[:4]:
                raise refused()
            roots[kind] = created
            atomic_record(directory, dict(record, pending_roots=roots))
            os.fsync(parent)
        finally:
            os.close(descriptor)


def _rename_new(source_parent, source, target_parent, target):
    """Linux atomic no-replace rename; unsupported kernels fail closed."""
    rename = getattr(ctypes.CDLL(None, use_errno=True), 'renameat2', None)
    if rename is None:
        raise refused()
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(source_parent, os.fsencode(source), target_parent, os.fsencode(target), 1):
        raise refused()


def publish_pending(directory, record, pending, destination, kind):
    expected = record['pending_roots'].get(kind)
    with (open_directory(directory) as binding, open_directory(pending.parent) as source,
          open_directory(destination.parent) as target):
        if identity(os.fstat(binding))[:4] != record['directory_identity']:
            raise refused()
        info = os.stat(pending.name, dir_fd=source, follow_symlinks=False)
        if expected is None or not stat.S_ISDIR(info.st_mode) or identity(info)[:4] != expected:
            raise refused()
        _rename_new(source, pending.name, target, destination.name)
        if identity(os.stat(destination.name, dir_fd=target, follow_symlinks=False))[:4] != expected:
            raise refused()
        os.fsync(source)
        os.fsync(target)

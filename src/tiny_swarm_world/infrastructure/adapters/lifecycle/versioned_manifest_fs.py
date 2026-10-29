"""Fixed-path descriptor traversal and cooperative durable draft writes."""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import secrets
import stat

from tiny_swarm_world.infrastructure.adapters.lifecycle.versioned_manifest_json import LIMIT as _LIMIT

_FINAL = "manifest-v2-draft.json"
_LOCK = "manifest-v2-draft.lock"
_DIRS = (".tiny-swarm-world", "staging")


class _MissingStaging(Exception):
    """Only a genuinely absent staging directory counts as an absent draft."""


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def _safe(info: os.stat_result, *, directory: bool) -> None:
    expected = 0o700 if directory else 0o600
    if (info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != expected
            or (not directory and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1))
            or (directory and not stat.S_ISDIR(info.st_mode))):
        raise ValueError("Unsafe draft storage.")


@contextmanager
def staging(root_path: Path, *, create: bool) -> Iterator[int]:
    descriptors: list[int] = []
    bindings: list[tuple[int, str, int, tuple[int, ...]]] = []
    try:
        root = os.open(root_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        descriptors.append(root)
        root_info = os.fstat(root)
        _safe(root_info, directory=True)
        parent = root
        for name in _DIRS:
            if create:
                try:
                    os.mkdir(name, 0o700, dir_fd=parent)
                except FileExistsError:
                    pass
            try:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
            except FileNotFoundError as exc:
                if not create:
                    raise _MissingStaging from exc
                raise
            descriptors.append(child)
            info = os.fstat(child)
            _safe(info, directory=True)
            if create:
                # Existing entries may originate from an earlier failed
                # fsync or another cooperating writer; sync every parent.
                os.fsync(parent)
            bindings.append((parent, name, child, _identity(info)))
            parent = child
        yield parent
        if _identity(os.stat(root_path, follow_symlinks=False)) != _identity(os.fstat(root)):
            raise ValueError("Unsafe draft storage.")
        for holder, name, child, before in bindings:
            current = os.fstat(child)
            _safe(current, directory=True)
            # Directory timestamps can change when this operation creates
            # the lock/temp; retain stable identity, ownership and mode.
            if (current.st_dev, current.st_ino, current.st_mode, current.st_uid) != (
                    before[0], before[1], before[2], before[3]):
                raise ValueError("Unsafe draft storage.")
            linked = os.stat(name, dir_fd=holder, follow_symlinks=False)
            if (linked.st_dev, linked.st_ino, linked.st_mode, linked.st_uid) != (
                    current.st_dev, current.st_ino, current.st_mode, current.st_uid):
                raise ValueError("Unsafe draft storage.")
    finally:
        failed = False
        for fd in reversed(descriptors):
            try:
                os.close(fd)
            except OSError:
                failed = True
        if failed:
            raise OSError("Draft cleanup failed.")

def read_raw(parent: int) -> bytes | None:
    try:
        fd = os.open(_FINAL, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
    except FileNotFoundError:
        return None
    try:
        before = os.fstat(fd)
        _safe(before, directory=False)
        data = bytearray()
        while len(data) <= _LIMIT:
            chunk = os.read(fd, min(65536, _LIMIT + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if (len(data) > _LIMIT or len(data) != before.st_size
                or _identity(before) != _identity(os.fstat(fd))
                or _identity(before) != _identity(os.stat(_FINAL, dir_fd=parent, follow_symlinks=False))):
            raise ValueError("Draft changed.")
        return bytes(data)
    finally:
        os.close(fd)

def check_lock(parent: int, lock: int, identity: tuple[int, ...]) -> None:
    info = os.fstat(lock)
    _safe(info, directory=False)
    linked = os.stat(_LOCK, dir_fd=parent, follow_symlinks=False)
    _safe(linked, directory=False)
    if _identity(info) != identity or _identity(linked) != identity:
        raise ValueError("Unsafe draft lock.")

def sync_unchanged(parent: int, expected: bytes) -> None:
    """Re-establish file and directory durability before no-op success."""
    fd = os.open(_FINAL, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
    try:
        before = os.fstat(fd)
        _safe(before, directory=False)
        if (_identity(before) != _identity(os.stat(_FINAL, dir_fd=parent, follow_symlinks=False))
                or read_raw(parent) != expected):
            raise ValueError("Draft changed.")
        os.fsync(fd)
        if (_identity(before) != _identity(os.fstat(fd))
                or _identity(before) != _identity(os.stat(_FINAL, dir_fd=parent, follow_symlinks=False))
                or read_raw(parent) != expected):
            raise ValueError("Draft changed.")
        os.fsync(parent)
    finally:
        os.close(fd)

@dataclass(slots=True)
class ReplaceAttempt:
    started: bool = False


@contextmanager
def locked(parent: int, check: Callable[[int, int, tuple[int, ...]], None]) -> Iterator[tuple[int, tuple[int, ...]]]:
    lock = os.open(_LOCK, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
    try:
        info = os.fstat(lock)
        _safe(info, directory=False)
        identity = _identity(info)
        check(parent, lock, identity)
        fcntl.flock(lock, fcntl.LOCK_EX)
        check(parent, lock, identity)
        yield lock, identity
    finally:
        os.close(lock)


@contextmanager
def _temporary(parent: int) -> Iterator[tuple[str, int]]:
    name = ".manifest-v2-" + secrets.token_hex(16) + ".tmp"
    fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
    try:
        _safe(os.fstat(fd), directory=False)
        yield name, fd
    finally:
        try:
            try:
                linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
                info = os.fstat(fd)
                if (linked.st_dev, linked.st_ino) == (info.st_dev, info.st_ino):
                    os.unlink(name, dir_fd=parent)
            except FileNotFoundError:
                pass
        finally:
            os.close(fd)


def _flush_temporary(parent: int, name: str, fd: int, content: bytes) -> None:
    remaining = memoryview(content)
    while remaining:
        written = os.write(fd, remaining)
        if written <= 0:
            raise OSError("Draft write failed.")
        remaining = remaining[written:]
    os.fsync(fd)
    written_info = os.fstat(fd)
    linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
    _safe(written_info, directory=False)
    _safe(linked, directory=False)
    if _identity(written_info) != _identity(linked) or written_info.st_size != len(content):
        raise ValueError("Draft changed.")


def write_changed(parent: int, content: bytes, current: bytes | None, lock: int,
                  lock_identity: tuple[int, ...], check: Callable[[int, int, tuple[int, ...]], None],
                  attempt: ReplaceAttempt) -> None:
    with _temporary(parent) as (name, fd):
        _flush_temporary(parent, name, fd, content)
        check(parent, lock, lock_identity)
        if read_raw(parent) != current:
            raise ValueError("Draft changed.")
        attempt.started = True
        os.replace(name, _FINAL, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)

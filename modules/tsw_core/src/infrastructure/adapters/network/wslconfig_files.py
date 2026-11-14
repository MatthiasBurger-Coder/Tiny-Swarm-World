"""Descriptor-bound file updates for an admitted Windows profile."""

from __future__ import annotations

import os
import stat
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO


WSLCONFIG_LIMIT = 65536
DirectoryChain = list[tuple[int, str, tuple[int, int]]]
FileIdentity = tuple[int, ...]


@contextmanager
def _wslconfig_parent(path: Path) -> Iterator[tuple[int, DirectoryChain]]:
    """Hold every admitted directory identity without following symbolic links."""
    if not path.is_absolute() or path.name != ".wslconfig" or ".." in path.parts:
        raise ValueError("Invalid configuration target.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    with ExitStack() as opened:
        parent = os.open("/", flags)
        opened.callback(os.close, parent)
        chain: DirectoryChain = []
        for part in path.parts[1:-1]:
            child = os.open(part, flags, dir_fd=parent)
            opened.callback(os.close, child)
            info = os.fstat(child)
            chain.append((parent, part, (info.st_dev, info.st_ino)))
            parent = child
        yield parent, chain


def _wslconfig_identity(info: os.stat_result) -> FileIdentity:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_uid, info.st_gid,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _require_wslconfig_file(info: os.stat_result) -> None:
    if (stat.S_IFMT(info.st_mode), info.st_nlink) != (stat.S_IFREG, 1):
        raise ValueError("Configuration target is not a singly linked regular file.")


def _wslconfig_source(parent: int, opened: ExitStack) -> tuple[BinaryIO | None, bytes, FileIdentity | None]:
    try:
        descriptor = os.open(".wslconfig", os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             dir_fd=parent)
    except FileNotFoundError:
        return None, b"", None
    opened.callback(os.close, descriptor)
    info = os.fstat(descriptor)
    _require_wslconfig_file(info)
    source = opened.enter_context(os.fdopen(descriptor, "r+b", closefd=False))
    content = source.read(WSLCONFIG_LIMIT + 1)
    if len(content) > WSLCONFIG_LIMIT:
        raise ValueError("Configuration target exceeds its bounded read limit.")
    return source, content, _wslconfig_identity(info)


def _check_wslconfig_state(parent: int, chain: DirectoryChain, expected: FileIdentity | None) -> None:
    for directory, name, identity in chain:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (info.st_dev, info.st_ino) != identity:
            raise ValueError("Configuration directory identity changed.")
    try:
        current = _wslconfig_identity(os.stat(".wslconfig", dir_fd=parent, follow_symlinks=False))
    except FileNotFoundError:
        current = None
    if current != expected:
        raise ValueError("Configuration file identity changed.")


def _write_wslconfig_backup(parent: int, name: str, content: bytes, changed: list[str]) -> FileIdentity:
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=parent)
    changed.append(name)
    with os.fdopen(descriptor, "wb") as backup:
        backup.write(content)
        backup.flush()
        os.fsync(backup.fileno())
        return _wslconfig_identity(os.fstat(backup.fileno()))


def _verify_entry(parent: int, name: str, identity: FileIdentity | None, expected: bytes) -> None:
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                         dir_fd=parent)
    with os.fdopen(descriptor, "rb") as observed:
        info = os.fstat(descriptor)
        _require_wslconfig_file(info)
        if _wslconfig_identity(info) != identity:
            raise ValueError("Configuration readback identity changed.")
        content = observed.read(len(expected) + 1)
        if content != expected or _wslconfig_identity(os.fstat(descriptor)) != identity:
            raise ValueError("Configuration readback did not match the expected bytes.")
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if _wslconfig_identity(current) != identity:
            raise ValueError("Configuration entry changed during readback.")


def _check_wslconfig_backup(parent: int, name: str | None, identity: FileIdentity | None,
                            original: bytes) -> None:
    if name is not None:
        _verify_entry(parent, name, identity, original)


def _readback_wslconfig(parent: int, source: BinaryIO, original_identity: FileIdentity | None,
                        expected: bytes) -> FileIdentity:
    written = os.fstat(source.fileno())
    identity = _wslconfig_identity(written)
    if original_identity is None or identity[:6] != original_identity[:6]:
        raise ValueError("Configuration ownership or metadata changed.")
    _verify_entry(parent, ".wslconfig", identity, expected)
    return identity


def update_wslconfig(path: Path, transform: Callable[[str], str]) -> tuple[bool, bool, str | None]:
    """Apply a text transformation and report success, file effects, and backup name."""
    changed: list[str] = []
    backup_name = None
    backup_identity = None
    try:
        with _wslconfig_parent(path) as (parent, chain), ExitStack() as opened:
            source, original, identity = _wslconfig_source(parent, opened)
            updated = transform(original.decode("utf-8")).encode("utf-8")
            _check_wslconfig_state(parent, chain, identity)
            if source is not None:
                backup_name = ".wslconfig.bak-" + datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                backup_identity = _write_wslconfig_backup(parent, backup_name, original, changed)
                os.fsync(parent)
            _check_wslconfig_state(parent, chain, identity)
            _check_wslconfig_backup(parent, backup_name, backup_identity, original)
            if source is None:
                descriptor = os.open(".wslconfig", os.O_WRONLY | os.O_CREAT | os.O_EXCL
                                     | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
                changed.append(".wslconfig")
                opened.callback(os.close, descriptor)
                source = opened.enter_context(os.fdopen(descriptor, "wb", closefd=False))
                identity = _wslconfig_identity(os.fstat(descriptor))
            changed.append(".wslconfig")
            source.seek(0)
            source.write(updated)
            source.truncate()
            source.flush()
            os.fsync(source.fileno())
            os.fsync(parent)
            verified = _readback_wslconfig(parent, source, identity, updated)
            _check_wslconfig_state(parent, chain, verified)
            _check_wslconfig_backup(parent, backup_name, backup_identity, original)
        return True, True, backup_name
    except (OSError, ValueError):
        return False, bool(changed), backup_name

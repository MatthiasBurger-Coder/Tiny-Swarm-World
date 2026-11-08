"""Bounded no-follow reads for unverified operator-local preview inputs."""
from __future__ import annotations

import os
from pathlib import Path
import stat
from types import TracebackType

from tiny_swarm_world.domain.deployment.service_stack_contract import service_stack_contracts_for_profile

STACK_IDS = frozenset({
    "portainer", "traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger", "infisical", "service-access",
})
MANIFEST = ".tiny-swarm-world/installation/manifest.json"
COMPOSE_FILES = frozenset(f"infra/config/compose/{name}/docker-compose.yml" for name in STACK_IDS)
ALLOWED = COMPOSE_FILES | {MANIFEST}
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_FILES = 16


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


class PreviewFileReader:
    """Pin a local root and every fixed path; data and observations remain private."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._fds: list[int] = []
        self._bindings: list[tuple[int, str, int, tuple[int, ...]]] = []
        self._root_identity: tuple[int, ...] | None = None
        self._seen: set[str] = set()
        self._total = 0

    def __enter__(self) -> PreviewFileReader:
        stacks = service_stack_contracts_for_profile("service-access")
        names = tuple(item.stack_name for item in stacks)
        if len(names) != len(STACK_IDS) or set(names) != STACK_IDS:
            raise ValueError("Unsupported preview asset set.")
        fd = os.open(self._root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        self._fds.append(fd)
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValueError("Invalid preview root.")
            self._root_identity = _identity(metadata)
            return self
        except BaseException:
            self._close()
            raise

    def _close(self) -> None:
        failed = False
        while self._fds:
            descriptor = self._fds.pop()
            try:
                os.close(descriptor)
            except OSError:
                # The descriptor's state is unspecified after a failed close;
                # do not retry it, but attempt each other close exactly once.
                failed = True
        if failed:
            raise OSError("Preview descriptor cleanup failed.") from None

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None,
                 traceback: TracebackType | None) -> None:
        try:
            if exc_type is None:
                self._recheck()
        finally:
            self._close()

    def _recheck(self) -> None:
        if not self._fds or self._root_identity is None:
            raise ValueError("Preview input unavailable.")
        if (_identity(os.fstat(self._fds[0])) != self._root_identity
                or _identity(os.stat(self._root, follow_symlinks=False)) != self._root_identity):
            raise ValueError("Preview input changed.")
        for parent, name, child, original in self._bindings:
            if (_identity(os.fstat(child)) != original
                    or _identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != original):
                raise ValueError("Preview input changed.")

    def read(self, relative: str) -> bytes:
        if (relative not in ALLOWED or relative in self._seen or len(self._seen) >= MAX_FILES
                or not self._fds):
            raise ValueError("Unsupported preview input.")
        parts = relative.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("Unsupported preview input.")
        self._seen.add(relative)
        parent = self._fds[0]
        for name in parts[:-1]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
            self._fds.append(child)
            info = os.fstat(child)
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError("Invalid preview directory.")
            self._bindings.append((parent, name, child, _identity(info)))
            parent = child
        name = parts[-1]
        child = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
        self._fds.append(child)
        info = os.fstat(child)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Invalid preview file.")
        original = _identity(info)
        self._bindings.append((parent, name, child, original))
        content = bytearray()
        while len(content) <= MAX_FILE_BYTES:
            block = os.read(child, min(65536, MAX_FILE_BYTES + 1 - len(content)))
            if not block:
                break
            content.extend(block)
        self._total += len(content)
        if (len(content) > MAX_FILE_BYTES or self._total > MAX_TOTAL_BYTES
                or len(content) != info.st_size or _identity(os.fstat(child)) != original):
            raise ValueError("Preview input invalid or changed.")
        self._recheck()
        return bytes(content)

    def read_text(self, relative: str) -> str:
        return self.read(relative).decode("utf-8", "strict")

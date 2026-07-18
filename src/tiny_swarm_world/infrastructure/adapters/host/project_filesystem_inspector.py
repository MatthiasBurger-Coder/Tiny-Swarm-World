from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tiny_swarm_world.application.ports.host.port_project_filesystem_inspector import (
    PortProjectFilesystemInspector,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
)

_OCTAL_ESCAPE = re.compile(r"\\([0-7]{3})")
_LINUX_FILESYSTEMS = frozenset(
    {
        "btrfs",
        "ext2",
        "ext3",
        "ext4",
        "f2fs",
        "overlay",
        "tmpfs",
        "xfs",
    }
)
_WINDOWS_9P_FILESYSTEMS = frozenset({"9p", "v9fs"})


@dataclass(frozen=True)
class _MountEntry:
    mount_point: Path
    filesystem_type: str
    source: str
    super_options: str


class ProjectFilesystemInspector(PortProjectFilesystemInspector):
    def __init__(
        self,
        *,
        mountinfo_reader: Callable[[], str] | None = None,
    ) -> None:
        self._mountinfo_reader = mountinfo_reader or _read_mountinfo

    def inspect(
        self,
        repository_root: str,
        host_environment: HostEnvironmentKind,
    ) -> ProjectFilesystemInspection:
        resolved = _resolve_path(repository_root)
        if host_environment is HostEnvironmentKind.NATIVE_LINUX:
            return ProjectFilesystemInspection(
                kind=ProjectFilesystemKind.NATIVE_LINUX,
                resolved_project_path=resolved.as_posix(),
                filesystem_type="native",
                classification_source="native_host",
            )
        if host_environment is not HostEnvironmentKind.WSL2:
            return _unknown(resolved, "host_unsupported")
        try:
            mountinfo = self._mountinfo_reader()
        except (OSError, RuntimeError, ValueError):
            return _unknown(resolved, "mountinfo_unreadable")
        entries = tuple(
            entry
            for line in mountinfo.splitlines()
            if (entry := _parse_mountinfo_line(line)) is not None
            and _path_is_within(resolved, entry.mount_point)
        )
        if not entries:
            return _unknown(resolved, "mountpoint_not_found")
        longest = max(len(entry.mount_point.parts) for entry in entries)
        selected = tuple(
            entry for entry in entries if len(entry.mount_point.parts) == longest
        )
        kinds = {_entry_kind(entry) for entry in selected}
        if len(kinds) != 1:
            return _unknown(resolved, "mountinfo_contradictory")
        kind = kinds.pop()
        if kind is ProjectFilesystemKind.UNKNOWN:
            return _unknown(resolved, "mountinfo_unrecognized")
        entry = selected[0]
        return ProjectFilesystemInspection(
            kind=kind,
            resolved_project_path=resolved.as_posix(),
            filesystem_type=entry.filesystem_type,
            classification_source="proc_self_mountinfo",
        )


def _read_mountinfo() -> str:
    return Path("/proc/self/mountinfo").read_text(encoding="utf-8")


def _resolve_path(value: str) -> Path:
    try:
        return Path(value).expanduser().resolve(strict=False)
    except (OSError, RuntimeError):
        return Path(value).expanduser().absolute()


def _parse_mountinfo_line(line: str) -> _MountEntry | None:
    fields = line.split()
    try:
        separator = fields.index("-")
        mount_point = Path(_decode_mountinfo(fields[4]))
        filesystem_type = fields[separator + 1].casefold()
        source = _decode_mountinfo(fields[separator + 2])
        super_options = ",".join(fields[separator + 3 :])
    except (IndexError, ValueError):
        return None
    if not mount_point.is_absolute():
        return None
    return _MountEntry(
        mount_point=mount_point,
        filesystem_type=filesystem_type,
        source=source,
        super_options=super_options,
    )


def _decode_mountinfo(value: str) -> str:
    return _OCTAL_ESCAPE.sub(lambda match: chr(int(match.group(1), 8)), value)


def _path_is_within(path: Path, mount_point: Path) -> bool:
    return path == mount_point or mount_point in path.parents


def _entry_kind(entry: _MountEntry) -> ProjectFilesystemKind:
    if entry.filesystem_type == "drvfs":
        return ProjectFilesystemKind.WINDOWS_MOUNTED
    characteristics = f"{entry.source},{entry.super_options}".casefold()
    if (
        entry.filesystem_type in _WINDOWS_9P_FILESYSTEMS
        and "drvfs" in characteristics
    ):
        return ProjectFilesystemKind.WINDOWS_MOUNTED
    if entry.filesystem_type in _LINUX_FILESYSTEMS:
        return ProjectFilesystemKind.WSL_LINUX
    return ProjectFilesystemKind.UNKNOWN


def _unknown(resolved: Path, source: str) -> ProjectFilesystemInspection:
    return ProjectFilesystemInspection(
        kind=ProjectFilesystemKind.UNKNOWN,
        resolved_project_path=resolved.as_posix(),
        classification_source=source,
    )

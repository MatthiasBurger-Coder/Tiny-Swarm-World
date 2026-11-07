"""WSL/native path qualification for live credentials and evidence."""

from __future__ import annotations

import os
import platform
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


WINDOWS_MOUNTED = "windows_mounted"
WSL_NATIVE = "wsl_linux"
NATIVE_LINUX = "native_linux"
UNKNOWN = "unknown"
_LINUX_FILESYSTEMS = frozenset(
    {"btrfs", "ext2", "ext3", "ext4", "f2fs", "overlay", "tmpfs", "xfs"}
)
_WINDOWS_9P_FILESYSTEMS = frozenset({"9p", "v9fs"})


@dataclass(frozen=True)
class RuntimePathAssessment:
    purpose: str
    path: Path = field(repr=False)
    filesystem_classification: str
    exists: bool
    is_directory: bool
    is_regular_file: bool
    owner_uid: int | None
    group_gid: int | None
    mode: int | None
    parent_exists: bool
    parent_owner_uid: int | None
    parent_group_gid: int | None
    parent_mode: int | None
    expected_uid: int
    expected_gid: int
    require_existing_file: bool = False

    @property
    def allowed(self) -> bool:
        if self.filesystem_classification not in {NATIVE_LINUX, WSL_NATIVE}:
            return False
        if not self.parent_exists:
            return False
        if self.parent_owner_uid != self.expected_uid:
            return False
        if self.parent_group_gid != self.expected_gid:
            return False
        if not self._parent_mode_allowed:
            return False
        if self.purpose == "evidence_directory":
            return (
                not self.exists
                or (
                    self.is_directory
                    and self.owner_uid == self.expected_uid
                    and self.group_gid == self.expected_gid
                    and self.mode == 0o700
                )
            )
        if self.require_existing_file and not self.exists:
            return False
        return (
            not self.exists
            or (
                self.is_regular_file
                and self.owner_uid == self.expected_uid
                and self.group_gid == self.expected_gid
                and self.mode == 0o600
            )
        )

    def reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.filesystem_classification not in {NATIVE_LINUX, WSL_NATIVE}:
            reasons.append("filesystem_not_linux_native")
        if not self.parent_exists:
            reasons.append("parent_missing")
        elif self.parent_owner_uid != self.expected_uid:
            reasons.append("parent_owner_mismatch")
        elif self.parent_group_gid != self.expected_gid:
            reasons.append("parent_group_mismatch")
        elif not self._parent_mode_allowed:
            reasons.append(
                "parent_mode_not_0700"
                if self.purpose != "evidence_directory"
                else "parent_mode_not_private"
            )
        if self.purpose == "evidence_directory":
            if self.exists and not self.is_directory:
                reasons.append("evidence_path_not_directory")
            if self.exists and self.owner_uid != self.expected_uid:
                reasons.append("evidence_owner_mismatch")
            if self.exists and self.group_gid != self.expected_gid:
                reasons.append("evidence_group_mismatch")
            if self.exists and self.mode != 0o700:
                reasons.append("evidence_mode_not_0700")
            return tuple(reasons)
        if self.require_existing_file and not self.exists:
            reasons.append("secret_file_missing")
        if self.exists and not self.is_regular_file:
            reasons.append("secret_path_not_regular_file")
        if self.exists and self.owner_uid != self.expected_uid:
            reasons.append("secret_owner_mismatch")
        if self.exists and self.group_gid != self.expected_gid:
            reasons.append("secret_group_mismatch")
        if self.exists and self.mode != 0o600:
            reasons.append("secret_mode_not_0600")
        return tuple(reasons)

    def to_safe_dict(self) -> dict[str, str]:
        return {
            "purpose": self.purpose,
            "filesystem_classification": self.filesystem_classification,
            "exists": _bool_text(self.exists),
            "directory": _bool_text(self.is_directory),
            "regular_file": _bool_text(self.is_regular_file),
            "owner_verified": _bool_text(self.owner_uid == self.expected_uid),
            "group_verified": _bool_text(self.group_gid == self.expected_gid),
            "mode_verified": _bool_text(
                self.mode == (0o700 if self.purpose == "evidence_directory" else 0o600)
            ),
            "parent_exists": _bool_text(self.parent_exists),
            "parent_owner_verified": _bool_text(self.parent_owner_uid == self.expected_uid),
            "parent_group_verified": _bool_text(self.parent_group_gid == self.expected_gid),
            "parent_mode_verified": _bool_text(self._parent_mode_allowed),
            "accepted": _bool_text(self.allowed),
            "reasons": ",".join(self.reasons()),
        }

    @property
    def _parent_mode_allowed(self) -> bool:
        if self.parent_mode is None:
            return False
        if self.purpose == "evidence_directory":
            return not bool(self.parent_mode & 0o022)
        return self.parent_mode == 0o700


def host_classification() -> str:
    release = platform.release().casefold()
    if Path("/run/WSL").exists() or "microsoft" in release or "wsl" in release:
        return "wsl2"
    return "native_linux"


def classify_path(
    path: Path,
    *,
    host: str | None = None,
    mountinfo_reader: Callable[[], str] | None = None,
) -> str:
    host = host or host_classification()
    resolved = _resolve(path)
    if host == "native_linux":
        return NATIVE_LINUX
    if host != "wsl2":
        return UNKNOWN
    try:
        mountinfo = (mountinfo_reader or _read_mountinfo)()
    except (OSError, RuntimeError, ValueError):
        return UNKNOWN
    entries = tuple(
        entry
        for line in mountinfo.splitlines()
        if (entry := _parse_mountinfo(line)) is not None
        and _within(resolved, entry[0])
    )
    if not entries:
        return WINDOWS_MOUNTED if resolved.as_posix().startswith("/mnt/") else UNKNOWN
    longest = max(len(entry[0].parts) for entry in entries)
    selected = tuple(entry for entry in entries if len(entry[0].parts) == longest)
    kinds = {_mount_kind(entry) for entry in selected}
    return kinds.pop() if len(kinds) == 1 else UNKNOWN


def assess_secret_file(
    path: Path,
    *,
    host: str | None = None,
    expected_uid: int | None = None,
    expected_gid: int | None = None,
    mountinfo_reader: Callable[[], str] | None = None,
) -> RuntimePathAssessment:
    resolved = _resolve(path)
    return _assess(
        "secret_file",
        resolved,
        host=host,
        expected_uid=os.geteuid() if expected_uid is None else expected_uid,
        expected_gid=os.getegid() if expected_gid is None else expected_gid,
        require_existing_file=True,
        mountinfo_reader=mountinfo_reader,
    )


def assess_evidence_directory(
    path: Path,
    *,
    host: str | None = None,
    expected_uid: int | None = None,
    expected_gid: int | None = None,
    mountinfo_reader: Callable[[], str] | None = None,
) -> RuntimePathAssessment:
    resolved = _resolve(path)
    return _assess(
        "evidence_directory",
        resolved,
        host=host,
        expected_uid=os.geteuid() if expected_uid is None else expected_uid,
        expected_gid=os.getegid() if expected_gid is None else expected_gid,
        require_existing_file=False,
        mountinfo_reader=mountinfo_reader,
    )


def ensure_secure_directory(path: Path) -> RuntimePathAssessment:
    before = assess_evidence_directory(path)
    if before.filesystem_classification not in {NATIVE_LINUX, WSL_NATIVE}:
        raise RuntimeError("secure evidence directory is not on a Linux-native filesystem")
    existed = before.exists
    if existed and before.mode != 0o700:
        raise RuntimeError("existing evidence directory must already be owner-only")
    path.mkdir(parents=True, exist_ok=True)
    if not existed:
        path.chmod(0o700)
    assessment = assess_evidence_directory(path)
    if not assessment.allowed:
        raise RuntimeError("secure evidence directory could not be verified")
    return assessment


def _assess(
    purpose: str,
    path: Path,
    *,
    host: str | None,
    expected_uid: int,
    expected_gid: int,
    require_existing_file: bool,
    mountinfo_reader: Callable[[], str] | None,
) -> RuntimePathAssessment:
    parent = path.parent
    if purpose == "evidence_directory":
        while parent != parent.parent and _safe_stat(parent) is None:
            parent = parent.parent
    path_stat = _safe_stat(path)
    parent_stat = _safe_stat(parent)
    classification_path = path if path_stat is not None else parent
    classification = classify_path(
        classification_path,
        host=host,
        mountinfo_reader=mountinfo_reader,
    )
    return RuntimePathAssessment(
        purpose=purpose,
        path=path,
        filesystem_classification=classification,
        exists=path_stat is not None,
        is_directory=path_stat is not None and stat.S_ISDIR(path_stat.st_mode),
        is_regular_file=path_stat is not None and stat.S_ISREG(path_stat.st_mode),
        owner_uid=path_stat.st_uid if path_stat is not None else None,
        group_gid=path_stat.st_gid if path_stat is not None else None,
        mode=stat.S_IMODE(path_stat.st_mode) if path_stat is not None else None,
        parent_exists=parent_stat is not None and stat.S_ISDIR(parent_stat.st_mode),
        parent_owner_uid=parent_stat.st_uid if parent_stat is not None else None,
        parent_group_gid=parent_stat.st_gid if parent_stat is not None else None,
        parent_mode=stat.S_IMODE(parent_stat.st_mode) if parent_stat is not None else None,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
        require_existing_file=require_existing_file,
    )


def _read_mountinfo() -> str:
    return Path("/proc/self/mountinfo").read_text(encoding="utf-8")


def _parse_mountinfo(line: str) -> tuple[Path, str, str, str] | None:
    fields = line.split()
    try:
        separator = fields.index("-")
        mount_point = Path(_decode(fields[4]))
        filesystem_type = fields[separator + 1].casefold()
        source = _decode(fields[separator + 2])
        options = ",".join(fields[separator + 3 :])
    except (IndexError, ValueError):
        return None
    if not mount_point.is_absolute():
        return None
    return mount_point, filesystem_type, source, options


def _mount_kind(entry: tuple[Path, str, str, str]) -> str:
    _, filesystem_type, source, options = entry
    if filesystem_type == "drvfs":
        return WINDOWS_MOUNTED
    if filesystem_type in _WINDOWS_9P_FILESYSTEMS and "drvfs" in f"{source},{options}".casefold():
        return WINDOWS_MOUNTED
    if filesystem_type in _LINUX_FILESYSTEMS:
        return WSL_NATIVE
    return UNKNOWN


def _resolve(path: Path) -> Path:
    try:
        return path.expanduser().resolve(strict=False)
    except (OSError, RuntimeError):
        return path.expanduser().absolute()


def _safe_stat(path: Path):
    try:
        return path.stat()
    except OSError:
        return None


def _within(path: Path, mount_point: Path) -> bool:
    return path == mount_point or mount_point in path.parents


def _decode(value: str) -> str:
    result = value
    for octal in ("040", "011", "012"):
        result = result.replace(f"\\{octal}", chr(int(octal, 8)))
    return result


def _bool_text(value: bool) -> str:
    return "true" if value else "false"

"""Standalone, allowlisted protected-file transaction helper; no project imports."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
from typing import Any
import uuid

ALLOWED_TARGETS = {
    "/etc/sysctl.d/90-tiny-swarm-world.conf": 0o644,
    "/etc/modules-load.d/tiny-swarm-world.conf": 0o644,
    "/usr/local/bin/tsw-apply-incus-forwarding.sh": 0o755,
    "/etc/systemd/system/tsw-incus-forwarding.service": 0o644,
    "/etc/hosts": None,
}
BEGIN = b"# BEGIN TINY SWARM WORLD"
END = b"# END TINY SWARM WORLD"
MAX_BYTES = 1024 * 1024


def _identity(info: os.stat_result) -> list[int]:
    return [info.st_dev, info.st_ino, info.st_uid, info.st_gid,
            stat.S_IMODE(info.st_mode)]


def _safe_directory(fd: int, uid: int) -> list[int]:
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != uid or info.st_mode & 0o022:
        raise ValueError("Unsafe protected-file ancestor")
    return _identity(info)


def _parent(path: Path, anchor: Path, uid: int) -> tuple[int, list[list[int]]]:
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("An absolute normalized target is required")
    parts = path.relative_to(anchor).parts
    if not parts:
        raise ValueError("Target must be a file")
    fd = os.open(anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    ancestors: list[list[int]] = []
    try:
        ancestors.append(_safe_directory(fd, uid))
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            ancestors.append(_safe_directory(fd, uid))
        return fd, ancestors
    except BaseException:
        os.close(fd)
        raise


def _read(fd: int, uid: int, gid: int) -> tuple[bytes, list[int]]:
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != uid
            or info.st_gid != gid or info.st_nlink != 1 or info.st_mode & 0o022
            or info.st_mode & 0o7000):
        raise ValueError("Unsafe protected-file metadata")
    if os.listxattr(fd):
        raise ValueError("Unsupported protected-file extended attributes or ACLs")
    content = os.read(fd, MAX_BYTES + 1)
    if len(content) != info.st_size or len(content) > MAX_BYTES:
        raise ValueError("Protected file exceeds size limit")
    after = os.fstat(fd)
    if info != after:
        raise RuntimeError("Protected file changed during observation")
    metadata = _identity(info) + [info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns]
    return content, metadata


def snapshot(path: Path, *, anchor: Path = Path("/"), uid: int = 0, gid: int = 0) -> dict[str, Any]:
    """Read via retained no-follow directory handles, without creating artifacts."""
    parent, ancestors = _parent(path, anchor, uid)
    try:
        metadata: list[int]
        try:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        except FileNotFoundError:
            content, metadata = b"", []
        else:
            try:
                content, metadata = _read(fd, uid, gid)
                linked = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if [linked.st_dev, linked.st_ino] != metadata[:2]:
                    raise RuntimeError("Protected path changed during observation")
            finally:
                os.close(fd)
        material = json.dumps([ancestors, metadata, hashlib.sha256(content).hexdigest()],
                              separators=(",", ":")).encode()
        return {"exists": bool(metadata), "content": content,
                "fingerprint": hashlib.sha256(material).hexdigest(),
                "mode": metadata[4] if metadata else 0,
                "uid": metadata[2] if metadata else 0,
                "gid": metadata[3] if metadata else 0}
    finally:
        os.close(parent)


def _host_parts(content: bytes) -> tuple[bytes, bytes]:
    lines = content.splitlines(keepends=True)
    markers = [(index, line.rstrip(b"\r\n")) for index, line in enumerate(lines)
               if BEGIN in line or END in line]
    if not markers:
        return content, b""
    if (len(markers) != 2 or markers[0][1] != BEGIN or markers[1][1] != END
            or markers[0][0] >= markers[1][0]):
        raise ValueError("Ambiguous Tiny Swarm World hosts markers")
    return b"".join(lines[:markers[0][0]]), b"".join(lines[markers[1][0] + 1:])


def hosts_payload(content: bytes, names: tuple[str, ...]) -> bytes:
    if (not names or len(set(names)) != len(names)
            or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", name)
                   or len(name) > 253 for name in names)):
        raise ValueError("Invalid canonical hosts names")
    prefix, suffix = _host_parts(content)
    targets = {name.encode().lower() for name in names}
    for line in (prefix + suffix).splitlines():
        fields = line.split(b"#", 1)[0].split()
        if targets.intersection(field.lower() for field in fields[1:]):
            raise ValueError("Canonical name conflicts outside the owned hosts block")
    newline = b"\r\n" if b"\r\n" in content else b"\n"
    separator = newline if prefix and not prefix.endswith((b"\n", b"\r")) else b""
    block = newline.join([BEGIN, *(b"127.0.0.1 " + name.encode() for name in names), END])
    return prefix + separator + block + newline + suffix


def _validate_hosts(before: bytes, payload: bytes) -> None:
    lines = payload.splitlines()
    try:
        start, end = lines.index(BEGIN), lines.index(END)
        entries = lines[start + 1:end]
        names = tuple(entry.removeprefix(b"127.0.0.1 ").decode("ascii") for entry in entries)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid owned hosts replacement") from exc
    if hosts_payload(before, names) != payload:
        raise ValueError("Replacement changes unrelated hosts bytes")


def _validate_request(path: Path, before: dict[str, Any], payload: bytes,
                      mode: int, shared: bool, targets: dict[str, int | None]) -> None:
    if str(path) not in targets or shared != (targets[str(path)] is None):
        raise ValueError("Target is outside the declared protected-file scope")
    expected_mode = before["mode"] if shared else targets[str(path)]
    if mode != expected_mode or len(payload) > MAX_BYTES:
        raise ValueError("Invalid protected-file payload or mode")
    if shared:
        if not before["exists"]:
            raise ValueError("Existing protected hosts file required")
        _validate_hosts(before["content"], payload)
    elif before["exists"] and (before["content"] != payload or before["mode"] != mode):
        raise ValueError("Incompatible persistence file; preserve and remediate its owner")


def _write_private(parent: int, name: str, content: bytes, mode: int,
                   uid: int = 0, gid: int = 0) -> None:
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=parent)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(content)
            stream.flush()
        os.fchown(fd, uid, gid)
        os.fchmod(fd, mode)
        os.fsync(fd)
    finally:
        os.close(fd)


def _check_parent(parent: int, path: Path, anchor: Path, uid: int) -> None:
    fresh, _ = _parent(path, anchor, uid)
    try:
        if _identity(os.fstat(parent)) != _identity(os.fstat(fresh)):
            raise RuntimeError("Protected parent changed before publication")
    finally:
        os.close(fresh)


def _backup(parent: int, before: dict[str, Any], uid: int) -> None:
    name = ".tsw-backup-hosts-" + uuid.uuid4().hex
    restoration = {key: before[key] for key in ("mode", "uid", "gid", "fingerprint")}
    restoration["sha256"] = hashlib.sha256(before["content"]).hexdigest()
    _write_private(parent, name, before["content"], 0o600, uid, before["gid"])
    _write_private(parent, name + ".metadata", json.dumps(restoration).encode(),
                   0o600, uid, before["gid"])
    os.fsync(parent)


def publish(path: Path, before: dict[str, Any], payload: bytes, mode: int,
            shared: bool = False, *, anchor: Path = Path("/"), uid: int = 0, gid: int = 0,
            targets: dict[str, int | None] | None = None) -> None:
    """Revalidate inside the privileged action, then atomically publish once."""
    _validate_request(path, before, payload, mode, shared,
                      ALLOWED_TARGETS if targets is None else targets)
    if snapshot(path, anchor=anchor, uid=uid, gid=gid) != before:
        raise RuntimeError("Protected-file plan is stale")
    if before["exists"] and before["content"] == payload:
        return
    parent, _ = _parent(path, anchor, uid)
    temporary = ".tsw-write-" + uuid.uuid4().hex
    try:
        if shared:
            _backup(parent, before, uid)
        _write_private(parent, temporary, payload, mode, uid,
                       before["gid"] if before["exists"] else gid)
        if snapshot(path, anchor=anchor, uid=uid, gid=gid) != before:
            raise RuntimeError("Protected-file plan changed before publication")
        _check_parent(parent, path, anchor, uid)
        # Safe root-owned ancestors exclude unprivileged races; concurrent root
        # editors must still serialize their changes outside this transaction.
        if before["exists"]:
            os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
        else:
            os.link(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent,
                    follow_symlinks=False)
            os.unlink(temporary, dir_fd=parent)
        os.fsync(parent)
        final = snapshot(path, anchor=anchor, uid=uid, gid=gid)
        if final["content"] != payload or final["mode"] != mode:
            raise RuntimeError("Protected-file publication postcheck failed")
    finally:
        try:
            os.unlink(temporary, dir_fd=parent)
        except FileNotFoundError:
            pass
        os.close(parent)


def _deadline(signum: int, frame: Any) -> None:
    raise TimeoutError("Protected-file action deadline expired")


def _production_target(value: object) -> Path:
    """Select a fixed policy path; never construct filesystem paths from input."""
    for target in ALLOWED_TARGETS:
        if isinstance(value, str) and value == target:
            return Path(target)
    raise ValueError("Target is outside the declared protected-file scope")


def main() -> None:
    """Only fixed production policy is exposed at the privilege boundary."""
    signal.signal(signal.SIGALRM, _deadline)
    signal.alarm(12)
    request = json.loads(sys.stdin.buffer.read(MAX_BYTES * 4 + 1))
    path = _production_target(request["path"])
    before = request["before"]
    before["content"] = base64.b64decode(before["content"], validate=True)
    publish(path, before,
            base64.b64decode(request["payload"], validate=True),
            request["mode"], request["shared"])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        print("Protected-file transaction failed; reobserve before recovery", file=sys.stderr)
        sys.exit(1)

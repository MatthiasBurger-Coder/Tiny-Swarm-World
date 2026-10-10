"""Private checkpoints are recovery evidence, never saved consent or readiness."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
from typing import Any, Iterator
import uuid

LIMIT = 262144


def context(release: str, selection: str = "service-access") -> dict[str, str]:
    """Hash identities and configuration; never publish arbitrary host file content."""
    root = Path(__file__).resolve().parents[4]
    assets = (root / "pyproject.toml", root / "requirements.lock", root / "requirements.build.lock",
              root / "infra/config/node-providers/provider_config.yaml", root / "infra/config/ports.yaml")
    digest = hashlib.sha256()
    for path in (*assets, *sorted((root / "src/tiny_swarm_world").rglob("*.py"))):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    identity = Path("/etc/machine-id").read_bytes().strip()
    if not identity:
        raise OSError("Bootstrap host identity unavailable.")
    distribution = os.environ.get("WSL_DISTRO_NAME", "native")
    return {"contract": "bootstrap-v1", "release": release, "selection": selection, "source_sha256": digest.hexdigest(),
            "host_sha256": hashlib.sha256(identity).hexdigest(),
            "distribution_sha256": hashlib.sha256(distribution.encode()).hexdigest(),
            "architecture": platform.machine(), "python": platform.python_version()}


def _private(metadata: os.stat_result, *, directory: bool) -> None:
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if (not kind(metadata.st_mode) or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != (0o700 if directory else 0o600)
            or (not directory and metadata.st_nlink != 1)):
        raise OSError("Bootstrap state is not private and operator-owned.")


@contextmanager
def directory(root: Path, *, create: bool) -> Iterator[int | None]:
    """Traverse retained no-follow descriptors; do not repair unsafe existing paths."""
    if not root.is_absolute() or ".." in root.parts:
        raise OSError("Bootstrap state root must be an absolute safe path.")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in root.parts[1:]:
            try:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    yield None
                    return
                os.mkdir(part, 0o700, dir_fd=fd)
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            info = os.fstat(fd)
            # Trusted system ancestors (including sticky /tmp for local tests) are
            # permitted; all project storage components are strictly private.
            if info.st_uid not in {0, os.geteuid()} or (
                info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)
            ):
                raise OSError("Bootstrap state ancestor is unsafe.")
        _private(os.fstat(fd), directory=True)
        yield fd
    finally:
        os.close(fd)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate checkpoint field.")
        result[key] = value
    return result


def _validate_record(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {"stage", "status", "planned", "confirmed", "uncertain", "timestamp", "exit_code", "observation_sha256", "restart", "cause"}:
        raise ValueError("Invalid checkpoint fields.")
    labels = [value["stage"], value["status"], value["timestamp"], value["cause"]]
    datetime.strptime(value["timestamp"], "%Y%m%dT%H%M%S%fZ")
    if value["status"].lower() not in {"started", "pending", "succeeded", "ready", "blocked", "failed", "interrupted", "partial", "restart_required"}:
        raise ValueError("Invalid checkpoint status.")
    if value["restart"] not in {"none", "login", "distro", "Windows", "WSL-wide"}:
        raise ValueError("Invalid checkpoint restart.")
    if value["observation_sha256"] != "unknown" and not re.fullmatch(r"[a-f0-9]{64}", value["observation_sha256"]):
        raise ValueError("Invalid observation fingerprint.")
    for key in ("planned", "confirmed", "uncertain"):
        if not isinstance(value[key], list) or len(value[key]) > 256:
            raise ValueError("Invalid checkpoint effects.")
        if any(not isinstance(item, str) for item in value[key]):
            raise ValueError("Invalid action type.")
        if len(set(value[key])) != len(value[key]):
            raise ValueError("Duplicate checkpoint action.")
        labels.extend(value[key])
    if any(not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9_./:-]{1,200}", item)
           or re.search(r"password|private.?key|secret|token", item, re.I) for item in labels):
        raise ValueError("Invalid checkpoint labels.")
    if value["exit_code"] is not None and (type(value["exit_code"]) is not int or not 0 <= value["exit_code"] <= 255):
        raise ValueError("Invalid checkpoint exit.")
    if set(value["confirmed"]) & set(value["uncertain"]):
        raise ValueError("Conflicting checkpoint effects.")
    if not set(value["confirmed"] + value["uncertain"]) <= set(value["planned"]):
        raise ValueError("Invalid checkpoint effects.")


class BootstrapState:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.operation = uuid.uuid4().hex
        self._lock: int | None = None

    def close(self) -> None:
        if self._lock is not None:
            os.close(self._lock)
            self._lock = None

    def __del__(self) -> None:
        self.close()

    def _read(self, fd: int, capability: str, identity: dict[str, str]) -> dict[str, Any] | None:
        try:
            source = os.open(capability + ".state.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        except FileNotFoundError:
            return None
        try:
            metadata = os.fstat(source)
            _private(metadata, directory=False)
            if metadata.st_size > LIMIT:
                raise OSError("Bootstrap checkpoint exceeds size limit.")
            with os.fdopen(os.dup(source), "r", encoding="utf-8") as stream:
                value = json.loads(stream.read(LIMIT + 1), object_pairs_hook=_pairs)
            if (not isinstance(value, dict) or set(value) != {"schema", "identity", "operation", "record"}
                    or type(value["schema"]) is not int or value["schema"] != 1 or value["identity"] != identity
                    or not isinstance(value["operation"], str) or not re.fullmatch(r"[a-f0-9]{32}", value["operation"])
                    or not isinstance(value["record"], dict)):
                raise ValueError("Invalid or stale checkpoint.")
            _validate_record(value["record"])
            return value
        except (ValueError, UnicodeError, TypeError, AttributeError):
            raise OSError("Bootstrap checkpoint is stale, corrupt or foreign; inspect before fresh apply.") from None
        finally:
            os.close(source)

    def validate(self, capability: str, identity: dict[str, str]) -> None:
        with directory(self.root, create=False) as fd:
            if fd is not None:
                self._read(fd, capability, identity)

    def publish(self, capability: str, identity: dict[str, str], record: dict[str, Any]) -> None:
        _validate_record(record)
        with directory(self.root, create=True) as fd:
            assert fd is not None
            if self._lock is None:
                lock = os.open("checkpoint.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=fd)
                try:
                    _private(os.fstat(lock), directory=False)
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    os.close(lock)
                    raise
                self._lock = lock
            try:
                self._read(fd, capability, identity)
                self._publish(fd, capability + ".state.json", {
                    "schema": 1, "identity": identity, "operation": self.operation, "record": record,
                })
            except (OSError, ValueError):
                self.close()
                raise

    @staticmethod
    def _publish(fd: int, target: str, payload: dict[str, Any]) -> None:
        temporary = ".checkpoint-" + uuid.uuid4().hex
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target, src_dir_fd=fd, dst_dir_fd=fd)
            os.fsync(fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=fd)
            except FileNotFoundError:
                pass

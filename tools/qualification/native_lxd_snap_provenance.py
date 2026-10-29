"""Bounded, read-only proof of the installed Snap LXD wrapper/child relation."""
from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime
import hashlib
import os
from pathlib import PurePosixPath
import re
import stat
import time
from typing import Any, Callable, Iterator, Protocol

import yaml

UNIT = "snap.lxd.daemon.service"
UNIT_FILE = "/etc/systemd/system/" + UNIT
DROP_IN = "/run/systemd/system/" + UNIT + ".d/lxd-shutdown.conf"
BASE_PROPERTIES = ("LoadState", "ActiveState", "SubState", "UnitFileState", "MainPID")
CONTEXT_PROPERTIES = ("ExecStart", "ControlGroup", "FragmentPath", "DropInPaths", "ExecCondition",
                      "ExecStartPre", "ExecStartPost", "RootDirectory", "RootImage", "BindPaths",
                      "BindReadOnlyPaths", "Environment", "EnvironmentFiles")
PROPERTIES = BASE_PROPERTIES + CONTEXT_PROPERTIES
OPTIONAL_EMPTY_PROPERTIES = ("ExecCondition", "ExecStartPre", "ExecStartPost", "EnvironmentFiles")
UNIT_ARGV = ["/usr/bin/systemctl", "show", UNIT, "--property=" + ",".join(PROPERTIES), "--no-pager"]
PROC_LIMIT = 64 * 1024
ENV_LIMIT = 256 * 1024
METADATA_LIMIT = 1024 * 1024
TOTAL_LIMIT = 16 * 1024 * 1024
MAX_CHILDREN = 64
MAX_SECONDS = 60
CANONICAL_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"
_DECIMAL = re.compile(r"[1-9][0-9]{0,18}\Z", re.ASCII)
_EXEC_START = re.compile(
    r"\{ path=/usr/bin/snap ; argv\[\]=/usr/bin/snap run lxd\.daemon ; ignore_errors=no ; "
    r"start_time=\[([^\[\]\r\n]{1,64})\] ; stop_time=\[([^\[\]\r\n]{1,64})\] ; "
    r"pid=([0-9]{1,19}) ; code=(\(null\)|exited|killed|dumped) ; "
    r"status=(-?[0-9]{1,10}(?:/(?:[0-9]{1,10}|SUCCESS|FAILURE|CHDIR|EXEC|SIGNAL|EXIT_CODE))?) \}\Z",
    re.ASCII,
)
_TIME = re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) ([A-Z]{2,8}|[+-][0-9]{4})\Z", re.ASCII)
_PACKAGE_PATH = re.compile(
    r"(?P<view>/proc/[1-9][0-9]{0,18}/root)?/snap/lxd/(?P<revision>[1-9][0-9]{0,18})/"
    r"(?P<directory>commands|meta|sbin|bin)/(?P<file>daemon\.start|snap\.yaml|lxd)\Z", re.ASCII,
)


class ProvenanceError(Exception):
    """Only fixed symbolic codes may cross the proof boundary."""

    def __init__(self, code: str):
        allowed = {"SNAP_WRAPPER_UNIT_INVALID", "SNAP_WRAPPER_CONTEXT_BLOCKED", "SNAP_WRAPPER_PROC_INVALID",
                   "SNAP_WRAPPER_FILE_UNVERIFIED", "SNAP_WRAPPER_METADATA_INVALID", "SNAP_WRAPPER_CHILD_ABSENT",
                   "SNAP_WRAPPER_CHILD_AMBIGUOUS", "SNAP_WRAPPER_DRIFT", "SNAP_WRAPPER_LIMIT_EXCEEDED"}
        super().__init__(code if code in allowed else "SNAP_WRAPPER_FILE_UNVERIFIED")


class _StageNegative(ProvenanceError):
    """An explicit comparison failure; sensitive snapshots remain in memory."""

    def __init__(self, stage: str, code: str, snapshots: tuple[Any, ...]):
        super().__init__(code)
        self.stage = stage
        self.snapshots = snapshots


class RunnerPort(Protocol):
    def run(self, argv: list[str], *, command_id: str, safe_args: list[str]) -> tuple[int, bytes, bytes]: ...


@dataclass(frozen=True)
class Observation:
    device: int
    inode: int
    mode: int
    uid: int
    readonly: bool
    data: bytes = b""

    @property
    def identity(self) -> tuple[int, int]:
        return self.device, self.inode


class ReadOnlyFS(Protocol):
    def observe(self, path: str, *, limit: int | None = None, follow: bool = False) -> Observation: ...

    def final_link(self, path: str) -> str | None: ...


class LocalReadOnlyFS:
    """Observe opened descriptors, never execute or write package/proc files."""

    @staticmethod
    @contextmanager
    def contained_parent(root: str, components: tuple[str, ...]) -> Iterator[tuple[int, int]]:
        """Pin a numeric package root and walk child directories without symlinks."""
        if (len(components) < 4 or components[:2] != ("snap", "lxd")
                or not _DECIMAL.fullmatch(components[2])
                or any(not part or part in {".", ".."} or "/" in part for part in components)):
            raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY
        descriptors: list[int] = []
        try:
            # Only the fixed proc process-root prefix may deliberately be followed.
            current = os.open(root, flags)
            descriptors.append(current)
            package_device: int | None = None
            for index, part in enumerate(components):
                current = os.open(part, flags | os.O_NOFOLLOW, dir_fd=current)
                descriptors.append(current)
                metadata = os.fstat(current)
                if not stat.S_ISDIR(metadata.st_mode):
                    raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
                if index == 2:
                    if not os.fstatvfs(current).f_flag & os.ST_RDONLY:
                        raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
                    package_device = metadata.st_dev
                elif package_device is not None and metadata.st_dev != package_device:
                    raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
            assert package_device is not None
            yield current, package_device
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    @staticmethod
    def package_parts(path: str) -> tuple[str, tuple[str, ...], str] | None:
        match = _PACKAGE_PATH.fullmatch(path)
        if match is None:
            return None
        return (match["view"] or "/", ("snap", "lxd", match["revision"], match["directory"]), match["file"])

    def open_file(self, path: str, flags: int) -> tuple[int, int | None]:
        parts = self.package_parts(path)
        if parts is None:
            return os.open(path, flags), None
        root, components, name = parts
        with self.contained_parent(root, components) as (parent, device):
            return os.open(name, flags | os.O_NOFOLLOW, dir_fd=parent), device

    def observe(self, path: str, *, limit: int | None = None, follow: bool = False) -> Observation:
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK | (0 if follow else os.O_NOFOLLOW)
        fd, package_device = self.open_file(path, flags)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
            readonly = bool(os.fstatvfs(fd).f_flag & os.ST_RDONLY)
            if package_device is not None and (before.st_dev != package_device or not readonly):
                raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
            chunks = bytearray()
            if limit is not None:
                while len(chunks) <= limit:
                    block = os.read(fd, min(65536, limit + 1 - len(chunks)))
                    if not block:
                        break
                    chunks.extend(block)
                if len(chunks) > limit:
                    raise ProvenanceError("SNAP_WRAPPER_LIMIT_EXCEEDED")
            after = os.fstat(fd)
            fields = ("st_dev", "st_ino", "st_mode", "st_uid", "st_size", "st_mtime_ns", "st_ctime_ns")
            if any(getattr(before, key) != getattr(after, key) for key in fields):
                raise ProvenanceError("SNAP_WRAPPER_DRIFT")
            return Observation(before.st_dev, before.st_ino, before.st_mode, before.st_uid, readonly, bytes(chunks))
        finally:
            os.close(fd)

    def final_link(self, path: str) -> str | None:
        parts = self.package_parts(path)
        if parts is None:
            metadata = os.lstat(path)
            return os.readlink(path) if stat.S_ISLNK(metadata.st_mode) else None
        root, components, name = parts
        with self.contained_parent(root, components) as (parent, device):
            metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if metadata.st_dev != device:
                raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
            return os.readlink(name, dir_fd=parent) if stat.S_ISLNK(metadata.st_mode) else None


class _UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ProvenanceError("SNAP_WRAPPER_METADATA_INVALID")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _text(raw: bytes, code: str) -> str:
    try:
        return raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise ProvenanceError(code) from exc


def _positive(value: str) -> int:
    if not _DECIMAL.fullmatch(value):
        raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
    return int(value)


def _normal_path(value: str) -> bool:
    path = PurePosixPath(value)
    return value.startswith("/") and not value.startswith("//") and str(path) == value and ".." not in path.parts and "\x00" not in value


def _valid_time(value: str) -> bool:
    if value == "n/a":
        return True
    match = _TIME.fullmatch(value)
    if match is None:
        return False
    try:
        stamp = datetime.strptime(match[2], "%Y-%m-%d %H:%M:%S")
        if stamp.strftime("%a") != match[1]:
            return False
        zone = match[3]
        return zone[0] not in "+-" or (int(zone[1:3]) <= 23 and int(zone[3:]) <= 59)
    except ValueError:
        return False


def _unit_fields(raw: bytes, expected: dict[str, Any]) -> dict[str, str]:
    if len(raw) > PROC_LIMIT:
        raise ProvenanceError("SNAP_WRAPPER_LIMIT_EXCEEDED")
    values: dict[str, str] = {}
    for line in _text(raw, "SNAP_WRAPPER_UNIT_INVALID").splitlines():
        key, sep, value = line.partition("=")
        if not sep or key not in PROPERTIES or key in values:
            raise ProvenanceError("SNAP_WRAPPER_UNIT_INVALID")
        values[key] = value
    # systemd's per-entry array printer omits these properties when empty.
    for key in OPTIONAL_EMPTY_PROPERTIES:
        values.setdefault(key, "")
    if set(values) != set(PROPERTIES):
        raise ProvenanceError("SNAP_WRAPPER_UNIT_INVALID")
    supplied = (expected.get("load_state"), expected.get("active_state"), expected.get("sub_state"),
                expected.get("unit_file_state"), str(expected.get("main_pid")))
    if tuple(values[key] for key in BASE_PROPERTIES) != supplied or supplied[:3] != ("loaded", "active", "running"):
        raise ProvenanceError("SNAP_WRAPPER_UNIT_INVALID")
    _positive(values["MainPID"])
    return values


def _context_reason(values: dict[str, str]) -> str | None:
    match = _EXEC_START.fullmatch(values["ExecStart"])
    if match is None or not all(_valid_time(value) for value in match.group(1, 2)):
        return "EXECSTART_FORMAT_OR_TIME"
    if not _normal_path(values["ControlGroup"]) or values["ControlGroup"] == "/":
        return "CONTROL_GROUP"
    if values["FragmentPath"] != UNIT_FILE or any(values[key] for key in (
            "ExecCondition", "ExecStartPre", "ExecStartPost", "RootDirectory", "RootImage", "BindPaths", "BindReadOnlyPaths")):
        return "FRAGMENT_OR_HOOK"
    if values["DropInPaths"] not in {"", DROP_IN} or values["Environment"] not in {"", "SNAPD_DEBUG=0"}:
        return "DROPIN_OR_ENV_SETTING"
    if values["EnvironmentFiles"] not in {"", "/etc/environment (ignore_errors=yes)"}:
        return "ENVIRONMENT_FILE_SPEC"
    return None


def _unit(raw: bytes, expected: dict[str, Any]) -> dict[str, str]:
    values = _unit_fields(raw, expected)
    if _context_reason(values) is not None:
        raise ProvenanceError("SNAP_WRAPPER_CONTEXT_BLOCKED")
    return {**values, "ExecStart": "snap-run-lxd-daemon"}


@dataclass(frozen=True)
class Process:
    pid: int
    parent: int
    started: int
    executable: Observation


class _Proof:
    def __init__(self, runner: RunnerPort, fs: ReadOnlyFS, clock: Callable[[], float]):
        self.runner, self.fs, self.clock = runner, fs, clock
        self.deadline = clock() + MAX_SECONDS
        self.total = 0

    def check_time(self) -> None:
        if self.clock() >= self.deadline:
            raise ProvenanceError("SNAP_WRAPPER_LIMIT_EXCEEDED")

    def observe(self, path: str, *, limit: int | None = None, follow: bool = False) -> Observation:
        self.check_time()
        result = self.fs.observe(path, limit=limit, follow=follow)
        self.check_time()
        self.total += len(result.data)
        if (limit is not None and len(result.data) > limit) or self.total > TOTAL_LIMIT:
            raise ProvenanceError("SNAP_WRAPPER_LIMIT_EXCEEDED")
        return result

    def link(self, path: str) -> str | None:
        self.check_time()
        result = self.fs.final_link(path)
        self.check_time()
        return result

    def unit(self, expected: dict[str, Any]) -> dict[str, str]:
        self.check_time()
        _, raw, _ = self.runner.run(list(UNIT_ARGV), command_id="systemctl_show_unit", safe_args=[UNIT])
        self.check_time()
        self.total += len(raw)
        if self.total > TOTAL_LIMIT:
            raise ProvenanceError("SNAP_WRAPPER_LIMIT_EXCEEDED")
        return _unit(raw, expected)

    @staticmethod
    def trusted(value: Observation, *, executable: bool = False, readonly: bool = False) -> Observation:
        if (not stat.S_ISREG(value.mode) or value.uid != 0 or value.mode & 0o022
                or (executable and not value.mode & 0o111) or (readonly and not value.readonly)):
            raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
        return value

    def context(self, unit: dict[str, str]) -> tuple[Observation, ...]:
        result = [self.trusted(self.observe(UNIT_FILE))]
        if unit["DropInPaths"]:
            drop = self.trusted(self.observe(DROP_IN, limit=PROC_LIMIT))
            lines = _text(drop.data, "SNAP_WRAPPER_CONTEXT_BLOCKED")
            if "\r" in lines or "\x00" in lines:
                raise ProvenanceError("SNAP_WRAPPER_CONTEXT_BLOCKED")
            significant = [line for line in lines.split("\n") if line.strip() and not line.lstrip().startswith("#")]
            if significant != ["[Unit]", "After=snap.microceph.daemon.service snap.microovn.daemon.service"]:
                raise ProvenanceError("SNAP_WRAPPER_CONTEXT_BLOCKED")
            result.append(drop)
        if unit["EnvironmentFiles"]:
            environment: Observation | None
            try:
                environment = self.trusted(self.observe("/etc/environment", limit=PROC_LIMIT))
            except FileNotFoundError:
                environment = None
            if environment is not None:
                text = _text(environment.data, "SNAP_WRAPPER_CONTEXT_BLOCKED")
                assignments = [line for line in text.split("\n") if line.strip() and not line.lstrip().startswith("#")]
                if ("\x00" in text or "\r" in text or len(assignments) > 1
                        or any(line not in {"PATH=" + CANONICAL_PATH, 'PATH="' + CANONICAL_PATH + '"'} for line in assignments)):
                    raise ProvenanceError("SNAP_WRAPPER_CONTEXT_BLOCKED")
                result.append(environment)
        return tuple(result)

    def diagnostic_unit(self, expected: dict[str, Any]) -> dict[str, str]:
        self.check_time()
        _, raw, _ = self.runner.run(list(UNIT_ARGV), command_id="systemctl_show_unit", safe_args=[UNIT])
        self.check_time()
        self.total += len(raw)
        if self.total > TOTAL_LIMIT:
            raise ProvenanceError("SNAP_WRAPPER_LIMIT_EXCEEDED")
        return _unit_fields(raw, expected)

    def diagnostic_files(self, unit: dict[str, str]) -> tuple[str | None, tuple[tuple[str, Observation | None], ...]]:
        observed: list[tuple[str, Observation | None]] = []
        observed.append((UNIT_FILE, self.trusted(self.observe(UNIT_FILE))))
        if unit["DropInPaths"]:
            drop = self.trusted(self.observe(DROP_IN, limit=PROC_LIMIT))
            observed.append((DROP_IN, drop))
            text = drop.data.decode("utf-8", "strict")
            significant = [line for line in text.split("\n") if line.strip() and not line.lstrip().startswith("#")]
            if "\r" in text or "\x00" in text or significant != ["[Unit]", "After=snap.microceph.daemon.service snap.microovn.daemon.service"]:
                return "DROPIN_CONTENT", tuple(observed)
        if unit["EnvironmentFiles"]:
            try:
                environment = self.trusted(self.observe("/etc/environment", limit=PROC_LIMIT))
            except FileNotFoundError:
                environment = None
            observed.append(("/etc/environment", environment))
            if environment is not None:
                text = environment.data.decode("utf-8", "strict")
                assignments = [line for line in text.split("\n") if line.strip() and not line.lstrip().startswith("#")]
                if ("\x00" in text or "\r" in text or len(assignments) > 1
                        or any(line not in {"PATH=" + CANONICAL_PATH, 'PATH="' + CANONICAL_PATH + '"'} for line in assignments)):
                    return "ENVIRONMENT_FILE_CONTENT", tuple(observed)
        return None, tuple(observed)

    def diagnostic_reobserve(self, observed: tuple[tuple[str, Observation | None], ...]) -> bool:
        for path, original in observed:
            try:
                current = self.trusted(self.observe(path, limit=None if path == UNIT_FILE else PROC_LIMIT))
            except FileNotFoundError:
                current = None
            if current != original:
                return False
        return True

    def process(self, pid: int, group: str) -> Process:
        root = f"/proc/{pid}"
        stat_observation = self.observe(root + "/stat", limit=PROC_LIMIT)
        text = _text(stat_observation.data, "SNAP_WRAPPER_PROC_INVALID")
        close = text.rfind(")")
        prefix, fields = text[:close + 1], text[close + 1:].split()
        if close < 0 or not prefix.startswith(f"{pid} (") or len(fields) < 20 or not re.fullmatch(r"[0-9]+", fields[1], re.ASCII):
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        parent, started = int(fields[1]), _positive(fields[19])
        status_observation = self.observe(root + "/status", limit=PROC_LIMIT)
        status = _text(status_observation.data, "SNAP_WRAPPER_PROC_INVALID")
        uid = [line for line in status.splitlines() if line.startswith("Uid:")]
        if len(uid) != 1 or not re.fullmatch(r"Uid:[ \t]+0[ \t]+0[ \t]+0[ \t]+0[ \t]*", uid[0], re.ASCII):
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        cgroup_observation = self.observe(root + "/cgroup", limit=PROC_LIMIT)
        cgroup = cgroup_observation.data
        if cgroup not in {f"0::{group}".encode(), f"0::{group}\n".encode()}:
            try:
                observed_group = cgroup.decode("utf-8", "strict").removesuffix("\n")
            except UnicodeError as exc:
                raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID") from exc
            if observed_group.startswith("0::") and _normal_path(observed_group[3:]):
                raise _StageNegative("PROCESS_BINDING", "SNAP_WRAPPER_PROC_INVALID",
                                     (stat_observation, status_observation, cgroup_observation))
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        executable = self.trusted(self.observe(root + "/exe", follow=True), executable=True)
        return Process(pid, parent, started, executable)

    def main_environment(self, pid: int) -> tuple[str, tuple[bytes, ...], tuple[tuple[bytes, bytes], ...]]:
        raw = self.observe(f"/proc/{pid}/environ", limit=ENV_LIMIT).data
        cmd = self.observe(f"/proc/{pid}/cmdline", limit=PROC_LIMIT).data
        if not raw.endswith(b"\x00") or not cmd.endswith(b"\x00"):
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        selected: dict[bytes, bytes] = {}
        for entry in raw[:-1].split(b"\x00"):
            key, sep, value = entry.partition(b"=")
            if not sep:
                raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
            if key in {b"SNAP", b"SNAP_NAME", b"SNAP_REVISION"}:
                if key in selected:
                    raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
                selected[key] = value
        if set(selected) != {b"SNAP", b"SNAP_NAME", b"SNAP_REVISION"} or selected[b"SNAP_NAME"] != b"lxd":
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        revision = _text(selected[b"SNAP_REVISION"], "SNAP_WRAPPER_PROC_INVALID")
        _positive(revision)
        base = f"/snap/lxd/{revision}"
        argv = tuple(cmd[:-1].split(b"\x00"))
        if selected[b"SNAP"] != base.encode() or len(argv) != 2 or argv[1] != (base + "/commands/daemon.start").encode():
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        shell = _text(argv[0], "SNAP_WRAPPER_PROC_INVALID")
        if not _normal_path(shell):
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        return base, argv, tuple(sorted(selected.items()))

    def shell(self, pid: int, argv: tuple[bytes, ...], process: Process) -> tuple[Observation, Observation]:
        shell = _text(argv[0], "SNAP_WRAPPER_PROC_INVALID")
        values = tuple(self.trusted(self.observe(path, follow=True), executable=True) for path in (
            f"/proc/{pid}/root{shell}", f"/proc/{pid}/root/bin/sh"))
        if any(value.identity != process.executable.identity for value in values):
            raise _StageNegative("SHELL_BINDING", "SNAP_WRAPPER_FILE_UNVERIFIED", values)
        return values[0], values[1]

    def pair(self, pid: int, path: str, *, limit: int | None = None, executable: bool = False) -> tuple[Observation, Observation]:
        values = tuple(self.trusted(self.observe(view, limit=limit), executable=executable, readonly=True)
                       for view in (path, f"/proc/{pid}/root{path}"))
        if values[0].identity != values[1].identity or values[0].data != values[1].data:
            raise _StageNegative("SCRIPT_PAIR_OR_DIGEST", "SNAP_WRAPPER_FILE_UNVERIFIED", values)
        return values[0], values[1]

    def package(self, pid: int, base: str) -> tuple[tuple[Any, ...], tuple[int, int]]:
        script = self.pair(pid, base + "/commands/daemon.start")
        metadata = self.pair(pid, base + "/meta/snap.yaml", limit=METADATA_LIMIT)
        try:
            document = yaml.load(_text(metadata[0].data, "SNAP_WRAPPER_METADATA_INVALID"), Loader=_UniqueLoader)
            if (not isinstance(document, dict) or document.get("name") != "lxd"
                    or not isinstance(document.get("apps"), dict) or not isinstance(document["apps"].get("daemon"), dict)
                    or document["apps"]["daemon"].get("command") != "commands/daemon.start"
                    or document["apps"]["daemon"].get("daemon") != "simple"):
                raise ProvenanceError("SNAP_WRAPPER_METADATA_INVALID")
        except (yaml.YAMLError, ValueError, TypeError, RecursionError) as exc:
            raise ProvenanceError("SNAP_WRAPPER_METADATA_INVALID") from exc
        binaries: list[tuple[str, tuple[Observation, Observation]]] = []
        for suffix, other in (("sbin/lxd", "bin/lxd"), ("bin/lxd", "sbin/lxd")):
            path = base + "/" + suffix
            try:
                host_link = self.link(path)
            except FileNotFoundError:
                with suppress(FileNotFoundError):
                    self.link(f"/proc/{pid}/root{path}")
                    raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
                continue
            process_link = self.link(f"/proc/{pid}/root{path}")
            if host_link != process_link or host_link not in {None, "../" + other}:
                raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
            target = base + "/" + other if host_link is not None else path
            # pair uses O_NOFOLLOW: a second symlink or a loop is never followed.
            binaries.append((suffix, self.pair(pid, target, executable=True)))
        identities = {pair[0].identity for _, pair in binaries}
        if len(identities) != 1:
            raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
        return (script, metadata, tuple(binaries)), next(iter(identities))

    def children(self, pid: int) -> tuple[int, ...]:
        raw = self.observe(f"/proc/{pid}/task/{pid}/children", limit=PROC_LIMIT).data
        parts = _text(raw, "SNAP_WRAPPER_PROC_INVALID").split()
        if len(parts) > MAX_CHILDREN:
            raise ProvenanceError("SNAP_WRAPPER_LIMIT_EXCEEDED")
        children = tuple(sorted(_positive(part) for part in parts))
        if len(set(children)) != len(children):
            raise ProvenanceError("SNAP_WRAPPER_PROC_INVALID")
        return children

    def run(self, row: dict[str, Any]) -> tuple[str, str]:
        if row.get("unit") != UNIT or type(row.get("main_pid")) is not int or row["main_pid"] <= 0:
            raise ProvenanceError("SNAP_WRAPPER_UNIT_INVALID")
        unit = self.unit(row)
        context = self.context(unit)
        pid, group = row["main_pid"], unit["ControlGroup"]
        main = self.process(pid, group)
        environment = self.main_environment(pid)
        base, argv, _ = environment
        shell = self.shell(pid, argv, main)
        package, binary = self.package(pid, base)
        children = self.children(pid)
        candidates = [self.process(child, group) for child in children]
        matches = [child for child in candidates if child.parent == pid and child.executable.identity == binary]
        if not matches:
            raise ProvenanceError("SNAP_WRAPPER_CHILD_ABSENT")
        if len(matches) != 1:
            raise ProvenanceError("SNAP_WRAPPER_CHILD_AMBIGUOUS")
        selected = matches[0]
        if (self.unit(row) != unit or self.context(unit) != context or self.process(pid, group) != main
                or self.main_environment(pid) != environment or self.shell(pid, argv, main) != shell
                or self.package(pid, base) != (package, binary) or self.children(pid) != children
                or self.process(selected.pid, group) != selected):
            raise ProvenanceError("SNAP_WRAPPER_DRIFT")
        return "lxd_snap", "snap:lxd"


def prove_snap_wrapper(runner: RunnerPort, row: dict[str, Any], *, fs: ReadOnlyFS | None = None,
                       clock: Callable[[], float] = time.monotonic) -> tuple[str, str]:
    """Return the existing identity pair only after the complete stable proof."""
    try:
        return _Proof(runner, LocalReadOnlyFS() if fs is None else fs, clock).run(row)
    except ProvenanceError:
        raise
    except (OSError, ValueError, TypeError, IndexError, OverflowError, RecursionError) as exc:
        raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED") from exc


def diagnose_context(runner: RunnerPort, expected: dict[str, Any], *, fs: ReadOnlyFS | None = None,
                     clock: Callable[[], float] = time.monotonic) -> str:
    """Classify one stable rejection without admitting an identity or exposing inputs."""
    try:
        proof = _Proof(runner, fs or LocalReadOnlyFS(), clock)
        before = proof.diagnostic_unit(expected)
        reason = _context_reason(before)
        observed: tuple[tuple[str, Observation | None], ...] = ()
        if reason is None:
            reason, observed = proof.diagnostic_files(before)
        after = proof.diagnostic_unit(expected)
        before_compare, after_compare = dict(before), dict(after)
        # Valid ExecStart records carry systemd runtime counters that F4 intentionally normalizes.
        if (_context_reason(before) != "EXECSTART_FORMAT_OR_TIME"
                and _context_reason(after) != "EXECSTART_FORMAT_OR_TIME"):
            before_compare["ExecStart"] = after_compare["ExecStart"] = "snap-run-lxd-daemon"
        if before_compare != after_compare or not proof.diagnostic_reobserve(observed):
            return "UNKNOWN"
        return reason or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _dropin_form(raw: bytes) -> str:
    """Classify only unambiguous text without returning any observed values."""
    text = raw.decode("utf-8", "strict")
    if any(ord(char) < 32 and char not in "\n\t" or ord(char) > 126 for char in text) or "\\" in text:
        return "UNKNOWN"
    lines = [line for line in text.split("\n") if line.strip() and not line.lstrip().startswith("#")]
    expected = ["[Unit]", "After=snap.microceph.daemon.service snap.microovn.daemon.service"]
    if lines == expected:
        return "UNKNOWN"
    if any('"' in line or "'" in line for line in lines):
        return "UNKNOWN"
    if any(re.fullmatch(r"\[[A-Za-z][A-Za-z0-9]*\]", line, re.ASCII) is None
           and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*=[ -~]*", line, re.ASCII) is None
           for line in lines):
        return "UNKNOWN"
    sections = [index for index, line in enumerate(lines) if line.startswith("[") and line.endswith("]")]
    if not lines or lines[0] != "[Unit]" or sections != [0]:
        return "SECTION_SHAPE"
    if len(lines) != 2 or not lines[1].startswith("After="):
        return "UNKNOWN_DIRECTIVE"
    return "DEPENDENCY_VARIANT"


def diagnose_dropin(runner: RunnerPort, expected: dict[str, Any], *, fs: ReadOnlyFS | None = None,
                    clock: Callable[[], float] = time.monotonic) -> str:
    """Classify a stable rejected fixed drop-in without admitting an identity."""
    try:
        proof = _Proof(runner, fs or LocalReadOnlyFS(), clock)
        before = proof.diagnostic_unit(expected)
        if _context_reason(before) is not None or before["DropInPaths"] != DROP_IN:
            return "UNKNOWN"
        unit_file = proof.trusted(proof.observe(UNIT_FILE))
        drop = proof.trusted(proof.observe(DROP_IN, limit=PROC_LIMIT))
        reason = _dropin_form(drop.data)
        after = proof.diagnostic_unit(expected)
        if _context_reason(after) is not None:
            return "UNKNOWN"
        before_compare, after_compare = dict(before), dict(after)
        before_compare["ExecStart"] = after_compare["ExecStart"] = "snap-run-lxd-daemon"
        observed = ((UNIT_FILE, unit_file), (DROP_IN, drop))
        if before_compare != after_compare or not proof.diagnostic_reobserve(observed):
            return "UNKNOWN"
        return reason
    except Exception:
        return "UNKNOWN"


# A deliberately narrow subset of Canonical LXD 3a06799's generator form.
_GENERATOR_DIGEST = "7ecbe39a07dc02666af544327dbaf5cfbe9967868bfb9d7c627061f14916b562"
_GENERATOR_REVISION = "40958"
_GENERATOR_TOKENS = (
    "snap.microceph.daemon.service", "snap.microceph.mds.service", "snap.microceph.mgr.service",
    "snap.microceph.mon.service", "snap.microceph.nfs.service", "snap.microceph.osd.service",
    "snap.microceph.rgw.service", "snap.microceph.rbd-mirror.service", "snap.microceph.cephfs-mirror.service",
    "snap.microovn.daemon.service", "snap.microovn.ovn-ovsdb-server-nb.service",
    "snap.microovn.ovn-ovsdb-server-sb.service", "snap.microovn.ovn-northd.service",
    "snap.microovn.chassis.service", "snap.microovn.switch.service", "snap.microovn.bird.service",
)
_GENERATOR_PREFIX = ("[Unit]\nAfter=" + " ".join(_GENERATOR_TOKENS) + " ").encode("ascii")


def _generator_form(raw: bytes) -> bool:
    """Match a bounded subset of the pinned public generator; never expose input."""
    if len(raw) > PROC_LIMIT or not raw.startswith(_GENERATOR_PREFIX) or not raw.endswith(b"\n"):
        return False
    suffix = raw[len(_GENERATOR_PREFIX):-1]
    if not suffix:
        return True
    if suffix.startswith(b" ") or not suffix.endswith(b" "):
        return False
    parts = suffix.split(b" ")
    tokens = [part for part in parts if part]
    allowed = {token.encode("ascii") for token in _GENERATOR_TOKENS}
    return len(tokens) <= 256 and all(part in allowed for part in tokens)


def _same_diagnostic_unit(before: dict[str, str], after: dict[str, str]) -> bool:
    """Compare only F7's validated, semantically stable unit fields."""
    left, right = dict(before), dict(after)
    if (_context_reason(before) != "EXECSTART_FORMAT_OR_TIME"
            and _context_reason(after) != "EXECSTART_FORMAT_OR_TIME"):
        left["ExecStart"] = right["ExecStart"] = "snap-run-lxd-daemon"
    return left == right


def _stage_reobserve(proof: _Proof, observed: list[tuple[str, Observation | None]]) -> bool:
    """Compare only successful trusted reads; unavailable data is never drift."""
    current: list[Observation] = []
    for path, original in observed:
        if original is None:
            raise ProvenanceError("SNAP_WRAPPER_FILE_UNVERIFIED")
        current.append(proof.trusted(proof.observe(path, limit=None if path == UNIT_FILE else PROC_LIMIT)))
    return all(item == original for item, (_, original) in zip(current, observed))


def _negative_again(call: Callable[[], Any], original: _StageNegative) -> bool:
    """Confirm the same explicit failure with the same private observations."""
    try:
        call()
    except _StageNegative as current:
        return current.stage == original.stage and current.snapshots == original.snapshots
    return False


def _probe_generator_form(runner: RunnerPort, expected: dict[str, Any], *, fs: ReadOnlyFS | None,
                          clock: Callable[[], float], stages: bool) -> str:
    """One shared F7/F8 probe; failed/ambiguous observations never establish identity."""
    try:
        proof = _Proof(runner, fs or LocalReadOnlyFS(), clock)
        before = proof.diagnostic_unit(expected)
        visited: list[tuple[str, Observation | None]] = []
        process: Process | None = None
        environment: tuple[str, tuple[bytes, ...], tuple[tuple[bytes, bytes], ...]] | None = None
        shell: tuple[Observation, Observation] | None = None
        script: tuple[Observation, Observation] | None = None
        pid, group = _positive(before["MainPID"]), before["ControlGroup"]

        def stable_prior() -> bool:
            after = proof.diagnostic_unit(expected)
            if not _same_diagnostic_unit(before, after):
                return False
            if not _stage_reobserve(proof, visited):
                return False
            if process is not None and proof.process(pid, group) != process:
                return False
            if environment is not None and proof.main_environment(pid) != environment:
                return False
            if shell is not None and environment is not None and process is not None:
                if proof.shell(pid, environment[1], process) != shell:
                    return False
            if script is not None and environment is not None:
                if proof.pair(pid, environment[0] + "/commands/daemon.start", limit=METADATA_LIMIT) != script:
                    return False
            return True

        def rejected(reason: str) -> str:
            if not stages:
                return "UNKNOWN"
            return reason if stable_prior() else "UNKNOWN"

        context_reason = _context_reason(before)
        if context_reason in {"EXECSTART_FORMAT_OR_TIME", "CONTROL_GROUP"}:
            return "UNKNOWN"
        if context_reason is not None or before["DropInPaths"] != DROP_IN:
            return rejected("UNIT_CONTEXT")
        visited.append((UNIT_FILE, proof.trusted(proof.observe(UNIT_FILE))))
        drop = proof.trusted(proof.observe(DROP_IN, limit=PROC_LIMIT))
        visited.append((DROP_IN, drop))
        dropin_form = _dropin_form(drop.data)
        if dropin_form == "UNKNOWN":
            return "UNKNOWN"
        if dropin_form != "DEPENDENCY_VARIANT" or not _generator_form(drop.data):
            return rejected("DROPIN_TRUST_OR_FORM")
        try:
            process = proof.process(pid, group)
        except _StageNegative as failure:
            if not stages or not stable_prior():
                return "UNKNOWN"
            return failure.stage if _negative_again(lambda: proof.process(pid, group), failure) else "UNKNOWN"
        environment = proof.main_environment(pid)
        base, argv, _ = environment
        if base != "/snap/lxd/" + _GENERATOR_REVISION:
            return rejected("REVISION_BINDING")
        try:
            shell = proof.shell(pid, argv, process)
        except _StageNegative as failure:
            if not stages or not stable_prior():
                return "UNKNOWN"
            return failure.stage if _negative_again(lambda: proof.shell(pid, argv, process), failure) else "UNKNOWN"
        try:
            script = proof.pair(pid, base + "/commands/daemon.start", limit=METADATA_LIMIT)
        except _StageNegative as failure:
            if not stages or not stable_prior():
                return "UNKNOWN"
            return failure.stage if _negative_again(
                lambda: proof.pair(pid, base + "/commands/daemon.start", limit=METADATA_LIMIT), failure) else "UNKNOWN"
        if hashlib.sha256(script[0].data).hexdigest() != _GENERATOR_DIGEST:
            return rejected("SCRIPT_PAIR_OR_DIGEST")
        after = proof.diagnostic_unit(expected)
        if _context_reason(after) is not None:
            return "UNKNOWN"
        unit_equal = _same_diagnostic_unit(before, after)
        if not stages:
            if (not unit_equal or proof.process(pid, group) != process
                    or proof.main_environment(pid) != environment or proof.shell(pid, argv, process) != shell
                    or proof.pair(pid, base + "/commands/daemon.start", limit=METADATA_LIMIT) != script
                    or not proof.diagnostic_reobserve(tuple(visited))):
                return "UNKNOWN"
            return "MATCH"
        current_process = proof.process(pid, group)
        current_environment = proof.main_environment(pid)
        current_shell = proof.shell(pid, argv, process)
        current_script = proof.pair(pid, base + "/commands/daemon.start", limit=METADATA_LIMIT)
        files_equal = _stage_reobserve(proof, visited)
        if (not unit_equal or current_process != process or current_environment != environment
                or current_shell != shell or current_script != script or not files_equal):
            return "RECHECK_DRIFT" if stages else "UNKNOWN"
        return "UNKNOWN" if stages else "MATCH"
    except Exception:
        return "UNKNOWN"


def diagnose_generator_form(runner: RunnerPort, expected: dict[str, Any], *, fs: ReadOnlyFS | None = None,
                            clock: Callable[[], float] = time.monotonic) -> str:
    """Compare a fixed, stable package and drop-in without admitting an identity."""
    return _probe_generator_form(runner, expected, fs=fs, clock=clock, stages=False)


def diagnose_generator_stage(runner: RunnerPort, expected: dict[str, Any], *, fs: ReadOnlyFS | None = None,
                             clock: Callable[[], float] = time.monotonic) -> str:
    """Report a stable fixed failure stage without admitting an identity."""
    return _probe_generator_form(runner, expected, fs=fs, clock=clock, stages=True)

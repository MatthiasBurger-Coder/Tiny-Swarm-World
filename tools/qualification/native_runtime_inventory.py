#!/usr/bin/env python3
"""Capture a bounded, read-only and redacted native LXD/Incus inventory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import grp
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

TARGET = "native-linux-test-host"
ROOT = Path(__file__).resolve().parents[2]
PRIVATE_REL = Path(".tiny-swarm/evidence/issue-449/s449-private-20261027/native-runtime-inventory.json")
MAX_COMMAND_SECONDS = 30
MAX_STREAM = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_ARTIFACT = 8 * 1024 * 1024
MAX_ENTITIES = 10_000
MAX_COMMANDS = 256
MAX_WALL_SECONDS = 300
ENV_BASE = {"LC_ALL": "C", "PATH": "/usr/bin:/bin"}
UNITS = ("lxd.service", "snap.lxd.daemon.service", "snap.lxd.daemon.unix.socket",
         "incus.service", "incus.socket")
SERVICE_UNITS = ("lxd.service", "snap.lxd.daemon.service", "incus.service")
SOCKETS = {
    "/var/lib/lxd/unix.socket": "lxd_system",
    "/var/snap/lxd/common/lxd/unix.socket": "lxd_snap",
    "/var/lib/incus/unix.socket": "incus_var_lib",
    "/run/incus/unix.socket": "incus_run",
}
PROPERTIES = ("LoadState", "ActiveState", "SubState", "UnitFileState", "MainPID")
UNIT_STATES = {"enabled", "enabled-runtime", "disabled", "disabled-runtime", "static",
               "indirect", "alias", "linked", "linked-runtime", "masked", "generated",
               "transient", "", "not-found"}
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]{0,62}$")
VOLUME_TYPES = {"container", "custom", "image", "virtual-machine"}
VOLUME_CONTENT_TYPES = {"block", "filesystem"}
REVISION_EXE = re.compile(r"^/snap/lxd/([1-9][0-9]*)/bin/lxd$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class InventoryError(Exception):
    """Safe failure; exception text is always a fixed code."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise InventoryError("INVALID_JSON_DUPLICATE_KEY")
        out[key] = value
    return out


def strict_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs,
                          parse_constant=lambda _v: (_ for _ in ()).throw(InventoryError("INVALID_JSON_CONSTANT")))
    except InventoryError:
        raise
    except (UnicodeError, ValueError, TypeError) as exc:
        raise InventoryError("INVALID_JSON") from exc


def _unit_state(unit: str, values: dict[str, str]) -> dict[str, Any]:
    socket_unit = unit in {"incus.socket", "snap.lxd.daemon.unix.socket"}
    expected = set(PROPERTIES) | ({"Listen"} if socket_unit else set())
    if socket_unit and "MainPID" not in values:
        expected.remove("MainPID")
    if set(values) != expected:
        raise InventoryError("UNIT_SCHEMA_INVALID")
    load, active, sub = values["LoadState"], values["ActiveState"], values["SubState"]
    unit_file, pid_raw = values["UnitFileState"], values.get("MainPID", "0")
    if unit_file not in UNIT_STATES or not re.fullmatch(r"[0-9]+", pid_raw):
        raise InventoryError("UNIT_VALUE_INVALID")
    if socket_unit and pid_raw != "0":
        raise InventoryError("UNIT_VALUE_INVALID")
    if load != "not-found" and unit_file in {"", "not-found"}:
        raise InventoryError("UNIT_VALUE_INVALID")
    if load == "not-found" and unit_file not in {"", "not-found"}:
        raise InventoryError("UNIT_VALUE_INVALID")
    pid = int(pid_raw)
    if unit.endswith(".socket"):
        valid = ((load == "loaded" and active == "active" and sub == "listening" and pid == 0)
                 or (unit == "incus.socket" and load == "loaded" and active == "active" and sub == "running" and pid == 0)
                 or (load == "loaded" and active == "inactive" and sub == "dead" and pid == 0)
                 or (load == "loaded" and active == "failed" and sub == "failed" and pid == 0)
                 or (load == "not-found" and active == "inactive" and sub == "dead" and pid == 0 and values["Listen"] == ""))
        if not valid:
            raise InventoryError("UNIT_STATE_BLOCKED")
        listen = _listen_endpoint(values["Listen"]) if values["Listen"] else ""
        return {"unit": unit, "load_state": load, "active_state": active, "sub_state": sub,
                "unit_file_state": "" if load == "not-found" else unit_file,
                "main_pid": 0, "listen": listen}
    valid = ((load == "loaded" and active == "active" and sub == "running" and pid > 0)
             or (load == "loaded" and active == "inactive" and sub == "dead" and pid == 0)
             or (load == "loaded" and active == "failed" and sub == "failed" and pid == 0)
             or (load == "not-found" and active == "inactive" and sub == "dead" and pid == 0
                 and unit_file in {"", "not-found"}))
    if not valid:
        raise InventoryError("UNIT_STATE_BLOCKED")
    return {"unit": unit, "load_state": load, "active_state": active, "sub_state": sub,
            "unit_file_state": "" if load == "not-found" else unit_file, "main_pid": pid}


def _listen_endpoint(value: str) -> str:
    # systemd Listen may contain a type prefix; paths are compared but never emitted.
    candidate = value
    match = re.fullmatch(r"(.+?)\s+\((?:Stream|SequentialPacket)\)", value)
    if match:
        candidate = match.group(1)
    elif value.startswith("Stream:") or value.startswith("SequentialPacket:"):
        candidate = value.split(":", 1)[-1]
    if candidate not in SOCKETS:
        raise InventoryError("SOCKET_LISTEN_BLOCKED")
    return SOCKETS[candidate]


def executable_identity(unit: str, path: str) -> tuple[str, str]:
    if unit == "snap.lxd.daemon.service" and REVISION_EXE.fullmatch(path):
        return "lxd_snap", "snap:lxd"
    mapping = {
        ("lxd.service", "/usr/lib/lxd/lxd"): ("lxd_system", "system:lxd"),
        ("lxd.service", "/usr/libexec/lxd/lxd"): ("lxd_system", "system:lxd"),
        ("incus.service", "/usr/libexec/incus/incusd"): ("incus_system", "system:incus"),
        ("incus.service", "/usr/lib/incus/incusd"): ("incus_system", "system:incus"),
    }
    if (unit, path) not in mapping:
        raise InventoryError("EXECUTABLE_IDENTITY_BLOCKED")
    return mapping[(unit, path)]


class Runner:
    """No-shell subprocess runner enforcing per-process and aggregate bounds."""
    def __init__(self, *, popen: Callable[..., Any] = subprocess.Popen, clock: Callable[[], float] = time.monotonic):
        self.popen, self.clock = popen, clock
        self.started = clock()
        self.total_bytes = 0
        self.commands = 0
        self.records: list[dict[str, Any]] = []

    def run(self, argv: list[str], *, env: dict[str, str] | None = None, command_id: str,
            safe_args: list[str] | None = None, expected: set[int] = {0}) -> tuple[int, bytes, bytes]:
        if self.commands >= MAX_COMMANDS or self.clock() - self.started > MAX_WALL_SECONDS:
            raise InventoryError("INVENTORY_BUDGET_EXCEEDED")
        if not argv or not os.path.isabs(argv[0]) or len(argv) > 16 or any("\x00" in a for a in argv):
            raise InventoryError("ARGV_INVALID")
        self.commands += 1
        child_env = dict(ENV_BASE if env is None else env)
        if set(child_env) - {"LC_ALL", "PATH", "LXD_SOCKET", "INCUS_SOCKET"} or child_env.get("LC_ALL") != "C" or child_env.get("PATH") != ENV_BASE["PATH"]:
            raise InventoryError("ENV_INVALID")
        lxd_client = argv[0] in {"/usr/bin/lxc", "/snap/bin/lxc"}
        incus_client = argv[0] == "/usr/bin/incus"
        if lxd_client:
            if set(child_env) - {"LC_ALL", "PATH", "LXD_SOCKET"} or child_env.get("LXD_SOCKET") not in {
                    "/var/lib/lxd/unix.socket", "/var/snap/lxd/common/lxd/unix.socket"}:
                raise InventoryError("ENDPOINT_ENV_INVALID")
            if ((argv[0] == "/snap/bin/lxc") !=
                    (child_env["LXD_SOCKET"] == "/var/snap/lxd/common/lxd/unix.socket")):
                raise InventoryError("CLIENT_SOCKET_BINDING_BLOCKED")
        elif incus_client:
            if set(child_env) - {"LC_ALL", "PATH", "INCUS_SOCKET"} or child_env.get("INCUS_SOCKET") not in {
                    "/run/incus/unix.socket", "/var/lib/incus/unix.socket"}:
                raise InventoryError("ENDPOINT_ENV_INVALID")
        elif argv[0] not in {"/usr/bin/systemctl", "/usr/bin/readlink", "/usr/bin/test"} or set(child_env) != {"LC_ALL", "PATH"}:
            raise InventoryError("COMMAND_IDENTITY_BLOCKED")
        process = None
        try:
            process = self.popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 shell=False, close_fds=True, env=child_env, start_new_session=True)
            selector = selectors.DefaultSelector()
            assert process.stdout is not None and process.stderr is not None
            selector.register(process.stdout, selectors.EVENT_READ, "out")
            selector.register(process.stderr, selectors.EVENT_READ, "err")
            streams = {"out": bytearray(), "err": bytearray()}
            deadline = self.clock() + MAX_COMMAND_SECONDS
            while selector.get_map():
                remaining = min(deadline - self.clock(), MAX_WALL_SECONDS - (self.clock() - self.started))
                if remaining <= 0:
                    raise InventoryError("COMMAND_TIMEOUT")
                for key, _ in selector.select(min(remaining, 0.2)):
                    chunk = os.read(key.fd, min(65536, MAX_STREAM + 1 - len(streams[key.data])))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    streams[key.data].extend(chunk)
                    if len(streams[key.data]) > MAX_STREAM:
                        raise InventoryError("COMMAND_OUTPUT_LIMIT")
                if process.poll() is not None and not selector.get_map():
                    break
            status = process.wait(timeout=max(0.01, min(1, deadline - self.clock())))
            out, err = bytes(streams["out"]), bytes(streams["err"])
            self.total_bytes += len(out) + len(err)
            if self.total_bytes > MAX_TOTAL_BYTES:
                raise InventoryError("TOTAL_OUTPUT_LIMIT")
            if status not in expected:
                raise InventoryError("COMMAND_FAILED")
            self.records.append({"command_id": command_id, "safe_args": safe_args or [],
                                 "exit_status": status, "stdout_bytes": len(out), "stderr_bytes": len(err)})
            return status, out, err
        except InventoryError:
            if process is not None:
                _kill_reap(process)
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            if process is not None:
                _kill_reap(process)
            raise InventoryError("COMMAND_EXECUTION_FAILED") from exc


def _kill_reap(process: Any) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (OSError, AttributeError):
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=2)
    except (OSError, subprocess.SubprocessError):
        pass


def _systemctl_show(runner: Runner, unit: str) -> dict[str, Any]:
    props = list(PROPERTIES) + (["Listen"] if unit.endswith(".socket") else [])
    argv = ["/usr/bin/systemctl", "show", unit]
    argv += [f"--property={p}" for p in props] + ["--no-pager"]
    _, raw, _ = runner.run(argv, command_id="systemctl_show_socket" if unit.endswith(".socket") else "systemctl_show_unit", safe_args=[unit])
    try:
        pairs = [line.split("=", 1) for line in raw.decode("utf-8", "strict").splitlines()]
        if any(len(pair) != 2 for pair in pairs):
            raise ValueError
        vals = dict(pairs)
        if len(vals) != len(pairs):
            raise ValueError
    except (UnicodeError, ValueError) as exc:
        raise InventoryError("UNIT_OUTPUT_INVALID") from exc
    return _unit_state(unit, vals)


def _read_executable_path(runner: Runner, row: dict[str, Any]) -> str:
    path = f"/proc/{row['main_pid']}/exe"
    _, raw, _ = runner.run(["/usr/bin/readlink", "-f", path], command_id="resolve_executable")
    try:
        resolved = raw.decode("utf-8", "strict").strip()
    except UnicodeError as exc:
        raise InventoryError("EXECUTABLE_OUTPUT_INVALID") from exc
    return resolved


def _resolve_executable(runner: Runner, row: dict[str, Any]) -> tuple[str, str]:
    try:
        return executable_identity(row["unit"], _read_executable_path(runner, row))
    except InventoryError as exc:
        if str(exc) != "EXECUTABLE_IDENTITY_BLOCKED" or row["unit"] != "snap.lxd.daemon.service":
            raise
    import importlib
    try:
        module_name = f"{__package__}.native_lxd_snap_provenance" if __package__ else "native_lxd_snap_provenance"
        proof = importlib.import_module(module_name)
    except ImportError as exc:
        raise InventoryError("SNAP_WRAPPER_METADATA_INVALID") from exc
    try:
        return proof.prove_snap_wrapper(runner, row)
    except proof.ProvenanceError as exc:
        raise InventoryError(str(exc)) from exc


def _unknown_executable_reason(unit: str, resolved: str) -> str:
    if unit != "snap.lxd.daemon.service":
        return "EXECUTABLE_IDENTITY_BLOCKED"
    if not resolved or not resolved.startswith("/") or "\x00" in resolved:
        return "SNAP_EXECUTABLE_UNCLASSIFIABLE"
    if resolved.startswith("/snap/lxd/"):
        return "SNAP_ROOT_PATH_MISMATCH"
    return "SNAP_EXECUTABLE_OUTSIDE_ROOT"


def diagnose_units(*, runner: Runner | None = None) -> tuple[dict[str, Any], int]:
    """Return symbolic unit identities without inventory queries or artifact writes."""
    runner = runner or Runner()
    services: list[dict[str, str]] = []
    for unit in UNITS:
        row = _systemctl_show(runner, unit)
        if unit not in SERVICE_UNITS:
            continue
        if row["active_state"] != "active":
            services.append({"unit": unit, "identity": "NOT_ACTIVE"})
            continue
        reason = "EXECUTABLE_IDENTITY_BLOCKED"
        resolved = ""
        try:
            resolved = _read_executable_path(runner, row)
            identity, _package = executable_identity(unit, resolved)
        except InventoryError as exc:
            if str(exc) != "EXECUTABLE_IDENTITY_BLOCKED":
                raise
            identity = "UNKNOWN"
            reason = _unknown_executable_reason(unit, resolved)
        current = _systemctl_show(runner, unit)
        if current != row:
            raise InventoryError("UNIT_DRIFT_BLOCKED")
        if identity == "UNKNOWN":
            return ({"mode": "diagnose-units", "status": "BLOCKED_UNKNOWN",
                     "unit": unit, "identity": "UNKNOWN", "reason": reason}, 2)
        services.append({"unit": unit, "identity": identity})
    return ({"mode": "diagnose-units", "status": "DIAGNOSTIC_COMPLETE",
             "services": services}, 0)


def _endpoint(runner: Runner, path: str, *, unit: str) -> tuple[str, bool]:
    endpoint = SOCKETS.get(path)
    if endpoint is None:
        raise InventoryError("SOCKET_PATH_BLOCKED")
    status, _, _ = runner.run(["/usr/bin/test", "-e", path], command_id="socket_exists",
                              safe_args=[endpoint], expected={0, 1})
    if status == 1:
        return endpoint, False
    status, _, _ = runner.run(["/usr/bin/test", "-S", path], command_id="socket_type",
                              safe_args=[endpoint], expected={0, 1})
    if status != 0:
        raise InventoryError("SOCKET_TYPE_BLOCKED")
    _, raw, _ = runner.run(["/usr/bin/readlink", "-f", path], command_id="canonical_socket",
                           safe_args=[endpoint])
    try:
        canonical = raw.decode("utf-8", "strict").strip()
    except UnicodeError as exc:
        raise InventoryError("SOCKET_CANONICAL_INVALID") from exc
    if canonical != path or SOCKETS.get(canonical) != endpoint:
        raise InventoryError("SOCKET_CANONICAL_BLOCKED")
    return endpoint, True


def _require_full_local_access(path: str, *, incus: bool) -> None:
    """Prove the current local-socket identity can enumerate every project."""
    if os.geteuid() == 0:
        return
    try:
        socket_stat = os.stat(path)
        socket_group = grp.getgrgid(socket_stat.st_gid).gr_name
    except (KeyError, OSError) as exc:
        raise InventoryError("RUNTIME_ACCESS_SCOPE_UNPROVEN") from exc
    admin_group = "incus-admin" if incus else "lxd"
    groups = set(os.getgroups()) | {os.getegid()}
    if socket_group != admin_group or socket_stat.st_gid not in groups:
        raise InventoryError("RUNTIME_ACCESS_SCOPE_UNPROVEN")


def _same_consumers(left: Any, right: Any, project: str) -> bool:
    return _consumer_refs(left, project) == _consumer_refs(right, project)


def _validate_complete_ownership(rows: list[dict[str, Any]]) -> None:
    """Reject profile and consumer edges that do not resolve in the full inventory."""
    projects = {row["project"]: row for row in rows}
    resources: dict[str, dict[str, set[str]]] = {}
    for project, row in projects.items():
        resources[project] = {
            "profiles": {item["name"] for item in row["profiles"]},
            "instances": {item["name"] for item in row["instances"]},
            "networks": {item["name"] for item in row["networks"]},
            "storage-pools": {item["name"] for item in row["pools"]},
            "storage-volumes": {f"{pool['name']}/{volume['type']}/{volume['name']}"
                                for pool in row["pools"] for volume in pool["volumes"]},
        }
    for project, row in projects.items():
        for instance in row["instances"]:
            if not set(instance["profiles"]).issubset(resources[project]["profiles"]):
                raise InventoryError("PROFILE_REFERENCE_UNRESOLVED")
        for profile in row["profiles"]:
            expected_users = {
                ("instances", instance["name"], project)
                for instance in row["instances"] if profile["name"] in instance["profiles"]
            }
            actual_users = {
                (ref["kind"], ref["name"], ref["project"])
                for ref in profile["used_by"]
            }
            if actual_users != expected_users:
                raise InventoryError("PROFILE_CONSUMER_RECIPROCITY_MISMATCH")
        for kind in ("profiles", "networks", "pools"):
            for resource in row[kind]:
                for ref in resource["used_by"]:
                    if kind == "pools" and ref["kind"] == "storage-volumes":
                        continue
                    target = resources.get(ref["project"])
                    if target is None or ref["name"] not in target[ref["kind"]]:
                        raise InventoryError("CONSUMER_REFERENCE_UNRESOLVED")
        for pool in row["pools"]:
            volume_refs = {ref["name"] for ref in pool["used_by"] if ref["kind"] == "storage-volumes"}
            expected_volume_refs = {f"{pool['name']}/{volume['type']}/{volume['name']}"
                                    for volume in pool["volumes"]}
            if volume_refs != expected_volume_refs:
                raise InventoryError("POOL_VOLUME_OWNERSHIP_MISMATCH")
            for volume in pool["volumes"]:
                for ref in volume["used_by"]:
                    target = resources.get(ref["project"])
                    if target is None or ref["name"] not in target[ref["kind"]]:
                        raise InventoryError("VOLUME_CONSUMER_UNRESOLVED")


def _network_device_users(devices: dict[str, dict[str, str]], project: str,
                          kind: str, name: str) -> dict[str, set[tuple[str, str, str]]]:
    refs: dict[str, set[tuple[str, str, str]]] = {}
    for device in devices.values():
        if device.get("type") == "nic" and "network" in device:
            network = _name(device["network"])
            refs.setdefault(network, set()).add((kind, name, project))
    return refs


def _volume_device_users(devices: dict[str, dict[str, str]], project: str,
                         kind: str, name: str, instance_type: str = "") -> dict[tuple[str, str, str], set[tuple[str, str, str]]]:
    refs: dict[tuple[str, str, str], set[tuple[str, str, str]]] = {}
    for device in devices.values():
        if device.get("type") != "disk" or "pool" not in device:
            continue
        pool = _name(device["pool"])
        if device.get("path") == "/" and kind == "instances":
            volume_type = "container" if instance_type == "container" else "virtual-machine"
            volume_name = name
        elif "source" in device:
            volume_type, volume_name = "custom", _name(device["source"])
        else:
            continue
        refs.setdefault((pool, volume_type, volume_name), set()).add((kind, name, project))
    return refs


def _pool_device_refs(devices: dict[str, dict[str, str]]) -> set[str]:
    return {_name(device["pool"]) for device in devices.values()
            if device.get("type") == "disk" and "pool" in device}


def _parse_json_command(runner: Runner, argv: list[str], *, command_id: str,
                        env: dict[str, str], safe_args: list[str]) -> Any:
    _, raw, _ = runner.run(argv, env=env, command_id=command_id, safe_args=safe_args)
    value = strict_json(raw)
    if isinstance(value, (dict, list)) and len(value) > MAX_ENTITIES:
        raise InventoryError("ENTITY_LIMIT")
    return value


def _name(value: Any) -> str:
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise InventoryError("RESOURCE_ID_INVALID")
    return value


def _only_keys(value: Any, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) - allowed:
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    return value


def _validate_list_metadata(row: dict[str, Any], project: str) -> None:
    if "project" in row and _name(row["project"]) != project:
        raise InventoryError("RESOURCE_PROJECT_MISMATCH")
    for field in ("description", "architecture", "location", "created_at", "last_used_at"):
        if field in row and not isinstance(row[field], str):
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
    for field in ("status", "type", "driver"):
        if field in row:
            _safe_enum(row[field])
    for field in ("config", "expanded_config"):
        if field in row:
            _string_map(row[field])
    for field in ("devices", "expanded_devices"):
        if field in row:
            _devices(row[field])
    for field in ("ephemeral", "stateful", "managed"):
        if field in row and not isinstance(row[field], bool):
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
    if "status_code" in row and (not isinstance(row["status_code"], int) or isinstance(row["status_code"], bool)):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    if "profiles" in row:
        if not isinstance(row["profiles"], list):
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
        for profile in row["profiles"]:
            _name(profile)
    if "locations" in row:
        if not isinstance(row["locations"], list) or any(not isinstance(location, str) for location in row["locations"]):
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
    if "used_by" in row:
        _consumer_refs(row["used_by"], project)


def _string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    return value


def _devices(value: Any) -> dict[str, dict[str, str]]:
    if not isinstance(value, dict):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    result: dict[str, dict[str, str]] = {}
    for name, device in value.items():
        _name(name)
        row = _string_map(device)
        if set(row) - {"type", "name", "nictype", "parent", "network", "listen", "connect", "bind", "ports", "path", "source", "pool", "size", "readonly", "required", "shift", "limits.cpu", "limits.memory", "boot.priority"}:
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
        if row.get("type") not in {"disk", "nic", "proxy"}:
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
        result[name] = row
    return result


def _consumer_refs(value: Any, project: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    refs: set[tuple[str, str, str]] = set()
    for link in value:
        if not isinstance(link, str):
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
        parsed = urlsplit(link)
        parts = parsed.path.split("/")
        if parsed.scheme or parsed.netloc or parsed.fragment or parts[:2] != ["", "1.0"]:
            raise InventoryError("RESOURCE_LINK_INVALID")
        if len(parts) == 7 and parts[2] == "storage-pools" and parts[4] == "volumes":
            pool, volume_type, volume_name = _name(parts[3]), _volume_type(parts[5]), _name(parts[6])
            kind, name = "storage-volumes", f"{pool}/{volume_type}/{volume_name}"
        elif len(parts) == 4 and parts[2] in {"profiles", "instances", "networks", "storage-pools"}:
            kind, name = parts[2], _name(parts[3])
        else:
            raise InventoryError("RESOURCE_LINK_INVALID")
        try:
            query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True) if parsed.query else {}
        except ValueError as exc:
            raise InventoryError("RESOURCE_LINK_INVALID") from exc
        if set(query) - {"project"} or ("project" in query and len(query["project"]) != 1):
            raise InventoryError("RESOURCE_LINK_INVALID")
        consumer_project = _name(query["project"][0]) if "project" in query else project
        refs.add((kind, name, consumer_project))
    return [{"kind": kind, "name": name, "project": consumer_project}
            for kind, name, consumer_project in sorted(refs)]


def _show(runner: Runner, prefix: list[str], args: list[str], *, command_id: str,
          env: dict[str, str], safe_args: list[str]) -> dict[str, Any]:
    return _parse_json_command(runner, prefix + args, command_id=command_id, env=env,
                               safe_args=safe_args)


def _validate_profile_show(value: Any, name: str, project: str) -> dict[str, Any]:
    row = _only_keys(value, {"name", "project", "description", "config", "devices", "used_by"})
    if _name(row.get("name")) != name or ("project" in row and _name(row["project"]) != project):
        raise InventoryError("RESOURCE_IDENTITY_MISMATCH")
    _string_map(row.get("config"))
    _devices(row.get("devices"))
    _consumer_refs(row.get("used_by"), project)
    _validate_list_metadata(row, project)
    return row


def _validate_instance_config(value: Any, name: str, project: str) -> dict[str, Any]:
    row = _only_keys(value, {"name", "project", "description", "architecture", "config", "devices",
                            "ephemeral", "profiles", "stateful", "location", "type"})
    if _name(row.get("name")) != name or ("project" in row and _name(row["project"]) != project):
        raise InventoryError("RESOURCE_IDENTITY_MISMATCH")
    _string_map(row.get("config"))
    _devices(row.get("devices"))
    if not isinstance(row.get("profiles"), list) or any(not isinstance(v, str) for v in row["profiles"]):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    if not isinstance(row.get("ephemeral"), bool) or not isinstance(row.get("stateful"), bool):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    _validate_list_metadata(row, project)
    return row


def _validate_network_show(value: Any, name: str, project: str) -> dict[str, Any]:
    row = _only_keys(value, {"name", "project", "type", "managed", "status", "config", "description", "used_by", "locations"})
    if _name(row.get("name")) != name or ("project" in row and _name(row["project"]) != project) or not isinstance(row.get("type"), str) or not isinstance(row.get("managed"), bool):
        raise InventoryError("RESOURCE_IDENTITY_MISMATCH")
    if "used_by" not in row:
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    _string_map(row.get("config"))
    _consumer_refs(row["used_by"], project)
    _validate_list_metadata(row, project)
    return row


def _validate_pool_show(value: Any, name: str, project: str) -> dict[str, Any]:
    row = _only_keys(value, {"name", "driver", "project", "config", "description", "used_by", "status", "locations"})
    if _name(row.get("name")) != name or ("project" in row and _name(row["project"]) != project) or not isinstance(row.get("driver"), str):
        raise InventoryError("RESOURCE_IDENTITY_MISMATCH")
    if "used_by" not in row:
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    _string_map(row.get("config"))
    _consumer_refs(row["used_by"], project)
    _validate_list_metadata(row, project)
    return row


def _validate_volume_show(value: Any, pool: str, volume_type: str, name: str, project: str) -> dict[str, Any]:
    row = _only_keys(value, {"name", "type", "content_type", "project", "description", "config",
                             "used_by", "location", "created_at"})
    if _name(row.get("name")) != name or _volume_type(row.get("type")) != volume_type:
        raise InventoryError("RESOURCE_IDENTITY_MISMATCH")
    if "project" not in row or _name(row["project"]) != project:
        raise InventoryError("VOLUME_OWNER_PROJECT_UNSUPPORTED")
    if "used_by" not in row or "config" not in row:
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    for field in ("content_type", "description", "location", "created_at"):
        if field in row and not isinstance(row[field], str):
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
    _string_map(row["config"])
    _consumer_refs(row["used_by"], project)
    return row


def _inventory_client(runner: Runner, identity: str, socket: str, *, incus: bool,
                      before_query: Callable[[], None]) -> tuple[str, list[dict[str, Any]]]:
    binary = "/usr/bin/incus" if incus else ("/snap/bin/lxc" if identity == "lxd_snap" else "/usr/bin/lxc")
    variable = "INCUS_SOCKET" if incus else "LXD_SOCKET"
    env = {**ENV_BASE, variable: socket}
    prefix = [binary, "--force-local"]
    kind = "incus" if incus else "lxd"
    before_query()
    _, version_raw, _ = runner.run(prefix + ["version"], command_id=f"{kind}_version", env=env, safe_args=[])
    try:
        version_text = version_raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise InventoryError("VERSION_OUTPUT_INVALID") from exc
    versions = re.findall(r"^Server version:\s*([A-Za-z0-9_.+-]{1,64})\s*$", version_text, re.MULTILINE)
    if len(versions) != 1:
        raise InventoryError("VERSION_SCHEMA_INVALID")
    before_query()
    projects = _parse_json_command(runner, prefix + ["project", "list", "--format", "json"],
                                   command_id=f"{kind}_project_list", env=env, safe_args=[])
    if not isinstance(projects, list) or len(projects) > MAX_ENTITIES:
        raise InventoryError("PROJECT_LIST_INVALID")
    names = []
    project_entries: dict[str, dict[str, Any]] = {}
    for entry in projects:
        row = _only_keys(entry, {"name", "description", "used_by", "config"})
        project_name = _name(row.get("name"))
        if "used_by" not in row:
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
        _validate_list_metadata(row, project_name)
        names.append(project_name)
        project_entries[project_name] = row
    if len(set(names)) != len(names):
        raise InventoryError("PROJECT_DUPLICATE")
    rows: list[dict[str, Any]] = []
    entity_count = len(names)
    network_users: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    volume_users: dict[tuple[str, str, str, str], set[tuple[str, str, str]]] = {}
    pool_device_refs: set[tuple[str, str]] = set()
    pool_device_users: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    project_consumers: dict[str, set[tuple[str, str, str]]] = {}
    for project in names:
        before_query()
        show = _parse_json_command(runner, prefix + ["project", "show", project, "--format", "json"],
                                   command_id=f"{kind}_project_show", env=env, safe_args=[project])
        show = _only_keys(show, {"name", "description", "config", "used_by"})
        if _name(show.get("name")) != project:
            raise InventoryError("PROJECT_IDENTITY_MISMATCH")
        if "used_by" not in show:
            raise InventoryError("RESOURCE_SCHEMA_INVALID")
        _validate_list_metadata(show, project)
        if not _same_consumers(project_entries[project]["used_by"], show["used_by"], project):
            raise InventoryError("PROJECT_CONSUMER_LIST_MISMATCH")
        project_consumers[project] = {
            (ref["kind"], ref["name"], ref["project"])
            for ref in _consumer_refs(show["used_by"], project)
        }
        before_query()
        profiles = _parse_json_command(runner, prefix + ["profile", "list", "--project", project, "--format", "json"],
                                       command_id=f"{kind}_profile_list", env=env, safe_args=[project])
        before_query()
        instances = _parse_json_command(runner, prefix + ["list", "--project", project, "--format", "json"],
                                        command_id=f"{kind}_instance_list", env=env, safe_args=[project])
        before_query()
        networks = _parse_json_command(runner, prefix + ["network", "list", "--project", project, "--format", "json"],
                                       command_id=f"{kind}_network_list", env=env, safe_args=[project])
        before_query()
        pools = _parse_json_command(runner, prefix + ["storage", "list", "--project", project, "--format", "json"],
                                    command_id=f"{kind}_storage_list", env=env, safe_args=[project])
        if not all(isinstance(x, list) for x in (profiles, instances, networks, pools)):
            raise InventoryError("RESOURCE_LIST_INVALID")
        entity_count += sum(map(len, (profiles, instances, networks, pools)))
        if entity_count > MAX_ENTITIES:
            raise InventoryError("ENTITY_LIMIT")
        profile_rows: list[dict[str, Any]] = []
        for item in profiles:
            p = _only_keys(item, {"name", "project", "description", "config", "devices", "used_by"})
            if "used_by" not in p:
                raise InventoryError("RESOURCE_SCHEMA_INVALID")
            _validate_list_metadata(p, project)
            pname = _name(p.get("name"))
            before_query()
            pdetail = _validate_profile_show(_show(runner, prefix,
                ["profile", "show", pname, "--project", project, "--format", "json"],
                command_id=f"{kind}_profile_show", env=env, safe_args=[pname, project]), pname, project)
            if not _same_consumers(p["used_by"], pdetail["used_by"], project):
                raise InventoryError("PROFILE_CONSUMER_LIST_MISMATCH")
            for network, users in _network_device_users(pdetail["devices"], project, "profiles", pname).items():
                network_users.setdefault((project, network), set()).update(users)
            for (pool_ref, volume_type, volume_name), users in _volume_device_users(
                    pdetail["devices"], project, "profiles", pname).items():
                volume_users.setdefault((project, pool_ref, volume_type, volume_name), set()).update(users)
            pool_device_refs.update((project, pool_ref) for pool_ref in _pool_device_refs(pdetail["devices"]))
            for pool_ref in _pool_device_refs(pdetail["devices"]):
                pool_device_users.setdefault((project, pool_ref), set()).add(("profiles", pname, project))
            device_rows = _device_types(pdetail["devices"])
            entity_count += len(device_rows)
            if entity_count > MAX_ENTITIES:
                raise InventoryError("ENTITY_LIMIT")
            profile_rows.append({"name": pname, "used_by": _consumer_refs(pdetail["used_by"], project),
                                 "devices": device_rows})
        instance_rows: list[dict[str, Any]] = []
        for item in instances:
            i = _only_keys(item, {"name", "project", "architecture", "config", "devices", "ephemeral",
                                  "expanded_config", "expanded_devices", "profiles", "stateful", "status",
                                  "status_code", "type", "location", "description", "created_at", "last_used_at"})
            _validate_list_metadata(i, project)
            iname = _name(i.get("name"))
            before_query()
            local = _validate_instance_config(_show(runner, prefix,
                ["config", "show", iname, "--project", project, "--format", "json"],
                command_id=f"{kind}_instance_config_show", env=env, safe_args=[iname, project]), iname, project)
            before_query()
            expanded = _validate_instance_config(_show(runner, prefix,
                ["config", "show", iname, "--project", project, "--format", "json", "--expanded"],
                command_id=f"{kind}_instance_config_show_expanded", env=env, safe_args=[iname, project]), iname, project)
            list_profiles = sorted(set(_name(v) for v in _strings(i.get("profiles"))))
            if list_profiles != sorted(set(_name(v) for v in local["profiles"])) or \
                    list_profiles != sorted(set(_name(v) for v in expanded["profiles"])):
                raise InventoryError("INSTANCE_PROFILE_LIST_MISMATCH")
            instance_type = _safe_enum(i.get("type"))
            if instance_type not in {"container", "virtual-machine"}:
                raise InventoryError("INSTANCE_TYPE_UNSUPPORTED")
            for network, users in _network_device_users(local["devices"], project, "instances", iname).items():
                network_users.setdefault((project, network), set()).update(users)
            for network, users in _network_device_users(expanded["devices"], project, "instances", iname).items():
                network_users.setdefault((project, network), set()).update(users)
            for (pool_ref, volume_type, volume_name), users in _volume_device_users(
                    {**expanded["devices"], **local["devices"]}, project, "instances", iname, instance_type).items():
                volume_users.setdefault((project, pool_ref, volume_type, volume_name), set()).update(users)
            pool_device_refs.update((project, pool_ref) for pool_ref in _pool_device_refs(
                {**expanded["devices"], **local["devices"]}))
            for pool_ref in _pool_device_refs({**expanded["devices"], **local["devices"]}):
                pool_device_users.setdefault((project, pool_ref), set()).add(("instances", iname, project))
            entity_count += len(local["devices"]) + len(expanded["devices"])
            if entity_count > MAX_ENTITIES:
                raise InventoryError("ENTITY_LIMIT")
            instance_rows.append({"name": iname, "status": _safe_enum(i.get("status")),
                                  "type": instance_type,
                                  "profiles": list_profiles,
                                  "local_devices": _device_types(local["devices"]),
                                  "expanded_devices": _device_types(expanded["devices"])})
        network_rows: list[dict[str, Any]] = []
        for item in networks:
            n = _only_keys(item, {"name", "project", "type", "managed", "status", "config", "description",
                                  "used_by", "locations"})
            _validate_list_metadata(n, project)
            if "used_by" not in n:
                raise InventoryError("RESOURCE_SCHEMA_INVALID")
            nname = _name(n.get("name"))
            before_query()
            ndetail = _validate_network_show(_show(runner, prefix,
                ["network", "show", nname, "--project", project, "--format", "json"],
                command_id=f"{kind}_network_show", env=env, safe_args=[nname, project]), nname, project)
            if not _same_consumers(n["used_by"], ndetail["used_by"], project):
                raise InventoryError("NETWORK_CONSUMER_LIST_MISMATCH")
            network_rows.append({"name": nname, "type": _safe_enum(ndetail["type"]),
                                 "used_by": _consumer_refs(ndetail.get("used_by", []), project)})
        pool_rows: list[dict[str, Any]] = []
        for item in pools:
            p = _only_keys(item, {"name", "project", "driver", "config", "description", "used_by",
                                  "status", "locations"})
            _validate_list_metadata(p, project)
            if "used_by" not in p:
                raise InventoryError("RESOURCE_SCHEMA_INVALID")
            pool_name = _name(p.get("name"))
            before_query()
            pdetail = _validate_pool_show(_show(runner, prefix,
                ["storage", "show", pool_name, "--project", project, "--format", "json"],
                command_id=f"{kind}_storage_show", env=env, safe_args=[pool_name, project]), pool_name, project)
            if not _same_consumers(p["used_by"], pdetail["used_by"], project):
                raise InventoryError("POOL_CONSUMER_LIST_MISMATCH")
            before_query()
            volumes = _parse_json_command(runner, prefix + ["storage", "volume", "list", pool_name,
                "--project", project, "--format", "json"], command_id=f"{kind}_storage_volume_list",
                env=env, safe_args=[pool_name, project])
            if not isinstance(volumes, list):
                raise InventoryError("RESOURCE_LIST_INVALID")
            entity_count += len(volumes)
            if entity_count > MAX_ENTITIES:
                raise InventoryError("ENTITY_LIMIT")
            volume_rows: list[dict[str, Any]] = []
            volume_ids: set[tuple[str, str]] = set()
            for volume_item in volumes:
                volume = _only_keys(volume_item, {"name", "type", "content_type", "project", "description",
                                                  "config", "created_at", "used_by", "location"})
                vname = _name(volume.get("name"))
                vtype = _volume_type(volume.get("type"))
                if "used_by" not in volume:
                    raise InventoryError("RESOURCE_SCHEMA_INVALID")
                if "project" not in volume or _name(volume["project"]) != project:
                    raise InventoryError("VOLUME_OWNER_PROJECT_UNSUPPORTED")
                if (vtype, vname) in volume_ids:
                    raise InventoryError("RESOURCE_DUPLICATE")
                volume_ids.add((vtype, vname))
                for field in ("content_type", "description", "location"):
                    if field in volume and not isinstance(volume[field], str):
                        raise InventoryError("RESOURCE_SCHEMA_INVALID")
                _validate_list_metadata(volume, project)
                before_query()
                detail = _validate_volume_show(_show(runner, prefix,
                    ["storage", "volume", "show", pool_name, f"{vtype}/{vname}", "--project", project,
                     "--format", "json"], command_id=f"{kind}_storage_volume_show", env=env,
                    safe_args=[pool_name, vtype, vname, project]), pool_name, vtype, vname, project)
                if not _same_consumers(volume["used_by"], detail["used_by"], project):
                    raise InventoryError("VOLUME_CONSUMER_LIST_MISMATCH")
                volume_rows.append({"name": vname, "type": vtype,
                                    "content_type": _volume_content_type(detail.get("content_type")),
                                    "used_by": _consumer_refs(detail["used_by"], project)})
            volume_rows.sort(key=lambda row: (row["type"], row["name"]))
            pool_rows.append({"name": pool_name, "type": _safe_enum(pdetail["driver"]),
                              "used_by": _consumer_refs(pdetail["used_by"], project), "volumes": volume_rows})
        profile_rows.sort(key=lambda row: row["name"])
        instance_rows.sort(key=lambda row: row["name"])
        network_rows.sort(key=lambda row: row["name"])
        pool_rows.sort(key=lambda row: row["name"])
        rows.append({"project": project, "profiles": profile_rows, "instances": instance_rows,
                     "networks": network_rows, "pools": pool_rows})
    rows.sort(key=lambda row: row["project"])
    _validate_complete_ownership(rows)
    for row in rows:
        project = row["project"]
        expected_project_users = {
            (kind, item["name"], project)
            for kind, resources in (("profiles", row["profiles"]), ("instances", row["instances"]),
                                    ("networks", row["networks"]))
            for item in resources
        }
        expected_project_users.update(
            ("storage-volumes", f"{pool['name']}/{volume['type']}/{volume['name']}", project)
            for pool in row["pools"] for volume in pool["volumes"]
        )
        if project_consumers[project] != expected_project_users:
            raise InventoryError("PROJECT_CONSUMER_RECIPROCITY_MISMATCH")
    available_networks = {(row["project"], network["name"])
                          for row in rows for network in row["networks"]}
    if set(network_users) - available_networks:
        raise InventoryError("NETWORK_DEVICE_REFERENCE_UNRESOLVED")
    available_volumes = {(row["project"], pool["name"], volume["type"], volume["name"])
                         for row in rows for pool in row["pools"] for volume in pool["volumes"]}
    available_pools = {(row["project"], pool["name"]) for row in rows for pool in row["pools"]}
    if pool_device_refs - available_pools:
        raise InventoryError("POOL_DEVICE_REFERENCE_UNRESOLVED")
    if set(volume_users) - available_volumes:
        raise InventoryError("VOLUME_DEVICE_REFERENCE_UNRESOLVED")
    for project_row in rows:
        project = project_row["project"]
        for network in project_row["networks"]:
            actual = {(ref["kind"], ref["name"], ref["project"]) for ref in network["used_by"]}
            expected = network_users.get((project, network["name"]), set())
            if actual != expected:
                raise InventoryError("NETWORK_CONSUMER_RECIPROCITY_MISMATCH")
        for pool in project_row["pools"]:
            actual_pool_users = {(ref["kind"], ref["name"], ref["project"])
                                 for ref in pool["used_by"]}
            expected_pool_users = set(pool_device_users.get((project, pool["name"]), set()))
            expected_pool_users.update(
                ("storage-volumes", f"{pool['name']}/{volume['type']}/{volume['name']}", project)
                for volume in pool["volumes"]
            )
            if actual_pool_users != expected_pool_users:
                raise InventoryError("POOL_CONSUMER_RECIPROCITY_MISMATCH")
            for volume in pool["volumes"]:
                actual = {(ref["kind"], ref["name"], ref["project"]) for ref in volume["used_by"]}
                expected = volume_users.get((project, pool["name"], volume["type"], volume["name"]), set())
                if actual != expected:
                    raise InventoryError("VOLUME_CONSUMER_RECIPROCITY_MISMATCH")
    return versions[0], rows


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    return value


def _safe_enum(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.+-]{1,64}", value):
        raise InventoryError("RESOURCE_SCHEMA_INVALID")
    return value


def _volume_type(value: Any) -> str:
    value = _safe_enum(value)
    if value not in VOLUME_TYPES:
        raise InventoryError("VOLUME_TYPE_UNSUPPORTED")
    return value


def _volume_content_type(value: Any) -> str:
    value = _safe_enum(value)
    if value not in VOLUME_CONTENT_TYPES:
        raise InventoryError("VOLUME_CONTENT_TYPE_UNSUPPORTED")
    return value


def _device_types(value: Any) -> list[dict[str, str]]:
    devices = _devices(value)
    return [{"name": name, "type": row["type"]} for name, row in sorted(devices.items())]


def capture(source_commit: str, *, runner: Runner | None = None, now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> dict[str, Any]:
    if not HEX40.fullmatch(source_commit):
        raise InventoryError("SOURCE_COMMIT_INVALID")
    runner = runner or Runner()
    units = {unit: _systemctl_show(runner, unit) for unit in UNITS}
    lxd_active = [u for u in ("lxd.service", "snap.lxd.daemon.service") if units[u]["active_state"] == "active"]
    if len(lxd_active) > 1:
        raise InventoryError("AMBIGUOUS_LXD_SERVICE")
    executables: dict[str, dict[str, Any]] = {}
    for unit in ("lxd.service", "snap.lxd.daemon.service", "incus.service"):
        row = units[unit]
        if row["active_state"] == "active":
            identity, package = _resolve_executable(runner, row)
            executables[unit] = {"unit": unit, "main_pid": row["main_pid"], "identity_id": identity,
                                 "package": package, "version": ""}
    if not lxd_active and any(units[unit]["load_state"] == "loaded"
                              for unit in ("lxd.service", "snap.lxd.daemon.service")):
        raise InventoryError("LXD_RUNTIME_INVENTORY_UNAVAILABLE")
    endpoints: dict[str, tuple[str, bool]] = {}
    for path in SOCKETS:
        endpoints[path] = _endpoint(runner, path, unit="")
    if not lxd_active and (units["snap.lxd.daemon.unix.socket"]["load_state"] != "not-found"
                           or endpoints["/var/lib/lxd/unix.socket"][1]
                           or endpoints["/var/snap/lxd/common/lxd/unix.socket"][1]):
        raise InventoryError("LXD_RUNTIME_INVENTORY_UNAVAILABLE")
    clients: dict[str, tuple[str, str, str]] = {}
    client_projects: dict[str, list[dict[str, Any]]] = {}
    for unit in lxd_active:
        identity = executables[unit]["identity_id"]
        path = "/var/snap/lxd/common/lxd/unix.socket" if identity == "lxd_snap" else "/var/lib/lxd/unix.socket"
        if not endpoints[path][1]:
            raise InventoryError("ACTIVE_LXD_SOCKET_MISSING")
        socket_unit = "snap.lxd.daemon.unix.socket"
        if units[socket_unit]["load_state"] == "loaded" and units[socket_unit]["listen"] != identity:
            raise InventoryError("LXD_SOCKET_BINDING_BLOCKED")
        clients["lxd"] = (unit, identity, path)
    if units["incus.service"]["active_state"] == "active":
        su = units["incus.socket"]
        if su["load_state"] == "loaded":
            matches = [path for path, endpoint in SOCKETS.items() if endpoint == su["listen"] and endpoints[path][1]
                       and path in {"/run/incus/unix.socket", "/var/lib/incus/unix.socket"}]
        else:
            matches = [path for path in ("/run/incus/unix.socket", "/var/lib/incus/unix.socket") if endpoints[path][1]]
        if len(matches) != 1:
            raise InventoryError("INCUS_SOCKET_BINDING_BLOCKED")
        clients["incus"] = ("incus.service", "incus_system", matches[0])
    elif units["incus.service"]["load_state"] == "not-found":
        if units["incus.socket"]["load_state"] != "not-found" or any(endpoints[p][1] for p in ("/run/incus/unix.socket", "/var/lib/incus/unix.socket")):
            raise InventoryError("INCUS_ABSENCE_UNVERIFIED")
    elif (units["incus.service"]["load_state"] == "loaded"
          or units["incus.socket"]["active_state"] == "active"):
        raise InventoryError("INCUS_SERVICE_UNAVAILABLE")
    if not clients:
        raise InventoryError("RUNTIME_INVENTORY_EMPTY")
    for key, (unit, identity, path) in clients.items():
        _require_full_local_access(path, incus=(key == "incus"))
        def recheck() -> None:
            _recheck_all(runner, units, executables, endpoints)
            for client_key, (_client_unit, _client_identity, client_path) in clients.items():
                _require_full_local_access(client_path, incus=(client_key == "incus"))
        version, rows = _inventory_client(runner, identity, path, incus=(key == "incus"), before_query=recheck)
        executables[unit]["version"] = version
        client_projects[key] = rows
    # Repeat every fixed service, socket unit, executable and endpoint before evidence is durable.
    _recheck_all(runner, units, executables, endpoints)
    for key, (_unit, _identity, path) in clients.items():
        _require_full_local_access(path, incus=(key == "incus"))
    stamp = now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    socket_rows = [{"endpoint_id": endpoint, "state": "present" if present else "absent",
                    "unit": "snap.lxd.daemon.unix.socket" if endpoint.startswith("lxd_") and endpoint == "lxd_snap" else
                    "incus.socket" if endpoint.startswith("incus_") else ""}
                   for _, (endpoint, present) in endpoints.items()]
    return {"schema_version": 1, "target_host": TARGET, "source_commit": source_commit,
            "captured_at_utc": stamp,
            "lxd_units": [units[u] for u in UNITS[:3]], "incus_units": [units[u] for u in UNITS[3:]],
            "lxd_executables": [executables[u] for u in ("lxd.service", "snap.lxd.daemon.service") if u in executables],
            "incus_executables": [executables["incus.service"]] if "incus.service" in executables else [],
            "sockets": socket_rows,
            "lxd_projects": client_projects.get("lxd", []),
            "incus_projects": client_projects.get("incus", []),
            "command_records": runner.records, "decision": "READ_ONLY_INVENTORY_COMPLETE"}


def _recheck_all(runner: Runner, initial_units: dict[str, dict[str, Any]],
                 initial_executables: dict[str, dict[str, Any]],
                 initial_endpoints: dict[str, tuple[str, bool]]) -> None:
    current_units = {unit: _systemctl_show(runner, unit) for unit in UNITS}
    if current_units != initial_units:
        raise InventoryError("RUNTIME_UNIT_DRIFT")
    current_executables: dict[str, tuple[str, str]] = {}
    for unit in ("lxd.service", "snap.lxd.daemon.service", "incus.service"):
        row = current_units[unit]
        if row["active_state"] == "active":
            current_executables[unit] = _resolve_executable(runner, row)
    expected_executables = {unit: (row["identity_id"], row["package"])
                            for unit, row in initial_executables.items()}
    if current_executables != expected_executables:
        raise InventoryError("RUNTIME_EXECUTABLE_DRIFT")
    current_endpoints = {path: _endpoint(runner, path, unit="") for path in SOCKETS}
    if current_endpoints != initial_endpoints:
        raise InventoryError("RUNTIME_ENDPOINT_DRIFT")


def _validate_artifact(artifact: dict[str, Any]) -> bytes:
    expected = {"schema_version", "target_host", "source_commit", "captured_at_utc", "lxd_units", "incus_units",
                "lxd_executables", "incus_executables", "sockets", "lxd_projects", "incus_projects", "command_records", "decision"}
    if set(artifact) != expected or artifact["decision"] != "READ_ONLY_INVENTORY_COMPLETE":
        raise InventoryError("ARTIFACT_SCHEMA_INVALID")
    if artifact["schema_version"] != 1 or artifact["target_host"] != TARGET or not HEX40.fullmatch(artifact["source_commit"]):
        raise InventoryError("ARTIFACT_IDENTITY_INVALID")
    unit_keys = {"unit", "load_state", "active_state", "sub_state", "unit_file_state", "main_pid"}
    for key, wanted in (("lxd_units", set(UNITS[:3])), ("incus_units", set(UNITS[3:]))):
        rows = artifact[key]
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise InventoryError("ARTIFACT_UNIT_SET_INVALID")
        if any(not isinstance(row.get("unit"), str) for row in rows):
            raise InventoryError("ARTIFACT_UNIT_SET_INVALID")
        if {row.get("unit") for row in rows} != wanted or len(rows) != len(wanted):
            raise InventoryError("ARTIFACT_UNIT_SET_INVALID")
        for row in rows:
            socket = row["unit"].endswith(".socket")
            if set(row) != unit_keys | ({"listen"} if socket else set()):
                raise InventoryError("ARTIFACT_UNIT_SCHEMA_INVALID")
            string_fields = ("unit", "load_state", "active_state", "sub_state", "unit_file_state")
            if any(not isinstance(row[field], str) for field in string_fields):
                raise InventoryError("ARTIFACT_UNIT_VALUE_INVALID")
            if not isinstance(row["main_pid"], int) or isinstance(row["main_pid"], bool) or row["main_pid"] < 0:
                raise InventoryError("ARTIFACT_UNIT_VALUE_INVALID")
            raw_state = {"LoadState": row["load_state"], "ActiveState": row["active_state"],
                         "SubState": row["sub_state"], "UnitFileState": row["unit_file_state"],
                         "MainPID": str(row["main_pid"])}
            if socket:
                if not isinstance(row["listen"], str):
                    raise InventoryError("ARTIFACT_UNIT_VALUE_INVALID")
                endpoint_path = {endpoint: path for path, endpoint in SOCKETS.items()}
                raw_state["Listen"] = endpoint_path.get(row["listen"], "") if row["listen"] else ""
            try:
                normalized = _unit_state(row["unit"], raw_state)
            except InventoryError as exc:
                raise InventoryError("ARTIFACT_UNIT_STATE_INVALID") from exc
            if normalized != row:
                raise InventoryError("ARTIFACT_UNIT_STATE_INVALID")
    exec_keys = {"unit", "main_pid", "identity_id", "package", "version"}
    for key, expected_ids in (("lxd_executables", {"lxd_snap", "lxd_system"}), ("incus_executables", {"incus_system"})):
        rows = artifact[key]
        if not isinstance(rows, list) or len(rows) > len(expected_ids):
            raise InventoryError("ARTIFACT_EXECUTABLES_INVALID")
        for row in rows:
            if set(row) != exec_keys or row["identity_id"] not in expected_ids or not isinstance(row["version"], str):
                raise InventoryError("ARTIFACT_EXECUTABLE_SCHEMA_INVALID")
            expected_unit = {"lxd_snap": "snap.lxd.daemon.service", "lxd_system": "lxd.service",
                             "incus_system": "incus.service"}[row["identity_id"]]
            if row["unit"] != expected_unit or not isinstance(row["main_pid"], int) or row["main_pid"] <= 0:
                raise InventoryError("ARTIFACT_EXECUTABLE_BINDING_INVALID")
            units = artifact["lxd_units"] if expected_unit.startswith(("lxd.", "snap.lxd.")) else artifact["incus_units"]
            match = next((unit for unit in units if unit["unit"] == expected_unit), None)
            if match is None or match["active_state"] != "active" or match["main_pid"] != row["main_pid"]:
                raise InventoryError("ARTIFACT_EXECUTABLE_BINDING_INVALID")
    executable_units = {row["unit"] for key in ("lxd_executables", "incus_executables") for row in artifact[key]}
    active_daemons = {row["unit"] for key in ("lxd_units", "incus_units") for row in artifact[key]
                      if not row["unit"].endswith(".socket") and row["active_state"] == "active"}
    if executable_units != active_daemons:
        raise InventoryError("ARTIFACT_EXECUTABLE_SET_INVALID")
    if not isinstance(artifact["sockets"], list):
        raise InventoryError("ARTIFACT_SOCKET_SCHEMA_INVALID")
    for row in artifact["sockets"]:
        if set(row) != {"endpoint_id", "state", "unit"} or row["endpoint_id"] not in set(SOCKETS.values()) or row["state"] not in {"present", "absent"} or row["unit"] not in {"", *UNITS}:
            raise InventoryError("ARTIFACT_SOCKET_SCHEMA_INVALID")
    if {row["endpoint_id"] for row in artifact["sockets"]} != set(SOCKETS.values()) or len(artifact["sockets"]) != len(SOCKETS):
        raise InventoryError("ARTIFACT_SOCKET_SET_INVALID")
    incus_socket = next(row for row in artifact["incus_units"] if row["unit"] == "incus.socket")
    if incus_socket["active_state"] == "active" and incus_socket["sub_state"] == "running":
        incus_service = next(row for row in artifact["incus_units"] if row["unit"] == "incus.service")
        incus_executable = next((row for row in artifact["incus_executables"]
                                 if row["unit"] == "incus.service"), None)
        endpoint = incus_socket["listen"]
        endpoint_row = next((row for row in artifact["sockets"] if row["endpoint_id"] == endpoint), None)
        if (incus_service["load_state"] != "loaded" or incus_service["active_state"] != "active"
                or incus_service["sub_state"] != "running" or incus_service["main_pid"] <= 0
                or incus_executable is None or incus_executable["identity_id"] != "incus_system"
                or incus_executable["main_pid"] != incus_service["main_pid"]
                or endpoint not in {"incus_run", "incus_var_lib"} or endpoint_row is None
                or endpoint_row["state"] != "present" or endpoint_row["unit"] != "incus.socket"):
            raise InventoryError("ARTIFACT_INCUS_SOCKET_BINDING_INVALID")
    command_ids = {"systemctl_show_unit", "systemctl_show_socket", "resolve_executable", "socket_exists",
                   "socket_type", "canonical_socket", "lxd_version", "lxd_project_list", "lxd_project_show",
                   "lxd_profile_list", "lxd_profile_show", "lxd_instance_list", "lxd_instance_config_show",
                   "lxd_instance_config_show_expanded", "lxd_network_list", "lxd_network_show", "lxd_storage_list", "lxd_storage_show",
                   "incus_version", "incus_project_list", "incus_project_show", "incus_profile_list",
                   "incus_profile_show", "incus_instance_list", "incus_instance_config_show",
                   "incus_instance_config_show_expanded", "incus_network_list", "incus_network_show",
                   "incus_storage_list", "incus_storage_show", "lxd_storage_volume_list",
                   "lxd_storage_volume_show", "incus_storage_volume_list", "incus_storage_volume_show"}
    if not isinstance(artifact["command_records"], list) or len(artifact["command_records"]) > MAX_COMMANDS:
        raise InventoryError("ARTIFACT_COMMANDS_INVALID")
    for row in artifact["command_records"]:
        if set(row) != {"command_id", "safe_args", "exit_status", "stdout_bytes", "stderr_bytes"} or row["command_id"] not in command_ids:
            raise InventoryError("ARTIFACT_COMMAND_SCHEMA_INVALID")
        if not isinstance(row["safe_args"], list) or any(not isinstance(v, str) or not (v in UNITS or v in SOCKETS.values() or NAME.fullmatch(v)) for v in row["safe_args"]):
            raise InventoryError("ARTIFACT_SAFE_ARGS_INVALID")
        if any(not isinstance(row[k], int) or row[k] < 0 for k in ("exit_status", "stdout_bytes", "stderr_bytes")):
            raise InventoryError("ARTIFACT_COMMAND_VALUE_INVALID")
    for family in ("lxd_projects", "incus_projects"):
        if not isinstance(artifact[family], list):
            raise InventoryError("ARTIFACT_RESOURCE_SCHEMA_INVALID")
        projects = artifact[family]
        project_names = [_name(project.get("project")) for project in projects if isinstance(project, dict)]
        if project_names != sorted(set(project_names)):
            raise InventoryError("ARTIFACT_PROJECT_ORDER_INVALID")
        for project in projects:
            if set(project) != {"project", "profiles", "instances", "networks", "pools"}:
                raise InventoryError("ARTIFACT_RESOURCE_SCHEMA_INVALID")
            _name(project["project"])
            for field, keys in (("profiles", {"name", "used_by", "devices"}),
                                ("instances", {"name", "status", "type", "profiles", "local_devices", "expanded_devices"}),
                                ("networks", {"name", "type", "used_by"}),
                                ("pools", {"name", "type", "used_by", "volumes"})):
                if not isinstance(project[field], list):
                    raise InventoryError("ARTIFACT_RESOURCE_SCHEMA_INVALID")
                names = [_name(resource.get("name")) for resource in project[field] if isinstance(resource, dict)]
                if names != sorted(set(names)):
                    raise InventoryError("ARTIFACT_RESOURCE_ORDER_INVALID")
                for resource in project[field]:
                    if set(resource) != keys:
                        raise InventoryError("ARTIFACT_RESOURCE_SCHEMA_INVALID")
                    _name(resource["name"])
                    if "used_by" in resource:
                        refs = resource["used_by"]
                        if not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs):
                            raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                        if refs != sorted(refs, key=lambda ref: (ref.get("kind", ""), ref.get("name", ""), ref.get("project", ""))):
                            raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                        identities = set()
                        for ref in refs:
                            if set(ref) != {"kind", "name", "project"} or ref["kind"] not in {
                                    "profiles", "instances", "networks", "storage-pools", "storage-volumes"}:
                                raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                            if ref["kind"] == "storage-volumes":
                                volume_identity = ref["name"].split("/")
                                if len(volume_identity) != 3:
                                    raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                                for part in volume_identity:
                                    _name(part)
                                ref_name = ref["name"]
                            else:
                                ref_name = _name(ref["name"])
                            identity = (ref["kind"], ref_name, _name(ref["project"]))
                            if identity in identities:
                                raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                            identities.add(identity)
                    if "volumes" in resource:
                        volumes = resource["volumes"]
                        if not isinstance(volumes, list) or volumes != sorted(
                                volumes, key=lambda volume: (volume.get("type", ""), volume.get("name", ""))):
                            raise InventoryError("ARTIFACT_VOLUME_INVALID")
                        volume_ids = set()
                        for volume in volumes:
                            if set(volume) != {"name", "type", "content_type", "used_by"}:
                                raise InventoryError("ARTIFACT_VOLUME_INVALID")
                            volume_identity = (_volume_type(volume["type"]), _name(volume["name"]))
                            if volume_identity in volume_ids:
                                raise InventoryError("ARTIFACT_VOLUME_INVALID")
                            volume_ids.add(volume_identity)
                            _volume_content_type(volume["content_type"])
                            refs = volume["used_by"]
                            if not isinstance(refs, list) or refs != sorted(
                                    refs, key=lambda ref: (ref.get("kind", ""), ref.get("name", ""), ref.get("project", ""))):
                                raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                            for ref in refs:
                                if set(ref) != {"kind", "name", "project"} or ref["kind"] not in {
                                        "profiles", "instances", "networks", "storage-pools", "storage-volumes"}:
                                    raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                                if ref["kind"] == "storage-volumes":
                                    parts = ref["name"].split("/")
                                    if len(parts) != 3:
                                        raise InventoryError("ARTIFACT_RESOURCE_LINK_INVALID")
                                    for part in parts:
                                        _name(part)
                                else:
                                    _name(ref["name"])
                                _name(ref["project"])
                    for device_field in ("devices", "local_devices", "expanded_devices"):
                        if device_field in resource:
                            devices = resource[device_field]
                            if not isinstance(devices, list) or devices != sorted(devices, key=lambda d: d.get("name", "")):
                                raise InventoryError("ARTIFACT_DEVICE_INVALID")
                            for device in devices:
                                if set(device) != {"name", "type"} or not NAME.fullmatch(device["name"]) or device["type"] not in {"disk", "nic", "proxy"}:
                                    raise InventoryError("ARTIFACT_DEVICE_INVALID")
        _validate_complete_ownership(projects)
    encoded = (json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
    if len(encoded) > MAX_ARTIFACT:
        raise InventoryError("ARTIFACT_LIMIT")
    forbidden = ("192.168.178.33", "/var/lib", "/var/run", "/run/incus", "/snap/lxd", "/proc/", "http://", "https://", "argv", "execstart", "environment")
    low = encoded.decode("ascii").lower()
    if any(term.lower() in low for term in forbidden):
        raise InventoryError("ARTIFACT_REDACTION_FAILED")
    return encoded


def _write_private(path: Path, raw: bytes) -> None:
    expected = ROOT / PRIVATE_REL
    if path.absolute() != expected.absolute():
        raise InventoryError("ARTIFACT_PATH_BLOCKED")
    if path.is_symlink() or path.exists():
        raise InventoryError("ARTIFACT_PATH_EXISTS")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        info = path.parent.stat(follow_symlinks=False)
    except OSError as exc:
        raise InventoryError("PRIVATE_DIRECTORY_UNVERIFIABLE") from exc
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise InventoryError("PRIVATE_DIRECTORY_UNSAFE")
    resolved = path.parent.resolve(strict=True)
    if resolved != path.parent or any(resolved == mount or mount in resolved.parents for mount in (Path("/mnt/c"), Path("/mnt/d"))):
        raise InventoryError("PRIVATE_PATH_UNSAFE")
    try:
        mountinfo = Path("/proc/self/mountinfo").read_text(encoding="utf-8")
        matches: list[tuple[int, str]] = []
        for line in mountinfo.splitlines():
            before, sep, after = line.partition(" - ")
            fields = before.split()
            fs_fields = after.split()
            if not sep or len(fields) < 5 or not fs_fields:
                raise ValueError
            mount = re.sub(r"\\(040|011|012|134)", lambda m: {"040": " ", "011": "\t", "012": "\n", "134": "\\"}[m.group(1)], fields[4])
            mount_path = Path(mount)
            if resolved == mount_path or mount_path in resolved.parents:
                matches.append((len(mount_path.parts), fs_fields[0]))
        if not matches or max(matches)[1] != "ext4" or len([x for x in matches if x[0] == max(matches)[0]]) != 1:
            raise InventoryError("PRIVATE_FILESYSTEM_UNSAFE")
    except InventoryError:
        raise
    except (OSError, ValueError, IndexError) as exc:
        raise InventoryError("PRIVATE_FILESYSTEM_UNVERIFIABLE") from exc
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def diagnose_snap_context(*, runner: Runner | None = None) -> str:
    """Return only a fixed context category; this never admits the service."""
    try:
        import importlib
        runner = runner or Runner()
        row = _systemctl_show(runner, "snap.lxd.daemon.service")
        if (row["load_state"], row["active_state"], row["sub_state"]) != ("loaded", "active", "running") or row["main_pid"] <= 0:
            return "UNKNOWN"
        name = f"{__package__}.native_lxd_snap_provenance" if __package__ else "native_lxd_snap_provenance"
        proof = importlib.import_module(name)
        reason = proof.diagnose_context(runner, row)
        allowed = {"EXECSTART_FORMAT_OR_TIME", "CONTROL_GROUP", "FRAGMENT_OR_HOOK", "DROPIN_OR_ENV_SETTING",
                   "ENVIRONMENT_FILE_SPEC", "DROPIN_CONTENT", "ENVIRONMENT_FILE_CONTENT", "UNKNOWN"}
        return reason if reason in allowed else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def diagnose_snap_dropin(*, runner: Runner | None = None) -> str:
    """Return a fixed structural category without admitting the service."""
    try:
        import importlib
        runner = runner or Runner()
        row = _systemctl_show(runner, "snap.lxd.daemon.service")
        if (row["load_state"], row["active_state"], row["sub_state"]) != ("loaded", "active", "running") or row["main_pid"] <= 0:
            return "UNKNOWN"
        name = f"{__package__}.native_lxd_snap_provenance" if __package__ else "native_lxd_snap_provenance"
        proof = importlib.import_module(name)
        reason = proof.diagnose_dropin(runner, row)
        allowed = {"SECTION_SHAPE", "UNKNOWN_DIRECTIVE", "DEPENDENCY_VARIANT", "UNKNOWN"}
        return reason if reason in allowed else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def diagnose_snap_generator_form(*, runner: Runner | None = None) -> str:
    """Return a fixed generator-form category without admitting the service."""
    try:
        import importlib
        runner = runner or Runner()
        row = _systemctl_show(runner, "snap.lxd.daemon.service")
        if (row["load_state"], row["active_state"], row["sub_state"]) != ("loaded", "active", "running") or row["main_pid"] <= 0:
            return "UNKNOWN"
        name = f"{__package__}.native_lxd_snap_provenance" if __package__ else "native_lxd_snap_provenance"
        proof = importlib.import_module(name)
        reason = proof.diagnose_generator_form(runner, row)
        return reason if reason in {"MATCH", "UNKNOWN"} else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if any(arg == "--diagnose-snap-generator-form" or arg.startswith("--diagnose-snap-generator-form=") for arg in arguments):
        reason = diagnose_snap_generator_form() if arguments == ["--diagnose-snap-generator-form"] else "UNKNOWN"
        print(json.dumps({"status": "BLOCKED_UNKNOWN", "reason": reason}, separators=(",", ":"), ensure_ascii=True))
        return 2
    if any(arg == "--diagnose-snap-dropin" or arg.startswith("--diagnose-snap-dropin=") for arg in arguments):
        reason = diagnose_snap_dropin() if arguments == ["--diagnose-snap-dropin"] else "UNKNOWN"
        print(json.dumps({"status": "BLOCKED_UNKNOWN", "reason": reason}, separators=(",", ":"), ensure_ascii=True))
        return 2
    if any(arg == "--diagnose-snap-context" or arg.startswith("--diagnose-snap-context=") for arg in arguments):
        reason = diagnose_snap_context() if arguments == ["--diagnose-snap-context"] else "UNKNOWN"
        print(json.dumps({"status": "BLOCKED_UNKNOWN", "reason": reason}, separators=(",", ":"), ensure_ascii=True))
        return 2
    if any(arg == "--diagnose-units" or arg.startswith("--diagnose-units=") for arg in arguments):
        if arguments != ["--diagnose-units"]:
            print("BLOCKED:DIAGNOSTIC_ARGUMENTS_INVALID", file=sys.stderr)
            return 2
        try:
            report, status = diagnose_units()
            print(json.dumps(report, separators=(",", ":"), ensure_ascii=True))
            return status
        except (InventoryError, OSError) as exc:
            code = str(exc) if isinstance(exc, InventoryError) else "DIAGNOSTIC_FAILED"
            print(f"BLOCKED:{code}", file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(arguments)
    try:
        artifact = capture(args.source_commit)
        raw = _validate_artifact(artifact)
        _write_private(args.output, raw)
        print("READ_ONLY_INVENTORY_COMPLETE")
        return 0
    except (InventoryError, OSError) as exc:
        code = str(exc) if isinstance(exc, InventoryError) else "ARTIFACT_WRITE_FAILED"
        print(f"BLOCKED:{code}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

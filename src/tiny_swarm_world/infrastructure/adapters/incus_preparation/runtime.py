"""Bounded local Incus/systemd execution and ordinary-account inspection."""
from __future__ import annotations

import grp
import json
import os
import pwd
import re
from typing import Any
from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.infrastructure.process.async_runner import AsyncProcessResult, run_async_process


# Incus 6.0 PostRun saves OIDC state when the user's config.yml exists, even
# under --force-local. The kernel-owned process directory has no config.yml
# and cannot persist client state or load ordinary user aliases.
LOCAL_INCUS_QUERY = ("/usr/bin/env", "INCUS_CONF=/proc/self", "incus", "--force-local")
LOCAL_INCUS = (*LOCAL_INCUS_QUERY, "--project", "default")


async def command(args: tuple[str, ...], timeout: float = 5.0) -> AsyncProcessResult:
    result = await run_async_process(args, timeout=timeout)
    if result.timed_out:
        raise IncusPreparationFailure("Incus command timed out; inspect observed state before retrying.", exit_code=124)
    if result.failure_hint:
        raise IncusPreparationFailure("Required command cannot be launched; inspect Incus/systemd/sudo installation.")
    return result


async def checked_command(args: tuple[str, ...], timeout: float = 5.0) -> str:
    result = await command(args, timeout)
    if result.returncode:
        raise IncusPreparationFailure("Incus preparation command failed; inspect permissions/systemd/resource state, then ./prepare_linux.sh --dry-run.")
    return result.stdout


async def query(path: str) -> Any:
    output = await checked_command((*LOCAL_INCUS_QUERY, "query", path))
    try:
        return json.loads(output)
    except (ValueError, TypeError):
        raise IncusPreparationFailure("Incus returned unreadable inventory; inspect Incus before retrying.") from None


async def json_command(args: tuple[str, ...]) -> list[dict[str, Any]]:
    output = await checked_command(args)
    try:
        data = json.loads(output)
    except ValueError:
        raise IncusPreparationFailure("Host networking inventory is unreadable; inspect iproute2.") from None
    return collection(data)


def collection(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise IncusPreparationFailure("Resource inventory is incomplete; inspect Incus/host networking.")
    return data


def named_resources(data: Any, kind: str) -> list[dict[str, Any]]:
    items = collection(data)
    names: set[str] = set()
    for item in items:
        name = item.get("name")
        if not isinstance(name, str) or not name or name in names:
            raise IncusPreparationFailure("Incus resource identities are unreadable or duplicated.")
        names.add(name)
        if kind == "instances":
            continue
        validate_resource_config(item, kind)
    return items


def validate_resource_config(item: dict[str, Any], kind: str) -> None:
    config = item.get("config")
    if not isinstance(config, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in config.items()):
        raise IncusPreparationFailure("Incus resource configuration is unreadable.")
    if kind == "profiles":
        devices = item.get("devices")
        if not isinstance(devices, dict) or any(not isinstance(device, dict) or any(not isinstance(value, str) for value in device.values()) for device in devices.values()):
            raise IncusPreparationFailure("Incus profile devices are unreadable.")


def account() -> tuple[str, bool, bool]:
    if os.geteuid() == 0:
        raise IncusPreparationFailure("Use an ordinary Linux account; never run whole preparation with sudo.")
    try:
        user = pwd.getpwuid(os.geteuid()).pw_name
        group = grp.getgrnam("incus-admin")
    except KeyError:
        raise IncusPreparationFailure("Ordinary account or incus-admin group is missing; inspect the Ubuntu Incus package.") from None
    if not re.fullmatch(r"[a-z_][a-z0-9_.-]*", user):
        raise IncusPreparationFailure("The invoking account cannot be resolved safely.")
    active = group.gr_gid in {*os.getgroups(), os.getegid()}
    persisted = active or user in group.gr_mem
    return user, active, persisted


async def daemon_state() -> dict[str, str]:
    output = await checked_command(("systemctl", "show", "incus.service", "--property=LoadState",
                                    "--property=ActiveState", "--property=UnitFileState"))
    values = {key: value for line in output.splitlines() if "=" in line
              for key, value in [line.split("=", 1)]}
    if (values.get("LoadState") != "loaded" or values.get("UnitFileState") == "masked"
            or values.get("ActiveState") not in {"active", "inactive"}):
        raise IncusPreparationFailure("Incus service is missing/masked/failed or changing; inspect systemctl status incus.service before retrying.")
    return values

"""Bounded argv execution; privileged reads never initialize a daemon."""
from __future__ import annotations

import json
from typing import Any

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.process.async_runner import run_async_process


TOOLS = {"iptables": "/usr/sbin/iptables", "iptables-save": "/usr/sbin/iptables-save",
         "ufw": "/usr/sbin/ufw", "nft": "/usr/sbin/nft", "modinfo": "/usr/sbin/modinfo",
         "modprobe": "/usr/sbin/modprobe", "sysctl": "/usr/sbin/sysctl", "systemctl": "/usr/bin/systemctl",
         "ss": "/usr/bin/ss", "getent": "/usr/bin/getent", "sudo": "/usr/bin/sudo"}
TOOLS["python3"] = "/usr/bin/python3"


async def command(args: tuple[str, ...], timeout: float = 5.0, *, permit_failure: bool = False) -> str:
    args = (TOOLS.get(args[0], args[0]), *args[1:])
    result = await run_async_process(args, timeout=timeout)
    if result.timed_out:
        raise NetworkPreparationFailure("Bounded network command timed out.", exit_code=124)
    if result.failure_hint or (result.returncode and not permit_failure):
        raise NetworkPreparationFailure("Network command unavailable or denied; inspect prepared packages and sudo -v.")
    if result.stderr and not permit_failure:
        raise NetworkPreparationFailure("Network inventory warned of incomplete or unsupported ownership; preserve state.")
    return result.stdout


async def privileged(args: tuple[str, ...], timeout: float = 5.0) -> str:
    executable = TOOLS.get(args[0])
    if executable is None:
        raise NetworkPreparationFailure("Unrecognized privileged network command.")
    return await command(("/usr/bin/sudo", "-n", "--", executable, *args[1:]), timeout)


async def json_command(args: tuple[str, ...], *, privileged_read: bool = False) -> Any:
    output = await (privileged(args) if privileged_read else command(args))
    try:
        return json.loads(output)
    except ValueError:
        raise NetworkPreparationFailure("Incomplete JSON network inventory.") from None

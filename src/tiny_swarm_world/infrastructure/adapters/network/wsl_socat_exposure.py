from __future__ import annotations

import asyncio
import shutil
from collections.abc import Awaitable, Callable

from tiny_swarm_world.application.ports.network import PortWslSocatExposure


ExecutableFinder = Callable[[str], str | None]
ProcessOperation = Callable[[str], Awaitable[bool]]


class WslSocatExposureAdapter(PortWslSocatExposure):
    """Typed WSL Socat boundary with injectable process operations.

    The default process operations are supplied by the infrastructure slice
    that owns command execution. Keeping them injected here makes the
    boundary independently testable without starting a host process.
    """

    def __init__(
        self,
        *,
        executable_finder: ExecutableFinder | None = None,
        process_probe: ProcessOperation | None = None,
        process_starter: ProcessOperation | None = None,
    ) -> None:
        self._executable_finder = executable_finder or shutil.which
        self._process_probe = process_probe or _process_exists
        self._process_starter = process_starter or _start_process

    async def is_available(self) -> bool:
        return self._executable_finder("socat") is not None

    async def process_exists(self, command: str) -> bool:
        return await self._process_probe(command)

    async def start(self, command: str) -> bool:
        return await self._process_starter(command)


async def _process_exists(pattern: str) -> bool:
    process = await asyncio.create_subprocess_exec(
        "pgrep",
        "-f",
        pattern,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return await process.wait() == 0


async def _start_process(command: str) -> bool:
    process = await asyncio.create_subprocess_exec(
        "sh",
        "-lc",
        f"nohup {command} >/dev/null 2>&1 &",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return await process.wait() == 0

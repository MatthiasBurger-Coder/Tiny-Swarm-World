from __future__ import annotations

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
        executable_finder: ExecutableFinder,
        process_probe: ProcessOperation,
        process_starter: ProcessOperation,
    ) -> None:
        self._executable_finder = executable_finder
        self._process_probe = process_probe
        self._process_starter = process_starter

    async def is_available(self) -> bool:
        return self._executable_finder("socat") is not None

    async def process_exists(self, command: str) -> bool:
        return await self._process_probe(command)

    async def start(self, command: str) -> bool:
        return await self._process_starter(command)

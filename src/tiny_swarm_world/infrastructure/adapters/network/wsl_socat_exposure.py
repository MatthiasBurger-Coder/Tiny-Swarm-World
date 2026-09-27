from __future__ import annotations

from tiny_swarm_world.application.ports.network.port_wsl_socat_exposure import SocatExposureError
from tiny_swarm_world.infrastructure.adapters.exceptions.operation_failure_mapping import process_failure, process_result_failure

import shutil
from collections.abc import Awaitable, Callable

from tiny_swarm_world.infrastructure.process.async_runner import run_async_process

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
        try:
            return await self._process_probe(command)
        except OSError as exc:
            raise SocatExposureError(process_failure(exc, "exposure.observe", "socat")) from None

    async def start(self, command: str) -> bool:
        try:
            return await self._process_starter(command)
        except OSError as exc:
            raise SocatExposureError(process_failure(exc, "exposure.start", "socat")) from None


async def _process_exists(pattern: str) -> bool:
    result = await run_async_process(("pgrep", "-f", pattern), discard_output=True)
    if result.timed_out or result.failure_hint or result.returncode not in (0, 1):
        raise SocatExposureError(process_result_failure("exposure.observe", "socat", timed_out=result.timed_out, failure_hint=result.failure_hint)) from None
    return result.returncode == 0


async def _start_process(command: str) -> bool:
    result = await run_async_process(
        ("sh", "-lc", f"nohup {command} >/dev/null 2>&1 &"), discard_output=True,
    )
    if result.timed_out or result.failure_hint or result.returncode != 0:
        raise SocatExposureError(process_result_failure("exposure.start", "socat", timed_out=result.timed_out, failure_hint=result.failure_hint)) from None
    return True

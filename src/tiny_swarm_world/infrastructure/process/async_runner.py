"""Shared bounded asyncio process execution and cancellation cleanup."""

from __future__ import annotations

import asyncio
import inspect
import os
import signal
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, cast

from tiny_swarm_world.infrastructure.process.runner import validate_timeout


@dataclass(frozen=True)
class AsyncProcessResult:
    returncode: int
    stdout: str = field(default="", repr=False)
    stderr: str = field(default="", repr=False)
    timed_out: bool = False
    failure_hint: str | None = None


def process_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else value


async def run_async_process(
    args: Sequence[str] | str,
    *,
    timeout: float = 60.0,
    shell: bool = False,
    discard_output: bool = False,
) -> AsyncProcessResult:
    """Return explicit process outcomes; propagate cancellation after child cleanup."""
    validate_timeout(timeout)
    if not args or (shell and not isinstance(args, str)) or (not shell and isinstance(args, str)):
        raise ValueError("Use a string for shell execution and argv for direct execution.")
    target = asyncio.subprocess.DEVNULL if discard_output else asyncio.subprocess.PIPE
    try:
        if shell:
            process = await asyncio.create_subprocess_shell(
                cast(str, args), stdout=target, stderr=target, start_new_session=True,
            )
        else:
            process = await asyncio.create_subprocess_exec(
                *args, stdout=target, stderr=target, start_new_session=True,
            )
    except FileNotFoundError:
        return AsyncProcessResult(127, failure_hint="launch_executable_missing")
    except PermissionError:
        return AsyncProcessResult(126, failure_hint="launch_permission_denied")
    except OSError:
        return AsyncProcessResult(-1, failure_hint="launch_os_error")
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        await terminate_async_process(process)
        return AsyncProcessResult(124, timed_out=True)
    except BaseException:
        await terminate_async_process(process)
        raise
    return AsyncProcessResult(
        process.returncode if process.returncode is not None else -1,
        process_text(stdout), process_text(stderr),
    )


async def terminate_async_process(process: asyncio.subprocess.Process) -> None:
    pid = getattr(process, "pid", None)
    if isinstance(pid, int) and hasattr(os, "killpg"):
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(pid, signal.SIGTERM)
        await _wait_for_exit(process, 5)
        # The session leader may exit before descendants; signal the original group.
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(pid, signal.SIGKILL)
    else:
        with suppress(ProcessLookupError):
            result = cast(Any, process).kill()
            if inspect.isawaitable(result):
                await result
    await _wait_for_exit(process, 5)


async def _wait_for_exit(process: asyncio.subprocess.Process, timeout: float) -> bool:
    try:
        async with asyncio.timeout(timeout):
            await process.wait()
        return True
    except asyncio.TimeoutError:
        return False

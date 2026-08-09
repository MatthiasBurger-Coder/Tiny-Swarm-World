"""Command transport primitives for the LXC node-provider adapter."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LxcNodeCommandResult:
    """Bounded result returned by one provider command invocation."""

    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class LxcNodeCommandRunner(Protocol):
    async def run(
        self,
        args: Sequence[str],
        timeout_seconds: float,
    ) -> LxcNodeCommandResult:
        """Run one provider command without exposing process details upstream."""
        pass


class AsyncLxcNodeCommandRunner:
    """Execute provider commands with bounded timeout and sanitized text."""

    async def run(
        self,
        args: Sequence[str],
        timeout_seconds: float,
    ) -> LxcNodeCommandResult:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            with suppress(ProcessLookupError):
                process.kill()
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(process.wait(), timeout=1.0)
            return LxcNodeCommandResult(returncode=124, timed_out=True)

        return LxcNodeCommandResult(
            returncode=process.returncode if process.returncode is not None else -1,
            stdout=safe_process_text(stdout),
            stderr=safe_process_text(stderr),
        )


def safe_process_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value

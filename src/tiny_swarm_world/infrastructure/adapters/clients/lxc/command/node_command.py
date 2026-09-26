"""Command transport primitives for the LXC node-provider adapter."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from tiny_swarm_world.infrastructure.process.async_runner import run_async_process


@dataclass(frozen=True)
class LxcNodeCommandResult:
    """Bounded result returned by one provider command invocation."""

    returncode: int
    stdout: str = field(default="", repr=False)
    stderr: str = field(default="", repr=False)
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
        result = await run_async_process(args, timeout=timeout_seconds)
        return LxcNodeCommandResult(
            result.returncode, result.stdout, result.stderr, result.timed_out,
        )


def safe_process_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value

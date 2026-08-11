from __future__ import annotations

import asyncio
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ReadinessRetry:
    """Validated retry metadata shared by asynchronous readiness services."""

    attempt: int
    max_attempts: int
    wait_seconds: float

    def __post_init__(self) -> None:
        if self.attempt < 1:
            raise ValueError("Readiness retry attempt must be positive.")
        if self.max_attempts < self.attempt:
            raise ValueError("Readiness retry attempt must not exceed its limit.")
        if self.wait_seconds < 0 or not math.isfinite(self.wait_seconds):
            raise ValueError("Readiness retry wait must be finite and non-negative.")


ReadinessWaitCallback = Callable[[ReadinessRetry], Awaitable[None] | None]


async def wait_for_readiness_retry(
    retry: ReadinessRetry,
    *,
    on_wait: ReadinessWaitCallback | None = None,
) -> None:
    """Publish an optional wait event, then yield without blocking the loop."""

    if on_wait is not None:
        callback_result = on_wait(retry)
        if callback_result is not None:
            await callback_result
    await asyncio.sleep(retry.wait_seconds)

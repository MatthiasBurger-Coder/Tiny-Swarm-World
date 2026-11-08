from __future__ import annotations

import asyncio


async def async_checkpoint() -> None:
    await asyncio.sleep(0)

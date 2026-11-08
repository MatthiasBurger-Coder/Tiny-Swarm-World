"""Keep operation authority until an already-started bounded adapter call settles."""
import asyncio


async def settled_blocking(operation, *args):
    """Retain journal ownership until an already started worker settles on cancellation."""
    worker = asyncio.create_task(asyncio.to_thread(operation, *args))
    try:
        return await asyncio.shield(worker)
    except asyncio.CancelledError:
        try:
            await _settle(worker)
        finally:
            raise


async def _settle(worker):
    """Repeated cancellation still waits for cleanup and is always re-raised."""
    try:
        await asyncio.shield(asyncio.gather(worker, return_exceptions=True))
    except asyncio.CancelledError:
        try:
            await _settle(worker)
        finally:
            raise

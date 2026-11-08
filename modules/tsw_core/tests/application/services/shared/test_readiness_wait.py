import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from tiny_swarm_world.application.services.shared import (
    ReadinessRetry,
    wait_for_readiness_retry,
)


class TestReadinessRetry(unittest.TestCase):
    def test_retry_metadata_rejects_invalid_attempts_and_waits(self):
        with self.assertRaises(ValueError):
            ReadinessRetry(attempt=0, max_attempts=1, wait_seconds=1)
        with self.assertRaises(ValueError):
            ReadinessRetry(attempt=2, max_attempts=1, wait_seconds=1)
        with self.assertRaises(ValueError):
            ReadinessRetry(attempt=1, max_attempts=1, wait_seconds=-1)

    def test_wait_publishes_callback_before_yielding(self):
        observed: list[str] = []

        async def callback(retry: ReadinessRetry) -> None:
            observed.append(f"callback:{retry.attempt}")

        async def run() -> None:
            with patch(
                "tiny_swarm_world.application.services.shared.readiness_wait.asyncio.sleep",
                new=AsyncMock(side_effect=lambda _: observed.append("sleep")),
            ):
                await wait_for_readiness_retry(
                    ReadinessRetry(attempt=1, max_attempts=2, wait_seconds=0),
                    on_wait=callback,
                )

        asyncio.run(run())
        self.assertEqual(["callback:1", "sleep"], observed)


if __name__ == "__main__":
    unittest.main()

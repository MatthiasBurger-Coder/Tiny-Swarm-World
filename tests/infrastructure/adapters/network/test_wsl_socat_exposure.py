import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

from tiny_swarm_world.infrastructure.adapters.network.wsl_socat_exposure import (
    WslSocatExposureAdapter,
)


class TestWslSocatExposureAdapter(unittest.TestCase):
    def test_boundary_delegates_typed_operations_without_live_commands(self):
        executable_finder = Mock(return_value="/usr/bin/socat")
        process_probe = AsyncMock(return_value=True)
        process_starter = AsyncMock(return_value=False)
        adapter = WslSocatExposureAdapter(
            executable_finder=executable_finder,
            process_probe=process_probe,
            process_starter=process_starter,
        )

        available = asyncio.run(adapter.is_available())
        existing = asyncio.run(adapter.process_exists("socat test"))
        started = asyncio.run(adapter.start("socat test"))

        self.assertTrue(available)
        self.assertTrue(existing)
        self.assertFalse(started)
        executable_finder.assert_called_once_with("socat")
        process_probe.assert_awaited_once_with("socat test")
        process_starter.assert_awaited_once_with("socat test")

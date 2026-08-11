import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import tiny_swarm_world.infrastructure.adapters.network.wsl_socat_exposure as exposure
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

    def test_default_process_probe_uses_pgrep_and_preserves_exit_semantics(self):
        process = SimpleNamespace(wait=AsyncMock(return_value=0))
        spawn = AsyncMock(return_value=process)

        with patch.object(exposure.asyncio, "create_subprocess_exec", spawn):
            result = asyncio.run(WslSocatExposureAdapter().process_exists("socat test"))

        self.assertTrue(result)
        spawn.assert_awaited_once_with(
            "pgrep",
            "-f",
            "socat test",
            stdout=exposure.asyncio.subprocess.DEVNULL,
            stderr=exposure.asyncio.subprocess.DEVNULL,
        )
        process.wait.assert_awaited_once_with()

    def test_default_process_probe_returns_false_for_missing_process(self):
        process = SimpleNamespace(wait=AsyncMock(return_value=1))

        with patch.object(
            exposure.asyncio,
            "create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ):
            result = asyncio.run(WslSocatExposureAdapter().process_exists("socat test"))

        self.assertFalse(result)

    def test_default_process_starter_uses_detached_shell_and_preserves_exit_semantics(self):
        process = SimpleNamespace(wait=AsyncMock(return_value=0))
        spawn = AsyncMock(return_value=process)

        with patch.object(exposure.asyncio, "create_subprocess_exec", spawn):
            result = asyncio.run(WslSocatExposureAdapter().start("socat test"))

        self.assertTrue(result)
        spawn.assert_awaited_once_with(
            "sh",
            "-lc",
            "nohup socat test >/dev/null 2>&1 &",
            stdout=exposure.asyncio.subprocess.DEVNULL,
            stderr=exposure.asyncio.subprocess.DEVNULL,
        )
        process.wait.assert_awaited_once_with()

    def test_default_process_starter_returns_false_for_nonzero_exit(self):
        process = SimpleNamespace(wait=AsyncMock(return_value=1))

        with patch.object(
            exposure.asyncio,
            "create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ):
            result = asyncio.run(WslSocatExposureAdapter().start("socat test"))

        self.assertFalse(result)

    def test_default_availability_uses_optional_socat_lookup(self):
        with patch.object(exposure.shutil, "which", return_value=None) as lookup:
            result = asyncio.run(WslSocatExposureAdapter().is_available())

        self.assertFalse(result)
        lookup.assert_called_once_with("socat")

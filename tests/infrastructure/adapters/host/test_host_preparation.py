import unittest
from pathlib import Path

from tiny_swarm_world.application.ports.host import WindowsCommandResult
from tiny_swarm_world.infrastructure.adapters.host import (
    NativeLinuxHostPreparation,
    WslHostPreparation,
)


class _Runner:
    def __init__(self, result: WindowsCommandResult, *additional: WindowsCommandResult) -> None:
        self.results = [result, *additional]
        self.actions: list[str] = []

    def run(self, action: str, **kwargs):
        self.actions.append(action)
        return self.results.pop(0)


class TestHostPreparationAdapters(unittest.TestCase):
    def test_native_linux_is_a_noop(self):
        adapter = NativeLinuxHostPreparation()

        result = adapter.prepare()

        self.assertTrue(result.succeeded)
        self.assertFalse(result.changed)
        self.assertEqual("not_selected", result.evidence["windows_command_runner"])

    def test_wsl_prepare_is_a_verified_noop_when_bridge_is_ready(self):
        runner = _Runner(WindowsCommandResult(0))
        adapter = WslHostPreparation(
            runner,
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
        )

        result = adapter.prepare()

        self.assertTrue(result.succeeded)
        self.assertFalse(result.changed)
        self.assertEqual(["verify"], runner.actions)

    def test_wsl_prepare_refreshes_only_after_read_only_drift(self):
        runner = _Runner(WindowsCommandResult(1), WindowsCommandResult(0))
        adapter = WslHostPreparation(
            runner,
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
        )

        result = adapter.prepare()

        self.assertTrue(result.succeeded)
        self.assertTrue(result.changed)
        self.assertEqual(["verify", "refresh"], runner.actions)

    def test_timeout_is_not_reported_as_functional_failure(self):
        runner = _Runner(WindowsCommandResult(None, timed_out=True))
        adapter = WslHostPreparation(
            runner,
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
        )

        result = adapter.verify()

        self.assertEqual("TIMED_OUT", result.status.value)
        self.assertFalse(result.succeeded)

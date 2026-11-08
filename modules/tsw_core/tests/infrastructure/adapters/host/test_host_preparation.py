import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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
    def test_native_linux_reports_all_required_controls_active(self):
        with TemporaryDirectory() as directory:
            proc_sys_root = Path(directory)
            self._write_kernel_control(
                proc_sys_root, "net/bridge/bridge-nf-call-iptables", "1"
            )
            self._write_kernel_control(
                proc_sys_root, "net/bridge/bridge-nf-call-ip6tables", "1"
            )
            self._write_kernel_control(proc_sys_root, "net/ipv4/ip_forward", "1")
            adapter = NativeLinuxHostPreparation(proc_sys_root=proc_sys_root)

            result = adapter.prepare()

        self.assertTrue(result.succeeded)
        self.assertFalse(result.changed)
        self.assertTrue(result.verified)
        self.assertEqual(
            {
                "net.bridge.bridge-nf-call-iptables": "active",
                "net.bridge.bridge-nf-call-ip6tables": "active",
                "net.ipv4.ip_forward": "active",
            },
            dict(result.evidence),
        )

    def test_native_linux_fails_closed_for_missing_control(self):
        with TemporaryDirectory() as directory:
            proc_sys_root = Path(directory)
            self._write_kernel_control(
                proc_sys_root, "net/bridge/bridge-nf-call-iptables", "1"
            )
            self._write_kernel_control(proc_sys_root, "net/ipv4/ip_forward", "1")

            result = NativeLinuxHostPreparation(proc_sys_root=proc_sys_root).verify()

        self.assertFalse(result.succeeded)
        self.assertFalse(result.verified)
        self.assertEqual(
            "missing", result.evidence["net.bridge.bridge-nf-call-ip6tables"]
        )

    def test_native_linux_fails_closed_for_disabled_control_without_leaking_value(self):
        with TemporaryDirectory() as directory:
            proc_sys_root = Path(directory)
            self._write_kernel_control(
                proc_sys_root, "net/bridge/bridge-nf-call-iptables", "1"
            )
            self._write_kernel_control(
                proc_sys_root, "net/bridge/bridge-nf-call-ip6tables", "1"
            )
            self._write_kernel_control(proc_sys_root, "net/ipv4/ip_forward", "sensitive")

            result = NativeLinuxHostPreparation(proc_sys_root=proc_sys_root).verify()

        self.assertFalse(result.succeeded)
        self.assertEqual("disabled", result.evidence["net.ipv4.ip_forward"])
        self.assertNotIn("sensitive", str(result.to_dict()))
        self.assertNotIn(directory, str(result.to_dict()))

    def test_native_linux_fails_closed_for_read_error(self):
        with TemporaryDirectory() as directory:
            proc_sys_root = Path(directory)
            for relative_path in (
                "net/bridge/bridge-nf-call-iptables",
                "net/bridge/bridge-nf-call-ip6tables",
                "net/ipv4/ip_forward",
            ):
                self._write_kernel_control(proc_sys_root, relative_path, "1")
            adapter = NativeLinuxHostPreparation(proc_sys_root=proc_sys_root)
            original_read_text = Path.read_text

            def read_text(path: Path, *args, **kwargs):
                if path.name == "ip_forward":
                    raise PermissionError("host-specific path must not escape")
                return original_read_text(path, *args, **kwargs)

            with patch.object(Path, "read_text", autospec=True, side_effect=read_text):
                result = adapter.verify()

        self.assertFalse(result.succeeded)
        self.assertEqual("read_error", result.evidence["net.ipv4.ip_forward"])
        self.assertNotIn("host-specific", str(result.to_dict()))

    def test_native_linux_cleanup_does_not_claim_operator_state_was_removed(self):
        result = NativeLinuxHostPreparation().cleanup()

        self.assertTrue(result.succeeded)
        self.assertFalse(result.changed)
        self.assertFalse(result.verified)
        self.assertEqual({}, dict(result.evidence))
        self.assertIn("left unchanged", result.message)

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

    @staticmethod
    def _write_kernel_control(root: Path, relative_path: str, value: str) -> None:
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

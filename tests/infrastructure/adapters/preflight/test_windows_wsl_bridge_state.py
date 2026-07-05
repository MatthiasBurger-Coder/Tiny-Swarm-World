import json
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state import (
    current_wsl_ipv4,
    windows_wsl_bridge_status,
)


class TestWindowsWslBridgeState(unittest.TestCase):
    def test_reports_invalid_json_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            state_path = _state_path(root)
            state_path.parent.mkdir(parents=True)
            state_path.write_text("{not-json", encoding="utf-8")

            status = windows_wsl_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("state_invalid", status.reason)
        self.assertEqual((80,), status.missing_ports)

    def test_reports_missing_generated_timestamp(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(root, {"wslIp": "172.20.0.2", "mappings": [_mapping(80)]})

            status = windows_wsl_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("generated_at_missing", status.reason)

    def test_reports_invalid_generated_timestamp(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": "not-a-date",
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                },
            )

            status = windows_wsl_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("generated_at_invalid", status.reason)

    def test_reports_stale_state_by_age(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": "2000-01-01T00:00:00Z",
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                },
            )

            status = windows_wsl_bridge_status(
                root,
                (80,),
                max_age_seconds=1,
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("state_stale_by_age", status.reason)
        self.assertIsNotNone(status.state_age_seconds)

    def test_reports_unavailable_current_wsl_ip(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                },
            )

            status = windows_wsl_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("wsl_ip_unavailable", status.reason)

    def test_ignores_invalid_mapping_entries(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [
                        {"listenPort": "invalid"},
                        {"listenPort": 0},
                        "not-a-mapping",
                        _mapping(80),
                    ],
                },
            )

            status = windows_wsl_bridge_status(
                root,
                (80, 10000),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("missing_ports", status.reason)
        self.assertEqual((80,), status.mapped_ports)
        self.assertEqual((10000,), status.missing_ports)

    def test_current_wsl_ipv4_reads_first_ipv4_from_hostname_output(self):
        completed = subprocess.CompletedProcess(
            ["hostname", "-I"],
            0,
            stdout="fe80::1 172.20.0.2 172.20.0.3\n",
            stderr="",
        )

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state.subprocess.run",
            return_value=completed,
        ):
            self.assertEqual("172.20.0.2", current_wsl_ipv4())

    def test_current_wsl_ipv4_returns_empty_on_timeout(self):
        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["hostname", "-I"], 5),
        ):
            self.assertEqual("", current_wsl_ipv4())


def _state_path(root: Path) -> Path:
    return root / "tools" / "windows" / ".tws-wsl-bridge.state.json"


def _write_state(root: Path, state: object) -> None:
    state_path = _state_path(root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state), encoding="utf-8")


def _mapping(port: int) -> dict[str, int]:
    return {"listenPort": port, "connectPort": port}


if __name__ == "__main__":
    unittest.main()

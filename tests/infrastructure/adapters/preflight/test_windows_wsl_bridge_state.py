import json
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state import (
    WINDOWS_WSL_BRIDGE_STATE,
    current_wsl_ipv4,
    windows_wsl_bridge_status,
)
from tiny_swarm_world.domain.preflight import WindowsWslBridgeStatus


TEST_BRIDGE_STATE_PATH = Path("tools/windows/.tws-wsl-bridge.state.json")


class TestWindowsWslBridgeState(unittest.TestCase):
    def test_default_state_path_is_protected_windows_program_data(self):
        self.assertEqual(
            Path("/mnt/c/ProgramData/TinySwarmWorld/WslBridge/bridge-state.json"),
            WINDOWS_WSL_BRIDGE_STATE,
        )

    def test_absolute_program_data_path_does_not_fall_back_to_checkout_state(self):
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
                state_path=Path("/definitely-missing/bridge-state.json"),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("state_missing", status.reason)

    def test_reports_invalid_json_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            state_path = _state_path(root)
            state_path.parent.mkdir(parents=True)
            state_path.write_text("{not-json", encoding="utf-8")

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("state_invalid", status.reason)
        self.assertEqual((80,), status.missing_ports)

    def test_reports_non_mapping_state_as_invalid(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(root, ["not", "a", "mapping"])

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("state_invalid", status.reason)

    def test_reports_missing_generated_timestamp(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(root, {"wslIp": "172.20.0.2", "mappings": [_mapping(80)]})

            status = _test_bridge_status(
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

            status = _test_bridge_status(
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

            status = _test_bridge_status(
                root,
                (80,),
                max_age_seconds=1,
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("state_stale_by_age", status.reason)
        self.assertIsNotNone(status.state_age_seconds)

    def test_accepts_naive_generated_timestamp_as_utc(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).replace(tzinfo=None).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                },
            )

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertTrue(status.prepared)

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

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("wsl_ip_unavailable", status.reason)

    def test_reports_missing_ports_when_mappings_are_not_a_list(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": "not-a-list",
                },
            )

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("missing_ports", status.reason)
        self.assertEqual((), status.mapped_ports)

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

            status = _test_bridge_status(
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

    def test_reports_legacy_state_without_discovery_agent_contract(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            state_path = _state_path(root)
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "generatedAt": datetime.now(UTC).isoformat(),
                        "wslIp": "172.20.0.2",
                        "mappings": [_mapping(80)],
                    }
                ),
                encoding="utf-8",
            )

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("agent_contract_missing", status.reason)

    def test_rejects_state_without_owned_service_and_bundle_identity(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            state = {
                "generatedAt": datetime.now(UTC).isoformat(),
                "wslIp": "172.20.0.2",
                "mappings": [_mapping(80)],
            }
            _write_state(root, state)
            state.pop("serviceName")
            state.pop("bundleId")
            state.pop("bundleHashes")
            _state_path(root).write_text(json.dumps(state), encoding="utf-8")

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("agent_contract_missing", status.reason)

    def test_reports_degraded_discovery_agent(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                    "agentStatus": "degraded",
                },
            )

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("agent_not_ready", status.reason)

    def test_rejects_legacy_scheduled_discovery_agent_mode(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                    "agentMode": "scheduled-discovery",
                },
            )

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
            )

        self.assertFalse(status.prepared)
        self.assertEqual("agent_contract_missing", status.reason)

    def test_reconcile_in_progress_retries_until_ready_state_is_observed(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                    "agentStatus": "degraded",
                    "driftReasons": ["reconcile_in_progress"],
                },
            )

            def finish_reconcile(_seconds: float) -> None:
                _write_state(
                    root,
                    {
                        "generatedAt": datetime.now(UTC).isoformat(),
                        "wslIp": "172.20.0.2",
                        "mappings": [_mapping(80)],
                        "agentStatus": "ready",
                        "driftReasons": [],
                    },
                )

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
                reconcile_retry_attempts=1,
                reconcile_retry_interval_seconds=0,
                sleep=finish_reconcile,
            )

        self.assertTrue(status.prepared)
        self.assertEqual("prepared", status.reason)

    def test_reconcile_in_progress_fails_closed_after_bounded_retries(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                    "agentStatus": "degraded",
                    "driftReasons": ["reconcile_in_progress"],
                },
            )
            sleep_calls: list[float] = []

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
                reconcile_retry_attempts=2,
                reconcile_retry_interval_seconds=0.25,
                sleep=sleep_calls.append,
            )

        self.assertFalse(status.prepared)
        self.assertEqual("agent_not_ready", status.reason)
        self.assertEqual([0.25, 0.25], sleep_calls)

    def test_reconcile_in_progress_then_persistent_invalid_or_missing_state_fails_closed(self):
        for terminal_reason in ("state_invalid", "state_missing"):
            with self.subTest(terminal_reason=terminal_reason):
                with tempfile.TemporaryDirectory() as tempdir:
                    root = Path(tempdir)
                    _write_state(
                        root,
                        {
                            "generatedAt": datetime.now(UTC).isoformat(),
                            "wslIp": "172.20.0.2",
                            "mappings": [_mapping(80)],
                            "agentStatus": "degraded",
                            "driftReasons": ["reconcile_in_progress"],
                        },
                    )
                    sleep_calls: list[float] = []

                    def replace_with_terminal_state(seconds: float) -> None:
                        sleep_calls.append(seconds)
                        state_path = _state_path(root)
                        if terminal_reason == "state_missing":
                            state_path.unlink(missing_ok=True)
                        else:
                            state_path.write_text("{not-json", encoding="utf-8")

                    status = _test_bridge_status(
                        root,
                        (80,),
                        current_wsl_ipv4=lambda: "172.20.0.2",
                        reconcile_retry_attempts=2,
                        reconcile_retry_interval_seconds=0.25,
                        sleep=replace_with_terminal_state,
                    )

                self.assertFalse(status.prepared)
                self.assertEqual(terminal_reason, status.reason)
                self.assertEqual([0.25, 0.25], sleep_calls)

    def test_reconcile_marker_mixed_with_real_drift_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            _write_state(
                root,
                {
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "wslIp": "172.20.0.2",
                    "mappings": [_mapping(80)],
                    "agentStatus": "degraded",
                    "driftReasons": ["reconcile_in_progress", "portproxy_drift"],
                },
            )

            status = _test_bridge_status(
                root,
                (80,),
                current_wsl_ipv4=lambda: "172.20.0.2",
                reconcile_retry_attempts=1,
                sleep=lambda _seconds: self.fail("real drift must not be retried"),
            )

        self.assertFalse(status.prepared)
        self.assertEqual("agent_not_ready", status.reason)

    def test_current_wsl_ipv4_returns_empty_on_nonzero_exit(self):
        completed = subprocess.CompletedProcess(
            ["hostname", "-I"],
            1,
            stdout="172.20.0.2\n",
            stderr="failed",
        )

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state.subprocess.run",
            return_value=completed,
        ):
            self.assertEqual("", current_wsl_ipv4())

    def test_current_wsl_ipv4_returns_empty_without_ipv4_output(self):
        completed = subprocess.CompletedProcess(
            ["hostname", "-I"],
            0,
            stdout="fe80::1\n",
            stderr="",
        )

        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state.subprocess.run",
            return_value=completed,
        ):
            self.assertEqual("", current_wsl_ipv4())

    def test_current_wsl_ipv4_returns_empty_on_timeout(self):
        with patch(
            "tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["hostname", "-I"], 5),
        ):
            self.assertEqual("", current_wsl_ipv4())

    def test_windows_wsl_bridge_status_stale_property_marks_repair_reasons(self):
        status = WindowsWslBridgeStatus(
            prepared=False,
            reason="generated_at_missing",
            state_path="tools/windows/.tws-wsl-bridge.state.json",
        )

        self.assertTrue(status.stale)


def _test_bridge_status(root: Path, expected_ports: tuple[int, ...], **kwargs):
    return windows_wsl_bridge_status(
        root,
        expected_ports,
        state_path=TEST_BRIDGE_STATE_PATH,
        **kwargs,
    )


def _state_path(root: Path) -> Path:
    return root / TEST_BRIDGE_STATE_PATH


def _write_state(root: Path, state: object) -> None:
    state_path = _state_path(root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(state, dict):
        state.setdefault("contractVersion", 2)
        state.setdefault("agentMode", "windows-service")
        state.setdefault("agentStatus", "ready")
        state.setdefault("serviceName", "TinySwarmWorldWslBridge")
        state.setdefault("bundleId", "B" * 64)
        state.setdefault(
            "bundleHashes",
            {
                "ports.yaml": "A" * 64,
                "tws-wsl-bridge-service.ps1": "A" * 64,
                "tws-wsl-bridge.config.json": "A" * 64,
                "tws-wsl-bridge.ps1": "A" * 64,
            },
        )
    state_path.write_text(json.dumps(state), encoding="utf-8")


def _mapping(port: int) -> dict[str, int]:
    return {"listenPort": port, "connectPort": port}


if __name__ == "__main__":
    unittest.main()

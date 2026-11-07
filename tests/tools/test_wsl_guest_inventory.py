"""WSL preservation projection and unchanged native-runner proof boundaries."""
from __future__ import annotations

import copy
import json
import unittest
from typing import Any
from unittest.mock import patch

from tests.tools import test_native_runtime_inventory as native_fixtures
from tools.linux.qualification import wsl_guest_inventory as guest


class WslGuestInventoryTests(unittest.TestCase):
    def test_restart_admission_respects_expanded_autostart_and_actual_detail_status(self) -> None:
        def dto(config: dict[str, Any]) -> dict[str, Any]:
            return {"status": "Stopped", "status_code": 102, "expanded_config": config}
        valid: tuple[dict[str, Any], ...] = ({}, {"boot.autostart": "false"}, {"volatile.last_state.power": "STOPPED"},
                       {"boot.autostart": "", "volatile.last_state.power": "STOPPED"},
                       {"boot.autostart": "false", "volatile.last_state.power": "RUNNING"})
        for config in valid:
            guest.assert_restart_safe(dto(config))
        invalid: tuple[dict[str, Any], ...] = (
            {"boot.autostart": "true"}, {"boot.autostart": True}, {"boot.autostart": False},
            {"boot.autostart": None}, {"boot.autostart": "FALSE"}, {"boot.autostart": "false\n"},
            {"boot.autostart": "0"}, {"volatile.last_state.power": "RUNNING"},
            {"volatile.last_state.power": ""}, {"volatile.last_state.power": None},
            {"boot.autostart": "false", "volatile.last_state.power": False},
        )
        for config in invalid:
            with self.subTest(config=config), self.assertRaisesRegex(guest.native.InventoryError, "GUEST_AUTOSTART_UNSAFE"):
                guest.assert_restart_safe(dto(config))
        status_changes: tuple[dict[str, Any], ...] = ({"status": "Running"}, {"status_code": True}, {"status_code": "102"})
        for values in status_changes:
            row = dto({})
            row.update(values)
            with self.assertRaisesRegex(guest.native.InventoryError, "GUEST_DETAIL_NOT_STOPPED"):
                guest.assert_restart_safe(row)

    def test_actual_native_client_flow_keeps_query_order_and_detail_guards(self) -> None:
        observed_runner = native_fixtures.NativeRuntimeInventoryTests._InventoryRunner()
        baseline = native_fixtures.NativeRuntimeInventoryTests._InventoryRunner()
        observer = guest.DetailObserver()
        for runner in (observed_runner, baseline):
            for command in ("incus_instance_config_show", "incus_instance_config_show_expanded"):
                runner.detail_overrides[command] = {"status": "Stopped", "status_code": 102}
        with patch.object(guest.native.Runner, "run", side_effect=observed_runner.run):
            observed = guest.native._inventory_client(
                observer, "incus_system", "/run/incus/unix.socket", incus=True,
                before_query=lambda: None, image_aware=True)
        expected = guest.native._inventory_client(
            baseline, "incus_system", "/run/incus/unix.socket", incus=True,
            before_query=lambda: None, image_aware=True)
        self.assertEqual(observed, expected)
        self.assertEqual(observed_runner.calls, baseline.calls)
        self.assertTrue(any(key[0] == "incus_instance_config_show" for key in observer.details))
        self.assertTrue(any(key[0] == "incus_storage_volume_show" for key in observer.details))
        self.assertTrue(any(key[0] == "incus_profile_show" for key in observer.details))

    def artifact(self) -> dict[str, Any]:
        return {
            "schema_version": 6, "source_commit": "a" * 40, "target_host": "NATIVE_HOST_MUST_NOT_ESCAPE",
            "captured_at_utc": "VOLATILE_TIME", "lxd_units": [{"main_pid": 999}], "incus_units": [],
            "lxd_executables": [], "incus_executables": [],
            "lxd_admission": None, "lxd_pools": [], "lxd_projects": [],
            "incus_admission": {"server": "incus", "server_clustered": False},
            "incus_pools": [], "incus_projects": [{"project": "default",
                "instances": [{"name": "preserved", "status": "Stopped"}]}],
            "command_records": [{"command_id": "incus_instance_config_show",
                                  "safe_args": ["preserved", "default"]}],
        }

    def test_projection_drops_native_identity_and_runtime_but_preserves_graph(self) -> None:
        artifact = self.artifact()
        details: dict[tuple[str, ...], str] = {("incus_instance_config_show", "preserved", "default"): "b" * 64}
        with patch.object(guest.native, "_validate_artifact") as validator:
            result = guest.project(artifact, details)
            validator.assert_called_once_with(artifact)
            changed_runtime = copy.deepcopy(artifact)
            changed_runtime["lxd_units"] = [{"main_pid": 123}]
            changed_runtime["captured_at_utc"] = "OTHER_TIME"
            self.assertEqual(result, guest.project(changed_runtime, details))
            changed_graph = copy.deepcopy(artifact)
            changed_graph["incus_projects"][0]["instances"][0]["name"] = "changed"
            self.assertNotEqual(result["graph_sha256"], guest.project(changed_graph, details)["graph_sha256"])
        self.assertEqual(result["scope"], "WSL_GUEST_PRESERVATION_ONLY")
        self.assertNotIn("NATIVE_HOST_MUST_NOT_ESCAPE", json.dumps(result))
        self.assertNotIn("preserved", json.dumps(result))

    def test_any_running_family_or_missing_detail_proof_refuses(self) -> None:
        artifact = self.artifact()
        details: dict[tuple[str, ...], str] = {("incus_instance_config_show", "preserved", "default"): "b" * 64}
        with patch.object(guest.native, "_validate_artifact"):
            with self.assertRaisesRegex(guest.native.InventoryError, "GUEST_DETAIL_PROOF_INCOMPLETE"):
                guest.project(artifact, {})
            for family in ("incus", "lxd"):
                changed = copy.deepcopy(artifact)
                changed[family + "_projects"] = [{"instances": [{"status": "Running"}]}]
                with self.assertRaisesRegex(guest.native.InventoryError, "GUEST_RUNNING_INSTANCE_BLOCKED"):
                    guest.project(changed, details)

    def test_structural_validation_failure_is_not_relabelled_as_wsl_success(self) -> None:
        with patch.object(guest.native, "_validate_artifact", side_effect=guest.native.InventoryError("BAD_GRAPH")):
            with self.assertRaisesRegex(guest.native.InventoryError, "BAD_GRAPH"):
                guest.project(self.artifact(), {})

    def test_image_unaware_schema_cannot_claim_complete_guest_preservation(self) -> None:
        old = self.artifact()
        old["schema_version"] = 5
        with patch.object(guest.native, "_validate_artifact") as validator:
            with self.assertRaisesRegex(guest.native.InventoryError, "GUEST_IMAGE_AWARE_SCHEMA_REQUIRED"):
                guest.project(old, {})
            validator.assert_not_called()

    def test_image_observer_preserves_all_metadata_except_deliberate_last_use(self) -> None:
        observer = guest.DetailObserver()
        metadata: dict[str, Any] = {"fingerprint": "a" * 64, "last_used_at": "FIRST",
                                    "properties": {"user.note": "PRIVATE_IMAGE_CANARY"}, "aliases": []}
        def response(*_args: Any, **_kwargs: Any) -> tuple[int, bytes, bytes]:
            return 0, json.dumps({"metadata": metadata}).encode(), b""
        with patch.object(guest.native.Runner, "run", side_effect=response):
            observer.run(["/usr/bin/incus"], command_id="incus_image_show", safe_args=["a" * 64, "default"])
            metadata["last_used_at"] = "SECOND"
            observer.run(["/usr/bin/incus"], command_id="incus_image_show", safe_args=["a" * 64, "default"])
            metadata["properties"] = {"user.note": "CHANGED"}
            with self.assertRaisesRegex(guest.native.InventoryError, "GUEST_DETAIL_DRIFT"):
                observer.run(["/usr/bin/incus"], command_id="incus_image_show", safe_args=["a" * 64, "default"])
        self.assertNotIn("PRIVATE_IMAGE_CANARY", json.dumps(list(observer.details.values())))

    def test_detail_observer_forwards_runner_and_detects_raw_config_drift(self) -> None:
        observer = guest.DetailObserver()
        dto: dict[str, Any] = {"name": "preserved", "config": {"volatile.uuid": "PRIVATE_UUID_CANARY"},
               "devices": {}, "expanded_config": {}, "expanded_devices": {},
               "status": "Stopped", "status_code": 102, "last_used_at": "FIRST"}
        args = ["/usr/bin/incus", "--force-local", "query", "--request", "GET", "--raw", "/1.0/instances/preserved?project=default"]
        keywords: dict[str, Any] = {"command_id": "incus_instance_config_show", "safe_args": ["preserved", "default"],
                    "env": {"LC_ALL": "C", "PATH": "/usr/bin:/bin", "INCUS_SOCKET": "/run/incus/unix.socket"}}
        def response() -> tuple[int, bytes, bytes]:
            return 0, json.dumps({"metadata": dto}).encode(), b""
        with patch.object(guest.native.Runner, "run", side_effect=lambda *_a, **_k: response()) as original:
            observer.run(args, **keywords)
            self.assertEqual(original.call_args.kwargs["env"], keywords["env"])
            self.assertEqual(original.call_args.kwargs["safe_args"], keywords["safe_args"])
            dto["last_used_at"] = "SECOND"
            observer.run(args, **keywords)
            dto["config"] = {"volatile.uuid": "OTHER_UUID"}
            with self.assertRaisesRegex(guest.native.InventoryError, "GUEST_DETAIL_DRIFT"):
                observer.run(args, **keywords)
        self.assertNotIn("PRIVATE_UUID_CANARY", json.dumps(list(observer.details.values())))

    def test_failed_runner_does_not_fabricate_detail_observation(self) -> None:
        observer = guest.DetailObserver()
        with patch.object(guest.native.Runner, "run", side_effect=guest.native.InventoryError("GUARD_FAILED")):
            with self.assertRaisesRegex(guest.native.InventoryError, "GUARD_FAILED"):
                observer.run(["/usr/bin/incus"], command_id="incus_profile_show", safe_args=["default", "default"])
        self.assertEqual(observer.details, {})

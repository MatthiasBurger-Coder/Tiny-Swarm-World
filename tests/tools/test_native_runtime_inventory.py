"""Regression tests for the fail-closed native runtime inventory."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from tools.qualification import native_runtime_inventory as inventory


class NativeRuntimeInventoryTests(unittest.TestCase):
    class _InventoryRunner(inventory.Runner):
        def __init__(self):
            self.calls: list[tuple[list[str], dict[str, str], str]] = []
            self.records: list[dict[str, Any]] = []
            self.list_rows: dict[str, list[dict[str, Any]]] = {}
            self.detail_profiles = ["bravo"]
            self.instance_network = "net"
            self.instance_pool = "pool"
            self.instance_custom_source: str | None = None
            self.project_used_by: list[str] = [
                "/1.0/profiles/bravo?project=alpha", "/1.0/profiles/zeta?project=alpha",
                "/1.0/instances/web?project=alpha", "/1.0/networks/net?project=alpha",
                "/1.0/storage-pools/pool/volumes/container/web?project=alpha",
            ]
            self.network_used_by = ["/1.0/profiles/bravo?project=alpha", "/1.0/instances/web?project=alpha"]
            self.volume_used_by = ["/1.0/instances/web?project=alpha"]
            self.pool_used_by = ["/1.0/profiles/bravo?project=alpha", "/1.0/instances/web?project=alpha",
                                 "/1.0/storage-pools/pool/volumes/container/web?project=alpha"]
            self.volume_owner_project = "alpha"

        @staticmethod
        def _json(value: Any) -> bytes:
            import json
            return json.dumps(value).encode()

        def run(self, argv: list[str], *, env: dict[str, str] | None = None, command_id: str,
                safe_args: list[str] | None = None, expected: set[int] | None = None) -> tuple[int, bytes, bytes]:
            self.calls.append((list(argv), dict(env or {}), command_id))
            suffix = argv[2:]
            if suffix == ["version"]:
                out = b"Client version: 6.0\nServer version: 6.0.5\n"
            elif suffix == ["project", "list", "--format", "json"]:
                out = self._json(self.list_rows.get("projects", [{"name": "alpha", "description": "", "config": {},
                                                                    "used_by": self.project_used_by}]))
            elif suffix == ["project", "show", "alpha", "--format", "json"]:
                out = self._json({"name": "alpha", "config": {}, "used_by": self.project_used_by})
            elif suffix == ["profile", "list", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("profiles", [
                    {"name": "zeta", "project": "alpha", "description": "", "config": {}, "devices": {}, "used_by": []},
                    {"name": "bravo", "project": "alpha", "description": "", "config": {}, "devices": {},
                     "used_by": ["/1.0/instances/web?project=alpha"]},
                ]))
            elif suffix == ["list", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("instances", [{
                    "name": "web", "project": "alpha", "architecture": "x86_64", "config": {}, "devices": {},
                    "ephemeral": False, "expanded_config": {}, "expanded_devices": {}, "profiles": ["bravo"],
                    "stateful": False, "status": "Running", "status_code": 103, "type": "container",
                    "location": "none", "description": "", "created_at": "2026-10-01T00:00:00Z",
                    "last_used_at": "2026-10-02T00:00:00Z",
                }]))
            elif suffix == ["network", "list", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("networks", [{"name": "net", "project": "alpha", "type": "bridge",
                    "managed": True, "status": "Created", "config": {}, "description": "",
                    "used_by": self.network_used_by, "locations": []}]))
            elif suffix == ["storage", "list", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("pools", [{"name": "pool", "project": "alpha", "driver": "dir",
                    "config": {}, "description": "", "used_by": self.pool_used_by,
                    "status": "Created", "locations": []}]))
            elif len(suffix) >= 3 and suffix[0] == "profile" and suffix[1] == "show" and suffix[3:] == ["--project", "alpha", "--format", "json"]:
                profile = {"name": suffix[2], "project": "alpha", "description": "", "config": {},
                           "devices": ({"root": {"type": "disk", "path": "/", "pool": "pool"},
                                        "eth0": {"type": "nic", "network": "net"}}
                                       if suffix[2] == "bravo" else {}),
                           "used_by": ["/1.0/instances/web?project=alpha"] if suffix[2] == "bravo" else []}
                out = self._json(profile)
            elif suffix == ["config", "show", "web", "--project", "alpha", "--format", "json"]:
                devices = {}
                if self.instance_custom_source is not None:
                    devices["custom"] = {"type": "disk", "path": "/data", "pool": self.instance_pool,
                                          "source": self.instance_custom_source}
                out = self._json({"name": "web", "project": "alpha", "config": {},
                                  "devices": devices,
                                  "ephemeral": False, "profiles": self.detail_profiles, "stateful": False})
            elif suffix == ["config", "show", "web", "--project", "alpha", "--format", "json", "--expanded"]:
                out = self._json({"name": "web", "project": "alpha", "config": {},
                                  "devices": {"root": {"type": "disk", "path": "/", "pool": self.instance_pool},
                                              "eth0": {"type": "nic", "network": self.instance_network}},
                                  "ephemeral": False, "profiles": self.detail_profiles, "stateful": False})
            elif suffix == ["network", "show", "net", "--project", "alpha", "--format", "json"]:
                out = self._json({"name": "net", "project": "alpha", "type": "bridge", "managed": True,
                                  "config": {}, "used_by": self.network_used_by})
            elif suffix == ["storage", "show", "pool", "--project", "alpha", "--format", "json"]:
                out = self._json({"name": "pool", "project": "alpha", "driver": "dir", "config": {},
                                  "used_by": self.pool_used_by})
            elif suffix == ["storage", "volume", "list", "pool", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("volumes", [{"name": "web", "type": "container",
                    "content_type": "filesystem", "project": "alpha", "description": "", "config": {"size": "10GiB"},
                    "created_at": "2026-10-01T00:00:00Z", "used_by": self.volume_used_by, "location": "none"}]))
            elif suffix == ["storage", "volume", "show", "pool", "container/web", "--project", "alpha", "--format", "json"]:
                out = self._json({"name": "web", "type": "container", "content_type": "filesystem",
                                  "project": self.volume_owner_project, "description": "", "config": {"size": "10GiB"},
                                  "created_at": "2026-10-01T00:00:00Z", "used_by": self.volume_used_by, "location": "none"})
            else:
                raise AssertionError(f"unexpected inventory argv: {argv}")
            self.records.append({"command_id": command_id, "safe_args": safe_args or [], "exit_status": 0,
                                 "stdout_bytes": len(out), "stderr_bytes": 0})
            return 0, out, b""

    class _Selector:
        def __init__(self) -> None:
            self.items: dict[Any, str] = {}

        def register(self, fileobj: Any, _events: int, data: str) -> None:
            self.items[fileobj] = data

        def get_map(self) -> dict[Any, str]:
            return self.items

        def select(self, _timeout: float) -> list[tuple[Any, int]]:
            return [(type("Key", (), {"fileobj": obj, "fd": obj.fileno(), "data": data})(), 1)
                    for obj, data in list(self.items.items())]

        def unregister(self, fileobj: Any) -> None:
            self.items.pop(fileobj)

    @staticmethod
    def _valid_artifact(command_records=None):
        units = []
        for unit in inventory.UNITS:
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive",
                   "sub_state": "dead", "unit_file_state": "", "main_pid": 0}
            if unit.endswith(".socket"):
                row["listen"] = ""
            units.append(row)
        return {"schema_version": 1, "target_host": inventory.TARGET, "source_commit": "a" * 40,
                "captured_at_utc": "2026-01-01T00:00:00Z", "lxd_units": units[:3], "incus_units": units[3:],
                "lxd_executables": [], "incus_executables": [],
                "sockets": [{"endpoint_id": endpoint, "state": "absent", "unit": ""}
                            for endpoint in inventory.SOCKETS.values()],
                "lxd_projects": [], "incus_projects": [], "command_records": command_records or [],
                "decision": "READ_ONLY_INVENTORY_COMPLETE"}

    class _UnitDiagnosticRunner:
        def __init__(self, unit_rows: dict[str, list[dict[str, Any]]], executable_paths: dict[int, bytes],
                     *, failure: inventory.InventoryError | None = None):
            self.unit_rows = unit_rows
            self.executable_paths = executable_paths
            self.failure = failure
            self.calls: list[list[str]] = []
            self.unit_counts: dict[str, int] = {}

        @staticmethod
        def _raw_unit(row: dict[str, Any]) -> bytes:
            values = {
                "LoadState": row["load_state"], "ActiveState": row["active_state"],
                "SubState": row["sub_state"], "UnitFileState": row["unit_file_state"],
                "MainPID": str(row["main_pid"]),
            }
            if row["unit"].endswith(".socket"):
                values["Listen"] = next((path for path, endpoint in inventory.SOCKETS.items()
                                          if endpoint == row["listen"]), "")
            return "".join(f"{key}={value}\n" for key, value in values.items()).encode()

        def run(self, argv: list[str], *, env: dict[str, str] | None = None, command_id: str,
                safe_args: list[str] | None = None, expected: set[int] | None = None) -> tuple[int, bytes, bytes]:
            self.calls.append(list(argv))
            self.assert_sanitized_runner_inputs(argv, env, command_id, safe_args)
            if argv[0] == "/usr/bin/systemctl":
                unit = argv[2]
                props = list(inventory.PROPERTIES) + (["Listen"] if unit.endswith(".socket") else [])
                expected_argv = ["/usr/bin/systemctl", "show", unit]
                expected_argv += [f"--property={prop}" for prop in props] + ["--no-pager"]
                if argv != expected_argv:
                    raise AssertionError("diagnostic used unexpected systemctl argv")
                count = self.unit_counts.get(unit, 0)
                self.unit_counts[unit] = count + 1
                rows = self.unit_rows[unit]
                return 0, self._raw_unit(rows[min(count, len(rows) - 1)]), b"systemctl stderr sentinel"
            if argv[0] == "/usr/bin/readlink":
                if len(argv) != 3 or argv[1] != "-f" or not argv[2].startswith("/proc/") or not argv[2].endswith("/exe"):
                    raise AssertionError("diagnostic used unexpected readlink argv")
                if self.failure is not None:
                    raise self.failure
                pid = int(argv[2].split("/")[2])
                return 0, self.executable_paths[pid], b"readlink stderr sentinel"
            raise AssertionError("diagnostic invoked an unapproved command")

        @staticmethod
        def assert_sanitized_runner_inputs(argv: list[str], env: dict[str, str] | None, command_id: str,
                                           safe_args: list[str] | None) -> None:
            if env is not None:
                raise AssertionError("diagnostic must use Runner's fixed environment")
            if command_id not in {"systemctl_show_unit", "systemctl_show_socket", "resolve_executable"}:
                raise AssertionError("diagnostic used an unexpected command id")
            if safe_args not in (None, [argv[2]] if argv[0] == "/usr/bin/systemctl" else None):
                raise AssertionError("diagnostic used unexpected safe arguments")

    def test_strict_json_rejects_duplicates_constants_and_invalid_utf8(self) -> None:
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff"):
            with self.subTest(raw=raw), self.assertRaises(inventory.InventoryError):
                inventory.strict_json(raw)

    def test_strict_json_accepts_valid_data(self) -> None:
        self.assertEqual(inventory.strict_json(b'{"x":[1,true]}'), {"x": [1, True]})

    def test_service_unit_exact_active_and_inactive_tuples(self) -> None:
        active = {"LoadState": "loaded", "ActiveState": "active", "SubState": "running",
                  "UnitFileState": "enabled", "MainPID": "42"}
        inactive = {**active, "ActiveState": "inactive", "SubState": "dead", "MainPID": "0"}
        self.assertEqual(inventory._unit_state("lxd.service", active)["main_pid"], 42)
        self.assertEqual(inventory._unit_state("lxd.service", inactive)["main_pid"], 0)
        for mutation in ({**active, "MainPID": "0"}, {**active, "SubState": "dead"},
                         {**inactive, "MainPID": "2"}, {**active, "UnitFileState": "unknown"}):
            with self.subTest(mutation=mutation), self.assertRaises(inventory.InventoryError):
                inventory._unit_state("lxd.service", mutation)

    def test_not_found_service_requires_empty_or_not_found_unit_file_state(self) -> None:
        row = {"LoadState": "not-found", "ActiveState": "inactive", "SubState": "dead",
               "UnitFileState": "not-found", "MainPID": "0"}
        self.assertEqual(inventory._unit_state("incus.service", row)["unit_file_state"], "")
        with self.assertRaises(inventory.InventoryError):
            inventory._unit_state("incus.service", {**row, "UnitFileState": "disabled"})

    def test_socket_unit_requires_zero_pid_and_allowlisted_listen(self) -> None:
        row = {"LoadState": "loaded", "ActiveState": "active", "SubState": "listening",
               "UnitFileState": "enabled", "MainPID": "0", "Listen": "/run/incus/unix.socket (Stream)"}
        self.assertEqual(inventory._unit_state("incus.socket", row)["listen"], "incus_run")
        for mutation in ({**row, "MainPID": "5"}, {**row, "Listen": "/tmp/evil.sock"}):
            with self.subTest(mutation=mutation), self.assertRaises(inventory.InventoryError):
                inventory._unit_state("incus.socket", mutation)

    def test_incus_socket_running_is_the_only_running_socket_state(self) -> None:
        row = {"LoadState": "loaded", "ActiveState": "active", "SubState": "running",
               "UnitFileState": "enabled", "MainPID": "0", "Listen": "/run/incus/unix.socket (Stream)"}
        self.assertEqual(inventory._unit_state("incus.socket", row)["sub_state"], "running")
        self.assertEqual(inventory._unit_state("incus.socket", {k: v for k, v in row.items() if k != "MainPID"})[
            "main_pid"], 0)
        for unit in ("snap.lxd.daemon.unix.socket", "other.socket"):
            with self.subTest(unit=unit), self.assertRaises(inventory.InventoryError):
                inventory._unit_state(unit, row)

    def test_systemctl_socket_output_may_omit_only_zero_main_pid(self) -> None:
        base = ("LoadState=loaded\nActiveState=active\nSubState=running\n"
                "UnitFileState=enabled\nListen=/run/incus/unix.socket (Stream)\n")
        runner = Mock()
        runner.run.return_value = (0, base.encode(), b"")
        self.assertEqual(inventory._systemctl_show(runner, "incus.socket")["main_pid"], 0)
        runner.run.return_value = (0, (base + "MainPID=0\n").encode(), b"")
        self.assertEqual(inventory._systemctl_show(runner, "incus.socket")["main_pid"], 0)
        for invalid_pid in ("", "nope", "42", "00", "٠"):
            with self.subTest(pid=invalid_pid):
                runner.run.return_value = (0, (base + f"MainPID={invalid_pid}\n").encode(), b"")
                with self.assertRaises(inventory.InventoryError):
                    inventory._systemctl_show(runner, "incus.socket")
        service_output = ("LoadState=loaded\nActiveState=active\nSubState=running\n"
                          "UnitFileState=enabled\n")
        runner.run.return_value = (0, service_output.encode(), b"")
        with self.assertRaises(inventory.InventoryError):
            inventory._systemctl_show(runner, "incus.service")

    @staticmethod
    def _diagnostic_active_service(unit: str, pid: int) -> dict[str, Any]:
        return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                "unit_file_state": "enabled", "main_pid": pid}

    @staticmethod
    def _diagnostic_missing_unit(unit: str, *, socket: bool = False) -> dict[str, Any]:
        row: dict[str, Any] = {"unit": unit, "load_state": "not-found", "active_state": "inactive",
                               "sub_state": "dead", "unit_file_state": "", "main_pid": 0}
        if socket:
            row["listen"] = ""
        return row

    def _diagnose_unknown_path(self, unit: str, raw_path: bytes) -> tuple[int, str, str, Any]:
        rows = {name: [self._diagnostic_missing_unit(name, socket=name.endswith(".socket"))]
                for name in inventory.UNITS}
        active = self._diagnostic_active_service(unit, 733)
        rows[unit] = [active, active]
        runner = self._UnitDiagnosticRunner(rows, {733: raw_path})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])
        return result, stdout.getvalue(), stderr.getvalue(), runner

    def test_diagnose_units_success_uses_exactly_eleven_commands_and_emits_symbols_only(self) -> None:
        rows = {
            "lxd.service": [self._diagnostic_active_service("lxd.service", 101)],
            "snap.lxd.daemon.service": [self._diagnostic_active_service("snap.lxd.daemon.service", 202)],
            "snap.lxd.daemon.unix.socket": [{"unit": "snap.lxd.daemon.unix.socket", "load_state": "loaded",
                "active_state": "active", "sub_state": "listening", "unit_file_state": "enabled",
                "main_pid": 0, "listen": "lxd_snap"}],
            "incus.service": [self._diagnostic_active_service("incus.service", 303)],
            "incus.socket": [{"unit": "incus.socket", "load_state": "loaded", "active_state": "active",
                "sub_state": "running", "unit_file_state": "enabled", "main_pid": 0, "listen": "incus_run"}],
        }
        runner = self._UnitDiagnosticRunner(rows, {101: b"/usr/lib/lxd/lxd\n",
            202: b"/snap/lxd/12345/bin/lxd\n", 303: b"/usr/libexec/incus/incusd\n"})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                patch.object(inventory, "_endpoint", side_effect=AssertionError("endpoint query is forbidden")), \
                patch.object(inventory, "_inventory_client", side_effect=AssertionError("client query is forbidden")), \
                patch.object(inventory, "_write_private") as write, \
                patch.object(inventory, "capture", side_effect=AssertionError("inventory capture is forbidden")), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), '{"mode":"diagnose-units","status":"DIAGNOSTIC_COMPLETE","services":[{"unit":"lxd.service","identity":"lxd_system"},{"unit":"snap.lxd.daemon.service","identity":"lxd_snap"},{"unit":"incus.service","identity":"incus_system"}]}\n')
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(runner.calls), 11)
        self.assertEqual(sum(call[0] == "/usr/bin/systemctl" for call in runner.calls), 8)
        self.assertEqual(sum(call[0] == "/usr/bin/readlink" for call in runner.calls), 3)
        self.assertEqual([call[2] for call in runner.calls if call[0] == "/usr/bin/systemctl"],
                         ["lxd.service", "lxd.service", "snap.lxd.daemon.service", "snap.lxd.daemon.service",
                          "snap.lxd.daemon.unix.socket", "incus.service", "incus.service", "incus.socket"])
        self.assertEqual([call for call in runner.calls if call[0] == "/usr/bin/readlink"], [
            ["/usr/bin/readlink", "-f", "/proc/101/exe"],
            ["/usr/bin/readlink", "-f", "/proc/202/exe"],
            ["/usr/bin/readlink", "-f", "/proc/303/exe"],
        ])
        for forbidden in ("101", "202", "303", "/proc/", "/usr/lib", "/snap/lxd", "stderr sentinel"):
            self.assertNotIn(forbidden, stdout.getvalue() + stderr.getvalue())
        write.assert_not_called()

    def test_diagnose_units_unknown_emits_only_first_unit_and_stops_before_later_queries(self) -> None:
        rows = {
            "lxd.service": [self._diagnostic_active_service("lxd.service", 411)],
            "snap.lxd.daemon.service": [self._diagnostic_active_service("snap.lxd.daemon.service", 422)],
            "snap.lxd.daemon.unix.socket": [self._diagnostic_missing_unit("snap.lxd.daemon.unix.socket", socket=True)],
            "incus.service": [self._diagnostic_missing_unit("incus.service")],
            "incus.socket": [self._diagnostic_missing_unit("incus.socket", socket=True)],
        }
        secret_path = b"/private/SENTINEL_EXECUTABLE_PATH\n"
        runner = self._UnitDiagnosticRunner(rows, {411: b"/usr/lib/lxd/lxd\n", 422: secret_path})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                patch.object(inventory, "_endpoint", side_effect=AssertionError("endpoint query is forbidden")), \
                patch.object(inventory, "_inventory_client", side_effect=AssertionError("client query is forbidden")), \
                patch.object(inventory, "_write_private") as write, redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])

        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"snap.lxd.daemon.service","identity":"UNKNOWN","reason":"SNAP_EXECUTABLE_OUTSIDE_ROOT"}\n')
        self.assertEqual(stderr.getvalue(), "")
        systemctl_units = [call[2] for call in runner.calls if call[0] == "/usr/bin/systemctl"]
        self.assertEqual(systemctl_units, ["lxd.service", "lxd.service", "snap.lxd.daemon.service",
                                           "snap.lxd.daemon.service"])
        self.assertEqual([call for call in runner.calls if call[0] == "/usr/bin/readlink"], [
            ["/usr/bin/readlink", "-f", "/proc/411/exe"],
            ["/usr/bin/readlink", "-f", "/proc/422/exe"],
        ])
        for forbidden in ("411", "422", "/proc/", "/usr/lib", "/private/", "SENTINEL_EXECUTABLE_PATH", "stderr sentinel"):
            self.assertNotIn(forbidden, stdout.getvalue() + stderr.getvalue())
        write.assert_not_called()

    def test_diagnose_units_classifies_snap_path_shape_without_disclosing_path(self) -> None:
        result, stdout, stderr, runner = self._diagnose_unknown_path(
            "snap.lxd.daemon.service", b"/snap/lxd/current/bin/SENTINEL_EXECUTABLE\n")
        self.assertEqual(result, 2)
        self.assertEqual(stdout, '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"snap.lxd.daemon.service","identity":"UNKNOWN","reason":"SNAP_ROOT_PATH_MISMATCH"}\n')
        self.assertEqual(stderr, "")
        self.assertEqual(len([call for call in runner.calls if call[0] == "/usr/bin/readlink"]), 1)
        self.assertNotIn("SENTINEL_EXECUTABLE", stdout + stderr)

    def test_diagnose_units_classifies_invalid_snap_paths_as_unclassifiable(self) -> None:
        for raw_path in (b"\n", b"relative/SENTINEL_PATH\n", b"/snap/lxd/invalid\x00SENTINEL_PATH\n"):
            with self.subTest(raw_path=raw_path):
                result, stdout, stderr, runner = self._diagnose_unknown_path("snap.lxd.daemon.service", raw_path)
                self.assertEqual(result, 2)
                self.assertEqual(stdout, '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"snap.lxd.daemon.service","identity":"UNKNOWN","reason":"SNAP_EXECUTABLE_UNCLASSIFIABLE"}\n')
                self.assertEqual(stderr, "")
                self.assertNotIn("SENTINEL_PATH", stdout + stderr)
                self.assertEqual(len([call for call in runner.calls if call[0] == "/usr/bin/readlink"]), 1)

    def test_diagnose_units_non_snap_unknown_uses_fixed_reason(self) -> None:
        result, stdout, stderr, runner = self._diagnose_unknown_path("lxd.service", b"/private/SENTINEL_EXECUTABLE\n")
        self.assertEqual(result, 2)
        self.assertEqual(stdout, '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"lxd.service","identity":"UNKNOWN","reason":"EXECUTABLE_IDENTITY_BLOCKED"}\n')
        self.assertEqual(stderr, "")
        self.assertNotIn("SENTINEL_EXECUTABLE", stdout + stderr)
        self.assertEqual(len([call for call in runner.calls if call[0] == "/usr/bin/readlink"]), 1)

    def test_diagnose_units_state_drift_stops_before_later_unit(self) -> None:
        rows = {
            "lxd.service": [self._diagnostic_active_service("lxd.service", 51),
                            self._diagnostic_active_service("lxd.service", 52)],
            "snap.lxd.daemon.service": [self._diagnostic_missing_unit("snap.lxd.daemon.service")],
            "snap.lxd.daemon.unix.socket": [self._diagnostic_missing_unit("snap.lxd.daemon.unix.socket", socket=True)],
            "incus.service": [self._diagnostic_missing_unit("incus.service")],
            "incus.socket": [self._diagnostic_missing_unit("incus.socket", socket=True)],
        }
        runner = self._UnitDiagnosticRunner(rows, {51: b"/usr/lib/lxd/lxd\n"})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().strip(), "BLOCKED:UNIT_DRIFT_BLOCKED")
        self.assertEqual([call[2] for call in runner.calls if call[0] == "/usr/bin/systemctl"],
                         ["lxd.service", "lxd.service"])

    def test_diagnose_units_timeout_uses_fixed_error_and_never_writes_artifact(self) -> None:
        rows = {unit: [self._diagnostic_active_service(unit, 61) if unit == "lxd.service"
                       else self._diagnostic_missing_unit(unit, socket=unit.endswith(".socket"))]
                for unit in inventory.UNITS}
        runner = self._UnitDiagnosticRunner(rows, {}, failure=inventory.InventoryError("COMMAND_TIMEOUT"))
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                patch.object(inventory, "_write_private") as write, redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().strip(), "BLOCKED:COMMAND_TIMEOUT")
        self.assertEqual(len(runner.calls), 2)
        write.assert_not_called()

    def test_diagnose_units_extra_arguments_are_rejected_without_echo(self) -> None:
        secret_arg = "/private/SENTINEL_ARGUMENT_PATH"
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner") as runner, \
                patch.object(inventory, "capture") as capture, redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units", "--output", secret_arg])
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().strip(), "BLOCKED:DIAGNOSTIC_ARGUMENTS_INVALID")
        self.assertNotIn(secret_arg, stderr.getvalue())
        self.assertNotIn("usage:", stderr.getvalue().lower())
        runner.assert_not_called()
        capture.assert_not_called()

    def test_artifact_incus_running_socket_requires_matching_service_and_endpoint(self) -> None:
        artifact = self._valid_artifact()
        service = next(row for row in artifact["incus_units"] if row["unit"] == "incus.service")
        service.update(load_state="loaded", active_state="active", sub_state="running",
                       unit_file_state="enabled", main_pid=42)
        socket = next(row for row in artifact["incus_units"] if row["unit"] == "incus.socket")
        socket.update(load_state="loaded", active_state="active", sub_state="running",
                      unit_file_state="enabled", main_pid=0, listen="incus_run")
        artifact["incus_executables"] = [{"unit": "incus.service", "main_pid": 42,
                                         "identity_id": "incus_system", "package": "system:incus",
                                         "version": "6.0.5"}]
        endpoint = next(row for row in artifact["sockets"] if row["endpoint_id"] == "incus_run")
        endpoint.update(state="present", unit="incus.socket")
        inventory._validate_artifact(artifact)
        endpoint["state"] = "absent"
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact(artifact)

    def test_executable_identity_is_an_exact_unit_path_pair(self) -> None:
        self.assertEqual(inventory.executable_identity("lxd.service", "/usr/lib/lxd/lxd"),
                         ("lxd_system", "system:lxd"))
        self.assertEqual(inventory.executable_identity("snap.lxd.daemon.service", "/snap/lxd/123/bin/lxd"),
                         ("lxd_snap", "snap:lxd"))
        for unit, path in (("incus.service", "/tmp/incusd"),
                           ("snap.lxd.daemon.service", "/snap/lxd/current/bin/lxd"),
                           ("lxd.service", "/usr/libexec/incus/incusd")):
            with self.subTest(unit=unit, path=path), self.assertRaises(inventory.InventoryError):
                inventory.executable_identity(unit, path)

    def test_source_commit_is_required_to_be_lowercase_full_hash(self) -> None:
        for value in ("", "a" * 39, "A" * 40, "g" * 40):
            with self.subTest(value=value), self.assertRaises(inventory.InventoryError):
                inventory.capture(value, runner=Mock())

    def test_runner_uses_shell_false_devnull_and_sanitized_environment(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 88
        proc.poll.return_value = 0
        proc.wait.return_value = 0
        popen = Mock(return_value=proc)
        runner = inventory.Runner(popen=popen)
        reads = {101: [b"ok", b""], 102: [b""]}
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "read", side_effect=lambda fd, _n: reads[fd].pop(0)):
            status, out, err = runner.run(["/usr/bin/systemctl", "show"], command_id="fixture")
        self.assertEqual((status, out, err), (0, b"ok", b""))
        kwargs = popen.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["env"], {"LC_ALL": "C", "PATH": "/usr/bin:/bin"})
        self.assertTrue(kwargs["start_new_session"])

    def test_runner_rejects_unbounded_or_nonabsolute_argv_and_bad_environment(self) -> None:
        runner = inventory.Runner(popen=Mock())
        for argv, env in ((["systemctl"], None), (["/usr/bin/x", "x\x00y"], None),
                          (["/usr/bin/example"], None),
                          (["/usr/bin/lxc"], {**inventory.ENV_BASE, "HOME": "/tmp"}),
                          (["/usr/bin/lxc"], {**inventory.ENV_BASE, "LXD_SOCKET": "/tmp/x"}),
                          (["/usr/bin/incus"], {**inventory.ENV_BASE, "INCUS_SOCKET": "/var/lib/lxd/unix.socket"})):
            with self.subTest(argv=argv, env=env), self.assertRaises(inventory.InventoryError):
                runner.run(argv, env=env, command_id="test")

    def test_runner_rejects_streams_over_two_mib(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 12
        proc.poll.return_value = None
        proc.kill = Mock()
        proc.wait.side_effect = [None, 0]
        popen = Mock(return_value=proc)
        reads = {101: [b"x" * (inventory.MAX_STREAM + 1)], 102: [b""]}
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "read", side_effect=lambda fd, _n: reads[fd].pop(0)), \
                self.assertRaises(inventory.InventoryError):
            inventory.Runner(popen=popen).run(["/usr/bin/systemctl", "show"], command_id="fixture")

    def test_runner_command_count_and_aggregate_budget_are_hard_limits(self) -> None:
        runner = inventory.Runner(popen=Mock())
        runner.commands = inventory.MAX_COMMANDS
        with self.assertRaises(inventory.InventoryError):
            runner.run(["/usr/bin/systemctl", "show"], command_id="x")
        runner = inventory.Runner(popen=Mock())
        runner.total_bytes = inventory.MAX_TOTAL_BYTES
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 88
        proc.poll.return_value = 0
        proc.wait.return_value = 0
        runner.popen = Mock(return_value=proc)
        reads = {101: [b"x", b""], 102: [b""]}
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "read", side_effect=lambda fd, _n: reads[fd].pop(0)), \
                self.assertRaises(inventory.InventoryError):
            runner.run(["/usr/bin/systemctl", "show"], command_id="x")

    def test_endpoint_allowlist_rejects_unrecognized_paths_and_non_socket(self) -> None:
        self.assertEqual(inventory.SOCKETS["/var/lib/incus/unix.socket"], "incus_var_lib")
        self.assertNotIn("/tmp/unknown.sock", inventory.SOCKETS)
        with self.assertRaises(inventory.InventoryError):
            inventory._endpoint(Mock(), "/tmp/unknown.sock", unit="")

    def test_detail_responses_are_validated_then_reduced_to_safe_identity(self) -> None:
        profile = {"name": "default", "description": "", "config": {},
                   "devices": {"eth0": {"type": "nic", "parent": "br0"}},
                   "used_by": ["/1.0/instances/web"]}
        parsed = inventory._validate_profile_show(profile, "default", "alpha")
        self.assertEqual(inventory._consumer_refs(parsed["used_by"], "alpha"),
                         [{"kind": "instances", "name": "web", "project": "alpha"}])
        self.assertEqual(inventory._device_types(parsed["devices"]), [{"name": "eth0", "type": "nic"}])
        private_device = inventory._validate_profile_show(
            {**profile, "devices": {"secret": {"type": "disk", "source": "/host/private"}}}, "default", "alpha")
        projected = inventory._device_types(private_device["devices"])
        self.assertEqual(projected, [{"name": "secret", "type": "disk"}])
        self.assertNotIn("source", str(projected))
        self.assertNotIn("/host/private", str(projected))
        with self.assertRaises(inventory.InventoryError):
            inventory._consumer_refs(["https://host/1.0/instances/web"], "alpha")
        self.assertEqual(inventory._consumer_refs(
            ["/1.0/storage-pools/default/volumes/container/web?project=alpha"], "alpha"),
            [{"kind": "storage-volumes", "name": "default/container/web", "project": "alpha"}])
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_profile_show({**profile, "project": "other"}, "default", "alpha")

    def test_instance_detail_requires_both_config_shapes(self) -> None:
        instance = {"name": "web", "config": {}, "devices": {}, "ephemeral": False,
                    "profiles": ["default"], "stateful": False}
        self.assertEqual(inventory._validate_instance_config(instance, "web", "alpha")["name"], "web")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_instance_config({**instance, "unknown": "value"}, "web", "alpha")

    def test_network_and_pool_detail_reject_project_scope_mismatch(self) -> None:
        network = {"name": "br0", "project": "alpha", "type": "bridge", "managed": True, "config": {}, "used_by": []}
        pool = {"name": "default", "project": "alpha", "driver": "dir", "config": {}, "used_by": []}
        self.assertEqual(inventory._validate_network_show(network, "br0", "alpha")["name"], "br0")
        self.assertEqual(inventory._validate_pool_show(pool, "default", "alpha")["name"], "default")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_network_show({**network, "project": "beta"}, "br0", "alpha")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_pool_show({**pool, "project": "beta"}, "default", "alpha")

    def test_network_and_pool_details_require_consumer_relationships(self) -> None:
        network = {"name": "br0", "project": "alpha", "type": "bridge", "managed": True, "config": {}}
        pool = {"name": "default", "project": "alpha", "driver": "dir", "config": {}}
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_network_show(network, "br0", "alpha")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_pool_show(pool, "default", "alpha")

    def test_unknown_storage_volume_type_fails_closed(self) -> None:
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_TYPE_UNSUPPORTED"):
            inventory._volume_type("future-volume-kind")

    def test_runner_requires_client_specific_canonical_socket(self) -> None:
        runner = inventory.Runner(popen=Mock())
        for binary, env in (("/usr/bin/lxc", {**inventory.ENV_BASE, "INCUS_SOCKET": "/run/incus/unix.socket"}),
                            ("/usr/bin/incus", {**inventory.ENV_BASE, "INCUS_SOCKET": "/tmp/socket"}),
                            ("/usr/bin/lxc", {**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/incus/unix.socket"}),
                            ("/snap/bin/lxc", {**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/lxd/unix.socket"})):
            with self.subTest(binary=binary, env=env), self.assertRaises(inventory.InventoryError):
                runner.run([binary, "--force-local", "version"], env=env, command_id="version")

    def test_inventory_client_uses_exact_detail_argv_and_projects_safe_consumer_identity(self) -> None:
        runner = self._InventoryRunner()
        version, projects = inventory._inventory_client(runner, "lxd_system", "/var/lib/lxd/unix.socket",
                                                          incus=False, before_query=lambda: None)
        self.assertEqual(version, "6.0.5")
        suffixes = [call[0][2:] for call in runner.calls]
        self.assertEqual(suffixes, [
            ["version"], ["project", "list", "--format", "json"],
            ["project", "show", "alpha", "--format", "json"],
            ["profile", "list", "--project", "alpha", "--format", "json"],
            ["list", "--project", "alpha", "--format", "json"],
            ["network", "list", "--project", "alpha", "--format", "json"],
            ["storage", "list", "--project", "alpha", "--format", "json"],
            ["profile", "show", "zeta", "--project", "alpha", "--format", "json"],
            ["profile", "show", "bravo", "--project", "alpha", "--format", "json"],
            ["config", "show", "web", "--project", "alpha", "--format", "json"],
            ["config", "show", "web", "--project", "alpha", "--format", "json", "--expanded"],
            ["network", "show", "net", "--project", "alpha", "--format", "json"],
            ["storage", "show", "pool", "--project", "alpha", "--format", "json"],
            ["storage", "volume", "list", "pool", "--project", "alpha", "--format", "json"],
            ["storage", "volume", "show", "pool", "container/web", "--project", "alpha", "--format", "json"],
        ])
        self.assertTrue(all(call[1] == {**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/lxd/unix.socket"}
                            for call in runner.calls))
        self.assertEqual([row["name"] for row in projects[0]["profiles"]], ["bravo", "zeta"])
        self.assertEqual(projects[0]["profiles"][0]["used_by"], [
            {"kind": "instances", "name": "web", "project": "alpha"},
        ])

    def test_incus_inventory_uses_exact_detail_argv_binary_and_socket_environment(self) -> None:
        runner = self._InventoryRunner()
        version, projects = inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                                          incus=True, before_query=lambda: None)
        self.assertEqual(version, "6.0.5")
        self.assertEqual(len(projects), 1)
        self.assertTrue(all(call[0][0:2] == ["/usr/bin/incus", "--force-local"] for call in runner.calls))
        self.assertTrue(all(call[1] == {**inventory.ENV_BASE, "INCUS_SOCKET": "/run/incus/unix.socket"}
                            for call in runner.calls))
        self.assertEqual([call[0][2:] for call in runner.calls], [
            ["version"], ["project", "list", "--format", "json"],
            ["project", "show", "alpha", "--format", "json"],
            ["profile", "list", "--project", "alpha", "--format", "json"],
            ["list", "--project", "alpha", "--format", "json"],
            ["network", "list", "--project", "alpha", "--format", "json"],
            ["storage", "list", "--project", "alpha", "--format", "json"],
            ["profile", "show", "zeta", "--project", "alpha", "--format", "json"],
            ["profile", "show", "bravo", "--project", "alpha", "--format", "json"],
            ["config", "show", "web", "--project", "alpha", "--format", "json"],
            ["config", "show", "web", "--project", "alpha", "--format", "json", "--expanded"],
            ["network", "show", "net", "--project", "alpha", "--format", "json"],
            ["storage", "show", "pool", "--project", "alpha", "--format", "json"],
            ["storage", "volume", "list", "pool", "--project", "alpha", "--format", "json"],
            ["storage", "volume", "show", "pool", "container/web", "--project", "alpha", "--format", "json"],
        ])
        self.assertIn("incus_profile_show", [record["command_id"] for record in runner.records])
        self.assertIn("incus_network_show", [record["command_id"] for record in runner.records])
        self.assertIn("incus_storage_show", [record["command_id"] for record in runner.records])
        self.assertTrue(all(record["command_id"].startswith("incus_") for record in runner.records))

    def test_capture_rechecks_each_query_and_returns_complete_sorted_projection(self) -> None:
        runner = self._InventoryRunner()
        def active(unit, pid):
            return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": pid}
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        incus_socket = {"unit": "incus.socket", "load_state": "loaded", "active_state": "active",
                        "sub_state": "running", "unit_file_state": "enabled", "main_pid": 0,
                        "listen": "incus_run"}
        unit_rows = {"lxd.service": active("lxd.service", 42),
                     "snap.lxd.daemon.service": missing("snap.lxd.daemon.service"),
                     "snap.lxd.daemon.unix.socket": missing("snap.lxd.daemon.unix.socket", True),
                     "incus.service": active("incus.service", 43), "incus.socket": incus_socket}
        endpoint_present = {"/var/lib/lxd/unix.socket", "/run/incus/unix.socket"}
        checked: list[bool] = []
        real_recheck = inventory._recheck_all
        def record_recheck(*args: Any) -> None:
            checked.append(True)
            real_recheck(*args)
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: dict(unit_rows[unit])), \
                patch.object(inventory, "_resolve_executable", side_effect=lambda _runner, row:
                             ("incus_system", "system:incus") if row["unit"] == "incus.service"
                             else ("lxd_system", "system:lxd")), \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit:
                             (inventory.SOCKETS[path], path in endpoint_present)), \
                patch.object(inventory, "_recheck_all", side_effect=record_recheck), \
                patch.object(inventory, "_require_full_local_access"):
            artifact = inventory.capture("a" * 40, runner=runner)
        self.assertEqual(len(checked), len(runner.calls) + 1)
        self.assertEqual(artifact["decision"], "READ_ONLY_INVENTORY_COMPLETE")
        self.assertEqual(artifact["incus_units"][1]["sub_state"], "running")
        self.assertEqual(artifact["incus_executables"][0]["identity_id"], "incus_system")
        self.assertEqual([row["name"] for row in artifact["lxd_projects"][0]["profiles"]], ["bravo", "zeta"])
        self.assertEqual([row["name"] for row in artifact["lxd_projects"][0]["networks"]], ["net"])
        self.assertTrue(artifact["incus_projects"])
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))

    def test_running_incus_socket_drift_blocks_before_first_client_query(self) -> None:
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        units = {unit: missing(unit, unit.endswith(".socket")) for unit in inventory.UNITS}
        units["incus.service"] = {"unit": "incus.service", "load_state": "loaded", "active_state": "active",
                                  "sub_state": "running", "unit_file_state": "enabled", "main_pid": 43}
        units["incus.socket"] = {"unit": "incus.socket", "load_state": "loaded", "active_state": "active",
                                 "sub_state": "running", "unit_file_state": "enabled", "main_pid": 0,
                                 "listen": "incus_run"}
        counts = {unit: 0 for unit in inventory.UNITS}
        runner = self._InventoryRunner()
        def systemctl(_runner, unit):
            counts[unit] += 1
            row = dict(units[unit])
            if unit == "incus.socket" and counts[unit] == 2:
                row["sub_state"] = "listening"
            return row
        with patch.object(inventory, "_systemctl_show", side_effect=systemctl), \
                patch.object(inventory, "_resolve_executable", return_value=("incus_system", "system:incus")), \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit:
                             (inventory.SOCKETS[path], path == "/run/incus/unix.socket")), \
                patch.object(inventory, "_require_full_local_access"):
            with self.assertRaisesRegex(inventory.InventoryError, "RUNTIME_UNIT_DRIFT"):
                inventory.capture("a" * 40, runner=runner)
        self.assertEqual(runner.calls, [])

    def test_service_or_socket_drift_blocks_the_next_cli_query(self) -> None:
        def active(unit, pid):
            return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": pid}
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        base = {"lxd.service": active("lxd.service", 42),
                "snap.lxd.daemon.service": missing("snap.lxd.daemon.service"),
                "snap.lxd.daemon.unix.socket": missing("snap.lxd.daemon.unix.socket", True),
                "incus.service": missing("incus.service"), "incus.socket": missing("incus.socket", True)}
        for drift in ("service", "socket"):
            with self.subTest(drift=drift):
                calls = {"unit": 0, "endpoint": 0}
                runner = self._InventoryRunner()
                def systemctl(_runner, unit):
                    if unit == "lxd.service":
                        calls["unit"] += 1
                        if drift == "service" and calls["unit"] == 2:
                            return {**base[unit], "main_pid": 43}
                    return dict(base[unit])
                def endpoint(_runner, path, unit):
                    present = path == "/var/lib/lxd/unix.socket"
                    if path == "/var/lib/lxd/unix.socket":
                        calls["endpoint"] += 1
                        if drift == "socket" and calls["endpoint"] == 2:
                            present = False
                    return inventory.SOCKETS[path], present
                with patch.object(inventory, "_systemctl_show", side_effect=systemctl), \
                        patch.object(inventory, "_resolve_executable", return_value=("lxd_system", "system:lxd")), \
                        patch.object(inventory, "_endpoint", side_effect=endpoint):
                    with self.assertRaises(inventory.InventoryError):
                        inventory.capture("a" * 40, runner=runner)
                self.assertEqual(runner.calls, [])

    def test_competing_service_appearing_during_capture_creates_no_query_or_artifact(self) -> None:
        def active(unit, pid):
            return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": pid}
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        units = {"lxd.service": active("lxd.service", 42),
                 "snap.lxd.daemon.service": missing("snap.lxd.daemon.service"),
                 "snap.lxd.daemon.unix.socket": missing("snap.lxd.daemon.unix.socket", True),
                 "incus.service": missing("incus.service"), "incus.socket": missing("incus.socket", True)}
        counts = {unit: 0 for unit in inventory.UNITS}
        runner = self._InventoryRunner()
        def systemctl(_runner, unit):
            counts[unit] += 1
            if unit == "snap.lxd.daemon.service" and counts[unit] == 2:
                return active(unit, 73)
            return dict(units[unit])
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "blocked-inventory.json"
            with patch.object(inventory, "Runner", return_value=runner), \
                    patch.object(inventory, "_systemctl_show", side_effect=systemctl), \
                    patch.object(inventory, "_resolve_executable", return_value=("lxd_system", "system:lxd")), \
                    patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit: (inventory.SOCKETS[path], path == "/var/lib/lxd/unix.socket")), \
                    patch.object(inventory, "_require_full_local_access"), \
                    patch.object(inventory, "_write_private") as write, redirect_stderr(stderr):
                result = inventory.main(["--source-commit", "a" * 40, "--output", str(artifact)])
            self.assertEqual(result, 2)
            self.assertFalse(artifact.exists())
            self.assertEqual(runner.calls, [])
            self.assertGreaterEqual(counts["lxd.service"], 1)
            self.assertEqual(counts["snap.lxd.daemon.service"], 2)
            write.assert_not_called()
            self.assertIn("BLOCKED:RUNTIME_UNIT_DRIFT", stderr.getvalue())

    def test_loaded_inactive_incus_and_no_active_runtime_fail_closed(self) -> None:
        with patch.object(inventory, "_systemctl_show") as show, patch.object(inventory, "_resolve_executable") as resolve, \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit: (inventory.SOCKETS[path], False)):
            rows = {unit: {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                           "unit_file_state": "", "main_pid": 0} for unit in inventory.UNITS}
            for unit in ("snap.lxd.daemon.unix.socket", "incus.socket"):
                rows[unit]["listen"] = ""
            rows["incus.service"] = {"unit": "incus.service", "load_state": "loaded", "active_state": "inactive",
                                     "sub_state": "dead", "unit_file_state": "enabled", "main_pid": 0}
            show.side_effect = lambda _runner, unit: rows[unit]
            resolve.side_effect = AssertionError("inactive process must not be resolved")
            with self.assertRaises(inventory.InventoryError):
                inventory.capture("a" * 40, runner=Mock())

    def test_no_installed_or_active_runtime_fails_instead_of_empty_success(self) -> None:
        rows = {unit: {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                       "unit_file_state": "", "main_pid": 0} for unit in inventory.UNITS}
        for unit in ("snap.lxd.daemon.unix.socket", "incus.socket"):
            rows[unit]["listen"] = ""
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit: (inventory.SOCKETS[path], False)):
            with self.assertRaisesRegex(inventory.InventoryError, "RUNTIME_INVENTORY_EMPTY"):
                inventory.capture("a" * 40, runner=Mock())

    def test_incus_active_does_not_mask_residual_unavailable_lxd_endpoint(self) -> None:
        for residual in ("socket_unit", "endpoint"):
            with self.subTest(residual=residual):
                rows = {unit: {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                               "unit_file_state": "", "main_pid": 0} for unit in inventory.UNITS}
                for unit in ("snap.lxd.daemon.unix.socket", "incus.socket"):
                    rows[unit]["listen"] = ""
                if residual == "socket_unit":
                    rows["snap.lxd.daemon.unix.socket"] = {"unit": "snap.lxd.daemon.unix.socket", "load_state": "loaded",
                        "active_state": "active", "sub_state": "listening", "unit_file_state": "enabled",
                        "main_pid": 0, "listen": "lxd_system"}
                rows["incus.service"] = {"unit": "incus.service", "load_state": "loaded", "active_state": "active",
                                         "sub_state": "running", "unit_file_state": "enabled", "main_pid": 77}
                def endpoint(_runner, path, unit):
                    return inventory.SOCKETS[path], residual == "endpoint" and path == "/var/lib/lxd/unix.socket"
                with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                        patch.object(inventory, "_resolve_executable", return_value=("incus_system", "system:incus")), \
                        patch.object(inventory, "_endpoint", side_effect=endpoint):
                    with self.assertRaisesRegex(inventory.InventoryError, "LXD_RUNTIME_INVENTORY_UNAVAILABLE"):
                        inventory.capture("a" * 40, runner=Mock())

    def test_unknown_resource_fields_fail_closed(self) -> None:
        self.assertEqual(inventory._only_keys({"name": "default"}, {"name"}), {"name": "default"})
        with self.assertRaises(inventory.InventoryError):
            inventory._only_keys({"name": "default", "config": {"secret": "redacted"}}, {"name"})

    def test_complete_ownership_requires_resolvable_profile_and_consumer_edges(self) -> None:
        _version, projects = inventory._inventory_client(
            self._InventoryRunner(), "incus_system", "/run/incus/unix.socket", incus=True,
            before_query=lambda: None)
        inventory._validate_complete_ownership(projects)

        projects[0]["instances"][0]["profiles"] = ["missing"]
        with self.assertRaisesRegex(inventory.InventoryError, "PROFILE_REFERENCE_UNRESOLVED"):
            inventory._validate_complete_ownership(projects)

        _version, projects = inventory._inventory_client(
            self._InventoryRunner(), "incus_system", "/run/incus/unix.socket", incus=True,
            before_query=lambda: None)
        projects[0]["networks"][0]["used_by"] = [
            {"kind": "instances", "name": "missing", "project": "alpha"}]
        with self.assertRaisesRegex(inventory.InventoryError, "CONSUMER_REFERENCE_UNRESOLVED"):
            inventory._validate_complete_ownership(projects)

        _version, projects = inventory._inventory_client(
            self._InventoryRunner(), "incus_system", "/run/incus/unix.socket", incus=True,
            before_query=lambda: None)
        projects[0]["profiles"][0]["used_by"] = []
        with self.assertRaisesRegex(inventory.InventoryError, "PROFILE_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._validate_complete_ownership(projects)

    def test_project_used_by_accepts_complete_inventory_and_rejects_missing_or_unknown_users(self) -> None:
        runner = self._InventoryRunner()
        _version, projects = inventory._inventory_client(
            runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)
        self.assertEqual(projects[0]["project"], "alpha")

        runner = self._InventoryRunner()
        runner.project_used_by = ["/1.0/instances/missing?project=alpha"]
        with self.assertRaisesRegex(inventory.InventoryError, "PROJECT_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.project_used_by.append("/1.0/images/fingerprint?project=alpha")
        with self.assertRaises(inventory.InventoryError):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_volume_detail_created_at_must_be_a_string_when_present(self) -> None:
        volume = {"name": "data", "type": "custom", "content_type": "filesystem", "project": "alpha",
                  "config": {}, "used_by": [], "created_at": "2026-10-01T00:00:00Z"}
        self.assertEqual(inventory._validate_volume_show(volume, "pool", "custom", "data", "alpha")["name"], "data")
        with self.assertRaisesRegex(inventory.InventoryError, "RESOURCE_SCHEMA_INVALID"):
            inventory._validate_volume_show({**volume, "created_at": 123}, "pool", "custom", "data", "alpha")
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_OWNER_PROJECT_UNSUPPORTED"):
            inventory._validate_volume_show({**volume, "project": "default"}, "pool", "custom", "data", "alpha")

    def test_volume_list_created_at_must_be_a_string_when_present(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["volumes"] = [{"name": "web", "type": "container", "content_type": "filesystem",
                                        "project": "alpha", "description": "", "config": {},
                                        "created_at": 123, "used_by": runner.volume_used_by, "location": "none"}]
        with self.assertRaisesRegex(inventory.InventoryError, "RESOURCE_SCHEMA_INVALID"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def _assert_main_blocks_without_private_artifact(self, runner: _InventoryRunner, expected_code: str) -> None:
        active_service = inventory._unit_state("lxd.service", {
            "LoadState": "loaded", "ActiveState": "active", "SubState": "running",
            "UnitFileState": "enabled", "MainPID": "4242"})
        missing_units = {
            unit: inventory._unit_state(unit, {
                "LoadState": "not-found", "ActiveState": "inactive", "SubState": "dead",
                "UnitFileState": "not-found", "MainPID": "0", **({"Listen": ""} if unit.endswith(".socket") else {})})
            for unit in inventory.UNITS if unit != "lxd.service"
        }
        units = {"lxd.service": active_service, **missing_units}
        endpoints = {"/var/lib/lxd/unix.socket": ("lxd_system", True),
                     "/var/snap/lxd/common/lxd/unix.socket": ("lxd_snap", False),
                     "/var/lib/incus/unix.socket": ("incus_var_lib", False),
                     "/run/incus/unix.socket": ("incus_run", False)}
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "inventory.json"
            with patch.object(inventory, "Runner", return_value=runner), \
                    patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: units[unit]), \
                    patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit="": endpoints[path]), \
                    patch.object(inventory, "_resolve_executable", return_value=("lxd_system", "system:lxd")), \
                    patch.object(inventory, "_require_full_local_access"), \
                    patch.object(inventory, "_recheck_all"), \
                    patch.object(inventory, "_write_private") as write, redirect_stderr(stderr):
                result = inventory.main(["--source-commit", "a" * 40, "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertFalse(output.exists())
            write.assert_not_called()
            self.assertEqual(stderr.getvalue().strip(), f"BLOCKED:{expected_code}")

    def test_inherited_volume_detail_owner_blocks_main_before_private_artifact_write(self) -> None:
        runner = self._InventoryRunner()
        runner.volume_owner_project = "default"
        self._assert_main_blocks_without_private_artifact(runner, "VOLUME_OWNER_PROJECT_UNSUPPORTED")

    def test_inherited_volume_list_owner_blocks_main_before_private_artifact_write(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["volumes"] = [{"name": "web", "type": "container", "content_type": "filesystem",
                                        "project": "default", "description": "", "config": {},
                                        "created_at": "2026-10-01T00:00:00Z", "used_by": runner.volume_used_by,
                                        "location": "none"}]
        self._assert_main_blocks_without_private_artifact(runner, "VOLUME_OWNER_PROJECT_UNSUPPORTED")

    def test_profile_custom_disk_maps_to_typed_volume_consumer(self) -> None:
        devices = {"shared-data": {"type": "disk", "path": "/srv/data", "pool": "pool", "source": "data"}}
        self.assertEqual(
            inventory._volume_device_users(devices, "alpha", "profiles", "shared"),
            {("pool", "custom", "data"): {("profiles", "shared", "alpha")}},
        )

    def test_device_relationships_must_resolve_reciprocally(self) -> None:
        runner = self._InventoryRunner()
        runner.network_used_by = []
        with self.assertRaisesRegex(inventory.InventoryError, "NETWORK_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.pool_used_by = ["/1.0/storage-pools/pool/volumes/container/web?project=alpha"]
        with self.assertRaisesRegex(inventory.InventoryError, "POOL_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.volume_used_by = []
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.instance_network = "missing"
        with self.assertRaisesRegex(inventory.InventoryError, "NETWORK_DEVICE_REFERENCE_UNRESOLVED"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.instance_pool = "missing"
        with self.assertRaisesRegex(inventory.InventoryError, "POOL_DEVICE_REFERENCE_UNRESOLVED"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.instance_custom_source = "missing"
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_DEVICE_REFERENCE_UNRESOLVED"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_pool_consumer_volume_set_must_match_listed_volumes(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["volumes"] = []
        with self.assertRaisesRegex(inventory.InventoryError, "POOL_VOLUME_OWNERSHIP_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_list_and_detail_consumer_views_must_match(self) -> None:
        mismatched_rows: dict[str, list[dict[str, Any]]] = {
            "projects": [{"name": "alpha", "description": "", "config": {},
                          "used_by": ["/1.0/profiles/bravo?project=alpha"]}],
            "profiles": [{"name": "bravo", "project": "alpha", "description": "", "config": {},
                          "devices": {}, "used_by": []}],
            "networks": [{"name": "net", "project": "alpha", "type": "bridge", "managed": True,
                          "status": "Created", "config": {}, "description": "", "used_by": [], "locations": []}],
            "pools": [{"name": "pool", "project": "alpha", "driver": "dir", "config": {},
                       "description": "", "used_by": ["/1.0/profiles/bravo?project=alpha"],
                       "status": "Created", "locations": []}],
            "volumes": [{"name": "web", "type": "container", "content_type": "filesystem",
                         "project": "alpha", "description": "", "used_by": [], "location": "none"}],
        }
        expected_errors = {"projects": "PROJECT_CONSUMER_LIST_MISMATCH",
                           "profiles": "PROFILE_CONSUMER_LIST_MISMATCH",
                           "networks": "NETWORK_CONSUMER_LIST_MISMATCH",
                           "pools": "POOL_CONSUMER_LIST_MISMATCH",
                           "volumes": "VOLUME_CONSUMER_LIST_MISMATCH"}
        for resource, rows in mismatched_rows.items():
            with self.subTest(resource=resource):
                runner = self._InventoryRunner()
                runner.list_rows[resource] = rows
                with self.assertRaisesRegex(inventory.InventoryError, expected_errors[resource]):
                    inventory._inventory_client(
                        runner, "incus_system", "/run/incus/unix.socket", incus=True,
                        before_query=lambda: None)

    def test_local_socket_access_requires_full_administrator_group(self) -> None:
        with patch.object(inventory.os, "geteuid", return_value=1000), \
                patch.object(inventory.os, "getegid", return_value=1000), \
                patch.object(inventory.os, "getgroups", return_value=[1000]), \
                patch.object(inventory.os, "stat", return_value=Mock(st_gid=2000)), \
                patch.object(inventory.grp, "getgrgid", return_value=Mock(gr_name="incus")):
            with self.assertRaisesRegex(inventory.InventoryError, "RUNTIME_ACCESS_SCOPE_UNPROVEN"):
                inventory._require_full_local_access("/run/incus/unix.socket", incus=True)

        with patch.object(inventory.os, "geteuid", return_value=1000), \
                patch.object(inventory.os, "getegid", return_value=1000), \
                patch.object(inventory.os, "getgroups", return_value=[1000, 2000]), \
                patch.object(inventory.os, "stat", return_value=Mock(st_gid=2000)), \
                patch.object(inventory.grp, "getgrgid", return_value=Mock(gr_name="incus-admin")):
            inventory._require_full_local_access("/run/incus/unix.socket", incus=True)

    def test_standard_extended_cli_list_rows_are_accepted_but_unknown_fields_are_rejected(self) -> None:
        runner = self._InventoryRunner()
        _version, projects = inventory._inventory_client(
            runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)
        instance = projects[0]["instances"][0]
        self.assertEqual(instance["name"], "web")
        self.assertEqual(instance["status"], "Running")
        self.assertNotIn("expanded_config", instance)
        self.assertNotIn("last_used_at", instance)
        self.assertNotIn("10GiB", str(projects))

        standard_rows = {
            "projects": {"name": "alpha", "unexpected": "value"},
            "profiles": {"name": "zeta", "unexpected": "value"},
            "instances": {"name": "web", "unexpected": "value"},
            "networks": {"name": "net", "unexpected": "value"},
            "pools": {"name": "pool", "unexpected": "value"},
            "volumes": {"name": "web", "unexpected": "value"},
        }
        for resource, row in standard_rows.items():
            with self.subTest(resource=resource):
                bad_runner = self._InventoryRunner()
                bad_runner.list_rows[resource] = [row]
                with self.assertRaises(inventory.InventoryError):
                    inventory._inventory_client(
                        bad_runner, "incus_system", "/run/incus/unix.socket", incus=True,
                        before_query=lambda: None)

    def test_instance_profiles_must_be_present_and_match_detail_responses(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["instances"] = [{
            "name": "web", "project": "alpha", "architecture": "x86_64", "config": {}, "devices": {},
            "ephemeral": False, "expanded_config": {}, "expanded_devices": {}, "stateful": False,
            "status": "Running", "status_code": 103, "type": "container", "location": "none",
            "description": "", "created_at": "2026-10-01T00:00:00Z", "last_used_at": "2026-10-02T00:00:00Z",
        }]
        with self.assertRaises(inventory.InventoryError):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.detail_profiles = ["different"]
        with self.assertRaisesRegex(inventory.InventoryError, "INSTANCE_PROFILE_LIST_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_artifact_schema_size_and_redaction_are_enforced(self) -> None:
        artifact = self._valid_artifact()
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))
        artifact["lxd_projects"] = [{"project": "alpha", "profiles": [], "instances": [], "networks": [],
                                     "pools": [{"name": "pool", "type": "dir", "used_by": [{
                                         "kind": "storage-volumes", "name": "pool/container/web", "project": "alpha"}],
                                                "volumes": [{"name": "web", "type": "container",
                                                             "content_type": "filesystem", "used_by": []}]}]}]
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))
        malformed_volume = self._valid_artifact()
        malformed_volume["lxd_projects"] = [{"project": "alpha", "profiles": [], "instances": [], "networks": [],
                                              "pools": [{"name": "pool", "type": "dir", "used_by": [],
                                                         "volumes": [{"name": "web", "type": "container",
                                                                      "content_type": "filesystem", "used_by": [],
                                                                      "config": {}}]}]}]
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact(malformed_volume)
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact({**artifact, "unexpected": "field"})
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact({**artifact, "lxd_projects": [{"path": "/var/lib/lxd"}]})
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact({**artifact, "target_host": "192.168.178.33"})
        malformed = self._valid_artifact()
        malformed["lxd_units"][0]["active_state"] = "active"
        with self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_UNIT_STATE_INVALID"):
            inventory._validate_artifact(malformed)
        malformed = self._valid_artifact()
        malformed["incus_units"][0]["main_pid"] = True
        with self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_UNIT_VALUE_INVALID"):
            inventory._validate_artifact(malformed)

    def test_output_has_no_raw_argv_or_endpoint_paths_in_command_records(self) -> None:
        runner = inventory.Runner(popen=Mock())
        runner.records.append({"command_id": "lxd_project_list", "safe_args": ["default"],
                              "exit_status": 0, "stdout_bytes": 10, "stderr_bytes": 0})
        artifact = self._valid_artifact(runner.records)
        raw = inventory._validate_artifact(artifact).decode()
        for forbidden in ("argv", "/var/lib/lxd", "/proc/", "https://", "/snap/lxd"):
            self.assertNotIn(forbidden, raw)

    def test_artifact_preserves_typed_project_scoped_consumer_references(self) -> None:
        artifact = self._valid_artifact()
        artifact["lxd_projects"] = [
            {"project": "alpha", "profiles": [], "instances": [],
             "networks": [{"name": "net", "type": "bridge", "used_by": [
                 {"kind": "instances", "name": "web", "project": "beta"}]}], "pools": []},
            {"project": "beta", "profiles": [], "instances": [{"name": "web", "status": "Running",
             "type": "container", "profiles": [], "local_devices": [], "expanded_devices": []}],
             "networks": [], "pools": []},
        ]
        encoded = inventory._validate_artifact(artifact)
        self.assertIn(b'"kind":"instances","name":"web","project":"beta"', encoded)
        malformed = {**artifact, "lxd_projects": [
            {**artifact["lxd_projects"][0], "networks": [{"name": "net", "type": "bridge", "used_by": [
                {"kind": "instances", "name": "web"}]}]}, artifact["lxd_projects"][1]]}
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact(malformed)

    def test_device_entries_are_counted_toward_inventory_entity_cap(self) -> None:
        runner = self._InventoryRunner()
        with patch.object(inventory, "MAX_ENTITIES", 6), self.assertRaisesRegex(inventory.InventoryError, "ENTITY_LIMIT"):
            inventory._inventory_client(runner, "lxd_system", "/var/lib/lxd/unix.socket",
                                        incus=False, before_query=lambda: None)

    def test_runner_timeout_and_aggregate_wall_clock_fail_closed(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 99
        proc.kill = Mock()
        proc.wait.return_value = 0
        ticks = iter((0.0, 0.0, 0.0, inventory.MAX_COMMAND_SECONDS + 1.0,
                      inventory.MAX_COMMAND_SECONDS + 1.0))
        timed = inventory.Runner(popen=Mock(return_value=proc), clock=lambda: next(ticks))
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "killpg"), self.assertRaisesRegex(inventory.InventoryError, "COMMAND_TIMEOUT"):
            timed.run(["/usr/bin/systemctl", "show"], command_id="timeout")
        clock_state = {"now": 0.0}
        bounded = inventory.Runner(popen=Mock(), clock=lambda: clock_state["now"])
        clock_state["now"] = inventory.MAX_WALL_SECONDS + 1.0
        with self.assertRaisesRegex(inventory.InventoryError, "INVENTORY_BUDGET_EXCEEDED"):
            bounded.run(["/usr/bin/systemctl", "show"], command_id="wall")

    def test_aggregate_wall_clock_expiring_during_child_kills_and_fails_closed(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 99
        proc.kill = Mock()
        proc.wait.return_value = 0
        clock_now = 0.0
        clock_sequence: list[float] = []
        def advancing_clock() -> float:
            if clock_sequence:
                return clock_sequence.pop(0)
            return clock_now
        runner = inventory.Runner(popen=Mock(return_value=proc), clock=advancing_clock)
        clock_sequence.extend((inventory.MAX_WALL_SECONDS - 1.0,
                               inventory.MAX_WALL_SECONDS - 1.0,
                               inventory.MAX_WALL_SECONDS - 1.0,
                               inventory.MAX_WALL_SECONDS + 1.0))
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "killpg") as kill_group, \
                self.assertRaisesRegex(inventory.InventoryError, "COMMAND_TIMEOUT"):
            runner.run(["/usr/bin/systemctl", "show"], command_id="aggregate-timeout")
        kill_group.assert_called_once_with(proc.pid, inventory.signal.SIGKILL)
        proc.wait.assert_called()

    def test_serialized_artifact_size_limit_is_enforced(self) -> None:
        with patch.object(inventory, "MAX_ARTIFACT", 1), \
                self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_LIMIT"):
            inventory._validate_artifact(self._valid_artifact())

    def test_capture_failure_does_not_create_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "never-created.json"
            stderr = StringIO()
            with patch.object(inventory, "capture", side_effect=inventory.InventoryError("FIXTURE_FAILURE")), \
                    patch.object(inventory, "_write_private") as write, redirect_stderr(stderr):
                result = inventory.main(["--source-commit", "a" * 40, "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertFalse(output.exists())
            write.assert_not_called()
            self.assertEqual(stderr.getvalue().strip(), "BLOCKED:FIXTURE_FAILURE")

    def test_private_writer_uses_exclusive_owner_only_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = Path("private/evidence/inventory.json")
            target = root / relative
            mountinfo = "29 23 0:26 / / rw,relatime - ext4 /dev/sda rw\n"
            with patch.object(inventory, "ROOT", root), patch.object(inventory, "PRIVATE_REL", relative), \
                    patch.object(Path, "read_text", return_value=mountinfo):
                inventory._write_private(target, b"safe\n")
                self.assertEqual(target.read_bytes(), b"safe\n")
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)
                with self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_PATH_EXISTS"):
                    inventory._write_private(target, b"replacement\n")


class SnapWrapperIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.row = {"unit": "snap.lxd.daemon.service", "load_state": "loaded", "active_state": "active",
                    "sub_state": "running", "unit_file_state": "enabled", "main_pid": 101}

    def test_fallback_normalizes_only_the_snap_unit_after_helper_success(self) -> None:
        from tools.qualification import native_lxd_snap_provenance as proof
        runner = Mock()
        with patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper", return_value=("lxd_snap", "snap:lxd")) as verify:
            self.assertEqual(inventory._resolve_executable(runner, self.row), ("lxd_snap", "snap:lxd"))
        verify.assert_called_once_with(runner, self.row)

    def test_direct_existing_identity_does_not_need_the_helper(self) -> None:
        from tools.qualification import native_lxd_snap_provenance as proof
        with patch.object(inventory, "_read_executable_path", return_value="/snap/lxd/123/bin/lxd"), \
                patch.object(proof, "prove_snap_wrapper") as verify:
            self.assertEqual(inventory._resolve_executable(Mock(), self.row), ("lxd_snap", "snap:lxd"))
        verify.assert_not_called()

    def test_other_units_and_readlink_failures_do_not_reach_fallback(self) -> None:
        from tools.qualification import native_lxd_snap_provenance as proof
        with patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper") as verify:
            with self.assertRaisesRegex(inventory.InventoryError, "^EXECUTABLE_IDENTITY_BLOCKED$"):
                inventory._resolve_executable(Mock(), {**self.row, "unit": "incus.service"})
        verify.assert_not_called()

        with patch.object(inventory, "_read_executable_path", side_effect=inventory.InventoryError("COMMAND_FAILED")), \
                patch.object(proof, "prove_snap_wrapper") as verify:
            with self.assertRaisesRegex(inventory.InventoryError, "^COMMAND_FAILED$"):
                inventory._resolve_executable(Mock(), self.row)
        verify.assert_not_called()

    def test_missing_helper_dependency_is_a_fixed_inventory_error(self) -> None:
        with patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch("importlib.import_module", side_effect=ModuleNotFoundError("secret-value")):
            with self.assertRaisesRegex(inventory.InventoryError, "^SNAP_WRAPPER_METADATA_INVALID$"):
                inventory._resolve_executable(Mock(), self.row)

    def test_failed_proof_blocks_capture_before_endpoint_client_or_artifact_work(self) -> None:
        from tools.qualification import native_lxd_snap_provenance as proof
        inactive = {"unit": "", "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                    "unit_file_state": "", "main_pid": 0, "listen": ""}
        rows = {unit: ({**self.row} if unit == self.row["unit"] else {**inactive, "unit": unit}) for unit in inventory.UNITS}
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper", side_effect=proof.ProvenanceError("SNAP_WRAPPER_CHILD_ABSENT")), \
                patch.object(inventory, "_endpoint") as endpoint, \
                patch.object(inventory, "_inventory_client") as client, \
                patch.object(inventory, "_write_private") as writer:
            with self.assertRaisesRegex(inventory.InventoryError, "^SNAP_WRAPPER_CHILD_ABSENT$"):
                inventory.capture("a" * 40, runner=Mock())
        endpoint.assert_not_called()
        client.assert_not_called()
        writer.assert_not_called()

    def test_successful_proof_still_requires_existing_socket_binding(self) -> None:
        from tools.qualification import native_lxd_snap_provenance as proof
        inactive = {"unit": "", "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                    "unit_file_state": "", "main_pid": 0, "listen": ""}
        rows = {unit: ({**self.row} if unit == self.row["unit"] else {**inactive, "unit": unit}) for unit in inventory.UNITS}
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper", return_value=("lxd_snap", "snap:lxd")), \
                patch.object(inventory, "_endpoint", return_value=("", False)), \
                patch.object(inventory, "_inventory_client") as client:
            with self.assertRaisesRegex(inventory.InventoryError, "^ACTIVE_LXD_SOCKET_MISSING$"):
                inventory.capture("a" * 40, runner=Mock())
        client.assert_not_called()


class SnapContextCliTests(unittest.TestCase):
    def test_invalid_diagnostic_combinations_have_no_host_io_or_leaks(self) -> None:
        cases = (["--diagnose-snap-context=secret"], ["--diagnose-snap-context", "secret"],
                 ["--diagnose-snap-context", "--help"], ["--diagnose-snap-context", "--diagnose-units"],
                 ["--diagnose-snap-context", "--diagnose-snap-context"])
        for argv in cases:
            with self.subTest(argv=argv), patch.object(inventory, "diagnose_snap_context") as diagnose:
                out, err = StringIO(), StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    self.assertEqual(inventory.main(argv), 2)
                self.assertEqual(out.getvalue(), '{"status":"BLOCKED_UNKNOWN","reason":"UNKNOWN"}\n')
                self.assertEqual(err.getvalue(), "")
                diagnose.assert_not_called()

    def test_valid_mode_returns_only_fixed_json(self) -> None:
        out, err = StringIO(), StringIO()
        with patch.object(inventory, "diagnose_snap_context", return_value="CONTROL_GROUP"), \
                redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(inventory.main(["--diagnose-snap-context"]), 2)
        self.assertEqual(out.getvalue(), '{"status":"BLOCKED_UNKNOWN","reason":"CONTROL_GROUP"}\n')
        self.assertEqual(err.getvalue(), "")

    def test_initial_snapshot_failure_and_exceptions_are_sanitized(self) -> None:
        runner = Mock()
        runner.run.side_effect = RuntimeError("secret-token /private/path")
        out, err = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(inventory.main(["--diagnose-snap-context"]), 2)
        self.assertEqual(out.getvalue(), '{"status":"BLOCKED_UNKNOWN","reason":"UNKNOWN"}\n')
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(runner.run.call_count, 1)
        self.assertEqual(runner.run.call_args.args[0][:3], ["/usr/bin/systemctl", "show", "snap.lxd.daemon.service"])

    def test_inactive_snapshot_stops_before_helper(self) -> None:
        row = {"load_state": "loaded", "active_state": "inactive", "sub_state": "dead", "main_pid": 0}
        with patch.object(inventory, "_systemctl_show", return_value=row), \
                patch("importlib.import_module") as importer:
            self.assertEqual(inventory.diagnose_snap_context(runner=Mock()), "UNKNOWN")
        importer.assert_not_called()


if __name__ == "__main__":
    unittest.main()

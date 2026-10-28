"""Regression tests for the fail-closed native runtime inventory."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
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
                out = self._json([{"name": "alpha"}])
            elif suffix == ["project", "show", "alpha", "--format", "json"]:
                out = self._json({"name": "alpha", "config": {}, "used_by": []})
            elif suffix == ["profile", "list", "--project", "alpha", "--format", "json"]:
                out = self._json([{"name": "zeta", "used_by": []}, {"name": "bravo", "used_by": []}])
            elif suffix == ["list", "--project", "alpha", "--format", "json"]:
                out = self._json([{"name": "web", "status": "Running", "type": "container", "profiles": ["default"]}])
            elif suffix == ["network", "list", "--project", "alpha", "--format", "json"]:
                out = self._json([{"name": "net", "type": "bridge", "managed": True, "used_by": []}])
            elif suffix == ["storage", "list", "--project", "alpha", "--format", "json"]:
                out = self._json([{"name": "pool", "driver": "dir", "used_by": []}])
            elif len(suffix) >= 3 and suffix[0] == "profile" and suffix[1] == "show" and suffix[3:] == ["--project", "alpha", "--format", "json"]:
                profile = {"name": suffix[2], "project": "alpha", "description": "", "config": {},
                           "devices": {"eth0": {"type": "nic", "parent": "br0"}},
                           "used_by": ["/1.0/instances/web?project=beta", "/1.0/networks/web?project=alpha"]}
                out = self._json(profile)
            elif suffix == ["config", "show", "web", "--project", "alpha", "--format", "json"]:
                out = self._json({"name": "web", "project": "alpha", "config": {}, "devices": {},
                                  "ephemeral": False, "profiles": ["default"], "stateful": False})
            elif suffix == ["config", "show", "web", "--project", "alpha", "--format", "json", "--expanded"]:
                out = self._json({"name": "web", "project": "alpha", "config": {}, "devices": {},
                                  "ephemeral": False, "profiles": ["default"], "stateful": False})
            elif suffix == ["network", "show", "net", "--project", "alpha", "--format", "json"]:
                out = self._json({"name": "net", "project": "alpha", "type": "bridge", "managed": True,
                                  "config": {}, "used_by": []})
            elif suffix == ["storage", "show", "pool", "--project", "alpha", "--format", "json"]:
                out = self._json({"name": "pool", "project": "alpha", "driver": "dir", "config": {}, "used_by": []})
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
        for mutation in ({**row, "MainPID": "5"}, {**row, "Listen": "/tmp/evil.sock"},
                         {**row, "SubState": "running"}):
            with self.subTest(mutation=mutation), self.assertRaises(inventory.InventoryError):
                inventory._unit_state("incus.socket", mutation)

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
        ])
        self.assertTrue(all(call[1] == {**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/lxd/unix.socket"}
                            for call in runner.calls))
        self.assertEqual([row["name"] for row in projects[0]["profiles"]], ["bravo", "zeta"])
        self.assertEqual(projects[0]["profiles"][0]["used_by"], [
            {"kind": "instances", "name": "web", "project": "beta"},
            {"kind": "networks", "name": "web", "project": "alpha"},
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
        unit_rows = {"lxd.service": active("lxd.service", 42),
                     "snap.lxd.daemon.service": missing("snap.lxd.daemon.service"),
                     "snap.lxd.daemon.unix.socket": missing("snap.lxd.daemon.unix.socket", True),
                     "incus.service": missing("incus.service"), "incus.socket": missing("incus.socket", True)}
        endpoint_present = "/var/lib/lxd/unix.socket"
        checked: list[bool] = []
        real_recheck = inventory._recheck_all
        def record_recheck(*args: Any) -> None:
            checked.append(True)
            real_recheck(*args)
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: dict(unit_rows[unit])), \
                patch.object(inventory, "_resolve_executable", return_value=("lxd_system", "system:lxd")), \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit: (inventory.SOCKETS[path], path == endpoint_present)), \
                patch.object(inventory, "_recheck_all", side_effect=record_recheck):
            artifact = inventory.capture("a" * 40, runner=runner)
        self.assertEqual(len(checked), len(runner.calls) + 1)
        self.assertEqual(artifact["decision"], "READ_ONLY_INVENTORY_COMPLETE")
        self.assertEqual([row["name"] for row in artifact["lxd_projects"][0]["profiles"]], ["bravo", "zeta"])
        self.assertEqual([row["name"] for row in artifact["lxd_projects"][0]["networks"]], ["net"])

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
                    patch.object(inventory, "_write_private") as write, redirect_stderr(stderr):
                result = inventory.main(["--source-commit", "a" * 40, "--output", str(artifact)])
            self.assertEqual(result, 2)
            self.assertFalse(artifact.exists())
            self.assertEqual(runner.calls, [])
            self.assertEqual(counts["lxd.service"], 2)
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

    def test_artifact_schema_size_and_redaction_are_enforced(self) -> None:
        artifact = self._valid_artifact()
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))
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
        artifact["lxd_projects"] = [{"project": "alpha", "profiles": [
            {"name": "default", "used_by": [{"kind": "instances", "name": "web", "project": "beta"},
                                               {"kind": "networks", "name": "web", "project": "alpha"}],
             "devices": []}], "instances": [], "networks": [], "pools": []}]
        encoded = inventory._validate_artifact(artifact)
        self.assertIn(b'"kind":"instances","name":"web","project":"beta"', encoded)
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact({**artifact, "lxd_projects": [
                {**artifact["lxd_projects"][0], "profiles": [
                    {**artifact["lxd_projects"][0]["profiles"][0], "used_by": [
                        {"kind": "instances", "name": "web"}]}]}]})

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


if __name__ == "__main__":
    unittest.main()

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from ruamel.yaml import YAML


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DRIVER_PATH = REPOSITORY_ROOT / ".tiny-swarm/evidence/issue-449/wsl-r46-live-driver.py"
SOURCE_PORTS_PATH = REPOSITORY_ROOT / "infra/config/ports.yaml"
DRIVER = None
if DRIVER_PATH.is_file():
    SPEC = importlib.util.spec_from_file_location("wsl_r46_live_driver", DRIVER_PATH)
    assert SPEC is not None and SPEC.loader is not None
    DRIVER = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = DRIVER
    SPEC.loader.exec_module(DRIVER)


def _ports_document():
    yaml = YAML(typ="safe")
    yaml.allow_duplicate_keys = False
    return yaml.load(SOURCE_PORTS_PATH.read_text(encoding="utf-8"))


@unittest.skipUnless(DRIVER_PATH.is_file(), "private R46 driver artifact is not part of a source checkout")
class R46PortsPolicyTests(unittest.TestCase):
    def setUp(self):
        self.source = _ports_document()
        self.source["ports"][1]["route_host"] = "tsw.local"
        self.target = deepcopy(self.source)
        self.target["ports"][1]["route_host"] = "traefik.tsw.local"

    def test_accepts_only_reviewed_host_change_in_eighteen_route_fields(self):
        self.assertEqual(
            sum("route_host" in item for item in self.source["ports"]),
            DRIVER.EXPECTED_PORTS_ROUTE_COUNT,
        )
        result = DRIVER.validate_ports_configuration(self.source, self.target)
        self.assertEqual(result["route_host_change"], ["tsw.local", "traefik.tsw.local"])
        self.assertEqual(result["route_host_path"], ["ports", 1, "route_host"])
        self.assertTrue(result["published_ports_unchanged"])

    def test_rejects_second_route_host_change(self):
        self.target["ports"][0]["route_host"] = "other.tsw.local"
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(self.source, self.target)

    def test_rejects_unrelated_port_change(self):
        self.target["ports"][0]["external_port"] += 1
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(self.source, self.target)

    def test_rejects_missing_route_host(self):
        del self.target["ports"][2]["route_host"]
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(self.source, self.target)

    def test_rejects_added_route_host(self):
        item = next(item for item in self.target["ports"] if "route_host" not in item)
        item["route_host"] = "unexpected.tsw.local"
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(self.source, self.target)

    def test_rejects_wrong_or_reversed_route_change(self):
        self.target["ports"][1]["route_host"] = "tsw.local"
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(self.source, self.target)
        self.target["ports"][1]["route_host"] = "unknown.tsw.local"
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(self.source, self.target)

        reversed_source = deepcopy(self.source)
        reversed_target = deepcopy(self.source)
        reversed_source["ports"][1]["route_host"] = "traefik.tsw.local"
        reversed_target["ports"][1]["route_host"] = "tsw.local"
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(reversed_source, reversed_target)

    def test_rejects_non_string_route_host(self):
        self.target["ports"][1]["route_host"] = 443
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.validate_ports_configuration(self.source, self.target)


@unittest.skipUnless(DRIVER_PATH.is_file(), "private R46 driver artifact is not part of a source checkout")
class R46StatePathPolicyTests(unittest.TestCase):
    def test_accepts_absent_state_directories_inside_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            DRIVER.validate_state_directory_ancestors(
                source, (source / ".tiny-swarm-world" / "installation",)
            )

    def test_rejects_symlinked_product_state_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            outside = root / "outside"
            source.mkdir()
            outside.mkdir()
            os.symlink(outside, source / ".tiny-swarm-world", target_is_directory=True)
            with self.assertRaises(DRIVER.DriverError):
                DRIVER.validate_state_directory_ancestors(
                    source, (source / ".tiny-swarm-world" / "installation",)
                )

    def test_rejects_symlinked_nested_state_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            outside = root / "outside"
            state = source / ".tiny-swarm-world"
            source.mkdir()
            state.mkdir()
            outside.mkdir()
            os.symlink(outside, state / "installation", target_is_directory=True)
            with self.assertRaises(DRIVER.DriverError):
                DRIVER.validate_state_directory_ancestors(
                    source, (state / "installation",)
                )

    def test_rejects_state_root_outside_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            outside = root / "outside"
            source.mkdir()
            outside.mkdir()
            with self.assertRaises(DRIVER.DriverError):
                DRIVER.validate_state_directory_ancestors(source, (outside,))

    def test_rejects_mounted_nested_state_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            installation = source / ".tiny-swarm-world" / "installation"
            installation.mkdir(parents=True)
            with patch.object(DRIVER, "read_linux_mountpoints", return_value={installation}):
                with self.assertRaises(DRIVER.DriverError):
                    DRIVER.validate_state_directory_ancestors(source, (installation,))

    def test_mountinfo_parser_decodes_escaped_mountpoint(self):
        parsed = DRIVER.parse_linux_mountinfo_mountpoints(
            b"36 25 0:32 / /source/.tiny-swarm-world/installation\\040state rw,nosuid - ext4 /dev/sda rw\n"
        )
        self.assertIn(Path("/source/.tiny-swarm-world/installation state"), parsed)

    def test_mountinfo_parser_rejects_malformed_records_and_escapes(self):
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.parse_linux_mountinfo_mountpoints(b"not-a-mountinfo-record\n")
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.parse_linux_mountinfo_mountpoints(
                b"36 25 0:32 / /source\\bad rw,nosuid - ext4 /dev/sda rw\n"
            )
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.parse_linux_mountinfo_mountpoints(
                b"36 25 0:32 / /source rw,nosuid x x x -\n"
            )
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.parse_linux_mountinfo_mountpoints(
                b"36 25 0:32 / /source\\777 rw,nosuid - ext4 /dev/sda rw\n"
            )
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.parse_linux_mountinfo_mountpoints(
                b"bad-id 25 0:32 / /source rw,nosuid - ext4 /dev/sda rw\n"
            )
        with self.assertRaises(DRIVER.DriverError):
            DRIVER.parse_linux_mountinfo_mountpoints(
                b"36 25 0:32 / /source rw,nosuid - ext4 /dev/sda rw extra\n"
            )


@unittest.skipUnless(DRIVER_PATH.is_file(), "private R46 driver artifact is not part of a source checkout")
class R46RuntimeJitComparisonTests(unittest.TestCase):
    def test_ignores_only_volatile_host_capacity_gauges(self):
        first = {
            "host": {
                "host_kind": "wsl2",
                "host_name": "qualification-host",
                "memory_total_bytes": 24 * 1024**3,
                "memory_available_bytes": 20 * 1024**3,
                "attempt_free_bytes": 100 * 1024**3,
            },
            "incus": {"instances": [{"uuid": "manager-a"}]},
            "writer_count": 0,
        }
        second = deepcopy(first)
        second["host"]["memory_available_bytes"] += 256 * 1024**2
        second["host"]["attempt_free_bytes"] -= 4096
        self.assertEqual(
            DRIVER.stable_runtime_projection(first),
            DRIVER.stable_runtime_projection(second),
        )
        self.assertNotEqual(first["host"]["memory_available_bytes"], second["host"]["memory_available_bytes"])
        self.assertNotEqual(first["host"]["attempt_free_bytes"], second["host"]["attempt_free_bytes"])

    def test_keeps_every_runtime_identity_and_inventory_field_strict(self):
        first = {
            "host": {
                "host_kind": "wsl2",
                "host_name": "qualification-host",
                "memory_total_bytes": 24 * 1024**3,
                "memory_available_bytes": 20 * 1024**3,
                "attempt_free_bytes": 100 * 1024**3,
            },
            "incus": {"instances": [{"uuid": "manager-a"}]},
            "writer_count": 0,
        }
        for path, value in (
            (("host", "host_name"), "different-host"),
            (("host", "memory_total_bytes"), 18 * 1024**3),
            (("incus", "instances"), [{"uuid": "manager-b"}]),
            (("writer_count",), 1),
        ):
            changed = deepcopy(first)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            self.assertNotEqual(
                DRIVER.stable_runtime_projection(first),
                DRIVER.stable_runtime_projection(changed),
            )

    def test_host_capacity_requires_admitted_memory_and_free_disk(self):
        baseline = {
            "host_kind": "wsl2",
            "host_name": "qualification-host",
            "memory_total_bytes": DRIVER.MINIMUM_HOST_MEMORY_BYTES,
            "memory_available_bytes": DRIVER.MINIMUM_AVAILABLE_MEMORY_BYTES,
            "attempt_free_bytes": DRIVER.EXPECTED_MIN_FREE_BYTES,
        }
        expected_host = {"host_name": "qualification-host"}
        DRIVER.validate_host_capacity(baseline, expected_host)

        for field, below_threshold in (
            ("memory_total_bytes", DRIVER.MINIMUM_HOST_MEMORY_BYTES - 1),
            ("memory_available_bytes", DRIVER.MINIMUM_AVAILABLE_MEMORY_BYTES - 1),
            ("attempt_free_bytes", DRIVER.EXPECTED_MIN_FREE_BYTES - 1),
        ):
            with self.subTest(field=field):
                changed = deepcopy(baseline)
                changed[field] = below_threshold
                with self.assertRaises(DRIVER.DriverError):
                    DRIVER.validate_host_capacity(changed, expected_host)

    def test_host_capacity_requires_exact_wsl_identity(self):
        baseline = {
            "host_kind": "wsl2",
            "host_name": "qualification-host",
            "memory_total_bytes": DRIVER.MINIMUM_HOST_MEMORY_BYTES,
            "memory_available_bytes": DRIVER.MINIMUM_AVAILABLE_MEMORY_BYTES,
            "attempt_free_bytes": DRIVER.EXPECTED_MIN_FREE_BYTES,
        }
        for field, wrong_value in (("host_kind", "linux"), ("host_name", "other-host")):
            with self.subTest(field=field):
                changed = deepcopy(baseline)
                changed[field] = wrong_value
                with self.assertRaises(DRIVER.DriverError):
                    DRIVER.validate_host_capacity(changed, {"host_name": "qualification-host"})


if __name__ == "__main__":
    unittest.main()

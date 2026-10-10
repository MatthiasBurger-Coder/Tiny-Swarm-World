"""Canonical resource projection and executable mocked preparation checks."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.test_prepare_windows import WINDOWS_POWERSHELL, _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "wsl_projection", ROOT / "tools/build_wsl_resource_projection.py"
)
assert SPEC and SPEC.loader
projection = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(projection)


class TestResourceProjection(unittest.TestCase):
    def test_committed_projection_equals_canonical_sources_and_node_limits(self) -> None:
        expected = projection.build(ROOT)
        self.assertEqual(json.loads((ROOT / projection.OUTPUT).read_text()), expected)
        self.assertEqual(expected["node_budget"], {"memory_gib": 19, "processors": 8, "disk_gib": 80})
        self.assertEqual(expected["profiles"]["service-access"]["memory_gib"], 16)
        self.assertEqual(expected["profiles"]["service-access"]["disk_gib"], 150)

    def test_changed_provider_changes_provenance_and_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for source in projection.SOURCES:
                target = root / source
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / source).read_bytes())
            provider = root / projection.SOURCES[2]
            provider.write_text(provider.read_text().replace("memory: 10GiB", "memory: 11GiB"))
            altered = projection.build(root)
            self.assertEqual(altered["node_budget"]["memory_gib"], 20)
            self.assertNotEqual(altered["sources"], projection.build(ROOT)["sources"])

    def test_selected_source_different_from_imported_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for source in projection.SOURCES:
                target = root / source
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / source).read_bytes())
            changed = root / projection.SOURCES[0]
            changed.write_text(changed.read_text().replace("service_access_memory = 16", "service_access_memory = 18"))
            with self.assertRaisesRegex(ValueError, "differ from imported"):
                projection.build(root)

    def test_ambiguous_and_unknown_provider_amounts_are_rejected(self) -> None:
        for value in ("0GiB", "2GB", "1.5GiB", "-1GiB", "bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                projection._amount(value)

    def test_effective_probe_respects_nested_and_parent_cgroup_limits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "group" / "nested"
            nested.mkdir(parents=True)
            (root / "group/memory.max").write_text(str(18 * 1024**3))
            (nested / "memory.max").write_text("max")
            identity = root / "identity"
            identity.write_text("0::/group/nested\n")
            meminfo = root / "meminfo"
            meminfo.write_text("MemTotal: 24000000 kB\nSwapTotal: 6000000 kB\n")
            script = (ROOT / "tools/windows/preparation/linux-resources.sh").read_text()
            script = script.replace("/sys/fs/cgroup", str(root)).replace("/proc/self/cgroup", str(identity)).replace("/proc/meminfo", str(meminfo))
            result = subprocess.run(["sh", "-s"], input=script, text=True, capture_output=True, timeout=10, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"effective_memory_bytes={18 * 1024**3}", result.stdout)
            # Real cgroup-v2 roots do not expose memory.max, including when
            # the process belongs directly to the root rather than a child.
            identity.write_text("0::/\n")
            root_scoped = subprocess.run(["sh", "-s"], input=script, text=True, capture_output=True, timeout=10, check=False)
            self.assertEqual(root_scoped.returncode, 0, root_scoped.stderr)
            self.assertIn(f"effective_memory_bytes={24000000 * 1024}", root_scoped.stdout)
            identity.write_text("0::/group/nested\n")
            for unknown in (None, "invalid"):
                with self.subTest(non_root_limit=unknown):
                    parent_limit = root / "group/memory.max"
                    if unknown is None:
                        parent_limit.unlink()
                    else:
                        parent_limit.write_text(unknown)
                    refused = subprocess.run(["sh", "-s"], input=script, text=True, capture_output=True, timeout=10, check=False)
                    self.assertEqual(refused.returncode, 2)
                    self.assertEqual(refused.stdout, "")
            identity.write_text("0::/../unsafe\n")
            refused = subprocess.run(["sh", "-s"], input=script, text=True, capture_output=True, timeout=10, check=False)
            self.assertEqual(refused.returncode, 2)

    @unittest.skipUnless(WINDOWS_POWERSHELL.exists(), "Windows PowerShell unavailable for disposable ACL tests")
    def test_disposable_windows_file_and_acl_boundaries(self) -> None:
        executable = str(WINDOWS_POWERSHELL)
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/windows/resource-files.Tests.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            capture_output=True, text=True, timeout=90, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("disposable Windows resource file assertions", result.stdout)

    @unittest.skipUnless(_powershell(), "PowerShell unavailable")
    def test_executable_policy_config_and_provenance_contracts(self) -> None:
        executable = _powershell()
        assert executable
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/windows/resources.Tests.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            capture_output=True, text=True, timeout=90, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("resource assertions", result.stdout)


if __name__ == "__main__":
    unittest.main()

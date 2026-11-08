"""EPIC 503 separation checks; all executable handoffs use disposable stubs."""
from __future__ import annotations

import ast
import json
import os
import runpy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.test_prepare_windows import _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[2]
MODULES = ("tsw_core", "tsw_native_linux", "tsw_windows_wsl")


def check_boundaries(root: Path) -> None:
    """Check declared edges, required assets and executable edition references."""
    for name in MODULES:
        descriptor = json.loads((root / "src" / name / "module.json").read_text())
        expected = [] if name == "tsw_core" else ["tsw_core"]
        if descriptor["name"] != name or descriptor["project_dependencies"] != expected:
            raise AssertionError(f"Invalid dependency boundary: {name}")
        assets = descriptor.get("owned_assets", descriptor.get("shared_bootstrap", []))
        for asset in assets + descriptor.get("required_assets", []):
            path = root / asset
            if not path.exists():
                raise AssertionError(f"Missing {name} asset: {asset}")
        sources: list[Path] = []
        if name == "tsw_core":
            sources.extend((root / "src/tiny_swarm_world").rglob("*.py"))
            sources.extend((root / "src/tsw_core").rglob("*.py"))
        for asset in assets:
            path = root / asset
            sources.extend(path.rglob("*") if path.is_dir() else [path])
        forbidden = set(MODULES) - {name, *expected}
        for source in sources:
            if not source.is_file() or source.suffix not in (".py", ".sh", ".ps1", ".psm1", ""):
                continue
            text = source.read_text()
            if source.suffix == ".py":
                for node in ast.walk(ast.parse(text)):
                    names = ([item.name for item in node.names] if isinstance(node, ast.Import)
                             else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                    if any(item.split(".")[0] in forbidden for item in names):
                        raise AssertionError(f"Forbidden import: {source}")
            if source.suffix != ".py" and name in ("tsw_native_linux", "tsw_core") and "bootstrap/windows/" in text:
                raise AssertionError(f"Forbidden edition path: {source}")
            if name == "tsw_windows_wsl" and any(token in text for token in
                    ("exec ./install.sh", "'install.sh'", '"install.sh"', "exec ./tsw")):
                raise AssertionError(f"WSL invokes native entry point: {source}")


class EditionModuleTests(unittest.TestCase):
    def test_declared_boundaries_and_assets(self):
        check_boundaries(ROOT)

    def test_checker_detects_forbidden_edges_imports_and_missing_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src/tiny_swarm_world").mkdir(parents=True)
            for name in MODULES:
                path = root / "src" / name
                path.mkdir(exist_ok=True)
                descriptor = {"name": name, "project_dependencies": [] if name == "tsw_core" else ["tsw_core"],
                              "owned_assets": []}
                (path / "module.json").write_text(json.dumps(descriptor))
            check_boundaries(root)
            for owner, dependency in (("tsw_core", "tsw_windows_wsl"),
                                      ("tsw_windows_wsl", "tsw_native_linux"),
                                      ("tsw_native_linux", "tsw_windows_wsl")):
                path = root / "src" / owner / "module.json"
                original = path.read_text()
                descriptor = json.loads(original)
                descriptor["project_dependencies"].append(dependency)
                path.write_text(json.dumps(descriptor))
                with self.assertRaises(AssertionError):
                    check_boundaries(root)
                path.write_text(original)
            injected = root / "src/tiny_swarm_world/invalid.py"
            injected.write_text("import tsw_windows_wsl\n")
            with self.assertRaises(AssertionError):
                check_boundaries(root)
            injected.unlink()
            for owner, text in (("tsw_native_linux", 'exec "$ROOT/bootstrap/windows/prepare_windows.ps1"'),
                                ("tsw_windows_wsl", "exec ./install.sh")):
                script = root / "bad.sh"
                script.write_text(text)
                descriptor_path = root / "src" / owner / "module.json"
                original = descriptor_path.read_text()
                descriptor = json.loads(original)
                descriptor["owned_assets"] = ["bad.sh"]
                descriptor_path.write_text(json.dumps(descriptor))
                with self.assertRaises(AssertionError):
                    check_boundaries(root)
                descriptor_path.write_text(original)
                script.unlink()
            path = root / "src/tsw_core/module.json"
            descriptor = json.loads(path.read_text())
            descriptor["owned_assets"] = ["missing-shared-script.sh"]
            path.write_text(json.dumps(descriptor))
            with self.assertRaises(AssertionError):
                check_boundaries(root)

    def test_native_public_entry_points_delegate_without_wsl_assets(self):
        with tempfile.TemporaryDirectory(prefix="tsw module ") as temporary:
            root = Path(temporary)
            (root / "bootstrap/linux").mkdir(parents=True)
            (root / "src/tiny_swarm_world").mkdir(parents=True)
            binary = root / "bin"
            binary.mkdir()
            python = binary / "python3"
            python.write_text('#!' + sys.executable + '\nimport json,os,sys\n'
                              'print(json.dumps({"argv":sys.argv[1:],"cwd":os.getcwd(),'
                              '"pythonpath":os.environ.get("PYTHONPATH"),'
                              '"marker":os.environ.get("TSW_FIXTURE_MARKER")}))\n'
                              'raise SystemExit(int(os.environ["TSW_FIXTURE_EXIT"]))\n')
            python.chmod(0o755)
            for public, core, module in (("install.sh", "install.sh", "tiny_swarm_world.simple_installer"),
                                         ("tsw", "run.sh", "tiny_swarm_world")):
                shutil.copy2(ROOT / public, root / public)
                shutil.copy2(ROOT / "bootstrap/linux" / core, root / "bootstrap/linux" / core)
                for status in (0, 17, 130):
                    arguments = ["--service-profile", "default", "space argument", "quote'\"$literal"]
                    env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                           "PYTHONPATH": "supplied", "TSW_FIXTURE_EXIT": str(status), "TSW_FIXTURE_MARKER": "preserved"}
                    result = subprocess.run([str(root / public), *arguments], cwd="/", env=env,
                                            text=True, capture_output=True, timeout=15)
                    self.assertEqual(result.returncode, status, result.stderr)
                    observed = json.loads(result.stdout)
                    self.assertEqual(observed["argv"], ["-m", module, *arguments])
                    self.assertEqual(observed["cwd"], str(root))
                    self.assertEqual(observed["pythonpath"], "supplied:src")
                    self.assertEqual(observed["marker"], "preserved")
                result = subprocess.run([str(root / public), "--help"], cwd="/", env={**env, "TSW_FIXTURE_EXIT": "0"},
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "bootstrap/windows").exists())

    def test_windows_release_proof_needs_core_but_no_native_assets(self):
        builder = runpy.run_path(str(ROOT / "tools/windows/build_windows_preparation_manifest.py"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (*builder["ASSETS"], "install.sh", "tsw", "src/tsw_native_linux/module.json"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n")
            def git(*arguments):
                return subprocess.run(["git", "-C", str(root), *arguments], check=True,
                                      capture_output=True, timeout=15).stdout
            git("init", "--quiet")
            git("add", ".")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture")
            for relative in ("install.sh", "tsw", "src/tsw_native_linux/module.json"):
                (root / relative).unlink()
            manifest = builder["build"](root)
            self.assertEqual(manifest["revision"], git("rev-parse", "HEAD").decode().strip())
            (root / "bootstrap/linux/install.sh").write_text("edited core\n")
            with self.assertRaises(ValueError):
                builder["build"](root)

    def test_touched_shell_syntax(self):
        for relative in ("install.sh", "tsw", "bootstrap/linux/install.sh", "bootstrap/linux/run.sh",
                         "bootstrap/windows/preparation/linux-handoff.sh"):
            result = subprocess.run(["bash", "-n", str(ROOT / relative)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(_powershell(), "PowerShell runtime required for isolated WSL delegation")
    def test_windows_public_entrypoint_and_stubbed_wsl_delegation(self):
        executable = _powershell()
        result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                                 _runtime_path(ROOT / "tests/windows/module-delegation.Tests.ps1", executable),
                                 "-RepositoryRoot", _runtime_path(ROOT, executable)],
                                capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

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

from modules.tsw_windows_wsl.tests.test_prepare_windows import _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[4]
MODULES = ("tsw_core", "tsw_native_linux", "tsw_windows_wsl")


def descriptor_path(root: Path, name: str) -> Path:
    module = root / "modules" / name
    return module / "src/module.json" if name == "tsw_core" else module / "module.json"


def check_boundaries(root: Path) -> None:
    """Check declared edges, required assets and executable edition references."""
    for name in MODULES:
        descriptor = json.loads(descriptor_path(root, name).read_text())
        expected = [] if name == "tsw_core" else ["tsw_core", "tsw_native_linux"] if name == "tsw_windows_wsl" else ["tsw_core"]
        if descriptor["name"] != name or descriptor["project_dependencies"] != expected:
            raise AssertionError(f"Invalid dependency boundary: {name}")
        assets = descriptor.get("owned_assets", descriptor.get("shared_bootstrap", []))
        for asset in assets + descriptor.get("required_assets", []):
            path = root / asset
            if not path.exists():
                raise AssertionError(f"Missing {name} asset: {asset}")
        sources: list[Path] = []
        if name == "tsw_core":
            sources.extend((root / "modules/tsw_core/src").rglob("*.py"))
            sources.append(root / "modules/tsw_core/__init__.py")
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
                    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                        literals = [item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)]
                        if any(owner in literal for owner in forbidden for literal in literals):
                            raise AssertionError(f"Forbidden edition path construction: {source}")
                    names = ([item.name for item in node.names] if isinstance(node, ast.Import)
                             else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                    if any(forbidden.intersection(item.split(".")) for item in names):
                        raise AssertionError(f"Forbidden import: {source}")
            if source.suffix != ".py" and name in ("tsw_native_linux", "tsw_core") and "modules/tsw_windows_wsl/bootstrap/" in text:
                raise AssertionError(f"Forbidden edition path: {source}")
            if name == "tsw_windows_wsl" and any(token in text for token in
                    ("exec ./install.sh", "'install.sh'", '"install.sh"', "exec ./tsw")):
                raise AssertionError(f"WSL invokes native entry point: {source}")


class EditionModuleTests(unittest.TestCase):
    def test_declared_boundaries_and_assets(self):
        check_boundaries(ROOT)

    def test_implementations_are_physically_owned_and_legacy_trees_only_forward(self):
        core = ROOT / "modules/tsw_core"
        self.assertTrue((core / "src/application/services").is_dir())
        self.assertTrue((core / "infra/config/compose").is_dir())
        self.assertGreater(len(list((core / "src").rglob("*.py"))), 100)
        for old in ("infra/config", "src/tiny_swarm_world/domain", "src/tiny_swarm_world/application",
                    "src/tiny_swarm_world/infrastructure"):
            self.assertFalse((ROOT / old).exists(), old)
        for name in ("install.sh", "tsw"):
            self.assertIn("modules/tsw_native_linux/" + name, (ROOT / name).read_text())
            self.assertIn("$SCRIPT_DIR/boostrap/", (ROOT / "modules/tsw_native_linux" / name).read_text())
        self.assertNotIn("function Invoke-", (ROOT / "modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1").read_text())
        self.assertIn("Invoke-WindowsPreparation", (ROOT / "modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1").read_text())
        for module in MODULES:
            self.assertFalse((ROOT / "modules" / module).is_symlink())

    def test_compatibility_imports_resolve_the_same_physical_core(self):
        code = ("import json,tiny_swarm_world,tsw_core; "
                "print(json.dumps([tiny_swarm_world.__file__,tsw_core.__file__,str(tsw_core.discover_root())]))")
        observations = []
        for bootstrap in ("", "import modules.tsw_core.src; "):
            result = subprocess.run([sys.executable, "-c", bootstrap + code], cwd=ROOT,
                                    env={**os.environ, "PYTHONPATH": str(ROOT)},
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            observations.append(json.loads(result.stdout))
        self.assertEqual(observations[0], observations[1])
        self.assertIn("modules/tsw_core/src", observations[0][0])
        self.assertEqual(observations[0][2], str(ROOT))

    def test_legacy_tool_alias_and_public_python_wrappers(self):
        code = ("import importlib.util,sys; "
                "from modules.tsw_native_linux.tools.live import secure_runtime_paths as legacy; "
                "from tiny_swarm_world.infrastructure.adapters import secure_runtime_paths as actual; "
                "assert legacy is actual; "
                "spec=importlib.util.spec_from_file_location('compat_secure', 'modules/tsw_native_linux/tools/live/secure_runtime_paths.py'); "
                "module=importlib.util.module_from_spec(spec); sys.modules['compat_secure']=module; "
                "spec.loader.exec_module(module); assert sys.modules['compat_secure'] is actual")
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                                env={**os.environ, "PYTHONPATH": str(ROOT / "modules/tsw_core/src")},
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        for entry in ("modules/tsw_native_linux/boostrap/install_debugger.py", "modules/tsw_native_linux/boostrap/preflight.py", "modules/tsw_native_linux/tools/quality_gate.py"):
            arguments = [sys.executable, str(ROOT / entry), "--help"]
            # preflight preserves its documented --preflight prefix and forwards
            # --help to the core CLI; every invocation remains read-only.
            result = subprocess.run(arguments, cwd=ROOT, env={**os.environ, "PYTHONPATH": "."},
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_checker_detects_forbidden_edges_imports_and_missing_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "modules/tsw_core/src").mkdir(parents=True)
            for name in MODULES:
                path = descriptor_path(root, name).parent
                path.mkdir(parents=True, exist_ok=True)
                descriptor = {"name": name, "project_dependencies": [] if name == "tsw_core" else ["tsw_core", "tsw_native_linux"] if name == "tsw_windows_wsl" else ["tsw_core"],
                              "owned_assets": []}
                (path / "module.json").write_text(json.dumps(descriptor))
            check_boundaries(root)
            for owner, dependency in (("tsw_core", "tsw_windows_wsl"),
                                      ("tsw_windows_wsl", "tsw_windows_wsl"),
                                      ("tsw_native_linux", "tsw_windows_wsl")):
                path = descriptor_path(root, owner)
                original = path.read_text()
                descriptor = json.loads(original)
                descriptor["project_dependencies"].append(dependency)
                path.write_text(json.dumps(descriptor))
                with self.assertRaises(AssertionError):
                    check_boundaries(root)
                path.write_text(original)
            injected = root / "modules/tsw_core/src/invalid.py"
            for content in ("import tsw_windows_wsl\n", "import modules.tsw_windows_wsl\n",
                            'asset = root / "modules/tsw_windows_wsl/bootstrap"\n'):
                injected.write_text(content)
                with self.assertRaises(AssertionError):
                    check_boundaries(root)
            injected.unlink()
            for owner, text in (("tsw_native_linux", 'exec "$ROOT/modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1"'),
                                ("tsw_windows_wsl", "exec ./install.sh")):
                script = root / "bad.sh"
                script.write_text(text)
                descriptor_file = descriptor_path(root, owner)
                original = descriptor_file.read_text()
                descriptor = json.loads(original)
                descriptor["owned_assets"] = ["bad.sh"]
                descriptor_file.write_text(json.dumps(descriptor))
                with self.assertRaises(AssertionError):
                    check_boundaries(root)
                descriptor_file.write_text(original)
                script.unlink()
            path = root / "modules/tsw_core/src/module.json"
            descriptor = json.loads(path.read_text())
            descriptor["owned_assets"] = ["missing-shared-script.sh"]
            path.write_text(json.dumps(descriptor))
            with self.assertRaises(AssertionError):
                check_boundaries(root)

    def test_native_public_entry_points_delegate_without_wsl_assets(self):
        with tempfile.TemporaryDirectory(prefix="tsw module ") as temporary:
            root = Path(temporary)
            (root / "modules/tsw_native_linux/boostrap").mkdir(parents=True)
            (root / "modules/tsw_native_linux").mkdir(parents=True, exist_ok=True)
            (root / "modules/tsw_core/src").mkdir(parents=True)
            binary = root / "bin"
            binary.mkdir()
            python = binary / "python3"
            python.write_text('#!' + sys.executable + '\nimport json,os,sys\n'
                              'print(json.dumps({"argv":sys.argv[1:],"cwd":os.getcwd(),'
                              '"pythonpath":os.environ.get("PYTHONPATH"),'
                              '"marker":os.environ.get("TSW_FIXTURE_MARKER"),"stdin":sys.stdin.read()}))\n'
                              'raise SystemExit(int(os.environ["TSW_FIXTURE_EXIT"]))\n')
            python.chmod(0o755)
            for public, core, module in (("install.sh", "install.sh", "modules.tsw_core.src.simple_installer"),
                                         ("tsw", "run.sh", "modules.tsw_core.src")):
                shutil.copy2(ROOT / public, root / public)
                shutil.copy2(ROOT / "modules/tsw_native_linux" / public, root / "modules/tsw_native_linux" / public)
                shutil.copy2(ROOT / "modules/tsw_native_linux/boostrap" / core, root / "modules/tsw_native_linux/boostrap" / core)
                for status in (0, 17, 130):
                    arguments = ["--service-profile", "default", "space argument", "quote'\"$literal"]
                    env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                           "PYTHONPATH": "supplied", "TSW_FIXTURE_EXIT": str(status), "TSW_FIXTURE_MARKER": "preserved"}
                    result = subprocess.run([str(root / public), *arguments], cwd="/", env=env, input="forwarded stdin",
                                            text=True, capture_output=True, timeout=15)
                    self.assertEqual(result.returncode, status, result.stderr)
                    observed = json.loads(result.stdout)
                    self.assertEqual(observed["argv"], ["-m", module, *arguments])
                    self.assertEqual(observed["cwd"], str(root))
                    self.assertEqual(observed["pythonpath"], "supplied:.")
                    self.assertEqual(observed["marker"], "preserved")
                    self.assertEqual(observed["stdin"], "forwarded stdin")
                physical = subprocess.run([str(root / "modules/tsw_native_linux" / public), *arguments], input="physical stdin", cwd="/", env={**env, "TSW_FIXTURE_EXIT": "17"}, text=True, capture_output=True, timeout=15)
                self.assertEqual(physical.returncode, 17, physical.stderr)
                self.assertEqual(json.loads(physical.stdout)["stdin"], "physical stdin")
                result = subprocess.run([str(root / public), "--help"], cwd="/", env={**env, "TSW_FIXTURE_EXIT": "0"},
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "modules/tsw_windows_wsl/bootstrap").exists())

    def test_windows_release_proof_requires_linux_bootstrap_but_not_native_entrypoints(self):
        builder = runpy.run_path(str(ROOT / "modules/tsw_windows_wsl/tools/build_windows_preparation_manifest.py"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (*builder["ASSETS"], "install.sh", "tsw", "modules/tsw_native_linux/module.json"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n")
            def git(*arguments):
                return subprocess.run(["git", "-C", str(root), *arguments], check=True,
                                      capture_output=True, timeout=15).stdout
            git("init", "--quiet")
            git("add", ".")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture")
            for relative in ("install.sh", "tsw", "modules/tsw_native_linux/module.json"):
                (root / relative).unlink()
            manifest = builder["build"](root)
            self.assertEqual(manifest["revision"], git("rev-parse", "HEAD").decode().strip())
            (root / "modules/tsw_native_linux/boostrap/install.sh").write_text("edited core\n")
            with self.assertRaises(ValueError):
                builder["build"](root)

    def test_touched_shell_syntax(self):
        for relative in ("install.sh", "tsw", "modules/tsw_native_linux/boostrap/install.sh", "modules/tsw_native_linux/boostrap/run.sh",
                         "modules/tsw_windows_wsl/bootstrap/preparation/linux-handoff.sh"):
            result = subprocess.run(["bash", "-n", str(ROOT / relative)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(_powershell(), "PowerShell runtime required for isolated WSL delegation")
    def test_windows_public_entrypoint_and_stubbed_wsl_delegation(self):
        executable = _powershell()
        result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                                 _runtime_path(ROOT / "modules/tsw_windows_wsl/tests/windows/module-delegation.Tests.ps1", executable),
                                 "-RepositoryRoot", _runtime_path(ROOT, executable)],
                                capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

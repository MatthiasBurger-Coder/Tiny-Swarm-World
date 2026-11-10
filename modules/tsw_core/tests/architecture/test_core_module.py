"""Focused MOD-01 ownership, import and external-resource boundary checks."""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import Mock, patch
import asyncio
from modules.tsw_core.tests.support.module_fixture import copy_core_source

from tsw_core import discover_root, module_descriptor, resource_root
from tiny_swarm_world.infrastructure.host_bindings import windows_bridge_binding
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths
from tiny_swarm_world.infrastructure.adapters.network_preparation.source_identity import preparation_asset_hashes

ROOT = Path(__file__).resolve().parents[4]


class CoreModuleTests(unittest.TestCase):
    def test_owned_assets_exist_under_one_core_anchor(self):
        descriptor = module_descriptor()
        self.assertEqual(descriptor["name"], "tsw_core")
        self.assertEqual(descriptor["project_dependencies"], [])
        self.assertEqual(discover_root(), ROOT)
        for name in ("source_root", "config_root", "infra_root"):
            self.assertTrue(resource_root(ROOT, name).is_dir())
        for asset in descriptor["shared_bootstrap"] + descriptor["runtime_metadata"]:
            self.assertTrue((ROOT / asset).is_file(), asset)
        self.assertEqual(ProjectPaths.from_roots(ROOT).config_root, resource_root(ROOT, "config_root"))
        with self.assertRaises(ValueError):
            resource_root(ROOT, "edition_root")

    def test_build_boundary_preserves_namespace_and_excludes_editions(self):
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertEqual(metadata["project"]["name"], "tiny-swarm-world")
        self.assertEqual(metadata["project"]["version"], "0.2.0")
        self.assertEqual(metadata["project"]["scripts"], {"tiny-swarm-world": "tiny_swarm_world.__main__:cli"})
        self.assertEqual(metadata["tool"]["setuptools"]["package-dir"], {
            "tiny_swarm_world": "modules/tsw_core/src", "tsw_core": "modules/tsw_core",
        })
        self.assertEqual(set(module_descriptor()["python_packages"]), {"tiny_swarm_world", "tsw_core"})

    def test_core_never_imports_editions_or_constructs_edition_paths(self):
        for package in (ROOT / "modules/tsw_core/src",):
            for source in package.rglob("*.py"):
                for node in ast.walk(ast.parse(source.read_text())):
                    names = []
                    if isinstance(node, ast.Import):
                        names = [item.name for item in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    for name in names:
                        self.assertNotIn(name.split(".")[0], {"tsw_native_linux", "tsw_windows_wsl"}, str(source))
        # Diagnostics may still mention documented public entry points. Actual
        # path composition and identity hashing must use injected bindings.
        for name in ("composition_platform.py", "host_bindings.py",
                     "adapters/network_preparation/windows.py", "adapters/network_preparation/source_identity.py"):
            source = (ROOT / "modules/tsw_core/src/infrastructure" / name).read_text()
            self.assertNotIn('"modules/tsw_windows_wsl/bootstrap', source)
            self.assertNotIn('/ "windows"', source)

    def test_cli_loads_with_only_core_owned_runtime_and_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            isolated = Path(directory)
            copy_core_source(ROOT, isolated)
            shutil.copytree(ROOT / "modules/tsw_core/infra", isolated / "modules/tsw_core/infra")
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("TSW_") and key != "PYTHONPATH"}
            env.update(PYTHONPATH=str(isolated), PYTHONDONTWRITEBYTECODE="1")
            code = ('import modules.tsw_core.src; from tsw_core import discover_root; '
                    'from tiny_swarm_world.__main__ import cli; '
                    'from tiny_swarm_world.infrastructure.project_paths import default_project_paths; '
                    'from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog; '
                    'assert NativeComponentCatalog(discover_root()).load().services; '
                    'assert callable(cli); assert default_project_paths().config_root.is_dir(); '
                    'assert discover_root().name == ' + repr(isolated.name))
            for arguments in (("-c", code), ("-m", "modules.tsw_core.src", "--help")):
                result = subprocess.run((sys.executable, *arguments), cwd=isolated, env=env,
                                        capture_output=True, text=True, timeout=45)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((isolated / "modules/tsw_windows_wsl/bootstrap").exists())
            self.assertFalse((isolated / "host-bindings.json").exists())

    def test_malformed_host_binding_is_a_blocked_runtime_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "host-bindings.json"
            with patch.dict(os.environ, {}, clear=True):
                for value in ({}, [], {"windows_bridge": []}, {"windows_bridge": {"script": 7}},
                              {"windows_bridge": {"script": "", "config": "c", "identity_glob": "*"}}):
                    with self.subTest(value=value):
                        manifest.write_text(json.dumps(value))
                        with self.assertRaises(RuntimeError):
                            windows_bridge_binding(root)

    def test_changed_binding_cannot_invoke_a_previously_cached_script(self):
        from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
        from tiny_swarm_world.infrastructure.adapters.network_preparation.windows import WindowsNetworkPreparation

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bridge.ps1").write_text("fixture")
            values = {"windows_bridge": {"script": "bridge.ps1", "config": "config.json", "identity_glob": "*.ps1"}}
            manifest = root / "host-bindings.json"
            manifest.write_text(json.dumps(values))
            runner = Mock()
            with patch.dict(os.environ, {}, clear=True):
                adapter = WindowsNetworkPreparation(runner, root, root)
                values["windows_bridge"]["script"] = "other.ps1"
                manifest.write_text(json.dumps(values))
                with self.assertRaises(NetworkPreparationFailure):
                    asyncio.run(adapter._run("inventory", "fixture", "172.20.1.2", 1))
            runner.run.assert_not_called()

    def test_host_assets_are_injected_and_still_fingerprinted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("requirements.lock", "requirements.build.lock", "pyproject.toml",
                             "modules/tsw_core/infra/config/host/tiny-swarm-world-sysctl.conf",
                             "modules/tsw_core/infra/config/host/tiny-swarm-world-modules.conf",
                             "modules/tsw_core/infra/config/node-providers/provider_config.yaml", "modules/tsw_core/infra/config/ports.yaml",
                             "modules/tsw_core/src/prepare_network.py", "modules/tsw_core/src/domain/network_preparation.py",
                             "modules/tsw_core/src/application/ports/network_preparation.py",
                             "modules/tsw_core/src/application/services/network_preparation.py",
                             "modules/tsw_core/src/infrastructure/composition_network_preparation.py",
                             "modules/tsw_core/src/infrastructure/adapters/network_preparation/files.py",
                             "modules/tsw_core/src/infrastructure/adapters/network_preparation/privileged_files.py",
                             "external-host/bridge.ps1", "external-host/config.json"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
            shim = root / "src/tsw_core/__init__.py"
            shim.parent.mkdir(parents=True)
            shim.write_text("# trusted compatibility fixture\n")
            initial_core = preparation_asset_hashes(root, is_wsl=False)
            shim.write_text("# altered compatibility fixture\n")
            self.assertNotEqual(initial_core, preparation_asset_hashes(root, is_wsl=False))
            binding = root / "host-bindings.json"
            binding.write_text(json.dumps({"windows_bridge": {"script": "external-host/bridge.ps1",
                "config": "external-host/config.json", "identity_glob": "external-host/**/*.ps1"}}))
            with patch.dict(os.environ, {}, clear=True):
                supplied = windows_bridge_binding(root)
                self.assertEqual(supplied.script, root / "external-host/bridge.ps1")
                before = preparation_asset_hashes(root, is_wsl=True)
                supplied.script.write_text("changed")
                self.assertNotEqual(before, preparation_asset_hashes(root, is_wsl=True))
                binding.unlink()
                # Native core has no dependency on a host binding.
                preparation_asset_hashes(root, is_wsl=False)
                with self.assertRaises(FileNotFoundError):
                    preparation_asset_hashes(root, is_wsl=True)

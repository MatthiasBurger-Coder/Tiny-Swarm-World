"""Execute archive identity proofs against real disposable Git commits."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.test_prepare_windows import ROOT, _powershell, _runtime_path
from tools.build_windows_preparation_manifest import ASSETS, build, git


class TestWindowsSourceProof(unittest.TestCase):
    @unittest.skipUnless(_powershell(), "PowerShell source-proof execution unavailable.")
    def test_real_commit_proof_and_tampering_are_verified_without_windows_git(self) -> None:
        parent = ROOT / "tests" / "_trial_temp"
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="w04-proof-", dir=parent) as directory:
            workspace = Path(directory)
            source = workspace / "source"
            source.mkdir()
            for asset in ASSETS:
                path = source / asset
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"committed fixture bytes for {asset}\n")
            git(source, "init", "--quiet")
            git(source, "add", "--", *ASSETS)
            git(source, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture")
            manifest = build(source)
            expected_revision = str(manifest["revision"])
            executable = _powershell()
            assert executable is not None
            cases: list[dict[str, object]] = []
            variants = (
                "valid", "wrong_revision", "tampered_commit", "tampered_tree",
                "tampered_blob", "missing_asset", "duplicate_object",
                "malformed_tree", "oversized_manifest", "duplicate_entry",
                "symlink_mode", "gitlink_mode", "missing_expected_revision",
                "symlink_asset", "duplicate_json_key",
                "tamper_bridge_helper", "tamper_bridge_script", "tamper_bridge_service",
                "tamper_bridge_config", "tamper_port_registry",
            )
            for name in variants:
                target = workspace / name
                shutil.copytree(source, target, ignore=shutil.ignore_patterns(".git"))
                variant = json.loads(json.dumps(manifest))
                revision = expected_revision
                runtime_tamper_assets = {
                    "tamper_bridge_helper": "tools/windows/preparation/Bridge.ps1",
                    "tamper_bridge_script": "tools/windows/tws-wsl-bridge.ps1",
                    "tamper_bridge_service": "tools/windows/tws-wsl-bridge-service.ps1",
                    "tamper_bridge_config": "tools/windows/tws-wsl-bridge.config.json",
                    "tamper_port_registry": "infra/config/ports.yaml",
                }
                if name in runtime_tamper_assets:
                    (target / runtime_tamper_assets[name]).write_text("tampered runtime bytes")
                elif name == "wrong_revision":
                    revision = "f" * 40
                elif name == "tampered_commit":
                    variant["commit"] = base64.b64encode(b"altered commit").decode()
                elif name == "tampered_tree":
                    variant["trees"][0]["data"] = base64.b64encode(b"malformed tree").decode()
                elif name == "tampered_blob":
                    (target / ASSETS[0]).write_text("tampered working file")
                elif name == "missing_asset":
                    (target / ASSETS[-1]).unlink()
                elif name == "duplicate_object":
                    variant["trees"].append(variant["trees"][0])
                elif name == "missing_expected_revision":
                    revision = ""
                elif name == "symlink_asset":
                    (target / ASSETS[0]).unlink()
                    (target / ASSETS[0]).symlink_to(source / ASSETS[0])
                elif name in {"malformed_tree", "duplicate_entry", "symlink_mode", "gitlink_mode"}:
                    raw_commit = base64.b64decode(variant["commit"])
                    root_identity = raw_commit.split(b"\n", 1)[0].split(b" ")[1].decode()
                    tree = next(item for item in variant["trees"] if item["id"] == root_identity)
                    raw_tree = base64.b64decode(tree["data"])
                    if name == "duplicate_entry":
                        raw_tree *= 2
                    elif name == "malformed_tree":
                        raw_tree = b"100644 bad\0" + b"\0" * 19
                    else:
                        mode = b"120000" if name == "symlink_mode" else b"160000"
                        raw_tree = raw_tree.replace(b"100644 prepare_windows.ps1\0", mode + b" prepare_windows.ps1\0")
                    new_tree = hashlib.sha1(b"tree " + str(len(raw_tree)).encode() + b"\0" + raw_tree).hexdigest()
                    tree.update(id=new_tree, data=base64.b64encode(raw_tree).decode())
                    raw_commit = raw_commit.replace(root_identity.encode(), new_tree.encode(), 1)
                    revision = hashlib.sha1(b"commit " + str(len(raw_commit)).encode() + b"\0" + raw_commit).hexdigest()
                    variant.update(revision=revision, commit=base64.b64encode(raw_commit).decode())
                manifest_path = target / "tools/windows/preparation/release-manifest.json"
                manifest_path.write_text(json.dumps(variant))
                if name == "duplicate_json_key":
                    manifest_path.write_text('{"revision": "' + revision + '",' + json.dumps(variant)[1:])
                if name == "oversized_manifest":
                    manifest_path.write_text(" " * (8388608 + 1))
                cases.append({
                    "name": name, "root": _runtime_path(target, executable),
                    "assets": ASSETS, "revision": revision, "expected": name == "valid",
                })
            catalog = workspace / "cases.json"
            catalog.write_text(json.dumps(cases))
            completed = subprocess.run(
                [executable, "-NoProfile", "-NonInteractive", "-File",
                 _runtime_path(ROOT / "tests/windows/source-proof.Tests.ps1", executable),
                 "-RepositoryRoot", _runtime_path(ROOT, executable),
                 "-FixtureCatalog", _runtime_path(catalog, executable)],
                check=False, text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("PASS 20", completed.stdout)
            (source / ASSETS[0]).write_text("dirty")
            with self.assertRaisesRegex(ValueError, "clean committed"):
                build(source)
            git(source, "update-index", "--assume-unchanged", ASSETS[0])
            with self.assertRaisesRegex(ValueError, "Asset bytes differ"):
                build(source)

"""Read-only source handoff and dependent-stage execution in disposable Linux fixtures."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestInstallHandoff(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tsw-handoff-", dir=Path.home())
        self.addCleanup(self.temporary.cleanup)
        self.checkout = Path(self.temporary.name) / "checkout with spaces"
        self.checkout.mkdir()
        for name in ("install.sh", "prepare_linux.sh", "requirements.lock", "requirements.build.lock", "pyproject.toml", "src/tiny_swarm_world/prepare_linux.py"):
            path = self.checkout / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# fixture bytes\n")
        (self.checkout / "install.sh").chmod(0o755)
        (self.checkout / "prepare_linux.sh").chmod(0o755)
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture")
        self.revision = self.git("rev-parse", "HEAD").decode().strip()

    def git(self, *arguments):
        return subprocess.run(["git", "-C", str(self.checkout), *arguments], check=True, capture_output=True, timeout=10).stdout

    def probe(self, path=None, revision=None):
        return subprocess.run(["sh", "-s", "--", str(path or self.checkout), revision or self.revision],
                              input=(ROOT / "tools/windows/preparation/linux-handoff.sh").read_text(),
                              text=True, capture_output=True, check=False, timeout=15)

    def test_read_only_matching_checkout_has_no_writes(self):
        before = {str(p.relative_to(self.checkout)): p.read_bytes() for p in self.checkout.rglob("*") if p.is_file()}
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("handoff_ready=true", result.stdout)
        self.assertIn(str(self.checkout), result.stdout)
        after = {str(p.relative_to(self.checkout)): p.read_bytes() for p in self.checkout.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_mismatched_revision_and_edits_hidden_from_git_status_are_refused(self):
        self.assertEqual(self.probe(revision="a" * 40).returncode, 2)
        asset = "src/tiny_swarm_world/prepare_linux.py"
        self.git("update-index", "--assume-unchanged", asset)
        (self.checkout / asset).write_text("edited product implementation\n")
        result = self.probe()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("handoff_ready=true", result.stdout)

    def test_source_links_extra_code_nonexecutable_and_windows_paths_are_refused(self):
        self.assertEqual(self.probe(path=Path("/mnt/c/checkout")).returncode, 2)
        link = self.checkout.parent / "linked"
        link.symlink_to(self.checkout)
        self.assertEqual(self.probe(path=link).returncode, 2)
        (self.checkout / "install.sh").chmod(0o644)
        self.assertEqual(self.probe().returncode, 2)
        (self.checkout / "install.sh").chmod(0o755)
        (self.checkout / "src/extra.py").write_text("untracked implementation\n")
        self.assertEqual(self.probe().returncode, 2)

    def test_extracted_release_proof_preserves_source_binding_without_git(self):
        trees = {}
        identities = [self.git("rev-parse", "HEAD:").decode().strip()]
        identities += [line.split()[2].decode() for line in self.git("ls-tree", "-r", "-d", "HEAD").splitlines()]
        for identity in identities:
            trees[identity] = base64.b64encode(self.git("cat-file", "tree", identity)).decode()
        manifest = {"schema_version": 1, "revision": self.revision,
                    "commit": base64.b64encode(self.git("cat-file", "commit", self.revision)).decode(),
                    "trees": [{"id": key, "data": value} for key, value in trees.items()]}
        import shutil
        shutil.rmtree(self.checkout / ".git")
        path = self.checkout / "tools/windows/preparation/release-manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(manifest))
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.checkout / "src/tiny_swarm_world/prepare_linux.py").write_text("tampered\n")
        self.assertEqual(self.probe().returncode, 2)

    def test_preparation_failure_stops_install_and_shell_keeps_stdin_and_exit(self):
        for prepare_exit, install_exit in ((2, 0), (3, 0), (4, 0), (124, 0), (130, 0), (0, 17), (0, 0)):
            with self.subTest(prepare_exit=prepare_exit, install_exit=install_exit):
                marker = self.checkout / "called"
                marker.unlink(missing_ok=True)
                (self.checkout / "prepare_linux.sh").write_text(f"#!/bin/sh\nread answer\n[ \"$answer\" = yes ] || exit 2\nexit {prepare_exit}\n")
                (self.checkout / "install.sh").write_text(f"#!/bin/sh\ntouch called\nexit {install_exit}\n")
                chain = f"cd -- '{self.checkout}' && ./prepare_linux.sh --service-profile default && exec ./install.sh --service-profile default"
                result = subprocess.run(["bash", "-lc", chain], input="yes\n", text=True, capture_output=True,
                                        env={**os.environ}, check=False, timeout=10)
                self.assertEqual(result.returncode, prepare_exit or install_exit)
                self.assertEqual(marker.exists(), prepare_exit == 0)

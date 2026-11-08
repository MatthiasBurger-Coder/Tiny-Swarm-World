"""Build an offline Git membership proof for a trusted, clean release checkout.

Run on Linux/WSL during packaging, never on the bare Windows preparation host.
The expected revision still comes from the operator's independently trusted channel.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import subprocess


MAX_TREE_OBJECTS = 144  # Physical module and compatibility-path ancestors.

ASSETS = (
    "modules/tsw_native_linux/boostrap/install.sh",
    "modules/tsw_native_linux/boostrap/prepare_linux.sh",
    "modules/tsw_windows_wsl/bootstrap/preparation/Handoff.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/linux-handoff.sh",
    "modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1",
    "modules/tsw_windows_wsl/bootstrap/preparation/Policy.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/Application.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/Adapters.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/Download.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/SourceProof.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/linux-config.sh",
    "modules/tsw_windows_wsl/bootstrap/preparation/Resources.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/ResourceAdapters.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/ResourceHost.ps1",
    "modules/tsw_windows_wsl/bootstrap/preparation/linux-resources.sh",
    "modules/tsw_windows_wsl/bootstrap/preparation/resource-projection.json",
    "modules/tsw_core/src/domain/preflight/resources.py",
    "modules/tsw_core/src/domain/host_environment.py",
    "modules/tsw_core/infra/config/node-providers/provider_config.yaml",
    "modules/tsw_windows_wsl/tools/build_wsl_resource_projection.py",
    "modules/tsw_windows_wsl/bootstrap/preparation/Bridge.ps1",
    "modules/tsw_windows_wsl/bootstrap/tws-wsl-bridge.ps1",
    "modules/tsw_windows_wsl/bootstrap/tws-wsl-bridge-service.ps1",
    "modules/tsw_windows_wsl/bootstrap/tws-wsl-bridge.config.json",
    "modules/tsw_core/infra/config/ports.yaml",
    "modules/tsw_windows_wsl/tools/qualification/windows_firewall_snapshot.ps1",
    "modules/tsw_windows_wsl/tools/qualification/windows_firewall_certificate.ps1",
)


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        timeout=15,
    ).stdout


def build(root: Path) -> dict[str, object]:
    if git(root, "status", "--porcelain", "--untracked-files=all", "--", ".",
           ":(exclude)install.sh", ":(exclude)tsw", ":(exclude)modules/tsw_native_linux").strip():
        raise ValueError("Release proof requires a clean committed checkout.")
    revision = git(root, "rev-parse", "HEAD").decode().strip()
    trees: dict[str, bytes] = {}
    assets = (*ASSETS, *(name for name in ("modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1",) if (root / name).is_file()))
    for asset in assets:
        current = root
        for component in Path(asset).parts:
            current = current / component
            if current.is_symlink():
                raise ValueError(f"Symlinked preparation asset: {asset}")
        mode = git(root, "ls-tree", "HEAD", "--", asset).split(b" ", 1)[0]
        if mode not in {b"100644", b"100755"}:
            raise ValueError(f"Nonregular preparation asset: {asset}")
        if git(root, "cat-file", "blob", f"HEAD:{asset}") != (root / asset).read_bytes():
            raise ValueError(f"Asset bytes differ from HEAD: {asset}")
        prefixes = ("", *tuple(str(parent) for parent in Path(asset).parents if str(parent) != "."))
        for prefix in prefixes:
            identity = git(root, "rev-parse", f"HEAD:{prefix}").decode().strip()
            trees[identity] = git(root, "cat-file", "tree", identity)
    # Include runtime/configuration trees for read-only Linux handoff integrity.
    for line in git(root, "ls-tree", "-r", "-d", "HEAD", "--", 'modules/tsw_core/src', 'modules/tsw_core/infra', 'modules/tsw_core/tools', 'modules/tsw_windows_wsl/bootstrap', 'modules/tsw_windows_wsl/tools', 'modules/tsw_native_linux/boostrap').splitlines():
        mode, kind, identity_path = line.split(b" ", 2)
        identity = identity_path.split(b"\t", 1)[0].decode()
        if mode == b"040000" and kind == b"tree":
            trees[identity] = git(root, "cat-file", "tree", identity)
    if len(trees) > MAX_TREE_OBJECTS:
        raise ValueError("Release proof exceeds the bounded tree catalogue.")
    return {
        "schema_version": 1,
        "revision": revision,
        "commit": base64.b64encode(git(root, "cat-file", "commit", revision)).decode(),
        "trees": [
            {"id": identity, "data": base64.b64encode(content).decode()}
            for identity, content in sorted(trees.items())
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    manifest = build(arguments.repository.resolve())
    arguments.output.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()

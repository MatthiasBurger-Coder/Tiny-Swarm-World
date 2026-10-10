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


ASSETS = (
    "prepare_windows.ps1",
    "tools/windows/preparation/Preparation.psm1",
    "tools/windows/preparation/Policy.ps1",
    "tools/windows/preparation/Application.ps1",
    "tools/windows/preparation/Adapters.ps1",
    "tools/windows/preparation/Download.ps1",
    "tools/windows/preparation/SourceProof.ps1",
    "tools/windows/preparation/linux-config.sh",
    "tools/windows/preparation/Resources.ps1",
    "tools/windows/preparation/ResourceAdapters.ps1",
    "tools/windows/preparation/ResourceHost.ps1",
    "tools/windows/preparation/linux-resources.sh",
    "tools/windows/preparation/resource-projection.json",
    "src/tiny_swarm_world/domain/preflight/resources.py",
    "src/tiny_swarm_world/domain/host_environment.py",
    "infra/config/node-providers/provider_config.yaml",
    "tools/build_wsl_resource_projection.py",
)


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        timeout=15,
    ).stdout


def build(root: Path) -> dict[str, object]:
    if git(root, "status", "--porcelain", "--untracked-files=all").strip():
        raise ValueError("Release proof requires a clean committed checkout.")
    revision = git(root, "rev-parse", "HEAD").decode().strip()
    trees: dict[str, bytes] = {}
    for asset in ASSETS:
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

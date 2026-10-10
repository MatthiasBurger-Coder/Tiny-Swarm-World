#!/bin/sh
# Bounded by the invoking WSL process adapter. Read-only, never executes checkout code.
set -eu
checkout=${1:-$HOME/Tiny-Swarm-World}
case "$checkout" in /*) ;; *) exit 2 ;; esac
case "$checkout" in /mnt/[a-z]|/mnt/[a-z]/*|*[!a-zA-Z0-9_./\ -]*) exit 2 ;; esac
[ "$(id -u)" -ge 1000 ] && [ "$(id -u)" -lt 65534 ] || exit 2
resolved=$(readlink -e -- "$checkout") || exit 2
[ "$resolved" = "$checkout" ] && [ -d "$checkout" ] && [ -w "$checkout" ] || exit 2
[ "$(stat -c %u -- "$checkout")" = "$(id -u)" ] || exit 2
filesystem=$(findmnt -n -o FSTYPE -T "$checkout") || exit 2
case "$filesystem" in ext4|btrfs|xfs) ;; *) exit 2 ;; esac
for asset in install.sh prepare_linux.sh requirements.lock requirements.build.lock pyproject.toml src/tiny_swarm_world/prepare_linux.py; do
    path=$checkout/$asset
    [ -f "$path" ] && [ ! -L "$path" ] && [ "$(readlink -e -- "$path")" = "$path" ] || exit 2
    [ "$(stat -c %u -- "$path")" = "$(id -u)" ] || exit 2
done
[ -x "$checkout/install.sh" ] && [ -x "$checkout/prepare_linux.sh" ] || exit 2
# Code below is supplied by the verified Windows source, never imported from checkout.
/usr/bin/python3 -I -S -B - "$checkout" "$2" <<'TSW_HANDOFF_SOURCE'
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

root = Path(sys.argv[1])
revision = sys.argv[2]
if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
    raise SystemExit(2)

def oid(kind, data):
    return hashlib.sha1(kind.encode() + b" " + str(len(data)).encode() + b"\0" + data).hexdigest()

def git(*args):
    result = subprocess.run(["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
                            check=True, capture_output=True, timeout=5)
    if len(result.stdout) > 4 * 1024 * 1024:
        raise ValueError("oversized_object")
    return result.stdout

try:
    archive = None
    if (root / ".git").exists():
        if git("rev-parse", "HEAD").decode().strip() != revision:
            raise ValueError("revision_mismatch")
        commit = git("cat-file", "commit", revision)
    else:
        manifest = root / "tools/windows/preparation/release-manifest.json"
        if manifest.is_symlink() or manifest.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("unsafe_manifest")
        archive = json.loads(manifest.read_bytes())
        if archive["schema_version"] != 1 or archive["revision"] != revision or len(archive["trees"]) > 128:
            raise ValueError("manifest_identity")
        commit = base64.b64decode(archive["commit"], validate=True)
    if oid("commit", commit) != revision:
        raise ValueError("commit_hash")
    match = re.match(rb"tree ([0-9a-f]{40})\n", commit)
    if match is None:
        raise ValueError("commit_tree")
    trees = {} if archive is None else {item["id"]: base64.b64decode(item["data"], validate=True) for item in archive["trees"]}
    seen = set()
    budget = [0, 0]
    def walk(identity, prefix):
        data = git("cat-file", "tree", identity) if archive is None else trees[identity]
        if oid("tree", data) != identity:
            raise ValueError("tree_hash")
        offset = 0
        while offset < len(data):
            space = data.index(b" ", offset)
            nul = data.index(b"\0", space)
            mode = data[offset:space]
            name = data[space + 1:nul].decode("utf-8")
            child = data[nul + 1:nul + 21].hex()
            offset = nul + 21
            if not name or name in (".", "..") or re.search(r"[/\\\x00-\x1f]", name):
                raise ValueError("unsafe_entry")
            relative = prefix / name
            # The executable release surface, excluding documentation/governance.
            if not prefix.parts and name not in ("src", "tools", "infra", "install.sh", "prepare_linux.sh", "requirements.lock", "requirements.build.lock", "pyproject.toml"):
                continue
            path = root / relative
            if path.is_symlink() or path.stat().st_uid != os.getuid():
                raise ValueError("unsafe_asset")
            if mode in (b"40000", b"040000"):
                if not path.is_dir():
                    raise ValueError("not_directory")
                walk(child, relative)
            elif mode in (b"100644", b"100755"):
                budget[0] += 1
                budget[1] += path.stat().st_size
                if budget[0] > 8192 or budget[1] > 128 * 1024 * 1024 or path.stat().st_size > 4 * 1024 * 1024 or not path.is_file():
                    raise ValueError("asset_budget")
                if oid("blob", path.read_bytes()) != child:
                    raise ValueError("edited_asset")
                seen.add(relative.as_posix())
            else:
                raise ValueError("unsupported_asset_mode")
    walk(match.group(1).decode(), Path())
    for directory in ("src", "tools", "infra"):
        for current, dirs, files in os.walk(root / directory, followlinks=False):
            dirs[:] = [name for name in dirs if name not in ("__pycache__", "logs")]
            if any((Path(current) / name).is_symlink() for name in dirs):
                raise ValueError("local_directory_link")
            for name in files:
                relative = (Path(current) / name).relative_to(root).as_posix()
                if relative.endswith((".pyc", ".log")) or relative == "tools/windows/preparation/release-manifest.json":
                    continue
                if relative not in seen:
                    raise ValueError("unknown_local_asset")
except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
    raise SystemExit(2) from None
TSW_HANDOFF_SOURCE
printf 'handoff_ready=true\nhandoff_checkout=%s\n' "$checkout"

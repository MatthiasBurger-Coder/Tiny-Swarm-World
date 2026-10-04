"""Read-only asset and user-path validation before prerequisite mutation."""

from __future__ import annotations

import os
import re
from pathlib import Path

from tiny_swarm_world.application.ports.installation import InstallerError


def validate_assets(root: Path) -> None:
    for relative in ("requirements.lock", "requirements.build.lock", "pyproject.toml", "src/tiny_swarm_world/prepare_linux.py"):
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise InstallerError("Complete trusted release assets are required; extract the release and retry ./prepare_linux.sh --dry-run.")
    # Validate the hash-locked grammar before creating a venv or invoking pip.
    for name in ("requirements.lock", "requirements.build.lock"):
        _validate_lock(root / name)


def _validate_lock(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    entries = content.replace("\\\n", " ").splitlines()
    requirements = [line.split("#", 1)[0].strip() for line in entries]
    requirements = [line for line in requirements if line]
    if not requirements or any(
        re.fullmatch(r"[A-Za-z0-9_.-]+==[^\s;]+(?:\s+--hash=sha256:[a-f0-9]{64})+", line) is None
        for line in requirements
    ):
        raise InstallerError("requirements.lock must contain pinned SHA256-hashed dependencies; restore the trusted release lock and retry.")


def validate_user_paths(root: Path, venv: Path, *, is_wsl: bool) -> None:
    if os.geteuid() == 0:
        raise InstallerError("Run ./prepare_linux.sh as an ordinary user; only package installation elevates.")
    for path in (root.absolute(), venv.absolute()):
        if is_wsl and re.match(r"^/mnt/[a-z](?:/|$)", path.as_posix()):
            raise InstallerError("Use an owned Linux-native checkout and venv, then retry ./prepare_linux.sh --dry-run.")
        for ancestor in (path, *path.parents):
            if ancestor.is_symlink():
                raise InstallerError("Preparation paths must not contain symlinks; choose an owned Linux-native directory.")
        existing = path
        while not existing.exists():
            existing = existing.parent
        if existing.stat().st_uid != os.geteuid() or not os.access(existing, os.W_OK):
            raise InstallerError("Preparation target must be owned and writable by the invoking user.")
    if venv.exists():
        if not venv.is_dir() or (venv / "pyvenv.cfg").is_symlink() or not (venv / "pyvenv.cfg").is_file():
            raise InstallerError("Existing venv target is not a recognized Python environment; preserve it and choose another TSW_NATIVE_LINUX_VENV.")
        # venv executables may link to the system Python, but their directory
        # and metadata must remain under the invoking user's ownership.
        if any(path.lstat().st_uid != os.geteuid() for path in venv.rglob("*")):
            raise InstallerError("Existing venv contains foreign-owned files; preserve it and choose another TSW_NATIVE_LINUX_VENV.")

        for path in venv.rglob("*"):
            if path.is_symlink() and path.is_dir() and not path.resolve().is_relative_to(venv.resolve()):
                raise InstallerError("Existing venv has an external directory link; preserve it and choose another venv.")

"""Create an opt-in local env file from the canonical internal-test catalog."""

from __future__ import annotations

import argparse
import os
import shlex
import stat
import sys
from pathlib import Path

from tiny_swarm_world.domain.configuration.internal_test_credentials import (
    internal_test_catalog,
    validate_internal_test_catalog,
)


def create_internal_test_env_file(path: Path) -> bool:
    """Write test credentials once; preserve an existing operator file."""
    path = path.expanduser()
    if not path.is_absolute():
        raise ValueError("The credential file path must be absolute.")
    parent = path.parent
    if parent.is_symlink() or path.is_symlink():
        raise ValueError("Credential file and parent must not be symbolic links.")
    if parent.resolve(strict=True).parts[:2] == ("/", "mnt"):
        raise ValueError("Credential files must be on a Linux-native filesystem.")
    parent_stat = parent.stat()
    if (
        not stat.S_ISDIR(parent_stat.st_mode)
        or parent_stat.st_uid != os.geteuid()
        or parent_stat.st_gid != os.getegid()
        or stat.S_IMODE(parent_stat.st_mode) != 0o700
    ):
        raise ValueError("Credential directory must be user-owned with mode 0700.")

    validate_internal_test_catalog()
    entries = (
        definition
        for definition in internal_test_catalog().definitions
        if definition.active and definition.required
    )
    lines = [
        "# INTERNAL/TEST ONLY: public, disposable credentials.",
        "# Do not use for production or shared environments.",
        *(f"{entry.key}={shlex.quote(entry.value)}" for entry in entries),
    ]
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        return False
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
    except Exception:
        path.unlink()
        raise
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Linux-native credential file path")
    args = parser.parse_args()
    try:
        created = create_internal_test_env_file(args.path)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Internal-test credential file created." if created else "Existing credential file preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

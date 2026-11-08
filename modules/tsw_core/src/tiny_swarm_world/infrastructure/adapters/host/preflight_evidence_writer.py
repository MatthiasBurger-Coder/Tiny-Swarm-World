from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Mapping


class PreflightEvidenceWriter:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def write(self, evidence: Mapping[str, object], relative_path: str) -> Path:
        self._ensure_private_root()
        target = (self.root / relative_path).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Preflight evidence path escapes the configured root.") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(dict(evidence), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    def _ensure_private_root(self) -> None:
        anchor = self.root.parent
        while not anchor.exists() and anchor != anchor.parent:
            anchor = anchor.parent
        anchor_stat = anchor.stat()
        if anchor_stat.st_uid != os.geteuid() or anchor_stat.st_gid != os.getegid():
            raise ValueError("Preflight evidence root parent is not user-owned.")
        if stat.S_IMODE(anchor_stat.st_mode) & 0o022:
            raise ValueError("Preflight evidence root parent is group- or world-writable.")
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)
            self.root.chmod(0o700)
        root_stat = self.root.stat()
        if not stat.S_ISDIR(root_stat.st_mode):
            raise ValueError("Preflight evidence root is not a directory.")
        if root_stat.st_uid != os.geteuid() or root_stat.st_gid != os.getegid():
            raise ValueError("Preflight evidence root is not owned by the effective user.")
        if stat.S_IMODE(root_stat.st_mode) != 0o700:
            raise ValueError("Preflight evidence root must be owner-only.")

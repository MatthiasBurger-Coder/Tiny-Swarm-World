from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


class PreflightEvidenceWriter:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def write(self, evidence: Mapping[str, object], relative_path: str) -> Path:
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

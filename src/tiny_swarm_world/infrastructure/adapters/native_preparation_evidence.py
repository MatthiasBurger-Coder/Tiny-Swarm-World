"""Protected, redacted local evidence for native package preparation."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path


class NativePreparationEvidenceWriter:
    def __init__(self, state_root: Path | None = None) -> None:
        self._state_root = state_root or Path(
            os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
        )

    def write(
        self,
        *,
        platform_release: str,
        status: str,
        planned: tuple[str, ...],
        added: tuple[str, ...],
        uncertain: tuple[str, ...],
        stage: str,
    ) -> Path:
        self._state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        project = self._state_root / "tiny-swarm-world"
        evidence = project / "evidence"
        directory = evidence / "native-preparation"
        for path in (project, evidence, directory):
            path.mkdir(mode=0o700, exist_ok=True)
            metadata = path.lstat()
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
                or metadata.st_gid != os.getegid()
                or stat.S_IMODE(metadata.st_mode) != 0o700
            ):
                raise OSError("Native preparation evidence directory is not private and operator-owned.")
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        target = directory / f"{timestamp}.json"
        payload = {
            "schema": "native-preparation-v1",
            "status": status,
            "stage": stage,
            "platform": f"ubuntu-{platform_release}-x86_64",
            "planned_packages": list(planned),
            "newly_observed_packages": list(added),
            "uncertain_packages": list(uncertain),
            "timestamp_utc": timestamp,
        }
        descriptor, temporary_name = tempfile.mkstemp(prefix=".native-preparation-", dir=directory)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, target)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
        return target

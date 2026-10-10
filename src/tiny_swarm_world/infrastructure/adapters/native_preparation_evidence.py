"""Protected, redacted local evidence for native package preparation."""

from __future__ import annotations

import os
import hashlib
import re
from datetime import UTC, datetime
from typing import Any
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.bootstrap_state import BootstrapState, context, directory


def _validate_labels(capability: str, labels: tuple[str, ...]) -> None:
    if capability not in {"packages", "python", "incus", "network"}:
        raise OSError("Unknown bootstrap capability.")
    if any(not re.fullmatch(r"[A-Za-z0-9_./:-]{1,200}", item)
           or re.search(r"password|private.?key|secret|token", item, re.I) for item in labels):
        raise OSError("Bootstrap evidence permits safe action labels only.")


def _exit_for(status: str, override: int | None) -> int | None:
    if override is not None:
        return override
    return {"interrupted": 130, "succeeded": 0, "ready": 0, "started": None,
            "pending": None, "restart_required": 3, "blocked": 2, "failed": 1}.get(status.lower(), 4)


def _evidence_directory(root: Path) -> Path:
    project = root / "tiny-swarm-world"
    target = project / "evidence/native-preparation"
    for path in (project, project / "evidence", target):
        with directory(path, create=True):
            pass
    return target


class NativePreparationEvidenceWriter:
    def __init__(self, state_root: Path | None = None, *, selection: str = "service-access") -> None:
        self._state_root = state_root or Path(
            os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
        )
        if selection not in {"default", "service-access"}:
            raise OSError("Unsupported bootstrap selection.")
        self.selection = selection
        self._checkpoint = BootstrapState(self._state_root / "tiny-swarm-world" / "bootstrap")

    @staticmethod
    def fingerprint(observation: object) -> str:
        return hashlib.sha256(repr(observation).encode()).hexdigest()

    def validate(self, *, platform_release: str, capability: str = "packages") -> None:
        self._checkpoint.validate(capability, context(platform_release, self.selection))

    def write(
        self,
        *,
        platform_release: str,
        status: str,
        planned: tuple[str, ...],
        added: tuple[str, ...],
        uncertain: tuple[str, ...],
        stage: str,
        capability: str = "packages",
        exit_code: int | None = None,
        observation: str = "unknown",
        restart: str = "none",
        cause: str = "none",

    ) -> Path:
        _validate_labels(capability, (*planned, *added, *uncertain, stage, status))
        identity = context(platform_release, self.selection)
        self._checkpoint.validate(capability, identity)
        target_directory = _evidence_directory(self._state_root)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        target = target_directory / f"{timestamp}.json"
        payload: dict[str, Any] = {
            "schema": capability + "-preparation-v1" if capability in {"incus", "network"} else "native-preparation-v1",
            "status": status,
            "stage": stage,
            "platform": f"ubuntu-{platform_release}-x86_64",
            "planned_actions" if capability in {"incus", "network"} else "planned_packages": list(planned),
            "newly_observed_actions" if capability in {"incus", "network"} else "newly_observed_packages": list(added),
            "uncertain_actions" if capability in {"incus", "network"} else "uncertain_packages": list(uncertain),
            "timestamp_utc": timestamp,
        }
        payload.update(operation=self._checkpoint.operation, context=identity,
                       exit_code=_exit_for(status, exit_code),
                       next_command=f"./prepare_linux.sh --service-profile {self.selection} --dry-run",
                       rollback="No automatic package/resource removal; inspect protected backups before explicit restoration.")
        checkpoint = {"stage": stage, "status": status, "planned": list(planned),
                      "confirmed": list(added), "uncertain": list(uncertain),
                      "timestamp": timestamp, "exit_code": payload["exit_code"],
                      "observation_sha256": observation, "restart": restart, "cause": cause}
        # Intent must be durable before the caller is allowed to execute a mutation.
        self._checkpoint.publish(capability, identity, checkpoint)
        try:
            with directory(target_directory, create=False) as fd:
                assert fd is not None
                payload.update(observation_sha256=observation, restart=restart, cause=cause)
                BootstrapState._publish(fd, target.name, payload)
        finally:
            if status.lower() not in {"started", "pending"}:
                self._checkpoint.close()
        return target

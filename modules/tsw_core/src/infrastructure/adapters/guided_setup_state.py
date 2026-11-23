"""Protected setup handoff identity and checkpoint rules."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import os
from pathlib import Path
import platform
from typing import Any

from tiny_swarm_world.infrastructure.adapters.bootstrap_state import BootstrapState
from tiny_swarm_world.infrastructure.process.runner import run_process


SOURCE_PATHS = (
    "setup_linux.sh", "install.sh", "tsw", "pyproject.toml", "requirements.lock",
    "requirements.build.lock", "modules/tsw_core/__init__.py", "modules/tsw_core/src",
    "modules/tsw_core/infra", "modules/tsw_native_linux/boostrap",
    "modules/tsw_native_linux/install.sh",
)


def _git(*args: str) -> bytes:
    result = run_process(("git", *args), capture_output=True, check=True, timeout=15)
    return bytes(result.stdout)


def _fingerprint() -> str:
    """Bind the observed checkout bytes, including local runtime and config edits."""
    digest = hashlib.sha256(_git("rev-parse", "--verify", "HEAD"))
    paths = _git("ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *SOURCE_PATHS)
    for name in sorted(set(paths.split(b"\0")) - {b""}):
        path = Path(os.fsdecode(name))
        if path.is_symlink() or not path.is_file():
            raise OSError("Invalid checkout asset.")
        with path.open("rb") as stream:
            digest.update(name + b"\0" + hashlib.file_digest(stream, "sha256").digest())
    return digest.hexdigest()


def _identity(profile: str) -> dict[str, str]:
    release = platform.freedesktop_os_release()
    machine = Path("/etc/machine-id").read_bytes().strip()
    if not machine:
        raise OSError("Missing machine identity.")
    checkout = Path.cwd()
    metadata = checkout.stat()
    return {
        "contract": "guided-setup-v1",
        "source": _fingerprint(),
        "host": hashlib.sha256(machine).hexdigest(),
        "release": release["ID"] + "-" + release["VERSION_ID"],
        "architecture": platform.machine(),
        "operator": str(os.geteuid()),
        "checkout": hashlib.sha256(f"{checkout}:{metadata.st_dev}:{metadata.st_ino}".encode()).hexdigest(),
        "profile": profile,
    }


class GuidedSetupState(BootstrapState):
    def __init__(self, state_home: Path, profile: str) -> None:
        self.project = state_home / "tiny-swarm-world"
        super().__init__(self.project / "guided-setup")
        self.profile = profile
        self.identity = _identity(profile)

    def unchanged_target(self) -> bool:
        return _identity(self.profile) == self.identity

    def restore(self, record: dict[str, Any]) -> None:
        self.publish("setup", self.identity, record)

    def has_preparation_record(self) -> bool:
        interpreter = self.project / "evidence/native-preparation/interpreter.state"
        states = (self.project / "bootstrap" / f"{name}.state.json"
                  for name in ("packages", "python", "incus", "network"))
        return any(path.exists() or path.is_symlink() for path in (interpreter, *states))

    def checkpoint(self, stage: str, status: str, code: int | None = None) -> None:
        stages = ["prepare"] if stage == "prepare" else ["prepare", "install"]
        confirmed = stages if status == "succeeded" else stages[:-1]
        self.restore({
            "stage": stage, "status": status, "planned": stages, "confirmed": confirmed,
            "uncertain": [] if status == "succeeded" else [stage],
            "timestamp": datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"),
            "exit_code": code, "observation_sha256": "unknown",
            "restart": "login" if status == "restart_required" else "none",
            "cause": "none" if status == "succeeded" else "stage_effects_uncertain",
        })

    def prior(self) -> dict[str, Any] | None:
        saved = self.read("setup", self.identity)
        if saved is None:
            return None
        record = saved["record"]
        stage, status = record["stage"], record["status"]
        valid = stage in {"prepare", "install"} and status in {
            "started", "succeeded", "partial", "interrupted", "restart_required",
        }
        planned = ["prepare"] if stage == "prepare" else ["prepare", "install"]
        expected = (planned, []) if status == "succeeded" else (planned[:-1], [stage])
        required_exit: dict[str, set[int | None]] = {
            "started": {None}, "succeeded": {0}, "interrupted": {130, 143},
            "restart_required": {3}, "partial": set(range(1, 256)),
        }
        expected_restart = "login" if status == "restart_required" else "none"
        if (not valid or (status == "restart_required" and stage != "prepare")
                or record["restart"] != expected_restart
                or record["exit_code"] not in required_exit.get(status, set())
                or record["planned"] != planned
                or (record["confirmed"], record["uncertain"]) != expected):
            raise OSError("Invalid guided stage checkpoint.")
        return record

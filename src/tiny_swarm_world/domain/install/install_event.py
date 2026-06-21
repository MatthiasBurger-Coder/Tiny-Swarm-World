from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Sequence

from tiny_swarm_world.domain.install.install_status import InstallStatus


class InstallEventType(StrEnum):
    INSTALL_STARTED = "INSTALL_STARTED"
    INSTALL_FINISHED = "INSTALL_FINISHED"
    STEP_STARTED = "STEP_STARTED"
    STEP_RUNNING = "STEP_RUNNING"
    STEP_SUCCEEDED = "STEP_SUCCEEDED"
    STEP_FAILED = "STEP_FAILED"
    CHECK_STARTED = "CHECK_STARTED"
    CHECK_SUCCEEDED = "CHECK_SUCCEEDED"
    CHECK_FAILED = "CHECK_FAILED"
    EVIDENCE_WRITTEN = "EVIDENCE_WRITTEN"


@dataclass(frozen=True)
class InstallEvent:
    event_type: InstallEventType
    status: InstallStatus
    step: str
    target: str = "host"
    message: str = ""
    reason: str | None = None
    evidence_path: Path | None = None
    suggested_commands: Sequence[str] = ()
    duration_seconds: float | None = None
    sequence: int | None = None
    total: int | None = None

    @classmethod
    def started(
        cls,
        step: str,
        *,
        target: str = "host",
        message: str = "",
        sequence: int | None = None,
        total: int | None = None,
    ) -> "InstallEvent":
        return cls(
            event_type=InstallEventType.STEP_STARTED,
            status=InstallStatus.STARTED,
            step=step,
            target=target,
            message=message,
            sequence=sequence,
            total=total,
        )

    @classmethod
    def succeeded(
        cls,
        step: str,
        *,
        target: str = "host",
        message: str = "",
        evidence_path: Path | None = None,
        sequence: int | None = None,
        total: int | None = None,
    ) -> "InstallEvent":
        return cls(
            event_type=InstallEventType.STEP_SUCCEEDED,
            status=InstallStatus.SUCCEEDED,
            step=step,
            target=target,
            message=message,
            evidence_path=evidence_path,
            sequence=sequence,
            total=total,
        )

    @classmethod
    def failed(
        cls,
        step: str,
        *,
        target: str = "host",
        reason: str,
        message: str = "",
        evidence_path: Path | None = None,
        suggested_commands: Sequence[str] = (),
        sequence: int | None = None,
        total: int | None = None,
    ) -> "InstallEvent":
        return cls(
            event_type=InstallEventType.STEP_FAILED,
            status=InstallStatus.FAILED,
            step=step,
            target=target,
            message=message,
            reason=reason,
            evidence_path=evidence_path,
            suggested_commands=tuple(suggested_commands),
            sequence=sequence,
            total=total,
        )

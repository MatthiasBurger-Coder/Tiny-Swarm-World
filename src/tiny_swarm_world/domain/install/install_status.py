from __future__ import annotations

from enum import StrEnum


class InstallStatus(StrEnum):
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HangDiagnosticCommand:
    name: str
    status: str
    output: str
    timed_out: bool = False
    classification: str = "unknown"


@dataclass(frozen=True)
class HangDiagnosticReport:
    commands: tuple[HangDiagnosticCommand, ...]
    read_only: bool = True

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from tiny_swarm_world.application.ports.install_reporter import InstallReporter
from tiny_swarm_world.domain.install import InstallEvent, InstallEventType, InstallStatus


class NoopInstallReporter:
    def report(self, event: InstallEvent) -> None:
        return None


class PlainConsoleInstallReporter:
    def __init__(self, *, stdout: TextIO | None = None, stderr: TextIO | None = None) -> None:
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def report(self, event: InstallEvent) -> None:
        stream = self._stderr if event.status is InstallStatus.FAILED else self._stdout
        for line in render_install_event(event):
            print(line, file=stream)


def render_install_event(event: InstallEvent) -> tuple[str, ...]:
    prefix = _status_label(event.status)
    header = _step_header(event)
    if event.event_type is InstallEventType.INSTALL_STARTED:
        return ("Tiny Swarm World Installer", _detail_line("RUNNING", event.message or event.step))
    if event.event_type is InstallEventType.INSTALL_FINISHED:
        return (_detail_line(prefix, event.message or event.step),)
    if event.status is InstallStatus.STARTED:
        return (header, _detail_line("RUNNING", _target_message(event)))
    if event.status is InstallStatus.FAILED:
        return _failure_lines(event)
    if event.event_type is InstallEventType.EVIDENCE_WRITTEN:
        evidence = _path_text(event.evidence_path)
        return (_detail_line("EVIDENCE", evidence or event.message or event.step),)
    return (_detail_line(prefix, _target_message(event)),)


def _failure_lines(event: InstallEvent) -> tuple[str, ...]:
    target = f" on {event.target}" if event.target else ""
    lines = [f"FAILED {event.step}{target}"]
    if event.reason:
        lines.extend(("", "Reason:", f"  {event.reason}"))
    evidence = _path_text(event.evidence_path)
    if evidence:
        lines.extend(("", "Evidence:", f"  {evidence}"))
    if event.suggested_commands:
        lines.extend(("", "Suggested checks:"))
        lines.extend(f"  {command}" for command in event.suggested_commands)
    return tuple(lines)


def _step_header(event: InstallEvent) -> str:
    if event.sequence is not None and event.total is not None:
        return f"[{event.sequence}/{event.total}] {event.step}"
    return event.step


def _target_message(event: InstallEvent) -> str:
    if event.message:
        return event.message
    return event.target if event.target else event.step


def _detail_line(status: str, message: str) -> str:
    return f"  {status:<8}{message}"


def _status_label(status: InstallStatus) -> str:
    if status is InstallStatus.SUCCEEDED:
        return "OK"
    if status is InstallStatus.STARTED or status is InstallStatus.RUNNING:
        return "RUNNING"
    return status.value


def _path_text(path: Path | None) -> str:
    return path.as_posix() if path is not None else ""


def default_install_reporter() -> InstallReporter:
    return PlainConsoleInstallReporter()

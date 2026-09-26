"""Streaming child-process lifecycle for the installer and legacy host bridge."""

from __future__ import annotations

import os
import signal
import subprocess
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, NamedTuple

from tiny_swarm_world.infrastructure.process.runner import validate_timeout


ProcessFactory = Callable[..., subprocess.Popen[str]]


class BoundedProcessResult(NamedTuple):
    returncode: int
    timed_out: bool = False
    interrupted: bool = False


def run_bounded_process(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: float,
    stdout: int | IO[str] | None = None,
    stdin: int | IO[str] | None = subprocess.DEVNULL,
) -> BoundedProcessResult:
    validate_timeout(timeout_seconds)
    try:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=dict(env),
            stdout=stdout,
            stderr=subprocess.STDOUT if stdout is not None else None,
            stdin=stdin,
            shell=False,
            start_new_session=True,
        )
    except OSError as exc:
        raise type(exc)(exc.errno, "Process executable could not be launched.") from None
    try:
        process.communicate(timeout=timeout_seconds)
        return BoundedProcessResult(process.returncode or 0)
    except subprocess.TimeoutExpired:
        terminate_process(process)
        return BoundedProcessResult(process.returncode if process.returncode is not None else 124, True)
    except KeyboardInterrupt:
        terminate_process(process)
        return BoundedProcessResult(process.returncode if process.returncode is not None else 130, interrupted=True)


def terminate_process(process: subprocess.Popen[bytes]) -> None:
    """Terminate a session without losing timeout outcomes to exit races."""
    process_group = process.pid if os.name != "nt" else None
    try:
        with suppress(ProcessLookupError):
            if process_group is not None:
                os.killpg(process_group, signal.SIGTERM)
            else:
                process.terminate()
        try:
            process.communicate(timeout=3.0)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                if process_group is not None:
                    os.killpg(process_group, signal.SIGKILL)
                else:
                    process.kill()
            process.communicate(timeout=3.0)
        else:
            if process_group is not None:
                with suppress(ProcessLookupError):
                    os.killpg(process_group, signal.SIGKILL)
    except subprocess.TimeoutExpired:
        raise subprocess.TimeoutExpired("<redacted>", 3.0) from None
    except OSError as exc:
        raise type(exc)(exc.errno, "Process cleanup failed.") from None


@dataclass(frozen=True)
class CapturedProcessResult:
    returncode: int | None
    stdout: str = field(default="", repr=False)
    stderr: str = field(default="", repr=False)
    timed_out: bool = False
    interrupted: bool = False


def run_captured_process(
    command: Sequence[str],
    *,
    timeout: float,
    popen: ProcessFactory | None = None,
    termination_grace_seconds: float = 3.0,
) -> CapturedProcessResult:
    """Bounded captured lifecycle retained for the legacy Windows bridge."""
    validate_timeout(timeout)
    validate_timeout(termination_grace_seconds)
    launch = popen or subprocess.Popen
    process = None
    try:
        process = launch(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, shell=False, start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout)
        return CapturedProcessResult(process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired as exc:
        if process is None:
            return CapturedProcessResult(None, timed_out=True)
        stdout, stderr = _terminate_captured(process, termination_grace_seconds)
        return CapturedProcessResult(
            process.returncode, _coalesce_output(stdout, exc.stdout),
            _coalesce_output(stderr, exc.stderr), timed_out=True,
        )
    except KeyboardInterrupt:
        if process is None:
            return CapturedProcessResult(None, interrupted=True)
        stdout, stderr = _terminate_captured(process, termination_grace_seconds)
        return CapturedProcessResult(process.returncode, stdout, stderr, interrupted=True)
    except OSError as exc:
        return CapturedProcessResult(None, stderr=type(exc).__name__)


def _terminate_captured(process: subprocess.Popen[str], grace: float) -> tuple[str, str]:
    try:
        with suppress(ProcessLookupError):
            process.terminate()
        try:
            return process.communicate(timeout=grace)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                process.kill()
            return process.communicate(timeout=grace)
    except subprocess.TimeoutExpired:
        raise subprocess.TimeoutExpired("<redacted>", grace) from None
    except OSError as exc:
        raise type(exc)(exc.errno, "Process cleanup failed.") from None


def _coalesce_output(primary: str | bytes | None, secondary: str | bytes | None) -> str:
    value = primary if primary is not None else secondary
    return value.decode(errors="replace") if isinstance(value, bytes) else value or ""

"""Safe, bounded process execution for infrastructure adapters."""

from __future__ import annotations

import math
import subprocess
from collections.abc import Mapping, Sequence
from os import PathLike
from typing import Any, Protocol, cast


PathValue = str | PathLike[str]


class ProcessRunnerError(RuntimeError):
    """Base class for sanitized process-runner failures."""


class ProcessLaunchError(ProcessRunnerError):
    """Raised when an executable cannot be launched."""

    def __init__(self) -> None:
        super().__init__("Process executable could not be launched.")


class ProcessTimeoutError(ProcessRunnerError):
    """Raised when a bounded process execution reaches its timeout."""

    def __init__(self) -> None:
        super().__init__("Process execution timed out.")


class ProcessExecutionError(ProcessRunnerError):
    """Raised for a non-zero result when the caller requests ``check``."""

    def __init__(self, returncode: int) -> None:
        self.returncode = returncode
        super().__init__(f"Process execution failed with exit code {returncode}.")


class ProcessRunner(Protocol):
    """Port used by infrastructure adapters for bounded process execution."""

    def run_text(
        self,
        args: Sequence[str],
        *,
        cwd: PathValue | None = None,
        env: Mapping[str, str] | None = None,
        input: str | None = None,
        timeout: float | None = None,
        check: bool = False,
        shell: bool = False,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute argv and return decoded text output."""

    def run_bytes(
        self,
        args: Sequence[str],
        *,
        cwd: PathValue | None = None,
        env: Mapping[str, str] | None = None,
        input: bytes | None = None,
        timeout: float | None = None,
        check: bool = False,
        shell: bool = False,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        """Execute argv and return byte output."""


class SubprocessProcessRunner:
    """Concrete runner backed by ``subprocess.run`` with safe defaults."""

    def __init__(self, default_timeout_seconds: float = 60.0) -> None:
        if not math.isfinite(default_timeout_seconds) or default_timeout_seconds <= 0:
            raise ValueError("Default process timeout must be finite and positive.")
        self.default_timeout_seconds = default_timeout_seconds

    def run_text(
        self,
        args: Sequence[str],
        *,
        cwd: PathValue | None = None,
        env: Mapping[str, str] | None = None,
        input: str | None = None,
        timeout: float | None = None,
        check: bool = False,
        shell: bool = False,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = self._run(
            args,
            cwd=cwd,
            env=env,
            input=input,
            timeout=timeout,
            check=check,
            shell=shell,
            capture_output=capture_output,
            text=True,
        )
        return cast(subprocess.CompletedProcess[str], result)

    def run_bytes(
        self,
        args: Sequence[str],
        *,
        cwd: PathValue | None = None,
        env: Mapping[str, str] | None = None,
        input: bytes | None = None,
        timeout: float | None = None,
        check: bool = False,
        shell: bool = False,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        result = self._run(
            args,
            cwd=cwd,
            env=env,
            input=input,
            timeout=timeout,
            check=check,
            shell=shell,
            capture_output=capture_output,
            text=False,
        )
        return cast(subprocess.CompletedProcess[bytes], result)

    def _run(
        self,
        args: Sequence[str],
        *,
        cwd: PathValue | None,
        env: Mapping[str, str] | None,
        input: str | bytes | None,
        timeout: float | None,
        check: bool,
        shell: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[Any]:
        if not args:
            raise ValueError("Process argv must not be empty.")
        effective_timeout = self.default_timeout_seconds if timeout is None else timeout
        if not math.isfinite(effective_timeout) or effective_timeout <= 0:
            raise ValueError("Process timeout must be finite and positive.")
        try:
            result = run_process(
                args,
                cwd=cwd,
                env=dict(env) if env is not None else None,
                input=input,
                capture_output=capture_output,
                text=text,
                check=False,
                shell=shell,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired:
            raise ProcessTimeoutError from None
        except OSError:
            raise ProcessLaunchError from None
        if check and result.returncode != 0:
            raise ProcessExecutionError(result.returncode)
        return result


class ProcessResult(subprocess.CompletedProcess[Any]):
    """Functional output is private; diagnostic representation never exposes payloads."""

    def __repr__(self) -> str:
        return f"ProcessResult(returncode={self.returncode}, payload='<redacted>')"

    def check_returncode(self) -> None:
        if self.returncode:
            raise subprocess.CalledProcessError(self.returncode, "<redacted>")


def run_process(args: Sequence[str], **options: Any) -> subprocess.CompletedProcess[Any]:
    """Bounded compatibility entry for adapters using subprocess result/error types.

    Output remains available to parsers and credential consumers. Commands, output,
    filenames and exception chains are omitted from diagnostic representations.
    """
    if not args:
        raise ValueError("Process argv must not be empty.")
    timeout = options.get("timeout")
    if timeout is None:
        timeout = 60.0
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Process timeout must be finite and positive.")
    options["timeout"] = timeout
    check = options.pop("check", False)
    try:
        result = subprocess.run(args, check=False, **options)
    except subprocess.TimeoutExpired as exc:
        raise subprocess.TimeoutExpired(
            "<redacted>", timeout,
            output="<redacted>" if exc.stdout else None,
            stderr="<redacted>" if exc.stderr else None,
        ) from None
    except subprocess.CalledProcessError as exc:
        raise subprocess.CalledProcessError(exc.returncode, "<redacted>") from None
    except OSError as exc:
        raise type(exc)(exc.errno, "Process executable could not be launched.") from None
    safe_result = ProcessResult("<redacted>", result.returncode, result.stdout, result.stderr)
    if check:
        safe_result.check_returncode()
    return safe_result


def validate_timeout(timeout: float) -> None:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Process timeout must be finite and positive.")


def redact_process_payload(value: object) -> str:
    """Omit arbitrary command/output payloads, including unlabelled credentials."""
    return "<redacted>" if value else ""

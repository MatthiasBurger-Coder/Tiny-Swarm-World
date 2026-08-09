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
        argv = tuple(args)
        if not argv:
            raise ValueError("Process argv must not be empty.")
        effective_timeout = self.default_timeout_seconds if timeout is None else timeout
        if not math.isfinite(effective_timeout) or effective_timeout <= 0:
            raise ValueError("Process timeout must be finite and positive.")
        try:
            result = subprocess.run(
                argv,
                cwd=cwd,
                env=dict(env) if env is not None else None,
                input=input,
                capture_output=capture_output,
                text=text,
                check=False,
                shell=shell,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProcessTimeoutError from exc
        except (FileNotFoundError, PermissionError, OSError) as exc:
            raise ProcessLaunchError from exc
        if check and result.returncode != 0:
            raise ProcessExecutionError(result.returncode)
        return result

"""Process responsibilities for the live installation boundary."""

from __future__ import annotations
from tiny_swarm_world.application.ports.installation import RESET_CONFIRMATION
from tiny_swarm_world.infrastructure.process.runner import run_process
from tiny_swarm_world.infrastructure.process.streaming import (
    run_bounded_process as _run_bounded_process,
)
import shlex
import subprocess
import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO
from tiny_swarm_world.application.ports.installation import (
    DEFAULT_INSTALLER_PROBE_TIMEOUT_SECONDS,
    DEFAULT_INSTALLER_SUBPROCESS_TIMEOUT_SECONDS,
    HostRuntime,
    INSTALLER_SUBPROCESS_TIMEOUT_ENVIRONMENT,
    InstallReporter,
    InstallerError,
    InstallerOptions,
    InstallerPaths,
)


def _filesystem_override_argument(options: InstallerOptions) -> str:
    if options.allow_wsl_windows_filesystem:
        return " --allow-wsl-windows-filesystem"
    return ""


def ensure_python_environment(
    host_runtime: HostRuntime,
    paths: InstallerPaths,
    env: Mapping[str, str],
) -> str:
    python_bin = "python3"
    if env.get("TSW_INSTALL_SKIP_NATIVE_DEPENDENCY_BOOTSTRAP") == "1":
        return python_bin
    if _python_imports_available(python_bin, env):
        return python_bin
    venv_python = paths.native_linux_venv / "bin" / "python"
    if venv_python.is_file() and _python_imports_available(venv_python.as_posix(), env):
        return venv_python.as_posix()
    runtime_label = "WSL" if host_runtime.name == "wsl2" else "Native Linux"
    print(
        f"{runtime_label} Python dependencies are missing; preparing {paths.native_linux_venv.as_posix()}.",
        file=sys.stderr,
    )
    if (
        env.get("TSW_INSTALL_TEST_MODE") == "1"
        and env.get("TSW_INSTALL_TEST_FORCE_MISSING_IMPORTS") == "1"
    ):
        _write_test_venv_python(venv_python)
        if not _python_imports_available(venv_python.as_posix(), env):
            raise InstallerError(
                "Native Linux Python dependency bootstrap did not make required modules importable."
            )
        return venv_python.as_posix()
    completed = _run_installer_subprocess(
        [python_bin, "-m", "venv", paths.native_linux_venv.as_posix()],
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise InstallerError(
            f"Could not create native Linux virtual environment at {paths.native_linux_venv.as_posix()}. "
            "Install python3-venv and rerun install.sh."
        )
    _run_installer_subprocess(
        [venv_python.as_posix(), "-m", "pip", "install", "--upgrade", "pip"],
        env=dict(env),
        check=True,
    )
    _run_installer_subprocess(
        [
            venv_python.as_posix(),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "-r",
            "requirements.lock",
        ],
        env=dict(env),
        check=True,
    )
    _run_installer_subprocess(
        [venv_python.as_posix(), "-m", "pip", "install", "--no-deps", "-e", "."],
        env=dict(env),
        check=True,
    )
    if not _python_imports_available(venv_python.as_posix(), env):
        raise InstallerError(
            "Native Linux Python dependency bootstrap did not make required modules importable."
        )
    return venv_python.as_posix()


def _write_test_venv_python(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            (
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'if [[ "${1:-}" == "-c" ]]; then exit 0; fi',
                'if [[ "${1:-}" == "-m" && "${2:-}" == "pip" ]]; then exit 0; fi',
                "exit 44",
                "",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _python_imports_available(python_bin: str, env: Mapping[str, str]) -> bool:
    if (
        env.get("TSW_INSTALL_TEST_MODE") == "1"
        and env.get("TSW_INSTALL_TEST_FORCE_MISSING_IMPORTS") == "1"
        and python_bin == "python3"
    ):
        return False
    code = "import pydantic\nimport requests\nimport ruamel.yaml\nimport yaml\n"
    return (
        _run_installer_subprocess(
            [python_bin, "-c", code],
            env=dict(env),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout_seconds=DEFAULT_INSTALLER_PROBE_TIMEOUT_SECONDS,
        ).returncode
        == 0
    )


def _run_installer_subprocess(
    command: Sequence[str],
    *,
    env: Mapping[str, str],
    check: bool,
    timeout_seconds: float | None = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else _installer_subprocess_timeout_seconds(env)
    )
    try:
        return run_process(
            list(command),
            env=dict(env),
            check=check,
            timeout=timeout,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.TimeoutExpired as exc:
        raise InstallerError(
            f"Installer subprocess timed out after {timeout:g}s."
        ) from exc


def _installer_subprocess_timeout_seconds(env: Mapping[str, str]) -> float:
    raw = env.get(
        INSTALLER_SUBPROCESS_TIMEOUT_ENVIRONMENT,
        str(DEFAULT_INSTALLER_SUBPROCESS_TIMEOUT_SECONDS),
    ).strip()
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise InstallerError(
            f"{INSTALLER_SUBPROCESS_TIMEOUT_ENVIRONMENT} must be a positive number."
        ) from exc
    if timeout <= 0:
        raise InstallerError(
            f"{INSTALLER_SUBPROCESS_TIMEOUT_ENVIRONMENT} must be a positive number."
        )
    return timeout


def _workflow_command(python_bin: str, workflow: str, args: str) -> str:
    return f"PYTHONPATH=src {shlex.quote(python_bin)} -m tiny_swarm_world {workflow} {args}"


def _run_phase(
    name: str,
    command: str,
    log_file: Path,
    options: InstallerOptions,
    env: Mapping[str, str],
    cwd: Path,
    reporter: InstallReporter | None = None,
    *,
    sequence: int | None = None,
    total: int | None = None,
) -> int:
    from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
        _default_install_reporter,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
        _phase_event,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.evidence import (
        _read_text,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
        _suggested_checks_for_phase,
    )

    reporter = reporter or _default_install_reporter()
    reporter.report(
        _phase_event(
            "STEP_STARTED",
            "STARTED",
            name,
            message=f"{name} started",
            evidence_path=log_file,
            sequence=sequence,
            total=total,
        )
    )
    if options.headless:
        print(f"Starting {name}. Headless output is recorded at: {log_file.as_posix()}")
    else:
        print(
            f"Starting {name}. Terminal UI is visible and recorded at: {log_file.as_posix()}"
        )
    log_file.parent.mkdir(parents=True, exist_ok=True)
    effective_command = command
    if env.get("TSW_INSTALL_COMMAND_GROUP"):
        effective_command = (
            f"sg {env['TSW_INSTALL_COMMAND_GROUP']} -c {shlex.quote(command)}"
        )
    try:
        timeout_seconds = float(env.get("TSW_INSTALL_PHASE_TIMEOUT_SECONDS", "3600"))
    except ValueError as exc:
        raise InstallerError(
            "TSW_INSTALL_PHASE_TIMEOUT_SECONDS must be a number."
        ) from exc
    if timeout_seconds <= 0:
        raise InstallerError("TSW_INSTALL_PHASE_TIMEOUT_SECONDS must be positive.")
    timed_out = False
    interrupted = False
    if options.headless:
        with log_file.open("w", encoding="utf-8") as output:
            exit_code, timed_out, interrupted = _run_bounded_process(
                ["bash", "-lc", effective_command],
                cwd=cwd,
                env=env,
                timeout_seconds=timeout_seconds,
                stdout=output,
            )
    else:
        exit_code, timed_out, interrupted = _run_bounded_process(
            ["script", "-q", "-e", "-c", effective_command, log_file.as_posix()],
            cwd=cwd,
            env=env,
            timeout_seconds=timeout_seconds,
            stdin=None,
        )
    if timed_out or interrupted:
        status = "TIMED_OUT" if timed_out else "INTERRUPTED"
        event_type = "STEP_TIMED_OUT" if timed_out else "STEP_FAILED"
        reporter.report(
            _phase_event(
                event_type,
                status,
                name,
                reason=(
                    f"{name} exceeded its bounded timeout of {timeout_seconds:g} seconds."
                    if timed_out
                    else f"{name} was interrupted."
                ),
                evidence_path=log_file,
                suggested_commands=_suggested_checks_for_phase(
                    name,
                    log_text=_read_text(log_file),
                ),
                sequence=sequence,
                total=total,
            )
        )
        return 124 if timed_out else 130
    if exit_code == 0:
        reporter.report(
            _phase_event(
                "STEP_SUCCEEDED",
                "SUCCEEDED",
                name,
                message=f"{name} completed",
                evidence_path=log_file,
                sequence=sequence,
                total=total,
            )
        )
    else:
        reporter.report(
            _phase_event(
                "STEP_FAILED",
                "FAILED",
                name,
                reason=f"{name} exited with code {exit_code}.",
                evidence_path=log_file,
                suggested_commands=_suggested_checks_for_phase(
                    name,
                    log_text=_read_text(log_file),
                ),
                sequence=sequence,
                total=total,
            )
        )
    return exit_code


def _run_text(command: tuple[str, ...], *, cwd: Path | None = None) -> str:
    return run_process(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=DEFAULT_INSTALLER_PROBE_TIMEOUT_SECONDS,
    ).stdout.strip()


def _run_optional_text(command: tuple[str, ...], *, cwd: Path | None = None) -> str:
    try:
        result = _run_text(command, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result or "unknown"


class PhaseRunnerAdapter:
    def ensure_python(
        self, host_runtime: HostRuntime, paths: InstallerPaths, env: Mapping[str, str]
    ) -> str:
        return ensure_python_environment(host_runtime, paths, env)

    def phase(
        self,
        name: str,
        command: str,
        log_file: Path,
        options: InstallerOptions,
        env: Mapping[str, str],
        cwd: Path,
        reporter: InstallReporter | None = None,
        *,
        sequence: int | None = None,
        total: int | None = None,
    ) -> int:
        return _run_phase(
            name,
            command,
            log_file,
            options,
            env,
            cwd,
            reporter,
            sequence=sequence,
            total=total,
        )

    def current_python(self) -> str:
        return sys.executable

    def recorder_available(self) -> bool:
        return shutil.which("script") is not None

    def command(
        self,
        python_bin: str,
        phase: str,
        options: InstallerOptions,
        approval_argument: str,
    ) -> str:
        arguments = f"--live{approval_argument}"
        if phase == "reset":
            arguments += f" --confirm {RESET_CONFIRMATION}"
        arguments += f" --service-profile {shlex.quote(options.service_profile)}{_filesystem_override_argument(options)}"
        return _workflow_command(
            python_bin, "platform reset" if phase == "reset" else "setup run", arguments
        )

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

RESET_CONFIRMATION = "RESET_TINY_SWARM_PLATFORM"
DEFAULT_SERVICE_PROFILE = "service-access"
DEFAULT_INFISICAL_LOGIN_EMAIL = "admin@tiny-swarm-world.local"
DEFAULT_SECRET_ENV_FILE = ".tiny-swarm-world/local/live-installation.env"
DEFAULT_FIXED_SECRET_ENV_FILE = ".tiny-swarm-world/local/fixed-secrets.env"
DEFAULT_INFISICAL_SECRET_ENV_FILE = ".tiny-swarm/secrets/bootstrap.local.env"
DEFAULT_GENERATED_SECRET_ENV_FILE = ".tiny-swarm/secrets/generated.local.env"
DEFAULT_NATIVE_LINUX_VENV = ".tiny-swarm-world/install-venv"
DEFAULT_SECRET_MANIFEST_PATH = Path("infra/config/secrets/infisical-secrets.yaml")
WINDOWS_WSL_BRIDGE_STATE_PATH = Path("tools/windows/.tws-wsl-bridge.state.json")
WINDOWS_WSL_BRIDGE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
WINDOWS_EXPOSURE_ENVIRONMENT = "TSW_WINDOWS_EXPOSURE"
INSTALLER_REQUIRED_SOURCES = frozenset({"generated_local_secret", "placeholder_only"})
SECRET_MODES = ("generated", "fixed", "infisical")
DEFAULT_LOCAL_SERVICE_URL_EXPORTS = {
    "TSW_DASHBOARD_URL": "http://localhost:10000",
    "TSW_INFISICAL_URL": "http://localhost:17080",
    "TSW_JENKINS_URL": "http://localhost:11080",
    "TSW_NEXUS_URL": "http://localhost:13081",
    "TSW_PORTAINER_URL": "http://localhost:10001",
    "TSW_PULSAR_PUBLIC_ADMIN_URL": "http://localhost:14080",
    "TSW_PULSAR_MANAGER_URL": "http://localhost:14081",
    "TSW_SONARQUBE_URL": "http://localhost:12000",
    "TSW_SWAGGER_URL": "http://localhost:16081",
}


@dataclass(frozen=True)
class InstallerOptions:
    service_profile: str
    generate_secrets: bool
    secrets_mode: str
    confirm_reset: bool
    non_interactive_live_approval: bool
    headless: bool


@dataclass(frozen=True)
class InstallerPaths:
    secret_env_file: Path
    fixed_secret_env_file: Path
    infisical_secret_env_file: Path
    generated_secret_env_file: Path
    native_linux_venv: Path


@dataclass(frozen=True)
class HostRuntime:
    name: str
    detection_source: str


@dataclass(frozen=True)
class InstallerSecretEntry:
    key: str
    source: str
    required: bool


@dataclass(frozen=True)
class WindowsWslBridgeGuardResult:
    passed: bool
    reason: str
    state_path: Path
    current_wsl_ip: str = ""
    state_wsl_ip: str = ""
    expected_ports: tuple[int, ...] = ()
    mapped_ports: tuple[int, ...] = ()
    missing_ports: tuple[int, ...] = ()


class InstallReporter(Protocol):
    def report(self, event: object) -> None:
        ...


@dataclass(frozen=True)
class _FallbackInstallEvent:
    event_type: str
    status: str
    step: str
    target: str = "host"
    message: str = ""
    reason: str | None = None
    evidence_path: Path | None = None
    suggested_commands: Sequence[str] = ()
    duration_seconds: float | None = None
    sequence: int | None = None
    total: int | None = None


class _FallbackInstallReporter:
    def report(self, event: object) -> None:
        if not isinstance(event, _FallbackInstallEvent):
            return
        stream = sys.stderr if event.status == "FAILED" else sys.stdout
        for line in _render_fallback_install_event(event):
            print(line, file=stream)


class InstallerError(RuntimeError):
    pass


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(parse_args(argv), env=os.environ, cwd=Path.cwd())
    except InstallerError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


def parse_args(argv: Sequence[str] | None = None) -> InstallerOptions:
    parser = argparse.ArgumentParser(description="Tiny Swarm World live installation wrapper.")
    parser.add_argument(
        "--service-profile",
        default=os.environ.get("SERVICE_PROFILE", DEFAULT_SERVICE_PROFILE),
        choices=("default", "service-access"),
        help="Service profile passed to setup run.",
    )
    parser.add_argument(
        "--no-generate-secrets",
        action="store_true",
        help="Fail if required TSW_* secrets are missing.",
    )
    parser.add_argument(
        "--secrets-mode",
        choices=SECRET_MODES,
        default=os.environ.get("TSW_SECRETS_MODE", "generated"),
        help="Secret source mode: generated, fixed, or infisical.",
    )
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Confirm the governed fresh-install reset without prompting.",
    )
    parser.add_argument(
        "--non-interactive-live-approval",
        action="store_true",
        help="Pass explicit non-interactive live approval to the CLI.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Disable terminal recorder/TUI presentation and capture command output directly.",
    )
    args = parser.parse_args(argv)
    if args.secrets_mode not in SECRET_MODES:
        parser.error("--secrets-mode must be one of generated, fixed, or infisical")
    return InstallerOptions(
        service_profile=args.service_profile,
        generate_secrets=not args.no_generate_secrets,
        secrets_mode=args.secrets_mode,
        confirm_reset=args.confirm_reset,
        non_interactive_live_approval=args.non_interactive_live_approval,
        headless=args.headless or os.environ.get("TSW_INSTALL_HEADLESS") == "1",
    )


def _phase_event(
    event_type: str,
    status: str,
    step: str,
    *,
    target: str = "host",
    message: str = "",
    reason: str | None = None,
    evidence_path: Path | None = None,
    suggested_commands: Sequence[str] = (),
    sequence: int | None = None,
    total: int | None = None,
) -> object:
    try:
        from tiny_swarm_world.domain.install import InstallEvent, InstallEventType, InstallStatus

        typed_event_type = InstallEventType(event_type)
        typed_status = InstallStatus(status)
        return InstallEvent(
            event_type=typed_event_type,
            status=typed_status,
            step=step,
            target=target,
            message=message,
            reason=reason,
            evidence_path=evidence_path,
            suggested_commands=tuple(suggested_commands),
            sequence=sequence,
            total=total,
        )
    except ModuleNotFoundError:
        return _FallbackInstallEvent(
        event_type=event_type,
        status=status,
        step=step,
        target=target,
        message=message,
        reason=reason,
        evidence_path=evidence_path,
        suggested_commands=tuple(suggested_commands),
        sequence=sequence,
        total=total,
    )


def _default_install_reporter() -> InstallReporter:
    try:
        from tiny_swarm_world.infrastructure.adapters.ui.install_reporter import default_install_reporter

        return default_install_reporter()
    except ModuleNotFoundError:
        return _FallbackInstallReporter()


def run(
    options: InstallerOptions,
    *,
    env: Mapping[str, str],
    cwd: Path,
    reporter: InstallReporter | None = None,
) -> int:
    install_reporter = reporter or _default_install_reporter()
    _require_repository(cwd)
    paths = _paths_from_env(env, cwd)
    host_runtime = detect_host_runtime(env)
    python_bin = ensure_python_environment(host_runtime, paths, env)
    install_env = dict(env)
    secret_mode = _secret_mode(options)
    install_env["TSW_SECRETS_MODE"] = secret_mode
    install_env["TSW_FIXED_SECRET_ENV_FILE"] = paths.fixed_secret_env_file.as_posix()

    _ensure_private_file(paths.secret_env_file)
    _ensure_private_file(paths.infisical_secret_env_file)
    _ensure_private_file(paths.generated_secret_env_file)
    install_env.update(_load_export_file(paths.secret_env_file))
    install_env.update(_load_export_file(paths.infisical_secret_env_file))

    required_entries = _required_installer_secret_entries(
        cwd / DEFAULT_SECRET_MANIFEST_PATH,
        sources=None if secret_mode == "fixed" else INSTALLER_REQUIRED_SOURCES,
    )
    secrets_generated_count = 0
    if secret_mode == "fixed":
        fixed_values = _fixed_installer_secret_values(paths.fixed_secret_env_file, required_entries)
        install_env.update(fixed_values)
    else:
        missing = [entry for entry in required_entries if not install_env.get(entry.key)]
        if missing and (secret_mode == "infisical" or not options.generate_secrets):
            _print_missing_secrets([entry.key for entry in missing])
            raise InstallerError(
                f"Provide the missing values in {paths.secret_env_file.as_posix()} "
                "or use --secrets-mode generated with secret generation enabled."
            )
        if missing:
            generated = _generated_secret_values(missing, install_env)
            _append_exports(
                paths.secret_env_file,
                f"Generated by install.sh at {_utc_timestamp()} UTC",
                generated,
            )
            install_env.update(generated)
            secrets_generated_count = len(missing)

    _normalize_infisical_login_email(paths, install_env)
    _ensure_sonarqube_password_policy(options, paths, install_env)
    _ensure_default_config_exports(paths, install_env)
    _normalize_export_file_if_duplicate_keys(paths.secret_env_file)
    _write_infisical_secret_file(paths.infisical_secret_env_file, install_env)
    install_env.setdefault("TSW_SEED_INFISICAL_ITEMS", "0")
    _configure_native_linux_command_group(host_runtime, install_env)

    if _inside_git_worktree(cwd) and not _git_check_ignore(cwd, ".tiny-swarm-world/"):
        print(
            "WARN: .tiny-swarm-world/ is not ignored by git; do not commit local evidence or generated secrets.",
            file=sys.stderr,
        )

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = cwd / ".tiny-swarm-world" / "evidence" / "installation-tests" / host_runtime.name / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    live_mode, approval_source, approval_argument = _live_approval(options)
    terminal_mode = "headless" if options.headless else "terminal_recorder"
    _write_context(
        evidence_dir,
        run_id=run_id,
        service_profile=options.service_profile,
        secrets_mode=secret_mode,
        secret_env_file=paths.secret_env_file,
        fixed_secret_env_file=paths.fixed_secret_env_file,
        checked_secret_keys=tuple(entry.key for entry in required_entries),
        secrets_generated_count=secrets_generated_count,
        host_runtime=host_runtime,
        live_execution_mode=live_mode,
        live_approval_source=approval_source,
        terminal_recording_mode=terminal_mode,
        cwd=cwd,
        env=install_env,
    )

    _print_install_plan(cwd, options, evidence_dir, paths.secret_env_file)
    install_reporter.report(
        _phase_event(
            "INSTALL_STARTED",
            "RUNNING",
            "install",
            message=(
                f"Mode: fresh-reset; Profile: {options.service_profile}; "
                f"Provider: {install_env.get('TSW_NODE_PROVIDER', 'lxc_native')}"
            ),
        )
    )
    _confirm_reset(options)
    if not options.headless and shutil.which("script") is None:
        raise InstallerError("Required command 'script' is not available for terminal recording. Use --headless to capture logs directly.")
    _append_context(
        evidence_dir,
        {
            "reset_confirmation_present": "yes",
            "reset_confirmation_source": "explicit_flag" if options.confirm_reset else "interactive_prompt",
        },
    )

    bridge_guard = _windows_wsl_bridge_guard(host_runtime, install_env, cwd)
    _append_context(
        evidence_dir,
        _windows_wsl_bridge_context(bridge_guard),
    )
    if not bridge_guard.passed:
        install_reporter.report(
            _phase_event(
                "INSTALL_FINISHED",
                "FAILED",
                "windows-wsl-bridge",
                reason="Windows <-> WSL bridge is not prepared.",
                evidence_path=evidence_dir,
                suggested_commands=_windows_wsl_bridge_suggested_commands(bridge_guard.reason),
            )
        )
        _print_windows_wsl_bridge_failure(bridge_guard, evidence_dir)
        _append_context(
            evidence_dir,
            {
                "reset_skipped_due_to_windows_wsl_bridge": "yes",
                "setup_skipped_due_to_windows_wsl_bridge": "yes",
                "finished_utc": _utc_timestamp(),
            },
        )
        return 1

    reset_command = _workflow_command(
        python_bin,
        "platform reset",
        f"--live{approval_argument} --confirm {RESET_CONFIRMATION} --service-profile {shlex.quote(options.service_profile)}",
    )
    setup_command = _workflow_command(
        python_bin,
        "setup run",
        f"--live{approval_argument} --service-profile {shlex.quote(options.service_profile)}",
    )

    reset_exit = _run_phase(
        "fresh-install reset",
        reset_command,
        evidence_dir / "reset-run.log",
        options,
        install_env,
        cwd,
        install_reporter,
        sequence=1,
        total=2,
    )
    _write_text(evidence_dir / "reset-run.exit", f"{reset_exit}\n")
    _append_context(evidence_dir, {"reset_exit": str(reset_exit)})
    if reset_exit != 0:
        install_reporter.report(
            _phase_event(
                "INSTALL_FINISHED",
                "FAILED",
                "install",
                reason="Fresh-install reset failed. Setup was not started.",
                evidence_path=evidence_dir,
            )
        )
        print(f"Fresh-install reset failed with exit code {reset_exit}. Setup will not start.", file=sys.stderr)
        print(f"Evidence directory: {evidence_dir.as_posix()}", file=sys.stderr)
        _append_context(
            evidence_dir,
            {
                "setup_skipped_due_to_reset_failure": "yes",
                "finished_utc": _utc_timestamp(),
            },
        )
        _print_tail(evidence_dir / "reset-run.log", "Last reset log lines")
        _print_reset_failure_guidance(evidence_dir / "reset-run.log")
        return reset_exit

    setup_exit = _run_phase(
        "live setup",
        setup_command,
        evidence_dir / "setup-run.log",
        options,
        install_env,
        cwd,
        install_reporter,
        sequence=2,
        total=2,
    )
    _write_text(evidence_dir / "setup-run.exit", f"{setup_exit}\n")
    _append_context(
        evidence_dir,
        {
            "setup_exit": str(setup_exit),
            "finished_utc": _utc_timestamp(),
        },
    )
    if setup_exit == 0:
        install_reporter.report(
            _phase_event(
                "INSTALL_FINISHED",
                "SUCCEEDED",
                "install",
                message="Installation completed successfully.",
                evidence_path=evidence_dir,
            )
        )
        print("Installation completed successfully.")
        print(f"Evidence directory: {evidence_dir.as_posix()}")
    else:
        install_reporter.report(
            _phase_event(
                "INSTALL_FINISHED",
                "FAILED",
                "install",
                reason=f"Live setup failed with exit code {setup_exit}.",
                evidence_path=evidence_dir,
            )
        )
        print(f"Installation failed with exit code {setup_exit}.", file=sys.stderr)
        print(f"Evidence directory: {evidence_dir.as_posix()}", file=sys.stderr)
        _print_tail(evidence_dir / "setup-run.log", "Last log lines")
        _print_setup_failure_guidance(evidence_dir / "setup-run.log")
    return setup_exit


def _paths_from_env(env: Mapping[str, str], cwd: Path) -> InstallerPaths:
    def resolve(path_value: str) -> Path:
        path = Path(path_value)
        return path if path.is_absolute() else cwd / path

    return InstallerPaths(
        secret_env_file=resolve(env.get("TSW_INSTALL_ENV_FILE", DEFAULT_SECRET_ENV_FILE)),
        fixed_secret_env_file=resolve(env.get("TSW_FIXED_SECRET_ENV_FILE", DEFAULT_FIXED_SECRET_ENV_FILE)),
        infisical_secret_env_file=resolve(env.get("TSW_INFISICAL_SECRET_ENV_FILE", DEFAULT_INFISICAL_SECRET_ENV_FILE)),
        generated_secret_env_file=resolve(env.get("TSW_GENERATED_SECRET_ENV_FILE", DEFAULT_GENERATED_SECRET_ENV_FILE)),
        native_linux_venv=resolve(env.get("TSW_NATIVE_LINUX_VENV", DEFAULT_NATIVE_LINUX_VENV)),
    )


def _require_repository(cwd: Path) -> None:
    if not (cwd / "src" / "tiny_swarm_world").is_dir():
        raise InstallerError("Run this script from the Tiny Swarm World repository root.")


def _required_installer_secret_entries(
    manifest_path: Path,
    *,
    sources: frozenset[str] | None = INSTALLER_REQUIRED_SOURCES,
) -> tuple[InstallerSecretEntry, ...]:
    try:
        import yaml

        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InstallerError(f"Secret manifest is invalid: {error}") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("secrets"), list):
        raise InstallerError("Secret manifest is invalid: expected a secrets list.")
    entries = tuple(_installer_secret_entry(item) for item in payload["secrets"])
    return tuple(
        entry
        for entry in entries
        if entry.required and (sources is None or entry.source in sources)
    )


def _installer_secret_entry(item: object) -> InstallerSecretEntry:
    if not isinstance(item, dict):
        raise InstallerError("Secret manifest is invalid: secret entries must be mappings.")
    key = str(item.get("key", ""))
    source = str(item.get("source", ""))
    if not key.startswith("TSW_"):
        raise InstallerError(f"Secret manifest is invalid: unsupported key {key!r}.")
    return InstallerSecretEntry(
        key=key,
        source=source,
        required=bool(item.get("required", False)),
    )


def _secret_mode(options: InstallerOptions) -> str:
    if options.secrets_mode not in SECRET_MODES:
        raise InstallerError("secrets mode must be generated, fixed, or infisical.")
    return options.secrets_mode


def _fixed_installer_secret_values(path: Path, required_entries: Sequence[InstallerSecretEntry]) -> dict[str, str]:
    if not path.exists():
        raise InstallerError(f"Fixed secret file is missing: {path.as_posix()}")
    values = _load_export_file(path)
    required_keys = tuple(entry.key for entry in required_entries)
    missing = [key for key in required_keys if key not in values]
    if missing:
        raise InstallerError(f"Fixed secret key is missing: {missing[0]}")
    empty = [key for key in required_keys if not values.get(key, "").strip()]
    if empty:
        raise InstallerError(f"Fixed secret value is empty: {empty[0]}")
    return {key: values[key] for key in required_keys}


def detect_host_runtime(env: Mapping[str, str]) -> HostRuntime:
    test_runtime = env.get("TSW_INSTALL_TEST_HOST_RUNTIME")
    if env.get("TSW_INSTALL_TEST_MODE") == "1" and test_runtime in {"wsl2", "native_linux"}:
        return HostRuntime(test_runtime, "test_override")
    if env.get("WSL_DISTRO_NAME") or env.get("WSL_INTEROP"):
        return HostRuntime("wsl2", "wsl_environment")
    kernel_text = _read_text(Path("/proc/sys/kernel/osrelease")).casefold()
    version_text = _read_text(Path("/proc/version")).casefold()
    if "microsoft" in kernel_text or "wsl" in kernel_text or "microsoft" in version_text or "wsl" in version_text:
        return HostRuntime("wsl2", "kernel_signal")
    return HostRuntime("native_linux", "uname_linux_without_wsl_signal")


def _windows_wsl_bridge_guard(
    host_runtime: HostRuntime,
    env: Mapping[str, str],
    cwd: Path,
) -> WindowsWslBridgeGuardResult:
    state_path = cwd / WINDOWS_WSL_BRIDGE_STATE_PATH
    expected_ports = _windows_wsl_bridge_expected_ports(cwd)
    if host_runtime.name != "wsl2":
        return WindowsWslBridgeGuardResult(True, "not_wsl2", state_path, expected_ports=expected_ports)
    if not _windows_exposure_required(env):
        return WindowsWslBridgeGuardResult(
            True,
            "windows_exposure_disabled",
            state_path,
            expected_ports=expected_ports,
        )
    if not state_path.exists():
        return WindowsWslBridgeGuardResult(
            False,
            "state_missing",
            state_path,
            expected_ports=expected_ports,
            missing_ports=expected_ports,
        )
    from tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state import (
        current_wsl_ipv4,
        windows_wsl_bridge_status,
    )

    status = windows_wsl_bridge_status(
        cwd,
        expected_ports,
        max_age_seconds=WINDOWS_WSL_BRIDGE_MAX_AGE_SECONDS,
        current_wsl_ipv4=current_wsl_ipv4,
    )
    return WindowsWslBridgeGuardResult(
        status.prepared,
        status.reason,
        state_path,
        current_wsl_ip=status.current_wsl_ip,
        state_wsl_ip=status.state_wsl_ip,
        expected_ports=status.expected_ports,
        mapped_ports=status.mapped_ports,
        missing_ports=status.missing_ports,
    )


def _windows_exposure_required(env: Mapping[str, str]) -> bool:
    value = env.get(WINDOWS_EXPOSURE_ENVIRONMENT, "").strip().casefold()
    return value not in {"0", "false", "no", "off", "disabled"}


def _windows_wsl_bridge_expected_ports(cwd: Path) -> tuple[int, ...]:
    registry_path = cwd / "infra" / "config" / "ports.yaml"
    ports: set[int] = set()
    current: dict[str, str] | None = None
    in_ports = False

    def commit_current() -> None:
        if current is None or "external_port" not in current:
            return
        protocol = current.get("protocol", "tcp").casefold()
        if protocol != "tcp":
            return
        ports.add(int(current["external_port"]))

    for line in _read_text(registry_path).splitlines():
        if re.match(r"^ports:\s*$", line):
            in_ports = True
            continue
        if not in_ports:
            continue
        if re.match(r"^\S", line) and not re.match(r"^ports:\s*$", line):
            break
        match = re.match(r"^\s*-\s+id:\s*(.+?)\s*$", line)
        if match:
            commit_current()
            current = {"id": _clean_yaml_scalar(match.group(1))}
            continue
        if current is None:
            continue
        match = re.match(r"^\s+external_port:\s*(\d+)\s*$", line)
        if match:
            current["external_port"] = match.group(1)
            continue
        match = re.match(r"^\s+protocol:\s*(\S+)\s*$", line)
        if match:
            current["protocol"] = _clean_yaml_scalar(match.group(1))
            continue

    commit_current()
    return tuple(sorted(ports))


def _clean_yaml_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


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
    if env.get("TSW_INSTALL_TEST_MODE") == "1" and env.get("TSW_INSTALL_TEST_FORCE_MISSING_IMPORTS") == "1":
        _write_test_venv_python(venv_python)
        if not _python_imports_available(venv_python.as_posix(), env):
            raise InstallerError("Native Linux Python dependency bootstrap did not make required modules importable.")
        return venv_python.as_posix()
    completed = subprocess.run(
        [python_bin, "-m", "venv", paths.native_linux_venv.as_posix()],
        env=dict(env),
        check=False,
    )
    if completed.returncode != 0:
        raise InstallerError(
            f"Could not create native Linux virtual environment at {paths.native_linux_venv.as_posix()}. "
            "Install python3-venv and rerun install.sh."
        )
    subprocess.run(
        [venv_python.as_posix(), "-m", "pip", "install", "--upgrade", "pip"],
        env=dict(env),
        check=True,
    )
    subprocess.run(
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
    subprocess.run(
        [venv_python.as_posix(), "-m", "pip", "install", "--no-deps", "-e", "."],
        env=dict(env),
        check=True,
    )
    if not _python_imports_available(venv_python.as_posix(), env):
        raise InstallerError("Native Linux Python dependency bootstrap did not make required modules importable.")
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
    return subprocess.run(
        [python_bin, "-c", code],
        env=dict(env),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _load_export_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        assignment = _export_assignment_from_line(raw_line)
        if assignment is None:
            continue
        name, raw_value = assignment
        values[name] = _parse_export_value(raw_value)
    return values


def _normalize_export_file_if_duplicate_keys(path: Path) -> None:
    duplicates = _duplicate_export_keys(path)
    if not duplicates:
        return
    _write_exports(
        path,
        f"Normalized by install.sh after duplicate key cleanup at {_utc_timestamp()} UTC",
        _load_export_file(path),
    )


def _duplicate_export_keys(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    seen: set[str] = set()
    duplicates: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        assignment = _export_assignment_from_line(raw_line)
        if assignment is None:
            continue
        name, _ = assignment
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    return tuple(sorted(duplicates))


def _export_assignment_from_line(raw_line: str) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line.removeprefix("export ").strip()
    if "=" not in line:
        return None
    name, raw_value = line.split("=", 1)
    if not name.isidentifier():
        return None
    return name, raw_value


def _parse_export_value(raw_value: str) -> str:
    try:
        parsed = shlex.split(raw_value, posix=True)
    except ValueError as exc:
        raise InstallerError("Local installer environment file contains invalid shell quoting.") from exc
    return parsed[0] if parsed else ""


def _generated_secret_values(
    entries: Sequence[InstallerSecretEntry],
    current_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    current_values = dict(current_env or {})
    generated: dict[str, str] = {}
    for entry in entries:
        name = entry.key
        if name == "TSW_INFISICAL_ENCRYPTION_KEY":
            generated[name] = secrets.token_hex(16)
        elif name == "TSW_INFISICAL_LOGIN_EMAIL":
            generated[name] = DEFAULT_INFISICAL_LOGIN_EMAIL
        elif name == "TSW_SONARQUBE_ADMIN_PASSWORD":
            generated[name] = f"{secrets.token_urlsafe(32)}!"
        elif name == "TSW_PULSAR_TOKEN_SECRET_KEY":
            generated[name] = _generated_pulsar_token_secret_key()
            generated["TSW_PULSAR_ADMIN_TOKEN"] = _generated_pulsar_admin_token(
                generated[name],
            )
        elif name == "TSW_PULSAR_ADMIN_TOKEN":
            secret_key = (
                generated.get("TSW_PULSAR_TOKEN_SECRET_KEY")
                or current_values.get("TSW_PULSAR_TOKEN_SECRET_KEY")
                or _generated_pulsar_token_secret_key()
            )
            generated.setdefault("TSW_PULSAR_TOKEN_SECRET_KEY", secret_key)
            generated[name] = _generated_pulsar_admin_token(secret_key)
        else:
            generated[name] = secrets.token_urlsafe(32)
    return generated


def _generated_pulsar_token_secret_key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode("ascii")


def _generated_pulsar_admin_token(secret_key: str) -> str:
    key = base64.b64decode(secret_key)
    header = _base64url_json({"alg": "HS256", "typ": "JWT"})
    payload = _base64url_json({"sub": "admin"})
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_base64url(signature)}"


def _base64url_json(payload: Mapping[str, str]) -> str:
    return _base64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def _base64url(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _ensure_sonarqube_password_policy(
    options: InstallerOptions,
    paths: InstallerPaths,
    env: dict[str, str],
) -> None:
    current = env.get("TSW_SONARQUBE_ADMIN_PASSWORD", "")
    if len(current) >= 12 and any(character in current for character in "!@#$%^&*()_+"):
        return
    if options.secrets_mode != "generated" or not options.generate_secrets:
        raise InstallerError("TSW_SONARQUBE_ADMIN_PASSWORD must be at least 12 characters and contain a special character.")
    value = f"{secrets.token_urlsafe(32)}!"
    env["TSW_SONARQUBE_ADMIN_PASSWORD"] = value
    exports = {"TSW_SONARQUBE_ADMIN_PASSWORD": value}
    label = f"Regenerated by install.sh for SonarQube password policy at {_utc_timestamp()} UTC"
    _append_exports(paths.secret_env_file, label, exports)
    _append_exports(paths.generated_secret_env_file, label, exports)


def _ensure_default_config_exports(paths: InstallerPaths, env: dict[str, str]) -> None:
    exports: dict[str, str] = {}
    if not env.get("TSW_TRAEFIK_TLS_CERT_SECRET_NAME"):
        exports["TSW_TRAEFIK_TLS_CERT_SECRET_NAME"] = "tsw_traefik_tls_cert"
    if not env.get("TSW_TRAEFIK_TLS_KEY_SECRET_NAME"):
        exports["TSW_TRAEFIK_TLS_KEY_SECRET_NAME"] = "tsw_traefik_tls_key"
    if not exports:
        return
    env.update(exports)
    _append_exports(
        paths.secret_env_file,
        f"Default non-secret config values written by install.sh at {_utc_timestamp()} UTC",
        exports,
    )


def _normalize_infisical_login_email(paths: InstallerPaths, env: dict[str, str]) -> None:
    current = env.get("TSW_INFISICAL_LOGIN_EMAIL", "")
    normalized = _normalized_email_value(current)
    if not normalized or normalized == current:
        return
    env["TSW_INFISICAL_LOGIN_EMAIL"] = normalized
    _append_exports(
        paths.secret_env_file,
        f"Corrected Infisical login email shell quoting at {_utc_timestamp()} UTC",
        {"TSW_INFISICAL_LOGIN_EMAIL": normalized},
    )


def _normalized_email_value(value: str) -> str:
    stripped = value.strip()
    quote_stripped = stripped.strip("'\"")
    if quote_stripped and "@" in quote_stripped and "." in quote_stripped.partition("@")[2]:
        return quote_stripped
    return stripped


def _write_infisical_secret_file(path: Path, env: Mapping[str, str]) -> None:
    exports = {
        **DEFAULT_LOCAL_SERVICE_URL_EXPORTS,
        "TSW_INFISICAL_ENCRYPTION_KEY": env["TSW_INFISICAL_ENCRYPTION_KEY"],
        "TSW_INFISICAL_AUTH_SECRET": env["TSW_INFISICAL_AUTH_SECRET"],
        "TSW_INFISICAL_POSTGRES_PASSWORD": env["TSW_INFISICAL_POSTGRES_PASSWORD"],
        "TSW_INFISICAL_REDIS_PASSWORD": env["TSW_INFISICAL_REDIS_PASSWORD"],
        "TSW_INFISICAL_LOGIN_EMAIL": env["TSW_INFISICAL_LOGIN_EMAIL"],
        "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": env["TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"],
    }
    _write_exports(path, "Generated by install.sh. Do not commit.", exports)


def _configure_native_linux_command_group(host_runtime: HostRuntime, env: dict[str, str]) -> None:
    return


def _confirm_reset(options: InstallerOptions) -> None:
    if options.confirm_reset:
        print("Fresh-install reset confirmed by explicit --confirm-reset flag.")
        return
    print("Fresh install will reset configured Tiny Swarm World managed state.")
    try:
        answer = input(f"Type {RESET_CONFIRMATION} to continue: ")
    except EOFError:
        raise InstallerError("Fresh-install reset confirmation was not provided.") from None
    if answer != RESET_CONFIRMATION:
        raise InstallerError("Fresh-install reset confirmation did not match.")


def _live_approval(options: InstallerOptions) -> tuple[str, str, str]:
    if options.non_interactive_live_approval:
        return "non_interactive", "explicit_automation_flag", " --approve-live"
    return "interactive", "operator_prompt", ""


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
        print(f"Starting {name}. Terminal UI is visible and recorded at: {log_file.as_posix()}")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    effective_command = command
    if env.get("TSW_INSTALL_COMMAND_GROUP"):
        effective_command = f"sg {env['TSW_INSTALL_COMMAND_GROUP']} -c {shlex.quote(command)}"
    if options.headless:
        with log_file.open("w", encoding="utf-8") as output:
            completed = subprocess.run(
                ["bash", "-lc", effective_command],
                cwd=cwd,
                env=dict(env),
                stdout=output,
                stderr=subprocess.STDOUT,
                check=False,
            )
        exit_code = completed.returncode
    else:
        exit_code = subprocess.run(
            ["script", "-q", "-e", "-c", effective_command, log_file.as_posix()],
            cwd=cwd,
            env=dict(env),
            check=False,
        ).returncode
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


def _suggested_checks_for_phase(name: str, *, log_text: str = "") -> tuple[str, ...]:
    normalized = name.casefold()
    commands: list[str]
    if "setup" in normalized:
        if "apt_repository_unreachable" in log_text:
            commands = [
                "./tsw doctor network",
                "./tsw network repair --linux-forwarding --apply",
                "powershell.exe -ExecutionPolicy Bypass -File .\\tools\\windows\\doctor-portproxy.ps1",
            ]
        else:
            commands = [
                "incus exec swarm-manager -- docker node ls",
                "incus exec swarm-manager -- docker service ls",
            ]
    elif "reset" in normalized:
        commands = [
            "incus list",
            "docker context ls",
        ]
    else:
        commands = []
    return tuple(commands)


def _render_fallback_install_event(event: _FallbackInstallEvent) -> tuple[str, ...]:
    lines: list[str]
    if event.event_type == "INSTALL_STARTED":
        lines = ["Tiny Swarm World Installer", f"  RUNNING {event.message or event.step}"]
        return tuple(lines)
    if event.status == "STARTED":
        header = f"[{event.sequence}/{event.total}] {event.step}" if event.sequence and event.total else event.step
        lines = [header, f"  RUNNING {event.message or event.target}"]
        return tuple(lines)
    if event.status == "SUCCEEDED":
        lines = [f"  OK      {event.message or event.target}"]
        return tuple(lines)
    if event.status == "FAILED":
        target = f" on {event.target}" if event.target else ""
        lines = [f"FAILED {event.step}{target}"]
        if event.reason:
            lines.extend(("", "Reason:", f"  {event.reason}"))
        if event.evidence_path:
            lines.extend(("", "Evidence:", f"  {event.evidence_path.as_posix()}"))
        if event.suggested_commands:
            lines.extend(("", "Suggested checks:"))
            lines.extend(f"  {command}" for command in event.suggested_commands)
        return tuple(lines)
    lines = [f"  {event.status:<8}{event.message or event.target}"]
    return tuple(lines)


def _write_context(
    evidence_dir: Path,
    *,
    run_id: str,
    service_profile: str,
    secrets_mode: str,
    secret_env_file: Path,
    fixed_secret_env_file: Path,
    checked_secret_keys: Sequence[str],
    secrets_generated_count: int,
    host_runtime: HostRuntime,
    live_execution_mode: str,
    live_approval_source: str,
    terminal_recording_mode: str,
    cwd: Path,
    env: Mapping[str, str],
) -> None:
    values = {
        "run_id": run_id,
        "started_utc": _utc_timestamp(),
        "repo": cwd.as_posix(),
        "git_branch": _run_text(("git", "branch", "--show-current"), cwd=cwd),
        "git_head": _run_text(("git", "rev-parse", "--short", "HEAD"), cwd=cwd),
        "service_profile": service_profile,
        "fresh_install_reset": "required",
        "secrets_mode": secrets_mode,
        "secret_env_file": secret_env_file.as_posix(),
        "fixed_secret_env_file": fixed_secret_env_file.as_posix(),
        "checked_secret_keys": ",".join(checked_secret_keys),
        "secrets_generated_count": str(secrets_generated_count),
        "host_runtime_type": host_runtime.name,
        "host_runtime_detection_source": host_runtime.detection_source,
        "selected_evidence_directory": evidence_dir.as_posix(),
        "live_execution_mode": live_execution_mode,
        "live_approval_source": live_approval_source,
        "terminal_recording_mode": terminal_recording_mode,
        "platform_system": _run_text(("uname", "-s")),
        "kernel_release": _run_text(("uname", "-r")),
        "proc_osrelease": _read_text(Path("/proc/sys/kernel/osrelease")).strip(),
        "wsl_distro_name_present": "yes" if env.get("WSL_DISTRO_NAME") else "no",
        "wsl_interop_present": "yes" if env.get("WSL_INTEROP") else "no",
    }
    _append_context(evidence_dir, values, replace=True)


def _append_context(evidence_dir: Path, values: Mapping[str, str], *, replace: bool = False) -> None:
    mode = "w" if replace else "a"
    with (evidence_dir / "context.txt").open(mode, encoding="utf-8") as context:
        for key, value in values.items():
            context.write(f"{key}={value}\n")


def _windows_wsl_bridge_context(
    guard: WindowsWslBridgeGuardResult,
) -> dict[str, str]:
    return {
        "windows_wsl_bridge_passed": "yes" if guard.passed else "no",
        "windows_wsl_bridge_reason": guard.reason,
        "windows_wsl_bridge_state_path": _relative_display_path(guard.state_path),
        "windows_wsl_bridge_current_wsl_ip": guard.current_wsl_ip,
        "windows_wsl_bridge_state_wsl_ip": guard.state_wsl_ip,
        "windows_wsl_bridge_expected_ports": _format_ints(guard.expected_ports),
        "windows_wsl_bridge_mapped_ports": _format_ints(guard.mapped_ports),
        "windows_wsl_bridge_missing_ports": _format_ints(guard.missing_ports),
    }


def _windows_wsl_bridge_suggested_commands(reason: str) -> tuple[str, ...]:
    if reason in {"wsl_ip_changed", "state_stale_by_age"}:
        return (
            'powershell.exe -NoProfile -Command "Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge"',
            "powershell.exe -ExecutionPolicy Bypass -File tools/windows/tws-wsl-bridge.ps1 -Action install",
        )
    return (
        "powershell.exe -ExecutionPolicy Bypass -File tools/windows/tws-wsl-bridge.ps1 -Action install",
    )


def _print_windows_wsl_bridge_failure(
    guard: WindowsWslBridgeGuardResult,
    evidence_dir: Path,
) -> None:
    print("[FAIL] Windows <-> WSL bridge is not prepared.", file=sys.stderr)
    print(f"Reason: {guard.reason}", file=sys.stderr)
    print(f"State file: {_relative_display_path(guard.state_path)}", file=sys.stderr)
    if guard.current_wsl_ip or guard.state_wsl_ip:
        print(f"Current WSL IP: {guard.current_wsl_ip or 'unknown'}", file=sys.stderr)
        print(f"State WSL IP: {guard.state_wsl_ip or 'unknown'}", file=sys.stderr)
    if guard.missing_ports:
        print(f"Missing bridge ports: {_format_ints(guard.missing_ports)}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Run PowerShell as Administrator:", file=sys.stderr)
    print("  tools/windows/tws-wsl-bridge.ps1 -Action install", file=sys.stderr)
    if guard.reason in {"wsl_ip_changed", "state_stale_by_age"}:
        print("", file=sys.stderr)
        print("Or refresh the existing scheduled task:", file=sys.stderr)
        print("  Start-ScheduledTask -TaskName TinySwarmWorld-WslBridge", file=sys.stderr)
    print("", file=sys.stderr)
    print("To run WSL2 without Windows localhost exposure, set:", file=sys.stderr)
    print("  TSW_WINDOWS_EXPOSURE=disabled", file=sys.stderr)
    print(f"Evidence directory: {evidence_dir.as_posix()}", file=sys.stderr)


def _relative_display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _format_ints(values: Sequence[int]) -> str:
    return ",".join(str(value) for value in values)


def _print_install_plan(cwd: Path, options: InstallerOptions, evidence_dir: Path, secret_env_file: Path) -> None:
    print(
        "\n".join(
            (
                "Tiny Swarm World live installation",
                "",
                f"Repository:      {cwd.as_posix()}",
                f"Service profile: {options.service_profile}",
                f"Secrets mode:    {options.secrets_mode}",
                f"Evidence:        {evidence_dir.as_posix()}",
                f"Secret file:     {secret_env_file.as_posix()}",
                "",
                "This will run live infrastructure automation. It may create or change VMs,",
                "Docker resources, local service state, networks, and deployment artifacts.",
                "Fresh install starts by resetting configured Tiny Swarm World managed state.",
            )
        )
    )


def _print_missing_secrets(missing: Sequence[str]) -> None:
    print("Missing required secrets:", file=sys.stderr)
    for name in missing:
        print(f"  {name}", file=sys.stderr)


def _print_tail(path: Path, title: str) -> None:
    print(f"\n{title}:", file=sys.stderr)
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
    for line in lines:
        print(line, file=sys.stderr)


def _print_reset_failure_guidance(path: Path) -> None:
    if not path.exists():
        return
    lines = _reset_failure_guidance_lines(
        path.read_text(encoding="utf-8", errors="replace")
    )
    if not lines:
        return
    print(file=sys.stderr)
    for line in lines:
        print(line, file=sys.stderr)


def _reset_failure_guidance_lines(log_text: str) -> tuple[str, ...]:
    if not _reset_log_mentions(
        log_text,
        "managed_nodes_reset_blocked",
        "unsafe_instance_config",
        "first_failure_unsafe_instance_settings: security.privileged",
    ):
        return ()
    return (
        "Reset recovery hint:",
        "  Existing configured LXC nodes are blocked by security.privileged.",
        "  Inspect instance and profile state from the same WSL/Linux shell:",
        "    for node in swarm-manager swarm-worker-1 swarm-worker-2; do",
        "      incus config get \"$node\" security.privileged",
        "    done",
        "    incus profile get docker-swarm security.privileged",
        "  If these are disposable Tiny Swarm World nodes, unset only the",
        "  setting that reports true, then rerun install.sh.",
        "  Details: documentation/user-handbook.adoc#_troubleshooting_checklist",
    )


def _reset_log_mentions(log_text: str, *needles: str) -> bool:
    return all(needle in log_text for needle in needles)


def _print_setup_failure_guidance(path: Path) -> None:
    if not path.exists():
        return
    lines = _setup_failure_guidance_lines(
        path.read_text(encoding="utf-8", errors="replace")
    )
    if not lines:
        return
    print(file=sys.stderr)
    for line in lines:
        print(line, file=sys.stderr)


def _setup_failure_guidance_lines(log_text: str) -> tuple[str, ...]:
    if "apt_repository_unreachable" not in log_text:
        return ()
    return (
        "Setup recovery hint:",
        "  Docker Engine installation inside the LXC nodes cannot reach APT repositories.",
        "  Run the read-only network diagnosis first:",
        "    ./tsw doctor network",
        "  If the diagnosis reports Docker blocking incusbr0 forwarding, apply only",
        "  the targeted forwarding repair:",
        "    ./tsw network repair --linux-forwarding --apply",
        "  If DNS or HTTP egress is blocked for another reason, fix that domain before",
        "  rerunning install.sh. The installer does not change iptables, Incus runtime",
        "  files, WSL mode, Windows portproxy, or Windows Firewall automatically.",
    )


def _append_exports(path: Path, label: str, values: Mapping[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(f"\n# {label}\n")
        for key, value in values.items():
            file.write(f"export {key}={shlex.quote(value)}\n")
    path.chmod(0o600)


def _write_exports(path: Path, label: str, values: Mapping[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        file.write(f"# {label}\n")
        for key, value in values.items():
            file.write(f"export {key}={shlex.quote(value)}\n")
    path.chmod(0o600)


def _ensure_private_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    path.chmod(0o600)


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _run_text(command: tuple[str, ...], *, cwd: Path | None = None) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    ).stdout.strip()


def _inside_git_worktree(cwd: Path) -> bool:
    return subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0


def _git_check_ignore(cwd: Path, path: str) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path], cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    raise SystemExit(main())

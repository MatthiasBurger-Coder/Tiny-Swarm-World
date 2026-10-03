"""Evidence responsibilities for the live installation boundary."""

from __future__ import annotations
from tiny_swarm_world.infrastructure.process.runner import run_process
import json
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from tiny_swarm_world.domain.configuration.credential_resolution import (
    CredentialResolutionError,
)
from tiny_swarm_world.application.services.credential_resolution import (
    CREDENTIAL_SOURCE_MAP_ENVIRONMENT,
    decode_source_metadata,
)
from tiny_swarm_world.application.ports.installation import (
    DEFAULT_INSTALLER_PROBE_TIMEOUT_SECONDS,
    HostRuntime,
    WindowsWslBridgeGuardResult,
    _EvidenceProbeSnapshot,
    _GitProbeResult,
    _InstallRunContext,
)


def _installation_evidence_directory(
    env: Mapping[str, str],
    *,
    cwd: Path,
    host_runtime: HostRuntime,
    run_id: str,
) -> Path:
    """Create installer evidence on the protected runtime filesystem."""
    configured_root = env.get("TSW_LIVE_EVIDENCE_ROOT", "").strip()
    if configured_root:
        root = Path(configured_root).expanduser()
    else:
        configured_state = env.get("XDG_STATE_HOME", "").strip()
        state_root = (
            Path(configured_state).expanduser()
            if configured_state
            else Path.home() / ".local" / "state"
        )
        root = state_root / "tiny-swarm-world" / "evidence" / "installation-tests"
    if not root.is_absolute():
        root = cwd / root

    # The source checkout may stay on /mnt/*, but mutable installer evidence
    # must live on the verified Linux-native filesystem. Setup preflight
    # validates the same configured root before platform mutation begins.
    from tools.live.secure_runtime_paths import ensure_secure_directory

    ensure_secure_directory(root)
    host_root = root / host_runtime.name
    ensure_secure_directory(host_root)
    evidence_dir = host_root / run_id
    evidence_dir.mkdir()
    evidence_dir.chmod(0o700)
    return evidence_dir


def _write_context(
    evidence_dir: Path,
    *,
    context: _InstallRunContext,
) -> None:
    values = {
        "run_id": context.run_id,
        "started_utc": _utc_timestamp(),
        "repo": context.cwd.as_posix(),
        "git_branch": context.evidence_probes.git_branch,
        "git_head": context.evidence_probes.git_head,
        "service_profile": context.service_profile,
        "fresh_install_reset": "skipped" if context.native_reconcile else "required",
        "secret_env_file": context.secret_env_file.as_posix(),
        "checked_secret_keys": ",".join(context.checked_secret_keys),
        "credential_sources": _safe_credential_source_metadata(context.env),
        "host_runtime_type": context.host_runtime.name,
        "host_runtime_detection_source": context.host_runtime.detection_source,
        "selected_evidence_directory": evidence_dir.as_posix(),
        "live_execution_mode": context.live_execution_mode,
        "live_approval_source": context.live_approval_source,
        "terminal_recording_mode": context.terminal_recording_mode,
        "platform_system": context.evidence_probes.platform_system,
        "kernel_release": context.evidence_probes.kernel_release,
        "proc_osrelease": context.evidence_probes.proc_osrelease,
        "wsl_distro_name_present": "yes"
        if context.env.get("WSL_DISTRO_NAME")
        else "no",
        "wsl_interop_present": "yes" if context.env.get("WSL_INTEROP") else "no",
    }
    _append_context(evidence_dir, values, replace=True)


def _safe_credential_source_metadata(env: Mapping[str, str]) -> str:
    """Serialize only source labels for operator-readable run context."""
    try:
        sources = decode_source_metadata(env.get(CREDENTIAL_SOURCE_MAP_ENVIRONMENT))
    except CredentialResolutionError:
        return "invalid"
    return json.dumps(
        {key: source.value for key, source in sorted(sources.items())},
        separators=(",", ":"),
        sort_keys=True,
    )


def _append_context(
    evidence_dir: Path, values: Mapping[str, str], *, replace: bool = False
) -> None:
    mode = "w" if replace else "a"
    with (evidence_dir / "context.txt").open(mode, encoding="utf-8") as context:
        for key, value in values.items():
            context.write(f"{key}={value}\n")


def _collect_evidence_probe_snapshot(
    cwd: Path,
    git_probe: _GitProbeResult,
) -> _EvidenceProbeSnapshot:
    from tiny_swarm_world.infrastructure.adapters.installation.process import (
        _run_optional_text,
    )

    git_branch, git_head = _git_revision_metadata(cwd, git_probe)
    system_metadata = _run_optional_text(("uname", "-srm"))
    if system_metadata == "unknown":
        platform_system = "unknown"
        kernel_release = "unknown"
    else:
        system_parts = system_metadata.split(maxsplit=2)
        platform_system = system_parts[0] if system_parts else "unknown"
        kernel_release = system_parts[1] if len(system_parts) > 1 else "unknown"
    proc_osrelease = _read_text(Path("/proc/sys/kernel/osrelease")).strip() or "unknown"
    return _EvidenceProbeSnapshot(
        git_branch=git_branch,
        git_head=git_head,
        platform_system=platform_system,
        kernel_release=kernel_release,
        proc_osrelease=proc_osrelease,
    )


def _git_revision_metadata(cwd: Path, git_probe: _GitProbeResult) -> tuple[str, str]:
    from tiny_swarm_world.infrastructure.adapters.installation.process import (
        _run_optional_text,
    )

    if not git_probe.inside_worktree:
        return "unknown", "unknown"
    metadata = _run_optional_text(
        ("git", "show", "-s", "--format=%D%x00%h", "HEAD"),
        cwd=cwd,
    )
    if metadata == "unknown":
        return "unknown", "unknown"
    decorations, separator, short_head = metadata.partition("\x00")
    if not separator:
        return "unknown", "unknown"
    branch = ""
    for decoration in decorations.split(","):
        candidate = decoration.strip()
        if candidate.startswith("HEAD -> "):
            branch = candidate.removeprefix("HEAD -> ")
            break
        if candidate.startswith("refs/heads/"):
            branch = candidate.removeprefix("refs/heads/")
    return branch, short_head or "unknown"


def _windows_wsl_bridge_context(
    guard: WindowsWslBridgeGuardResult,
) -> dict[str, str]:
    from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
        _format_ints,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
        _relative_display_path,
    )

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


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _probe_git_ignore(cwd: Path, path: str) -> _GitProbeResult:
    try:
        result = run_process(
            ["git", "check-ignore", "-q", "--", path],
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=DEFAULT_INSTALLER_PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return _GitProbeResult(False, False, "unknown")
    if result.returncode == 0:
        return _GitProbeResult(True, True, "ignored")
    if result.returncode == 1:
        return _GitProbeResult(True, False, "not_ignored")
    if result.returncode == 128:
        return _GitProbeResult(False, False, "outside_worktree")
    return _GitProbeResult(False, False, f"unknown_{result.returncode}")


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class InstallationEvidenceAdapter:
    def git_probe(self, cwd: Path, path: str) -> _GitProbeResult:
        return _probe_git_ignore(cwd, path)

    def directory(
        self,
        env: Mapping[str, str],
        *,
        cwd: Path,
        host_runtime: HostRuntime,
        run_id: str,
    ) -> Path:
        return _installation_evidence_directory(
            env, cwd=cwd, host_runtime=host_runtime, run_id=run_id
        )

    def probes(self, cwd: Path, git_probe: _GitProbeResult) -> _EvidenceProbeSnapshot:
        return _collect_evidence_probe_snapshot(cwd, git_probe)

    def write_context(self, evidence_dir: Path, *, context: _InstallRunContext) -> None:
        return _write_context(evidence_dir, context=context)

    def append(
        self, evidence_dir: Path, values: Mapping[str, str], *, replace: bool = False
    ) -> None:
        return _append_context(evidence_dir, values, replace=replace)

    def bridge_context(self, guard: WindowsWslBridgeGuardResult) -> dict[str, str]:
        return _windows_wsl_bridge_context(guard)

    def timestamp(self) -> str:
        return _utc_timestamp()

    def write(self, path: Path, value: str) -> None:
        return _write_text(path, value)

    def run_id(self) -> str:
        return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")

    def path(self, evidence_dir: Path, name: str) -> Path:
        return evidence_dir / name

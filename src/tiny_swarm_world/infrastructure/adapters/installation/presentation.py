"""Presentation responsibilities for the live installation boundary."""

from __future__ import annotations
import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO, cast
from tiny_swarm_world.application.ports.installation import (
    DEFAULT_SERVICE_PROFILE,
    InstallReporter,
    InstallerError,
    InstallerOptions,
    RESET_CONFIRMATION,
    WindowsWslBridgeGuardResult,
    _FallbackInstallEvent,
)


class _FallbackInstallReporter:
    def report(self, event: object) -> None:
        if not isinstance(event, _FallbackInstallEvent):
            return
        stream = sys.stderr if event.status == "FAILED" else sys.stdout
        for line in _render_fallback_install_event(event):
            print(line, file=stream)


def parse_args(argv: Sequence[str] | None = None) -> InstallerOptions:
    parser = argparse.ArgumentParser(
        description="Tiny Swarm World live installation wrapper."
    )
    parser.add_argument(
        "--service-profile",
        default=os.environ.get("SERVICE_PROFILE", DEFAULT_SERVICE_PROFILE),
        choices=("default", "service-access"),
        help="Service profile passed to setup run.",
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
    parser.add_argument(
        "--allow-wsl-windows-filesystem",
        action="store_true",
        help=(
            "Allow a confirmed Windows-mounted WSL2 repository and record the "
            "applied override in protected local evidence."
        ),
    )
    args = parser.parse_args(argv)
    return InstallerOptions(
        service_profile=args.service_profile,
        confirm_reset=args.confirm_reset,
        native_reconcile=not args.confirm_reset,
        non_interactive_live_approval=args.non_interactive_live_approval,
        headless=args.headless or os.environ.get("TSW_INSTALL_HEADLESS") == "1",
        allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem,
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
        from tiny_swarm_world.domain.install import (
            InstallEvent,
            InstallEventType,
            InstallStatus,
        )

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
        from tiny_swarm_world.infrastructure.adapters.ui.install_reporter import (
            default_install_reporter,
        )

        return cast(InstallReporter, default_install_reporter())
    except ModuleNotFoundError:
        return _FallbackInstallReporter()


def _confirm_reset(options: InstallerOptions) -> None:
    if options.confirm_reset:
        print("Fresh-install reset confirmed by explicit --confirm-reset flag.")
        return
    print("Fresh install will reset configured Tiny Swarm World managed state.")
    try:
        answer = input(f"Type {RESET_CONFIRMATION} to continue: ")
    except EOFError:
        raise InstallerError(
            "Fresh-install reset confirmation was not provided."
        ) from None
    if answer != RESET_CONFIRMATION:
        raise InstallerError("Fresh-install reset confirmation did not match.")


def _live_approval(options: InstallerOptions) -> tuple[str, str, str]:
    if options.non_interactive_live_approval:
        return "non_interactive", "explicit_automation_flag", " --approve-live"
    return "interactive", "operator_prompt", ""


def _suggested_checks_for_phase(name: str, *, log_text: str = "") -> tuple[str, ...]:
    normalized = name.casefold()
    commands: list[str]
    if "setup" in normalized:
        if _has_setup_network_failure(log_text):
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
        lines = [
            "Tiny Swarm World Installer",
            f"  RUNNING {_safe_installer_line_value(event.message or event.step)}",
        ]
        return tuple(lines)
    if event.status == "STARTED":
        header = (
            f"[{event.sequence}/{event.total}] {event.step}"
            if event.sequence and event.total
            else event.step
        )
        lines = [
            header,
            f"  RUNNING {_safe_installer_line_value(event.message or event.target)}",
        ]
        return tuple(lines)
    if event.status == "SUCCEEDED":
        lines = [
            f"  OK      {_safe_installer_line_value(event.message or event.target)}"
        ]
        return tuple(lines)
    if event.status in {"FAILED", "TIMED_OUT", "INTERRUPTED"}:
        target = f" on {event.target}" if event.target else ""
        lines = [f"FAILED {event.step}{target}"]
        if event.reason:
            lines.extend(
                ("", "Reason:", f"  {_safe_installer_line_value(event.reason)}")
            )
        if event.evidence_path:
            lines.extend(("", "Evidence:", f"  {event.evidence_path.as_posix()}"))
        if event.suggested_commands:
            lines.extend(("", "Suggested checks:"))
            lines.extend(f"  {command}" for command in event.suggested_commands)
        return tuple(lines)
    lines = [
        f"  {event.status:<8}{_safe_installer_line_value(event.message or event.target)}"
    ]
    return tuple(lines)


def _safe_installer_line_value(value: str) -> str:
    text = " ".join(value.replace("\r", " ").replace("\n", " ").split())
    if text.startswith(("{", "[")) and text.endswith(("}", "]")):
        return "structured event details recorded in evidence"
    return text


def _windows_wsl_bridge_suggested_commands(reason: str) -> tuple[str, ...]:
    if reason in {"wsl_ip_changed", "state_stale_by_age", "agent_not_ready"}:
        return (
            'powershell.exe -NoProfile -Command "Restart-Service -Name TinySwarmWorldWslBridge"',
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
        print(
            f"Missing bridge ports: {_format_ints(guard.missing_ports)}",
            file=sys.stderr,
        )
    print("", file=sys.stderr)
    print("Run PowerShell as Administrator:", file=sys.stderr)
    print("  tools/windows/tws-wsl-bridge.ps1 -Action install", file=sys.stderr)
    if guard.reason in {"wsl_ip_changed", "state_stale_by_age", "agent_not_ready"}:
        print("", file=sys.stderr)
        print("Or restart the existing Windows bridge service:", file=sys.stderr)
        print("  Restart-Service -Name TinySwarmWorldWslBridge", file=sys.stderr)
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


def _print_install_plan(
    cwd: Path,
    options: InstallerOptions,
    evidence_dir: Path,
) -> None:
    print(
        "\n".join(
            (
                "Tiny Swarm World live installation",
                "",
                f"Repository:      {cwd.as_posix()}",
                f"Service profile: {options.service_profile}",
                f"Evidence:        {evidence_dir.as_posix()}",
                "Credentials:     deterministic catalog defaults plus explicit operator overrides",
                "",
                "This will run live infrastructure automation. It may create or change VMs,",
                "Docker resources, local service state, networks, and deployment artifacts.",
                (
                    "Linux/WSL installation reconciles managed state without a reset."
                    if options.native_reconcile
                    else "Fresh install starts by resetting configured Tiny Swarm World managed state."
                ),
            )
        )
    )


def _print_install_completion_summary(
    exit_code: int,
    evidence_dir: Path,
    *,
    stream: IO[str],
) -> None:
    if exit_code == 0:
        print("Installation completed successfully.", file=stream)
    else:
        print(f"Installation failed with exit code {exit_code}.", file=stream)
    print(f"Evidence directory: {evidence_dir.as_posix()}", file=stream)


def _print_tail(path: Path, title: str) -> None:
    print(f"\n{title}:", file=sys.stderr)
    if not path.exists():
        return
    print(f"Full log retained at: {path.as_posix()}", file=sys.stderr)
    for line in _safe_log_tail_lines(path):
        print(line, file=sys.stderr)


def _safe_log_tail_lines(path: Path) -> tuple[str, ...]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
    rendered: list[str] = []
    structured_depth = 0
    for line in lines:
        stripped = line.strip()
        if structured_depth:
            structured_depth += _structured_delimiter_delta(stripped)
            if structured_depth <= 0:
                structured_depth = 0
            continue
        if _starts_structured_log_value(stripped):
            rendered.append(
                "[structured log block omitted from console; full content is in the evidence log]"
            )
            structured_depth = max(0, _structured_delimiter_delta(stripped))
            continue
        rendered.append(line)
    return tuple(rendered)


def _starts_structured_log_value(value: str) -> bool:
    if value.startswith("{"):
        return True
    return value.startswith("[") and len(value) > 1 and value[1] in "\"'{0123456789-]"


def _structured_delimiter_delta(value: str) -> int:
    return value.count("{") + value.count("[") - value.count("}") - value.count("]")


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
        '      incus config get "$node" security.privileged',
        "    done",
        "    incus profile get docker-swarm security.privileged",
        "  If these are disposable Tiny Swarm World nodes, unset only the",
        "  setting that reports true, then rerun install.sh.",
        "  Details: documentation/user_guide/troubleshooting.adoc#first-response",
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


def _has_setup_network_failure(log_text: str) -> bool:
    return any(
        reason in log_text
        for reason in (
            "apt_repository_unreachable",
            "docker_apt_gpg_unreachable",
            "apt_dns_resolution_failed",
            "apt_no_route_to_host",
        )
    )


def _setup_failure_guidance_lines(log_text: str) -> tuple[str, ...]:
    if not _has_setup_network_failure(log_text):
        return ()
    return (
        "Setup recovery hint:",
        "  Docker Engine installation inside the LXC nodes cannot reach APT repositories or the Docker signing-key endpoint.",
        "  Run the read-only network diagnosis first:",
        "    ./tsw doctor network",
        "  If the diagnosis reports Docker blocking incusbr0 forwarding, apply only",
        "  the targeted forwarding repair:",
        "    ./tsw network repair --linux-forwarding --apply",
        "  If DNS or HTTP egress is blocked for another reason, fix that domain before",
        "  rerunning install.sh. The installer does not change iptables, Incus runtime",
        "  files, WSL mode, Windows portproxy, or Windows Firewall automatically.",
    )


class InstallationPresentationAdapter:
    def reporter(self) -> InstallReporter:
        return _default_install_reporter()

    def approval(self, options: InstallerOptions) -> tuple[str, str, str]:
        return _live_approval(options)

    def plan(self, cwd: Path, options: InstallerOptions, evidence_dir: Path) -> None:
        return _print_install_plan(cwd, options, evidence_dir)

    def event(
        self,
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
        return _phase_event(
            event_type,
            status,
            step,
            target=target,
            message=message,
            reason=reason,
            evidence_path=evidence_path,
            suggested_commands=suggested_commands,
            sequence=sequence,
            total=total,
        )

    def confirm_reset(self, options: InstallerOptions) -> None:
        return _confirm_reset(options)

    def bridge_commands(self, reason: str) -> tuple[str, ...]:
        return _windows_wsl_bridge_suggested_commands(reason)

    def bridge_failure(
        self, guard: WindowsWslBridgeGuardResult, evidence_dir: Path
    ) -> None:
        return _print_windows_wsl_bridge_failure(guard, evidence_dir)

    def tail(self, path: Path, title: str) -> None:
        return _print_tail(path, title)

    def reset_guidance(self, path: Path) -> None:
        return _print_reset_failure_guidance(path)

    def setup_guidance(self, path: Path) -> None:
        return _print_setup_failure_guidance(path)

    def message(self, message: str, *, failed: bool = False) -> None:
        print(message, file=sys.stderr if failed else sys.stdout)

    def completion(self, exit_code: int, evidence_dir: Path, *, failed: bool) -> None:
        _print_install_completion_summary(
            exit_code, evidence_dir, stream=sys.stderr if failed else sys.stdout
        )


def main(argv: Sequence[str] | None = None) -> int:
    from tiny_swarm_world.infrastructure.composition_installation import (
        build_installation_service,
    )

    try:
        options = parse_args(argv)
        if options.confirm_reset:
            print("DEPRECATED: --confirm-reset requests destructive WSL fresh-reset. Prefer a separately confirmed platform reset, then ./install.sh.", file=sys.stderr)
        return build_installation_service().run(
            options, env=os.environ, cwd=Path.cwd()
        )
    except InstallerError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

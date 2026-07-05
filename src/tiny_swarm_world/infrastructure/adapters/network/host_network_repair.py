from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from tiny_swarm_world.application.ports.network import (
    CommandObservation,
    NetworkRepairMutationResult,
)


CommandExecutor = Callable[[str, int], CommandObservation]

INCUS_DNSMASQ_PID = Path("/var/lib/incus/networks/incusbr0/dnsmasq.pid")
INCUS_NETWORK_DIR = Path("/var/lib/incus/networks/incusbr0")
FORWARDING_SCRIPT_PATH = Path("/usr/local/bin/tsw-apply-incus-forwarding.sh")
FORWARDING_SERVICE_PATH = Path("/etc/systemd/system/tsw-incus-forwarding.service")


class SubprocessNetworkRepair:
    def __init__(self, executor: CommandExecutor | None = None) -> None:
        self.executor = executor or _run_shell_command

    async def apply_wsl2_nat_runtime(self) -> NetworkRepairMutationResult:
        profile = self.executor(
            "powershell.exe -NoProfile -Command \"[Environment]::GetFolderPath('UserProfile')\"",
            10,
        )
        if not profile.ok or not profile.stdout.strip():
            return NetworkRepairMutationResult(
                target="runtime",
                applied=False,
                success=False,
                message="Could not determine the Windows user profile path.",
                commands=(profile,),
            )
        wsl_path = self.executor(f"wslpath -u {shlex.quote(profile.stdout.strip())}", 10)
        if not wsl_path.ok or not wsl_path.stdout.strip():
            return NetworkRepairMutationResult(
                target="runtime",
                applied=False,
                success=False,
                message="Could not map the Windows user profile path into WSL.",
                commands=(profile, wsl_path),
            )

        windows_profile = profile.stdout.strip()
        config_path = Path(wsl_path.stdout.strip()) / ".wslconfig"
        backup_path: Path | None = None
        if config_path.exists():
            timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            backup_path = config_path.with_name(f".wslconfig.bak-{timestamp}")
            backup_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
            original = config_path.read_text(encoding="utf-8")
        else:
            original = ""
        config_path.write_text(_set_wsl_networking_mode(original, "nat"), encoding="utf-8")

        details = []
        if backup_path is not None:
            details.append(
                "Backed up "
                f"{windows_profile}\\.wslconfig to {windows_profile}\\{backup_path.name}"
            )
        else:
            details.append(f"Created {windows_profile}\\.wslconfig")
        details.extend(
            (
                "Set networkingMode=nat",
                "Please run:",
                "  wsl --shutdown",
                "Then restart the installer.",
            )
        )
        return NetworkRepairMutationResult(
            target="runtime",
            applied=True,
            success=True,
            message="Configured WSL networkingMode=nat.",
            details=tuple(details),
            commands=(profile, wsl_path),
        )

    async def apply_incus_repair(self) -> NetworkRepairMutationResult:
        commands: list[CommandObservation] = []
        details: list[str] = []

        path_check = self.executor(f"test -e {shlex.quote(INCUS_DNSMASQ_PID.as_posix())}", 5)
        commands.append(path_check)
        if path_check.ok:
            realpath = self.executor(f"realpath -m -- {shlex.quote(INCUS_DNSMASQ_PID.as_posix())}", 5)
            pid_read = self.executor(f"cat {shlex.quote(INCUS_DNSMASQ_PID.as_posix())}", 5)
            dnsmasq_running = self.executor("pgrep -x dnsmasq >/dev/null", 5)
            commands.extend((realpath, pid_read, dnsmasq_running))
            safe_path = _inside_incus_network_dir(realpath.stdout.strip())
            pid = pid_read.stdout.strip()
            pid_running = self.executor(f"ps -p {shlex.quote(pid)} -o pid= >/dev/null", 5) if pid else _failed_command("missing pid")
            commands.append(pid_running)
            if not safe_path:
                return _repair_blocked(
                    "incus",
                    "Refused to remove an Incus runtime file outside the incusbr0 directory.",
                    commands,
                )
            if dnsmasq_running.ok:
                return _repair_blocked(
                    "incus",
                    "Refused to remove dnsmasq.pid because a dnsmasq process is running.",
                    commands,
                )
            if pid_running.ok:
                return _repair_blocked(
                    "incus",
                    "Refused to remove dnsmasq.pid because its referenced process is running.",
                    commands,
                )
            details.extend(
                (
                    "About to remove stale Incus runtime file:",
                    f"  {INCUS_DNSMASQ_PID.as_posix()}",
                    "Reason:",
                    "  referenced process is not running",
                )
            )
            remove = self.executor(_sudo_command(f"rm -f -- {shlex.quote(INCUS_DNSMASQ_PID.as_posix())}"), 10)
            commands.append(remove)
            if not remove.ok:
                return _repair_failed("incus", "Failed to remove stale Incus runtime file.", commands, details)
        else:
            details.append("No stale Incus dnsmasq.pid file was present.")

        restart = self.executor(_sudo_command("systemctl restart incus"), 60)
        network_list = self.executor("incus network list", 15)
        network_info = self.executor("incus network info incusbr0", 15)
        commands.extend((restart, network_list, network_info))
        success = restart.ok and network_list.ok and network_info.ok
        return NetworkRepairMutationResult(
            target="incus",
            applied=True,
            success=success,
            message="Incus repair completed." if success else "Incus repair did not verify cleanly.",
            details=tuple(details),
            commands=tuple(commands),
        )

    async def apply_linux_forwarding(self, bridge: str, node_name: str) -> NetworkRepairMutationResult:
        commands: list[CommandObservation] = []
        details = [
            f"Installing {FORWARDING_SCRIPT_PATH.as_posix()}",
            f"Installing {FORWARDING_SERVICE_PATH.as_posix()}",
        ]
        with tempfile.TemporaryDirectory(prefix="tsw-network-repair-") as temporary_directory:
            temp_root = Path(temporary_directory)
            script_file = temp_root / FORWARDING_SCRIPT_PATH.name
            service_file = temp_root / FORWARDING_SERVICE_PATH.name
            script_file.write_text(_forwarding_script(), encoding="utf-8")
            service_file.write_text(_forwarding_service(), encoding="utf-8")

            install_script = self.executor(
                _sudo_command(
                    "install -m 0755 "
                    f"{shlex.quote(script_file.as_posix())} "
                    f"{shlex.quote(FORWARDING_SCRIPT_PATH.as_posix())}"
                ),
                10,
            )
            install_service = self.executor(
                _sudo_command(
                    "install -m 0644 "
                    f"{shlex.quote(service_file.as_posix())} "
                    f"{shlex.quote(FORWARDING_SERVICE_PATH.as_posix())}"
                ),
                10,
            )
            commands.extend((install_script, install_service))
            if not install_script.ok or not install_service.ok:
                return _repair_failed(
                    "linux-forwarding",
                    "Failed to install forwarding persistence files.",
                    commands,
                    details,
                )

        apply_rules = self.executor(
            _sudo_command(
                f"{shlex.quote(FORWARDING_SCRIPT_PATH.as_posix())} {shlex.quote(bridge)}"
            ),
            10,
        )
        daemon_reload = self.executor(_sudo_command("systemctl daemon-reload"), 20)
        enable_service = self.executor(
            _sudo_command("systemctl enable --now tsw-incus-forwarding.service"),
            30,
        )
        verify = self.executor(
            f"incus exec {shlex.quote(node_name)} -- "
            "curl -4 -I --connect-timeout 8 http://archive.ubuntu.com",
            12,
        )
        commands.extend((apply_rules, daemon_reload, enable_service, verify))
        success = all(command.ok for command in commands)
        details.extend(
            (
                f"Bridge: {bridge}",
                "Applied idempotent incusbr0 FORWARD rules.",
                f"Verified LXC HTTP egress on {node_name}."
                if verify.ok
                else f"LXC HTTP egress verification failed on {node_name}.",
            )
        )
        return NetworkRepairMutationResult(
            target="linux-forwarding",
            applied=True,
            success=success,
            message=(
                "Persistent Incus forwarding rules were applied."
                if success
                else "Persistent Incus forwarding repair did not verify cleanly."
            ),
            details=tuple(details),
            commands=tuple(commands),
        )


def _run_shell_command(command: str, timeout: int) -> CommandObservation:
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _decoded_timeout_output(exc.stdout)
        stderr = _decoded_timeout_output(exc.stderr)
        return CommandObservation(
            command=command,
            return_code=124,
            stdout=stdout,
            stderr=stderr or f"Command timed out after {timeout} seconds.",
            timed_out=True,
        )
    except OSError as exc:
        return CommandObservation(command=command, return_code=127, stderr=str(exc))
    return CommandObservation(
        command=command,
        return_code=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def _set_wsl_networking_mode(content: str, mode: str) -> str:
    lines = content.splitlines()
    output: list[str] = []
    in_wsl2 = False
    saw_wsl2 = False
    wrote_mode = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_wsl2 and not wrote_mode:
                output.append(f"networkingMode={mode}")
                wrote_mode = True
            in_wsl2 = stripped.casefold() == "[wsl2]"
            saw_wsl2 = saw_wsl2 or in_wsl2
            output.append(line)
            continue
        if in_wsl2 and stripped.casefold().startswith("networkingmode"):
            output.append(f"networkingMode={mode}")
            wrote_mode = True
            continue
        output.append(line)

    if in_wsl2 and not wrote_mode:
        output.append(f"networkingMode={mode}")
    if not saw_wsl2:
        if output and output[-1].strip():
            output.append("")
        output.extend(("[wsl2]", f"networkingMode={mode}"))
    return "\n".join(output).rstrip() + "\n"


def _forwarding_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

BRIDGE="${1:-incusbr0}"

iptables -C FORWARD -i "$BRIDGE" -j ACCEPT 2>/dev/null || \\
  iptables -I FORWARD 1 -i "$BRIDGE" -j ACCEPT

iptables -C FORWARD -o "$BRIDGE" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \\
  iptables -I FORWARD 1 -o "$BRIDGE" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
"""


def _forwarding_service() -> str:
    return """[Unit]
Description=Tiny-Swarm-World Incus forwarding rules
After=network-online.target docker.service incus.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/tsw-apply-incus-forwarding.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""


def _sudo_command(command: str) -> str:
    if os.geteuid() == 0:
        return command
    return f"sudo {command}"


def _inside_incus_network_dir(path: str) -> bool:
    if not path:
        return False
    candidate = Path(path)
    return candidate == INCUS_DNSMASQ_PID and candidate.parent == INCUS_NETWORK_DIR


def _repair_blocked(
    target: str,
    message: str,
    commands: list[CommandObservation],
) -> NetworkRepairMutationResult:
    return NetworkRepairMutationResult(
        target=target,
        applied=False,
        success=False,
        message=message,
        commands=tuple(commands),
    )


def _repair_failed(
    target: str,
    message: str,
    commands: list[CommandObservation],
    details: list[str],
) -> NetworkRepairMutationResult:
    return NetworkRepairMutationResult(
        target=target,
        applied=True,
        success=False,
        message=message,
        details=tuple(details),
        commands=tuple(commands),
    )


def _failed_command(reason: str) -> CommandObservation:
    return CommandObservation(command="not-run", return_code=1, stderr=reason)


def _decoded_timeout_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return value.strip()

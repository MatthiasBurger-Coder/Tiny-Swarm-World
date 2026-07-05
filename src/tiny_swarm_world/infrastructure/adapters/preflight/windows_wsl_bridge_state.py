from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from tiny_swarm_world.domain.preflight import WindowsWslBridgeStatus


WINDOWS_WSL_BRIDGE_STATE = Path("tools/windows/.tws-wsl-bridge.state.json")
DEFAULT_WINDOWS_WSL_BRIDGE_STATE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def windows_wsl_bridge_status(
    root: Path,
    expected_ports: Sequence[int],
    *,
    state_path: Path = WINDOWS_WSL_BRIDGE_STATE,
    max_age_seconds: int = DEFAULT_WINDOWS_WSL_BRIDGE_STATE_MAX_AGE_SECONDS,
    current_wsl_ipv4: Callable[[], str] = lambda: _current_wsl_ipv4(),
) -> WindowsWslBridgeStatus:
    absolute_state_path = root / state_path
    relative_state_path = state_path.as_posix()
    expected = tuple(int(port) for port in expected_ports)
    if not absolute_state_path.exists():
        return WindowsWslBridgeStatus(
            prepared=False,
            reason="state_missing",
            state_path=relative_state_path,
            expected_ports=expected,
            missing_ports=expected,
        )

    try:
        raw_state = json.loads(absolute_state_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return WindowsWslBridgeStatus(
            prepared=False,
            reason="state_invalid",
            state_path=relative_state_path,
            expected_ports=expected,
            missing_ports=expected,
        )
    if not isinstance(raw_state, Mapping):
        return WindowsWslBridgeStatus(
            prepared=False,
            reason="state_invalid",
            state_path=relative_state_path,
            expected_ports=expected,
            missing_ports=expected,
        )

    mapped_ports = _mapped_ports_from_bridge_state(raw_state)
    missing_ports = tuple(sorted(set(expected) - set(mapped_ports)))
    generated_at = str(raw_state.get("generatedAt", ""))
    listen_address = str(raw_state.get("listenAddress", ""))
    state_wsl_ip = str(raw_state.get("wslIp", ""))
    current_wsl_ip = current_wsl_ipv4()
    state_age_seconds = _state_age_seconds(generated_at)

    def bridge_status(prepared: bool, reason: str) -> WindowsWslBridgeStatus:
        return WindowsWslBridgeStatus(
            prepared=prepared,
            reason=reason,
            state_path=relative_state_path,
            current_wsl_ip=current_wsl_ip,
            state_wsl_ip=state_wsl_ip,
            generated_at=generated_at,
            listen_address=listen_address,
            expected_ports=expected,
            mapped_ports=mapped_ports,
            missing_ports=missing_ports,
            state_age_seconds=state_age_seconds,
        )

    if not generated_at:
        return bridge_status(False, "generated_at_missing")
    if state_age_seconds is None:
        return bridge_status(False, "generated_at_invalid")
    if state_age_seconds > max_age_seconds:
        return bridge_status(False, "state_stale_by_age")
    if not current_wsl_ip:
        return bridge_status(False, "wsl_ip_unavailable")
    if state_wsl_ip != current_wsl_ip:
        return bridge_status(False, "wsl_ip_changed")
    if missing_ports:
        return bridge_status(False, "missing_ports")
    return bridge_status(True, "prepared")


def current_wsl_ipv4() -> str:
    return _current_wsl_ipv4()


def _mapped_ports_from_bridge_state(state: Mapping[object, object]) -> tuple[int, ...]:
    mappings = state.get("mappings", ())
    if not isinstance(mappings, Sequence) or isinstance(mappings, str):
        return ()
    ports: set[int] = set()
    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            continue
        try:
            ports.add(int(mapping.get("listenPort", 0)))
        except (TypeError, ValueError):
            continue
    return tuple(sorted(port for port in ports if port > 0))


def _state_age_seconds(generated_at: str) -> int | None:
    generated = _parse_bridge_timestamp(generated_at)
    if generated is None:
        return None
    now = datetime.now(UTC)
    return max(0, int((now - generated).total_seconds()))


def _parse_bridge_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    normalized = re.sub(r"(\.\d{6})\d+([+-]\d{2}:\d{2})$", r"\1\2", normalized)
    normalized = re.sub(r"(\.\d{6})\d+$", r"\1", normalized)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _current_wsl_ipv4() -> str:
    try:
        completed = subprocess.run(
            ["hostname", "-I"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    for part in completed.stdout.split():
        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", part):
            return part
    return ""

"""Shared local-service addressing helpers for LXC service adapters."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.diagnostics import (
    is_transient_manager_shell_failure,
)


_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
_MAX_ATTEMPTS = 3
_RETRY_DELAYS_SECONDS = (0.5, 1.0)


def validate_local_http_scheme(scheme: str) -> str:
    normalized = scheme.strip().lower()
    if normalized not in {"http", "https"}:
        raise ValueError("Local service URL scheme must be 'http' or 'https'.")
    return normalized


def local_service_url(scheme: str, host: str, port: int) -> str:
    return f"{scheme}://{host}:{port}"


def lxc_manager_ip(
    backend: ManagedLxcBackend,
    manager_node: str,
    timeout_seconds: int,
    *,
    run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> str:
    runner = run or subprocess.run
    sleeper = sleep or time.sleep
    result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            result = runner(
                [
                    _BACKEND_CLI[backend],
                    "exec",
                    manager_node,
                    "--",
                    "sh",
                    "-lc",
                    "ip -4 -o addr show dev eth0 | awk '{print $4}' | cut -d/ -f1",
                ],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LXC manager IP lookup timed out.") from exc
        if not is_transient_manager_shell_failure(result):
            break
        if attempt >= _MAX_ATTEMPTS:
            break
        sleeper(_RETRY_DELAYS_SECONDS[min(attempt - 1, len(_RETRY_DELAYS_SECONDS) - 1)])
    if result is None:
        raise RuntimeError("LXC manager IP lookup did not execute.")
    if result.returncode != 0:
        raise RuntimeError("LXC manager IP lookup failed.")
    addresses = [part for part in result.stdout.split() if "." in part]
    if not addresses:
        raise RuntimeError("LXC manager IP lookup returned no IPv4 address.")
    return addresses[0]

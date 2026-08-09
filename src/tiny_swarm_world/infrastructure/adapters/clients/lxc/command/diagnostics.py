"""Shared diagnostics for LXC command adapters."""

from __future__ import annotations

import re
import subprocess


_INCUS_CHILD_PID_FAILURE = "Failed to retrieve PID of executing child process"
_SENSITIVE_LOG_ASSIGNMENT_PATTERN = re.compile(
    r"\b([A-Za-z0-9_]*(?:PASSWORD|TOKEN|SECRET|KEY)[A-Za-z0-9_]*)="
    r"(?:'[^']*'|\"[^\"]*\"|\S+)",
    re.IGNORECASE,
)
_SENSITIVE_BEARER_PATTERN = re.compile(
    r"(authorization:\s*bearer\s+)\S+",
    re.IGNORECASE,
)
_SENSITIVE_TOKEN_PARAMETER_PATTERN = re.compile(
    r"\b(token:)[^\s'\"]+",
    re.IGNORECASE,
)


def is_transient_manager_shell_failure(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether an LXC shell result is safe to retry."""

    return result.returncode == 255 and _INCUS_CHILD_PID_FAILURE in result.stderr


def safe_log_text(value: str, limit: int = 500) -> str:
    """Collapse, redact, and bound command output before it reaches logs."""

    collapsed = " ".join(value.split())
    collapsed = _SENSITIVE_LOG_ASSIGNMENT_PATTERN.sub(r"\1=***", collapsed)
    collapsed = _SENSITIVE_BEARER_PATTERN.sub(r"\1***", collapsed)
    collapsed = _SENSITIVE_TOKEN_PARAMETER_PATTERN.sub(r"\1***", collapsed)
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}..."


def command_failed(result: object) -> bool:
    """Return whether a command result represents a timeout or failure."""

    return bool(getattr(result, "timed_out", False)) or getattr(result, "returncode", 0) != 0


# Compatibility aliases for adapters that still use the old private names.
_is_transient_manager_shell_failure = is_transient_manager_shell_failure
_safe_log_text = safe_log_text

from __future__ import annotations

import re
import shlex


RAW_EVIDENCE_KEYS = frozenset(
    {
        "args",
        "authorization",
        "command",
        "command_line",
        "env",
        "environment",
        "output",
        "raw_command",
        "raw_stderr",
        "raw_stdout",
        "response",
        "response_body",
        "stderr",
        "stdout",
    }
)
SENSITIVE_EVIDENCE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "auth",
    "credential",
    "key",
    "password",
    "secret",
    "token",
)
COMMAND_EXECUTABLES = frozenset(
    {
        "curl",
        "docker",
        "docker-compose",
        "multipass",
        "netplan",
        "python",
        "python3",
        "socat",
    }
)
COMMAND_VERBS = frozenset(
    {
        "alias",
        "apply",
        "build",
        "buildx",
        "compose",
        "config",
        "container",
        "context",
        "cp",
        "create",
        "delete",
        "events",
        "exec",
        "generate",
        "image",
        "images",
        "info",
        "inspect",
        "launch",
        "load",
        "login",
        "logs",
        "ls",
        "network",
        "networks",
        "node",
        "ps",
        "pull",
        "purge",
        "push",
        "restart",
        "rm",
        "rmi",
        "run",
        "save",
        "secret",
        "service",
        "stack",
        "start",
        "stop",
        "swarm",
        "system",
        "transfer",
        "try",
        "up",
        "update",
        "version",
        "volume",
    }
)
URL_USERINFO_PATTERN = re.compile(r"://[^/\s@]+@")
SENSITIVE_LABEL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[\"']?([A-Za-z][A-Za-z0-9_-]{1,120})[\"']?\s*[:=]"
)
SENSITIVE_ASSIGNMENT_TERMS = frozenset(
    {"auth", "authorization", "credential", "key", "password", "secret", "token"}
)
TARGET_ID_PATTERN = re.compile(r"^(?:[a-z0-9][a-z0-9:._-]*|_[A-Za-z][A-Za-z0-9_]*)$")
RAW_EVIDENCE_VALUE_PATTERNS = (
    re.compile(r"[\r\n]"),
    re.compile(r"\b(stdout|stderr)\b", re.IGNORECASE),
    re.compile(
        r"\b(multipass|docker|sudo|netplan|socat)\s+"
        r"(exec|info|inspect|logs|ps|swarm|system|volume|stack|run|compose|login|pull|push|network|"
        r"service|node|secret|config|cp|ssh|launch|delete|purge|restart|list|"
        r"transfer|set|install|update|apply|version|images|container|context|events)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bpython3?\s+[\w./-]+\.py\b", re.IGNORECASE),
    re.compile(r"\b(?:bash|sh)\s+[\w./-]+", re.IGNORECASE),
    re.compile(r"\bcurl\s+https?://", re.IGNORECASE),
    re.compile(r"\bsocat\s+(tcp|udp|unix|stdio|exec|fork|open|pty|file|system|pipe)", re.IGNORECASE),
    re.compile(
        r"(^|[^A-Za-z0-9])(bearer|authorization|api[_-]?key|credential|token|password|secret)([^A-Za-z0-9]|$)",
        re.IGNORECASE,
    ),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
)
RAW_MESSAGE_VALUE_PATTERNS = (
    re.compile(r"[\r\n]"),
    re.compile(r"\b(stdout|stderr)\b", re.IGNORECASE),
    re.compile(
        r"\b(multipass|docker|sudo|netplan|socat)\s+"
        r"(exec|info|inspect|logs|ps|swarm|system|volume|stack|run|compose|login|pull|push|network|"
        r"service|node|secret|config|cp|ssh|launch|delete|purge|restart|list|"
        r"transfer|set|install|update|apply|version|images|container|context|events)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bpython3?\s+[\w./-]+\.py\b", re.IGNORECASE),
    re.compile(r"\b(?:bash|sh)\s+[\w./-]+", re.IGNORECASE),
    re.compile(r"\bcurl\s+https?://", re.IGNORECASE),
    re.compile(r"\bsocat\s+(tcp|udp|unix|stdio|exec|fork|open|pty|file|system|pipe)", re.IGNORECASE),
    re.compile(
        r"(^|[^A-Za-z0-9])(bearer|authorization|api[_-]?key|credential|token|password|secret)([^A-Za-z0-9]|$)",
        re.IGNORECASE,
    ),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
)


def validate_evidence_key(key: str) -> None:
    normalized_key = str(key).strip().lower()
    if not normalized_key:
        raise ValueError("verification evidence keys must not be empty")
    if normalized_key in RAW_EVIDENCE_KEYS:
        raise ValueError(f"raw verification evidence key is not allowed: {key}")
    if any(fragment in normalized_key for fragment in SENSITIVE_EVIDENCE_KEY_FRAGMENTS):
        raise ValueError(f"sensitive verification evidence key is not allowed: {key}")


def validate_evidence_value(key: str, value: str) -> None:
    validate_summary_text(key, value, RAW_EVIDENCE_VALUE_PATTERNS)


def validate_message_text(key: str, value: str) -> None:
    validate_summary_text(key, value, RAW_MESSAGE_VALUE_PATTERNS)


def validate_target_id(value: str) -> None:
    if not value:
        raise ValueError("verification target_id must not be empty")
    if not TARGET_ID_PATTERN.fullmatch(value):
        raise ValueError("verification target_id contains invalid characters")
    validate_summary_text("target_id", value, RAW_EVIDENCE_VALUE_PATTERNS)


def validate_observed_inventory_text(key: str, value: str) -> str:
    text = str(value)
    validate_summary_text(key, text, RAW_EVIDENCE_VALUE_PATTERNS)
    return text


def validate_summary_text(
    key: str,
    value: str,
    raw_value_patterns: tuple[re.Pattern[str], ...],
) -> None:
    if (
        any(pattern.search(value) for pattern in raw_value_patterns)
        or URL_USERINFO_PATTERN.search(value)
        or _contains_sensitive_assignment(value)
        or _contains_command_snippet(value)
    ):
        raise ValueError(f"raw or sensitive verification text is not allowed: {key}")


def _contains_sensitive_assignment(value: str) -> bool:
    for match in SENSITIVE_LABEL_PATTERN.finditer(value):
        name = match.group(1)
        camel_split_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
        parts = tuple(
            part
            for part in re.split(r"[_-]+", camel_split_name.lower())
            if part
        )
        if any(part in SENSITIVE_ASSIGNMENT_TERMS for part in parts):
            return True
    return False


def _contains_command_snippet(value: str) -> bool:
    try:
        tokens = shlex.split(value)
    except ValueError:
        return True

    normalized_tokens = tuple(token.strip() for token in tokens if token.strip())
    for index, token in enumerate(normalized_tokens[:-1]):
        normalized_token = token.lower()
        if normalized_token not in COMMAND_EXECUTABLES:
            continue
        next_token = normalized_tokens[index + 1]
        if (
            token == normalized_token
            or next_token.startswith("-")
            or next_token.lower() in COMMAND_VERBS
            or next_token.lower().endswith(".py")
            or "/" in next_token
            or "://" in next_token
        ):
            return True
    return False
